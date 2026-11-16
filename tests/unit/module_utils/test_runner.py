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

# Differs from the above only in metadata.resourceVersion, which diff_objects()
# treats as a match while still producing a diff.
versioned_def = deepcopy(definition)
versioned_def["metadata"]["resourceVersion"] = "1"
rereconciled_def = deepcopy(definition)
rereconciled_def["metadata"]["resourceVersion"] = "2"

NO_MEANINGFUL_DIFF = (
    "No meaningful diff was generated, but the API may not be idempotent "
    "(only metadata.generation or metadata.resourceVersion were changed)"
)


@pytest.mark.parametrize(
    "action, params, existing, instance_warnings, expected, expected_warnings",
    [
        (
            "delete",
            {"state": "absent"},
            {},
            {},
            {"changed": False, "method": "delete", "result": {}},
            [],
        ),
        (
            "delete",
            {"state": "absent"},
            definition,
            {"kind": "Status"},
            {"changed": True, "method": "delete", "result": {"kind": "Status"}},
            [],
        ),
        (
            "apply",
            {"apply": "yes"},
            {},
            (definition, []),
            {"changed": True, "method": "apply", "result": definition},
            [],
        ),
        (
            "apply",
            {"apply": "yes"},
            {},
            (definition, ["test warning"]),
            {"changed": True, "method": "apply", "result": definition},
            ["test warning"],
        ),
        (
            "create",
            {"state": "patched"},
            {},
            ({}, []),
            {"changed": False, "result": {}},
            [
                "resource 'kind=Pod,name=foo' was not found but will not be created as 'state' parameter has been set to 'patched'"
            ],
        ),
        (
            "create",
            {},
            {},
            (definition, []),
            {"changed": True, "method": "create", "result": definition},
            [],
        ),
        (
            "create",
            {},
            {},
            (definition, ["test warning"]),
            {"changed": True, "method": "create", "result": definition},
            ["test warning"],
        ),
        (
            "replace",
            {"force": "yes"},
            definition,
            (definition, []),
            {"changed": False, "method": "replace", "result": definition},
            [],
        ),
        (
            "replace",
            {"force": "yes"},
            definition,
            (modified_def, []),
            {"changed": True, "method": "replace", "result": modified_def},
            [],
        ),
        (
            "replace",
            {"force": "yes"},
            definition,
            (modified_def, ["test warning"]),
            {"changed": True, "method": "replace", "result": modified_def},
            ["test warning"],
        ),
        (
            "update",
            {},
            definition,
            (definition, []),
            {"changed": False, "method": "update", "result": definition},
            [],
        ),
        (
            "update",
            {},
            definition,
            (modified_def, []),
            {"changed": True, "method": "update", "result": modified_def},
            [],
        ),
        (
            "update",
            {},
            definition,
            (modified_def, ["test warning"]),
            {"changed": True, "method": "update", "result": modified_def},
            ["test warning"],
        ),
        (
            "update",
            {},
            versioned_def,
            (rereconciled_def, []),
            {"changed": False, "method": "update", "result": rereconciled_def},
            [NO_MEANINGFUL_DIFF],
        ),
        (
            "update",
            {},
            versioned_def,
            (rereconciled_def, ["test warning"]),
            {"changed": False, "method": "update", "result": rereconciled_def},
            ["test warning", NO_MEANINGFUL_DIFF],
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
            [],
        ),
        (
            "create",
            {"label_selectors": ["app=nginx"]},
            {},
            (definition, []),
            {"changed": True, "method": "create", "result": definition},
            [],
        ),
    ],
)
def test_perform_action(
    action, params, existing, instance_warnings, expected, expected_warnings
):
    svc = Mock()
    svc.find_resource.return_value = Mock(
        kind=definition["kind"], group_version=definition["apiVersion"]
    )
    svc.retrieve.return_value = ResourceInstance(None, existing) if existing else None
    spec = {action + ".return_value": instance_warnings}
    svc.configure_mock(**spec)

    result = perform_action(svc, definition, params)
    assert expected.items() <= result.items()

    # Warnings must be emitted through AnsibleModule.warn, never smuggled into the
    # result dict: run_module()/k8s_service unpack that dict into exit_json(), and
    # passing `warnings` to exit_json() is deprecated since ansible-core 2.19
    # (https://github.com/ansible-collections/kubernetes.core/issues/1264).
    assert "warnings" not in result
    assert [c.args[0] for c in svc.module.warn.call_args_list] == expected_warnings
