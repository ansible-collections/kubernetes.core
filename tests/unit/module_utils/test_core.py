from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

import kubernetes
import pytest
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.core import (
    AnsibleK8SModule,
)

MINIMAL_K8S_VERSION = "24.2.0"
UNSUPPORTED_K8S_VERSION = "11.0.0"


@pytest.mark.parametrize("stdin", [{}], indirect=["stdin"])
def test_no_warn(monkeypatch, stdin, capfd):
    monkeypatch.setattr(kubernetes, "__version__", MINIMAL_K8S_VERSION)

    module = AnsibleK8SModule(argument_spec={})
    with pytest.raises(SystemExit):
        module.exit_json()
    out, err = capfd.readouterr()

    return_value = json.loads(out)

    assert return_value.get("exception") is None
    assert return_value.get("warnings") is None
    assert return_value.get("failed") is None


@pytest.mark.parametrize("stdin", [{}], indirect=["stdin"])
def test_warn_on_k8s_version(monkeypatch, stdin, capfd):
    monkeypatch.setattr(kubernetes, "__version__", UNSUPPORTED_K8S_VERSION)

    module = AnsibleK8SModule(argument_spec={})
    with pytest.raises(SystemExit):
        module.exit_json()
    out, err = capfd.readouterr()

    return_value = json.loads(out)

    assert return_value.get("warnings") is not None
    warnings = return_value["warnings"]
    assert len(warnings) == 1
    assert "kubernetes" in warnings[0]
    assert MINIMAL_K8S_VERSION in warnings[0]


dependencies = [
    ["28.20.0", "24.2.1", False],
    ["28.20.0", "28.20.0", True],
    ["24.2.1", "28.20.0", True],
]


@pytest.mark.parametrize(
    "stdin,desired,actual,result", [({}, *d) for d in dependencies], indirect=["stdin"]
)
def test_has_at_least(monkeypatch, stdin, desired, actual, result, capfd):
    monkeypatch.setattr(kubernetes, "__version__", actual)

    module = AnsibleK8SModule(argument_spec={})

    assert module.has_at_least("kubernetes", desired) is result


dependencies = [
    ["kubernetes", "28.20.0", "(kubernetes>=28.20.0)"],
    ["foobar", "1.0.0", "(foobar>=1.0.0)"],
    ["foobar", None, "(foobar)"],
]


@pytest.mark.parametrize(
    "stdin,dependency,version,msg", [({}, *d) for d in dependencies], indirect=["stdin"]
)
def test_requires_fails_with_message(
    monkeypatch, stdin, dependency, version, msg, capfd
):
    monkeypatch.setattr(kubernetes, "__version__", "24.2.0")
    module = AnsibleK8SModule(argument_spec={})
    with pytest.raises(SystemExit):
        module.requires(dependency, version)
    out, err = capfd.readouterr()
    return_value = json.loads(out)

    assert return_value.get("failed")
    assert msg in return_value.get("msg")
