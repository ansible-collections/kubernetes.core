# -*- coding: utf-8 -*-
# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os.path
import random
import string
import tempfile
from unittest.mock import MagicMock

import pytest
import yaml
from ansible_collections.kubernetes.core.plugins.module_utils.helm import (
    AnsibleHelmModule,
    write_temp_kubeconfig,
)


@pytest.fixture()
def _ansible_helm_module():
    module = MagicMock()
    module.params = {
        "api_key": None,
        "ca_cert": None,
        "host": None,
        "kube_context": None,
        "kubeconfig": None,
        "release_namespace": None,
        "validate_certs": None,
    }
    module.fail_json = MagicMock()
    module.fail_json.side_effect = SystemExit(1)
    module.run_command = MagicMock()

    helm_module = AnsibleHelmModule(module=module)
    helm_module.get_helm_binary = MagicMock()
    helm_module.get_helm_binary.return_value = "some/path/to/helm/executable"

    return helm_module


def test_write_temp_kubeconfig_server_only():
    content = write_temp_kubeconfig("ff")

    assert content == {
        "apiVersion": "v1",
        "clusters": [{"cluster": {"server": "ff"}, "name": "generated-cluster"}],
        "contexts": [
            {"context": {"cluster": "generated-cluster"}, "name": "generated-context"}
        ],
        "current-context": "generated-context",
        "kind": "Config",
    }


def test_write_temp_kubeconfig_server_inscure_certs():
    content = write_temp_kubeconfig("ff", False, "my-certificate")

    assert content["clusters"][0]["cluster"]["insecure-skip-tls-verify"] is True
    assert (
        content["clusters"][0]["cluster"]["certificate-authority"] == "my-certificate"
    )


def test_write_temp_kubeconfig_with_kubeconfig():
    kubeconfig = {
        "apiVersion": "v1",
        "kind": "Config",
        "clusters": [
            {"cluster": {"server": "myfirstserver"}, "name": "cluster-01"},
            {"cluster": {"server": "mysecondserver"}, "name": "cluster-02"},
        ],
        "contexts": [{"context": {"cluster": "cluster-01"}, "name": "test-context"}],
        "current-context": "test-context",
    }
    content = write_temp_kubeconfig(
        server="mythirdserver",
        validate_certs=False,
        ca_cert="some-ca-cert-for-test",
        kubeconfig=kubeconfig,
    )

    expected = {
        "apiVersion": "v1",
        "kind": "Config",
        "clusters": [
            {
                "cluster": {
                    "server": "mythirdserver",
                    "insecure-skip-tls-verify": True,
                    "certificate-authority": "some-ca-cert-for-test",
                },
                "name": "cluster-01",
            },
            {
                "cluster": {
                    "server": "mythirdserver",
                    "insecure-skip-tls-verify": True,
                    "certificate-authority": "some-ca-cert-for-test",
                },
                "name": "cluster-02",
            },
        ],
        "contexts": [{"context": {"cluster": "cluster-01"}, "name": "test-context"}],
        "current-context": "test-context",
    }

    assert content == expected


def test_module_get_helm_binary_from_params():
    helm_binary_path = MagicMock()
    helm_sys_binary_path = MagicMock()

    module = MagicMock()
    module.params = {
        "binary_path": helm_binary_path,
    }
    module.get_bin_path.return_value = helm_sys_binary_path

    helm_module = AnsibleHelmModule(module=module)
    assert helm_module.get_helm_binary() == helm_binary_path


def test_module_get_helm_binary_from_system():
    helm_sys_binary_path = MagicMock()
    module = MagicMock()
    module.params = {}
    module.get_bin_path.return_value = helm_sys_binary_path

    helm_module = AnsibleHelmModule(module=module)
    assert helm_module.get_helm_binary() == helm_sys_binary_path


def test_module_get_helm_plugin_list(_ansible_helm_module):
    _ansible_helm_module.run_helm_command = MagicMock()
    _ansible_helm_module.run_helm_command.return_value = (0, "output", "error")

    rc, out, err, command = _ansible_helm_module.get_helm_plugin_list()

    assert (rc, out, err) == (0, "output", "error")
    assert command == "some/path/to/helm/executable plugin list"

    _ansible_helm_module.get_helm_binary.assert_called_once()
    _ansible_helm_module.run_helm_command.assert_called_once_with(
        "some/path/to/helm/executable plugin list"
    )


def test_module_get_helm_plugin_list_failure(_ansible_helm_module):
    _ansible_helm_module.run_helm_command = MagicMock()
    _ansible_helm_module.run_helm_command.return_value = (-1, "output", "error")

    with pytest.raises(SystemExit):
        _ansible_helm_module.get_helm_plugin_list()

    _ansible_helm_module.fail_json.assert_called_once_with(
        msg="Failed to get Helm plugin info",
        command="some/path/to/helm/executable plugin list",
        stdout="output",
        stderr="error",
        rc=-1,
    )


