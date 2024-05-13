from json import dumps
from unittest.mock import Mock

import pytest
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.service import (
    K8sService,
    diff_objects,
    parse_quoted_string,
)
from kubernetes.dynamic.exceptions import NotFoundError
from kubernetes.dynamic.resource import Resource, ResourceInstance

pod_definition = {
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {
        "name": "foo",
        "labels": {"environment": "production", "app": "nginx"},
        "namespace": "foo",
    },
    "spec": {
        "containers": [
            {
                "name": "nginx",
                "image": "nginx:1.14.2",
                "command": ["/bin/sh", "-c", "sleep 10"],
            }
        ]
    },
}

pod_definition_updated = {
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {
        "name": "foo",
        "labels": {"environment": "testing", "app": "nginx"},
        "namespace": "bar",
    },
    "spec": {
        "containers": [
            {
                "name": "nginx",
                "image": "nginx:1.14.2",
                "command": ["/bin/sh", "-c", "sleep 10"],
            }
        ]
    },
}


@pytest.fixture(scope="module")
def mock_pod_resource_instance():
    return ResourceInstance(None, pod_definition)


@pytest.fixture(scope="module")
def mock_pod_updated_resource_instance():
    return ResourceInstance(None, pod_definition_updated)


@pytest.fixture(scope="module")
def mock_pod_response():
    resp = Mock()
    resp.data.decode.return_value = dumps(pod_definition)
    resp.headers = {}
    return resp


@pytest.fixture(scope="module")
def mock_pod_warnings_response():
    resp = Mock()
    resp.data.decode.return_value = dumps(pod_definition)
    resp.headers = {"warning": '299 - "test warning 1", 299 - "test warning 2"'}
    return resp


def test_diff_objects_no_diff():
    match, diff = diff_objects(pod_definition, pod_definition)

    assert match is True
    assert diff == {}


def test_diff_objects_meta_diff():
    match, diff = diff_objects(pod_definition, pod_definition_updated)

    assert match is False
    assert diff["before"] == {
        "metadata": {"labels": {"environment": "production"}, "namespace": "foo"}
    }
    assert diff["after"] == {
        "metadata": {"labels": {"environment": "testing"}, "namespace": "bar"}
    }


def test_diff_objects_spec_diff():
    pod_definition_updated = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": "foo",
            "labels": {"environment": "production", "app": "nginx"},
            "namespace": "foo",
        },
        "spec": {
            "containers": [
                {
                    "name": "busybox",
                    "image": "busybox",
                    "command": ["/bin/sh", "-c", "sleep 3600"],
                }
            ]
        },
    }
    match, diff = diff_objects(pod_definition, pod_definition_updated)

    assert match is False
    assert diff["before"]["spec"] == pod_definition["spec"]
    assert diff["after"]["spec"] == pod_definition_updated["spec"]


def test_find_resource():
    mock_pod_resource = Resource(
        api_version="v1", kind="Pod", namespaced=False, preferred=True, prefix="api"
    )
    spec = {"resource.return_value": mock_pod_resource}
    client = Mock(**spec)
    svc = K8sService(client, Mock())
    resource = svc.find_resource("Pod", "v1")

    assert isinstance(resource, Resource)
    assert resource.to_dict().items() <= mock_pod_resource.to_dict().items()


def test_service_delete_existing_resource(mock_pod_resource_instance):
    spec = {"delete.side_effect": [mock_pod_resource_instance]}
    client = Mock(**spec)
    module = Mock(
        params={"delete_options": {"gracePeriodSeconds": 2}}, check_mode=False
    )
    resource = Mock()
    svc = K8sService(client, module)
    result = svc.delete(resource, pod_definition, mock_pod_resource_instance)

    assert isinstance(result, dict)
    assert result == mock_pod_resource_instance.to_dict()
    client.delete.assert_called_with(
        resource,
        name=pod_definition["metadata"]["name"],
        namespace=pod_definition["metadata"]["namespace"],
        body={"apiVersion": "v1", "kind": "DeleteOptions", "gracePeriodSeconds": 2},
    )


