import pytest
from unittest.mock import MagicMock, call

from ansible_collections.kubernetes.core.plugins.module_utils.k8s.runner import (
    perform_action,
)

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


@pytest.mark.parametrize(
    "params, expected",
    [
        ({"state": "absent"}, call.__setitem__("method", "delete")),
        ({"apply": True}, call.__setitem__("method", "apply")),
        ({"force": True}, call.__setitem__("method", "replace")),
        ({"apply": False}, call.__setitem__("method", "update")),
        ({}, call.__setitem__("method", "update")),
    ],
)
def test_perform_action(params, expected):
    module = MagicMock()
    module.params = params

    result = perform_action(MagicMock(), definition, module.params)
    result.assert_has_calls([expected], any_order=True)


def test_perform_action_create():
    spec = {"retrieve.side_effect": [{}]}
    svc = MagicMock(**spec)
    module = MagicMock()
    module.params = {}

    result = perform_action(svc, definition, module.params)
    result.assert_has_calls([call.__setitem__("method", "create")], any_order=True)
