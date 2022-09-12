# -*- coding: utf-8 -*-
# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os.path
import yaml
import tempfile
import json


from ansible_collections.kubernetes.core.plugins.module_utils.helm import (
    run_helm,
    write_temp_kubeconfig,
)


class MockedModule:
    def __init__(self):

        self.params = {
            "api_key": None,
            "ca_cert": None,
            "host": None,
            "kube_context": None,
            "kubeconfig": None,
            "release_namespace": None,
            "validate_certs": None,
        }

        self.r = {}
        self.files_to_delete = []

    def run_command(self, command, environ_update=None):
        self.r = {"command": command, "environ_update": environ_update}
        return 0, "", ""

    def add_cleanup_file(self, file_path):
        self.files_to_delete.append(file_path)

    def do_cleanup_files(self):
        for file in self.files_to_delete:
            try:
                os.remove(file)
            except Exception:
                pass


def test_write_temp_kubeconfig_server_only():
    file_name = write_temp_kubeconfig("ff")
    try:
        with open(file_name, "r") as fd:
            content = yaml.safe_load(fd)
    finally:
        os.remove(file_name)

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
    file_name = write_temp_kubeconfig("ff", False, "my-certificate")
    try:
        with open(file_name, "r") as fd:
            content = yaml.safe_load(fd)
    finally:
        os.remove(file_name)

    assert content["clusters"][0]["cluster"]["insecure-skip-tls-verify"] is True
    assert (
        content["clusters"][0]["cluster"]["certificate-authority"] == "my-certificate"
    )


def test_run_helm_naked():
    module = MockedModule()
    run_helm(module, "helm foo")

    assert module.r["command"] == "helm foo"
    assert module.r["environ_update"] == {}


def test_run_helm_with_params():
    module = MockedModule()
    module.params = {
        "api_key": "my-api-key",
        "ca_cert": "my-ca-cert",
        "host": "some-host",
        "context": "my-context",
        "release_namespace": "a-release-namespace",
        "validate_certs": False,
    }

    run_helm(module, "helm foo")

    assert module.r["command"] == "helm foo"
    assert module.r["environ_update"]["HELM_KUBEAPISERVER"] == "some-host"
    assert module.r["environ_update"]["HELM_KUBECONTEXT"] == "my-context"
    assert module.r["environ_update"]["HELM_KUBETOKEN"] == "my-api-key"
    assert module.r["environ_update"]["HELM_NAMESPACE"] == "a-release-namespace"
    assert module.r["environ_update"]["KUBECONFIG"]
    assert os.path.exists(module.r["environ_update"]["KUBECONFIG"])
    module.do_cleanup_files()


def test_run_helm_with_kubeconfig():

    custom_config = {
        "apiVersion": "v1",
        "clusters": [
            {
                "cluster": {
                    "certificate-authority-data": "LS0tLS1CRUdJTiBDRV",
                    "server": "https://api.cluster.testing:6443",
                },
                "name": "api-cluster-testing:6443",
            }
        ],
        "contexts": [
            {
                "context": {
                    "cluster": "api-cluster-testing:6443",
                    "namespace": "default",
                    "user": "kubeadmin",
                },
                "name": "context-1",
            }
        ],
        "current-context": "context-1",
        "kind": "Config",
        "users": [
            {
                "name": "developer",
                "user": {"token": "sha256~jbIvVieBC_8W6Pb-iH5vqC_BvvPHIxQMxUPLDnYvHYM"},
            }
        ],
    }

    # kubeconfig defined as path
    _fd, tmpfile_name = tempfile.mkstemp()
    with os.fdopen(_fd, "w") as fp:
        yaml.dump(custom_config, fp)

    k1_module = MockedModule()
    k1_module.params = {"kubeconfig": tmpfile_name}
    run_helm(k1_module, "helm foo")
    assert k1_module.r["environ_update"] == {"KUBECONFIG": tmpfile_name}
    os.remove(tmpfile_name)

    # kubeconfig defined as string
    k2_module = MockedModule()
    k2_module.params = {"kubeconfig": custom_config}
    run_helm(k2_module, "helm foo")

    assert os.path.exists(k2_module.r["environ_update"]["KUBECONFIG"])
    with open(k2_module.r["environ_update"]["KUBECONFIG"]) as f:
        assert json.loads(f.read()) == custom_config
    k2_module.do_cleanup_files()
