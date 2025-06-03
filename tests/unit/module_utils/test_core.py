from __future__ import absolute_import, division, print_function

__metaclass__ = type

import re

import kubernetes
import pytest
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.core import (
    AnsibleK8SModule,
)
from mock import MagicMock, patch

MINIMAL_K8S_VERSION = "24.2.0"
UNSUPPORTED_K8S_VERSION = "11.0.0"


class FakeAnsibleModule:
    def __init__(self, **kwargs):
        pass

    def exit_json(self):
        raise SystemExit(0)


@patch.object(AnsibleK8SModule, "warn")
def test_no_warn(m_ansible_k8s_module_warn, monkeypatch, capfd):
    monkeypatch.setattr(kubernetes, "__version__", MINIMAL_K8S_VERSION)

    m_ansible_k8s_module_warn.side_effect = print
    module = AnsibleK8SModule(argument_spec={}, module_class=FakeAnsibleModule)
    with pytest.raises(SystemExit):
        module.exit_json()
    out, err = capfd.readouterr()
    m_ansible_k8s_module_warn.assert_not_called()


@patch.object(AnsibleK8SModule, "warn")
def test_warn_on_k8s_version(m_ansible_k8s_module_warn, monkeypatch, capfd):
    monkeypatch.setattr(kubernetes, "__version__", UNSUPPORTED_K8S_VERSION)

    m_ansible_k8s_module_warn.side_effect = print
    module = AnsibleK8SModule(argument_spec={}, module_class=FakeAnsibleModule)
    with pytest.raises(SystemExit):
        module.exit_json()

    m_ansible_k8s_module_warn.assert_called_once()
    out, err = capfd.readouterr()
    assert (
        re.search(
            r"kubernetes<([0-9]+\.[0-9]+\.[0-9]+) is not supported or tested. Some features may not work.",
            out,
        )
        is not None
    )


dependencies = [
    ["28.20.0", "24.2.1", False],
    ["28.20.0", "28.20.0", True],
    ["24.2.1", "28.20.0", True],
]


@pytest.mark.parametrize(
    "stdin,desired,actual,result", [({}, *d) for d in dependencies], indirect=["stdin"]
)
@patch.object(AnsibleK8SModule, "warn")
def test_has_at_least(
    m_ansible_k8s_module_warn, monkeypatch, stdin, desired, actual, result, capfd
):
    monkeypatch.setattr(kubernetes, "__version__", actual)

    def fake_warn(x):
        print(x)
        raise SystemExit(1)

    m_ansible_k8s_module_warn.side_effect = fake_warn
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
    module = AnsibleK8SModule(argument_spec={}, module_class=FakeAnsibleModule)

    def fake_fail_json(**kwargs):
        print(f"Printing message => {kwargs}")
        print(kwargs.get("msg"))
        raise SystemExit(1)

    module.fail_json = MagicMock()
    module.fail_json.side_effect = fake_fail_json

    with pytest.raises(SystemExit):
        module.requires(dependency, version)
    module.fail_json.assert_called_once()
    out, err = capfd.readouterr()
    assert msg in out
