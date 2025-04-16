from copy import deepcopy
from unittest.mock import Mock

import pytest
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.runner import (
    perform_action,
)
from kubernetes.dynamic.resource import ResourceInstance

definition = {
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

modified_def = deepcopy(definition)
modified_def["metadata"]["labels"]["environment"] = "testing"


@pytest.mark.parametrize(
    "action, params, existing, instance_warnings, expected",
    [
        (
            "delete",
            {"state": "absent"},
            {},
            {},
            {"changed": False, "method": "delete", "result": {}},
        ),
        (
            "delete",
            {"state": "absent"},
            definition,
            {"kind": "Status"},
            {"changed": True, "method": "delete", "result": {"kind": "Status"}},
        ),
        (
            "apply",
            {"apply": "yes"},
            {},
            (definition, []),
            {"changed": True, "method": "apply", "result": definition},
        ),
        (
            "apply",
            {"apply": "yes"},
            {},
            (definition, ["test warning"]),
            {
                "changed": True,
                "method": "apply",
                "result": definition,
                "warnings": ["test warning"],
            },
        ),
        (
            "create",
            {"state": "patched"},
            {},
            ({}, []),
            {
                "changed": False,
                "result": {},
                "warnings": [
                    "resource 'kind=Pod,name=foo' was not found but will not be created as 'state' parameter has been set to 'patched'"
                ],
            },
        ),
        (
            "create",
            {},
            {},
            (definition, []),
            {"changed": True, "method": "create", "result": definition},
        ),
        (
            "create",
            {},
            {},
            (definition, ["test warning"]),
            {
                "changed": True,
                "method": "create",
                "result": definition,
                "warnings": ["test warning"],
            },
        ),
        (
            "replace",
            {"force": "yes"},
            definition,
            (definition, []),
            {"changed": False, "method": "replace", "result": definition},
        ),
        (
            "replace",
            {"force": "yes"},
            definition,
            (modified_def, []),
            {"changed": True, "method": "replace", "result": modified_def},
        ),
        (
            "replace",
            {"force": "yes"},
            definition,
            (modified_def, ["test warning"]),
            {
                "changed": True,
                "method": "replace",
                "result": modified_def,
                "warnings": ["test warning"],
            },
        ),
        (
            "update",
            {},
            definition,
            (definition, []),
            {"changed": False, "method": "update", "result": definition},
        ),
        (
            "update",
            {},
            definition,
            (modified_def, []),
            {"changed": True, "method": "update", "result": modified_def},
        ),
        (
            "update",
            {},
            definition,
            (modified_def, ["test warning"]),
            {
                "changed": True,
                "method": "update",
                "result": modified_def,
                "warnings": ["test warning"],
            },
        ),
        (
            "create",
            {"label_selectors": ["app=foo"]},
            {},
            (definition, []),
            {
                "changed": False,
                "msg": "resource 'kind=Pod,name=foo,namespace=foo' filtered by label_selectors.",
            },
        ),
        (
            "create",
            {"label_selectors": ["app=nginx"]},
            {},
            (definition, []),
            {"changed": True, "method": "create", "result": definition},
        ),
    ],
)
def test_perform_action(action, params, existing, instance_warnings, expected):
    svc = Mock()
    svc.find_resource.return_value = Mock(
        kind=definition["kind"], group_version=definition["apiVersion"]
    )
    svc.retrieve.return_value = ResourceInstance(None, existing) if existing else None
    spec = {action + ".return_value": instance_warnings}
    svc.configure_mock(**spec)

    result = perform_action(svc, definition, params)
    assert expected.items() <= result.items()