def test_service_delete_no_existing_resource():
    module = Mock()
    module.params = {}
    module.check_mode = False
    client = Mock()
    client.delete.return_value = mock_pod_resource_instance
    svc = K8sService(client, module)
    result = svc.delete(Mock(), pod_definition)

    assert result == {}
    client.delete.assert_not_called()


def test_service_delete_existing_resource_check_mode(mock_pod_resource_instance):
    module = Mock(params={}, check_mode=True)
    client = Mock(dry_run=False)
    client.delete.return_value = mock_pod_resource_instance
    svc = K8sService(client, module)
    result = svc.delete(Mock(), pod_definition, mock_pod_resource_instance)

    assert result == {}
    client.delete.assert_not_called()


def test_service_create_resource(mock_pod_response, mock_pod_resource_instance):
    spec = {"create.side_effect": [mock_pod_response]}
    client = Mock(**spec)
    module = Mock()
    module.params = {}
    module.check_mode = False
    svc = K8sService(client, module)
    result, warnings = svc.create(Mock(), pod_definition)

    assert result == mock_pod_resource_instance.to_dict()
    assert not warnings


def test_service_create_resource_warnings(
    mock_pod_warnings_response, mock_pod_resource_instance
):
    spec = {"create.side_effect": [mock_pod_warnings_response]}
    client = Mock(**spec)
    module = Mock()
    module.params = {}
    module.check_mode = False
    svc = K8sService(client, module)
    result, warnings = svc.create(Mock(), pod_definition)

    assert result == mock_pod_resource_instance.to_dict()
    assert warnings[0] == "test warning 1"
    assert warnings[1] == "test warning 2"


def test_service_create_resource_check_mode():
    client = Mock(dry_run=False)
    client.create.return_value = mock_pod_resource_instance
    module = Mock(params={}, check_mode=True)
    svc = K8sService(client, module)
    result, warnings = svc.create(Mock(), pod_definition)

    assert result == pod_definition
    assert not warnings
    client.create.assert_not_called()


def test_service_retrieve_existing_resource(mock_pod_resource_instance):
    spec = {"get.side_effect": [mock_pod_resource_instance]}
    client = Mock(**spec)
    module = Mock()
    module.params = {}
    svc = K8sService(client, module)
    results = svc.retrieve(Mock(), pod_definition)

    assert isinstance(results, ResourceInstance)
    assert results.to_dict() == pod_definition


def test_service_retrieve_no_existing_resource():
    spec = {"get.side_effect": [NotFoundError(Mock())]}
    client = Mock(**spec)
    module = Mock()
    module.params = {}
    svc = K8sService(client, module)
    results = svc.retrieve(Mock(), pod_definition)

    assert results is None


def test_create_project_request():
    project_definition = {
        "apiVersion": "v1",
        "kind": "ProjectRequest",
        "metadata": {"name": "test"},
    }
    spec = {"create.side_effect": [ResourceInstance(None, project_definition)]}
    client = Mock(**spec)
    module = Mock()
    module.check_mode = False
    module.params = {"state": "present"}
    svc = K8sService(client, module)
    results = svc.create_project_request(project_definition)

    assert isinstance(results, dict)
    assert results["changed"] is True
    assert results["result"] == project_definition


def test_service_apply_existing_resource(mock_pod_response, mock_pod_resource_instance):
    spec = {"apply.side_effect": [mock_pod_response]}
    client = Mock(**spec)
    module = Mock()
    module.params = {"apply": True}
    module.check_mode = False
    svc = K8sService(client, module)
    result, warnings = svc.apply(
        Mock(), pod_definition_updated, mock_pod_resource_instance
    )

    assert result == mock_pod_resource_instance.to_dict()
    assert not warnings


