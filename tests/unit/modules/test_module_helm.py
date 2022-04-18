# -*- coding: utf-8 -*-
# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.kubernetes.core.plugins.modules.helm import (
    run_dep_update
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

    def run_command(self, command, environ_update=None):
        self.r = {"command": command, "environ_update": environ_update}
        return 0, "", ""


def test_dependency_update_naked():
    module = MockedModule()
    module.params = {}
    common_cmd = "helm"
    chart_ref = "/tmp/path/chart"
    run_dep_update(module, common_cmd, chart_ref)
    assert module.r["command"] == "helm dependency update /tmp/path/chart"
    assert module.r["environ_update"] == {}