@pytest.mark.parametrize("no_values", [True, False])
@pytest.mark.parametrize("get_all", [True, False])
def test_module_get_values(_ansible_helm_module, no_values, get_all):
    expected = {"test": "units"}
    output = "---\ntest: units\n"

    if no_values:
        expected = {}
        output = "null"

    _ansible_helm_module.run_helm_command = MagicMock()
    _ansible_helm_module.run_helm_command.return_value = (0, output, "error")

    release_name = "".join(
        random.choice(string.ascii_letters + string.digits) for x in range(10)
    )
    result = _ansible_helm_module.get_values(release_name, get_all=get_all)

    _ansible_helm_module.get_helm_binary.assert_called_once()
    command = f"some/path/to/helm/executable get values --output=yaml {release_name}"
    if get_all:
        command += " -a"
    _ansible_helm_module.run_helm_command.assert_called_once_with(command)
    assert result == expected


@pytest.mark.parametrize(
    "output,expected",
    [
        (
            'version.BuildInfo{Version:"v3.10.3", GitCommit:7870ab3ed4135f136eec, GoVersion:"go1.18.9"}',
            "3.10.3",
        ),
        ('Client: &version.Version{SemVer:"v3.12.3", ', "3.12.3"),
        ('Client: &version.Version{SemVer:"v3.12.3"', None),
    ],
)
def test_module_get_helm_version(_ansible_helm_module, output, expected):
    _ansible_helm_module.run_command = MagicMock()
    _ansible_helm_module.run_command.return_value = (0, output, "error")

    result = _ansible_helm_module.get_helm_version()

    _ansible_helm_module.get_helm_binary.assert_called_once()
    command = "some/path/to/helm/executable version"
    _ansible_helm_module.run_command.assert_called_once_with(command)
    assert result == expected


def test_module_run_helm_command(_ansible_helm_module):
    error = "".join(
        random.choice(string.ascii_letters + string.digits) for x in range(10)
    )
    output = "".join(
        random.choice(string.ascii_letters + string.digits) for x in range(10)
    )

    _ansible_helm_module.run_command.return_value = (0, output, error)

    _ansible_helm_module._prepare_helm_environment = MagicMock()
    env_update = {x: random.choice(string.ascii_letters) for x in range(10)}
    _ansible_helm_module._prepare_helm_environment.return_value = env_update

    command = "".join(
        random.choice(string.ascii_letters + string.digits) for x in range(10)
    )
    rc, out, err = _ansible_helm_module.run_helm_command(command)

    assert (rc, out, err) == (0, output, error)

    _ansible_helm_module.run_command.assert_called_once_with(
        command, environ_update=env_update
    )


@pytest.mark.parametrize("fails_on_error", [True, False])
def test_module_run_helm_command_failure(_ansible_helm_module, fails_on_error):
    error = "".join(
        random.choice(string.ascii_letters + string.digits) for x in range(10)
    )
    output = "".join(
        random.choice(string.ascii_letters + string.digits) for x in range(10)
    )
    return_code = random.randint(1, 10)
    _ansible_helm_module.run_command.return_value = (return_code, output, error)

    _ansible_helm_module._prepare_environment = MagicMock()

    command = "".join(
        random.choice(string.ascii_letters + string.digits) for x in range(10)
    )

    if fails_on_error:
        with pytest.raises(SystemExit):
            rc, out, err = _ansible_helm_module.run_helm_command(
                command, fails_on_error=fails_on_error
            )
        _ansible_helm_module.fail_json.assert_called_with(
            msg="Failure when executing Helm command. Exited {0}.\nstdout: {1}\nstderr: {2}".format(
                return_code, output, error
            ),
            stdout=output,
            stderr=error,
            command=command,
        )
    else:
        rc, out, err = _ansible_helm_module.run_helm_command(
            command, fails_on_error=fails_on_error
        )
        assert (rc, out, err) == (return_code, output, error)


