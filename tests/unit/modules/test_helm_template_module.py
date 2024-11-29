# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import unittest
from unittest.mock import patch

from ansible.module_utils import basic
from ansible_collections.kubernetes.core.plugins.modules import helm_template
from ansible_collections.kubernetes.core.tests.unit.utils.ansible_module_mock import (
    AnsibleExitJson,
    AnsibleFailJson,
    exit_json,
    fail_json,
    get_bin_path,
    set_module_args,
)


class TestDependencyUpdateWithoutChartRepoUrlOption(unittest.TestCase):
    def setUp(self):
        self.mock_module_helper = patch.multiple(
            basic.AnsibleModule,
            exit_json=exit_json,
            fail_json=fail_json,
            get_bin_path=get_bin_path,
        )
        self.mock_module_helper.start()

        # Stop the patch after test execution
        # like tearDown but executed also when the setup failed
        self.addCleanup(self.mock_module_helper.stop)

    def test_module_fail_when_required_args_missing(self):
        with self.assertRaises(AnsibleFailJson):
            set_module_args({})
            helm_template.main()

    def test_dependency_update_option_not_defined(self):
        set_module_args({"chart_ref": "/tmp/path"})
        with patch.object(basic.AnsibleModule, "run_command") as mock_run_command:
            mock_run_command.return_value = (
                0,
                "configuration updated",
                "",
            )  # successful execution
            with self.assertRaises(AnsibleExitJson) as result:
                helm_template.main()
        mock_run_command.assert_called_once_with(
            "/usr/bin/helm template /tmp/path", environ_update={}, data=None
        )
        assert result.exception.args[0]["command"] == "/usr/bin/helm template /tmp/path"

    def test_dependency_update_option_false(self):
        set_module_args(
            {
                "chart_ref": "test",
                "chart_repo_url": "https://charts.com/test",
                "dependency_update": False,
            }
        )
        with patch.object(basic.AnsibleModule, "run_command") as mock_run_command:
            mock_run_command.return_value = (
                0,
                "configuration updated",
                "",
            )  # successful execution
            with self.assertRaises(AnsibleExitJson) as result:
                helm_template.main()
        mock_run_command.assert_called_once_with(
            "/usr/bin/helm template test --repo=https://charts.com/test",
            environ_update={},
            data=None,
        )
        assert (
            result.exception.args[0]["command"]
            == "/usr/bin/helm template test --repo=https://charts.com/test"
        )

    def test_dependency_update_option_true(self):
        set_module_args(
            {"chart_ref": "https://charts/example.tgz", "dependency_update": True}
        )
        with patch.object(basic.AnsibleModule, "run_command") as mock_run_command:
            mock_run_command.return_value = (
                0,
                "configuration updated",
                "",
            )  # successful execution
            with self.assertRaises(AnsibleExitJson) as result:
                helm_template.main()
        mock_run_command.assert_called_once_with(
            "/usr/bin/helm template https://charts/example.tgz --dependency-update",
            environ_update={},
            data=None,
        )
        assert (
            result.exception.args[0]["command"]
            == "/usr/bin/helm template https://charts/example.tgz --dependency-update"
        )