def test_service_apply_existing_resource_warnings(
    mock_pod_warnings_response, mock_pod_resource_instance
):
    spec = {"apply.side_effect": [mock_pod_warnings_response]}
    client = Mock(**spec)
    module = Mock()
    module.params = {"apply": True}
    module.check_mode = False
    svc = K8sService(client, module)
    result, warnings = svc.apply(
        Mock(), pod_definition_updated, mock_pod_resource_instance
    )

    assert result == mock_pod_resource_instance.to_dict()
    assert warnings[0] == "test warning 1"
    assert warnings[1] == "test warning 2"


def test_service_replace_existing_resource(
    mock_pod_response, mock_pod_resource_instance
):
    spec = {"replace.side_effect": [mock_pod_response]}
    client = Mock(**spec)
    module = Mock()
    module.params = {}
    module.check_mode = False
    svc = K8sService(client, module)
    result, warnings = svc.replace(Mock(), pod_definition, mock_pod_resource_instance)

    assert result == mock_pod_resource_instance.to_dict()
    assert not warnings


def test_service_replace_existing_resource_warnings(
    mock_pod_warnings_response, mock_pod_resource_instance
):
    spec = {"replace.side_effect": [mock_pod_warnings_response]}
    client = Mock(**spec)
    module = Mock()
    module.params = {}
    module.check_mode = False
    svc = K8sService(client, module)
    result, warnings = svc.replace(Mock(), pod_definition, mock_pod_resource_instance)

    assert result == mock_pod_resource_instance.to_dict()
    assert warnings[0] == "test warning 1"
    assert warnings[1] == "test warning 2"


def test_service_update_existing_resource(
    mock_pod_response, mock_pod_resource_instance
):
    spec = {"replace.side_effect": [mock_pod_response]}
    client = Mock(**spec)
    module = Mock()
    module.params = {}
    module.check_mode = False
    svc = K8sService(client, module)
    result, warnings = svc.replace(Mock(), pod_definition, mock_pod_resource_instance)

    assert result == mock_pod_resource_instance.to_dict()
    assert not warnings


def test_service_update_existing_resource_warnings(
    mock_pod_warnings_response, mock_pod_resource_instance
):
    spec = {"replace.side_effect": [mock_pod_warnings_response]}
    client = Mock(**spec)
    module = Mock()
    module.params = {}
    module.check_mode = False
    svc = K8sService(client, module)
    result, warnings = svc.replace(Mock(), pod_definition, mock_pod_resource_instance)

    assert result == mock_pod_resource_instance.to_dict()
    assert warnings[0] == "test warning 1"
    assert warnings[1] == "test warning 2"


def test_service_find(mock_pod_resource_instance):
    spec = {"get.side_effect": [mock_pod_resource_instance]}
    client = Mock(**spec)
    module = Mock()
    module.params = {}
    module.check_mode = False
    svc = K8sService(client, module)
    results = svc.find("Pod", "v1", name="foo", namespace="foo")

    assert isinstance(results, dict)
    assert results["api_found"] is True
    assert results["resources"] is not []
    assert len(results["resources"]) == 1
    assert results["resources"][0] == pod_definition


def test_service_find_error():
    spec = {"get.side_effect": [NotFoundError(Mock())]}
    client = Mock(**spec)
    module = Mock()
    module.params = {}
    module.check_mode = False
    svc = K8sService(client, module)
    results = svc.find("Pod", "v1", name="foo", namespace="foo")

    assert isinstance(results, dict)
    assert results["api_found"] is True
    assert results["resources"] == []


@pytest.mark.parametrize(
    "quoted_string,expected_val,expected_remainder",
    [
        (
            '"Response is stale" Tue, 15 Nov 1994 12:45:26 GMT',
            "Response is stale",
            "Tue, 15 Nov 1994 12:45:26 GMT",
        ),
        (
            '"unknown field \\"spec.template.spec.disk\\""',
            'unknown field "spec.template.spec.disk"',
            "",
        ),
    ],
)
def test_parse_quoted_string(quoted_string, expected_val, expected_remainder):
    val, remainder = parse_quoted_string(quoted_string)
    assert val == expected_val
    assert remainder == expected_remainder