@pytest.mark.parametrize(
    "params,env_update,kubeconfig",
    [
        (
            {
                "api_key": "my-api-key",
                "host": "some-host",
                "context": "my-context",
                "release_namespace": "a-release-namespace",
            },
            {
                "HELM_KUBEAPISERVER": "some-host",
                "HELM_KUBECONTEXT": "my-context",
                "HELM_KUBETOKEN": "my-api-key",
                "HELM_NAMESPACE": "a-release-namespace",
            },
            False,
        ),
        ({"kubeconfig": {"kube": "config"}}, {}, True),
        ({"kubeconfig": "path_to_a_config_file"}, {}, True),
    ],
)
def test_module_prepare_helm_environment(params, env_update, kubeconfig):
    module = MagicMock()
    module.params = params

    helm_module = AnsibleHelmModule(module=module)

    p_kubeconfig = params.get("kubeconfig")
    tmpfile_name = None
    if isinstance(p_kubeconfig, str):
        _fd, tmpfile_name = tempfile.mkstemp()
        with os.fdopen(_fd, "w") as fp:
            yaml.dump({"some_custom": "kube_config"}, fp)
        params["kubeconfig"] = tmpfile_name

    result = helm_module._prepare_helm_environment()

    kubeconfig_path = result.pop("KUBECONFIG", None)

    assert env_update == result

    if kubeconfig:
        assert os.path.exists(kubeconfig_path)
        if not tmpfile_name:
            module.add_cleanup_file.assert_called_with(kubeconfig_path)
    else:
        assert kubeconfig_path is None

    if tmpfile_name:
        os.remove(tmpfile_name)


@pytest.mark.parametrize(
    "helm_version, is_env_var_set",
    [
        ("3.10.1", True),
        ("3.10.0", True),
        ("3.5.0", False),
        ("3.8.0", False),
        ("3.9.35", False),
    ],
)
def test_module_prepare_helm_environment_with_validate_certs(
    helm_version, is_env_var_set
):
    module = MagicMock()
    module.params = {"validate_certs": False}

    helm_module = AnsibleHelmModule(module=module)
    helm_module.get_helm_version = MagicMock()
    helm_module.get_helm_version.return_value = helm_version

    result = helm_module._prepare_helm_environment()

    if is_env_var_set:
        assert result == {"HELM_KUBEINSECURE_SKIP_TLS_VERIFY": "true"}
    else:
        assert list(result.keys()) == ["KUBECONFIG"]
        kubeconfig_path = result["KUBECONFIG"]
        assert os.path.exists(kubeconfig_path)

        with open(kubeconfig_path) as fd:
            content = yaml.safe_load(fd)
            assert content["clusters"][0]["cluster"]["insecure-skip-tls-verify"] is True
        os.remove(kubeconfig_path)


@pytest.mark.parametrize(
    "helm_version, is_env_var_set",
    [
        ("3.10.0", True),
        ("3.5.0", True),
        ("3.4.9", False),
    ],
)
def test_module_prepare_helm_environment_with_ca_cert(helm_version, is_env_var_set):
    ca_cert = "".join(
        random.choice(string.ascii_letters + string.digits) for i in range(50)
    )
    module = MagicMock()
    module.params = {"ca_cert": ca_cert}

    helm_module = AnsibleHelmModule(module=module)
    helm_module.get_helm_version = MagicMock()
    helm_module.get_helm_version.return_value = helm_version

    result = helm_module._prepare_helm_environment()

    if is_env_var_set:
        assert list(result.keys()) == ["HELM_KUBECAFILE"]
        assert result["HELM_KUBECAFILE"] == ca_cert
    else:
        assert list(result.keys()) == ["KUBECONFIG"]
        kubeconfig_path = result["KUBECONFIG"]
        assert os.path.exists(kubeconfig_path)

        with open(kubeconfig_path) as fd:
            content = yaml.safe_load(fd)
            import json

            print(json.dumps(content, indent=2))
            assert content["clusters"][0]["cluster"]["certificate-authority"] == ca_cert
        os.remove(kubeconfig_path)


@pytest.mark.parametrize(
    "set_values, expected",
    [
        ([{"value": "test"}], ["--set test"]),
        ([{"value_type": "raw", "value": "test"}], ["--set test"]),
        (
            [{"value_type": "string", "value": "string_value"}],
            ["--set-string 'string_value'"],
        ),
        ([{"value_type": "file", "value": "file_path"}], ["--set-file 'file_path'"]),
        (
            [{"value_type": "json", "value": '{"a": 1, "b": "some_value"}'}],
            ['--set-json \'{"a": 1, "b": "some_value"}\''],
        ),
        (
            [
                {"value_type": "string", "value": "string_value"},
                {"value_type": "file", "value": "file_path"},
            ],
            ["--set-string 'string_value'", "--set-file 'file_path'"],
        ),
    ],
)
def test_module_get_helm_set_values_args(set_values, expected):
    module = MagicMock()
    module.params = {}
    module.fail_json.side_effect = SystemExit(1)

    helm_module = AnsibleHelmModule(module=module)
    helm_module.get_helm_version = MagicMock()
    helm_module.get_helm_version.return_value = "3.10.1"

    result = helm_module.get_helm_set_values_args(set_values)
    assert " ".join(expected) == result
