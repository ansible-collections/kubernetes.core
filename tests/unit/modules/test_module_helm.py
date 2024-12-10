# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import unittest
from unittest.mock import MagicMock, call, patch

from ansible.module_utils import basic
from ansible_collections.kubernetes.core.plugins.modules import helm
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

        self.chart_info_without_dep = {
            "apiVersion": "v2",
            "appVersion": "default",
            "description": "A chart used in molecule tests",
            "name": "test-chart",
            "type": "application",
            "version": "0.1.0",
        }

        self.chart_info_with_dep = {
            "apiVersion": "v2",
            "appVersion": "default",
            "description": "A chart used in molecule tests",
            "name": "test-chart",
            "type": "application",
            "version": "0.1.0",
            "dependencies": [
                {
                    "name": "test",
                    "version": "0.1.0",
                    "repository": "file://../test-chart",
                }
            ],
        }

    def test_module_fail_when_required_args_missing(self):
        with self.assertRaises(AnsibleFailJson):
            set_module_args({})
            helm.main()

    def test_dependency_update_option_not_defined(self):
        set_module_args(
            {
                "release_name": "test",
                "release_namespace": "test",
                "chart_ref": "/tmp/path",
            }
        )
        helm.get_release_status = MagicMock(return_value=None)
        helm.fetch_chart_info = MagicMock(return_value=self.chart_info_without_dep)
        helm.run_dep_update = MagicMock()
        with patch.object(basic.AnsibleModule, "run_command") as mock_run_command:
            mock_run_command.return_value = (
                0,
                "configuration updated",
                "",
            )  # successful execution
            with self.assertRaises(AnsibleExitJson) as result:
                helm.main()
        helm.run_dep_update.assert_not_called()
        mock_run_command.assert_called_once_with(
            "/usr/bin/helm upgrade -i --reset-values test '/tmp/path'",
            environ_update={"HELM_NAMESPACE": "test"},
            data=None,
        )
        assert (
            result.exception.args[0]["command"]
            == "/usr/bin/helm upgrade -i --reset-values test '/tmp/path'"
        )

    def test_dependency_update_option_false(self):
        set_module_args(
            {
                "release_name": "test",
                "release_namespace": "test",
                "chart_ref": "/tmp/path",
                "dependency_update": False,
            }
        )
        helm.get_release_status = MagicMock(return_value=None)
        helm.fetch_chart_info = MagicMock(return_value=self.chart_info_without_dep)
        helm.run_dep_update = MagicMock()
        with patch.object(basic.AnsibleModule, "run_command") as mock_run_command:
            mock_run_command.return_value = (
                0,
                "configuration updated",
                "",
            )  # successful execution
            with self.assertRaises(AnsibleExitJson) as result:
                helm.main()
        helm.run_dep_update.assert_not_called()
        mock_run_command.assert_called_once_with(
            "/usr/bin/helm upgrade -i --reset-values test '/tmp/path'",
            environ_update={"HELM_NAMESPACE": "test"},
            data=None,
        )
        assert (
            result.exception.args[0]["command"]
            == "/usr/bin/helm upgrade -i --reset-values test '/tmp/path'"
        )

    def test_dependency_update_option_true(self):
        set_module_args(
            {
                "release_name": "test",
                "release_namespace": "test",
                "chart_ref": "/tmp/path",
                "dependency_update": True,
            }
        )
        helm.get_release_status = MagicMock(return_value=None)
        helm.fetch_chart_info = MagicMock(return_value=self.chart_info_with_dep)

        with patch.object(basic.AnsibleModule, "run_command") as mock_run_command:
            mock_run_command.return_value = 0, "configuration updated", ""
            with patch.object(basic.AnsibleModule, "warn") as mock_warn:
                with self.assertRaises(AnsibleExitJson) as result:
                    helm.main()
        mock_warn.assert_not_called()
        mock_run_command.assert_has_calls(
            [
                call(
                    "/usr/bin/helm upgrade -i --reset-values test '/tmp/path'",
                    environ_update={"HELM_NAMESPACE": "test"},
                    data=None,
                )
            ]
        )
        assert (
            result.exception.args[0]["command"]
            == "/usr/bin/helm upgrade -i --reset-values test '/tmp/path'"
        )

    def test_dependency_update_option_true_without_dependencies_block(self):
        set_module_args(
            {
                "release_name": "test",
                "release_namespace": "test",
                "chart_ref": "/tmp/path",
                "dependency_update": True,
            }
        )
        helm.get_release_status = MagicMock(return_value=None)
        helm.fetch_chart_info = MagicMock(return_value=self.chart_info_without_dep)
        with patch.object(basic.AnsibleModule, "run_command") as mock_run_command:
            mock_run_command.return_value = (
                0,
                "configuration updated",
                "",
            )  # successful execution
            with patch.object(basic.AnsibleModule, "warn") as mock_warn:
                with self.assertRaises(AnsibleExitJson) as result:
                    helm.main()
        mock_warn.assert_called_once()
        mock_run_command.assert_has_calls(
            [
                call(
                    "/usr/bin/helm upgrade -i --reset-values test '/tmp/path'",
                    environ_update={"HELM_NAMESPACE": "test"},
                    data=None,
                )
            ]
        )
        assert (
            result.exception.args[0]["command"]
            == "/usr/bin/helm upgrade -i --reset-values test '/tmp/path'"
        )


class TestDependencyUpdateWithChartRepoUrlOption(unittest.TestCase):
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

        self.chart_info_without_dep = {
            "apiVersion": "v2",
            "appVersion": "default",
            "description": "A chart used in molecule tests",
            "name": "test-chart",
            "type": "application",
            "version": "0.1.0",
        }

        self.chart_info_with_dep = {
            "apiVersion": "v2",
            "appVersion": "default",
            "description": "A chart used in molecule tests",
            "name": "test-chart",
            "type": "application",
            "version": "0.1.0",
            "dependencies": [
                {
                    "name": "test",
                    "version": "0.1.0",
                    "repository": "file://../test-chart",
                }
            ],
        }

    def test_dependency_update_option_not_defined(self):
        set_module_args(
            {
                "release_name": "test",
                "release_namespace": "test",
                "chart_ref": "chart1",
                "chart_repo_url": "http://repo.example/charts",
            }
        )
        helm.get_release_status = MagicMock(return_value=None)
        helm.fetch_chart_info = MagicMock(return_value=self.chart_info_without_dep)
        with patch.object(basic.AnsibleModule, "run_command") as mock_run_command:
            mock_run_command.return_value = (
                0,
                "configuration updated",
                "",
            )  # successful execution
            with self.assertRaises(AnsibleExitJson) as result:
                helm.main()
        mock_run_command.assert_called_once_with(
            "/usr/bin/helm --repo=http://repo.example/charts upgrade -i --reset-values test 'chart1'",
            environ_update={"HELM_NAMESPACE": "test"},
            data=None,
        )
        assert (
            result.exception.args[0]["command"]
            == "/usr/bin/helm --repo=http://repo.example/charts upgrade -i --reset-values test 'chart1'"
        )

    def test_dependency_update_option_False(self):
        set_module_args(
            {
                "release_name": "test",
                "release_namespace": "test",
                "chart_ref": "chart1",
                "chart_repo_url": "http://repo.example/charts",
                "dependency_update": False,
            }
        )
        helm.get_release_status = MagicMock(return_value=None)
        helm.fetch_chart_info = MagicMock(return_value=self.chart_info_without_dep)
        with patch.object(basic.AnsibleModule, "run_command") as mock_run_command:
            mock_run_command.return_value = (
                0,
                "configuration updated",
                "",
            )  # successful execution
            with self.assertRaises(AnsibleExitJson) as result:
                helm.main()
        mock_run_command.assert_called_once_with(
            "/usr/bin/helm --repo=http://repo.example/charts upgrade -i --reset-values test 'chart1'",
            environ_update={"HELM_NAMESPACE": "test"},
            data=None,
        )
        assert (
            result.exception.args[0]["command"]
            == "/usr/bin/helm --repo=http://repo.example/charts upgrade -i --reset-values test 'chart1'"
        )

    def test_dependency_update_option_True_and_replace_option_disabled(self):
        set_module_args(
            {
                "release_name": "test",
                "release_namespace": "test",
                "chart_ref": "chart1",
                "chart_repo_url": "http://repo.example/charts",
                "dependency_update": True,
            }
        )
        helm.get_release_status = MagicMock(return_value=None)
        helm.fetch_chart_info = MagicMock(return_value=self.chart_info_with_dep)
        with patch.object(basic.AnsibleModule, "run_command") as mock_run_command:
            mock_run_command.return_value = (
                0,
                "configuration updated",
                "",
            )  # successful execution
            with self.assertRaises(AnsibleFailJson) as result:
                helm.main()
        # mock_run_command.assert_called_once_with('/usr/bin/helm --repo=http://repo.example/charts upgrade -i --reset-values test chart1',
        #                                          environ_update={'HELM_NAMESPACE': 'test'})
        assert result.exception.args[0]["msg"] == (
            "'--dependency-update' hasn't been supported yet with 'helm upgrade'. "
            "Please use 'helm install' instead by adding 'replace' option"
        )
        assert result.exception.args[0]["failed"]

    def test_dependency_update_option_True_and_replace_option_enabled(self):
        set_module_args(
            {
                "release_name": "test",
                "release_namespace": "test",
                "chart_ref": "chart1",
                "chart_repo_url": "http://repo.example/charts",
                "dependency_update": True,
                "replace": True,
            }
        )
        helm.get_release_status = MagicMock(return_value=None)
        helm.fetch_chart_info = MagicMock(return_value=self.chart_info_without_dep)
        with patch.object(basic.AnsibleModule, "run_command") as mock_run_command:
            mock_run_command.return_value = (
                0,
                "configuration updated",
                "",
            )  # successful execution
            with self.assertRaises(AnsibleExitJson) as result:
                helm.main()
        mock_run_command.assert_called_once_with(
            "/usr/bin/helm --repo=http://repo.example/charts install --dependency-update --replace test 'chart1'",
            environ_update={"HELM_NAMESPACE": "test"},
            data=None,
        )
        assert (
            result.exception.args[0]["command"]
            == "/usr/bin/helm --repo=http://repo.example/charts install --dependency-update --replace test 'chart1'"
        )


class TestDependencyUpdateWithChartRefIsUrl(unittest.TestCase):
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

        self.chart_info_without_dep = {
            "apiVersion": "v2",
            "appVersion": "default",
            "description": "A chart used in molecule tests",
            "name": "test-chart",
            "type": "application",
            "version": "0.1.0",
        }

        self.chart_info_with_dep = {
            "apiVersion": "v2",
            "appVersion": "default",
            "description": "A chart used in molecule tests",
            "name": "test-chart",
            "type": "application",
            "version": "0.1.0",
            "dependencies": [
                {
                    "name": "test",
                    "version": "0.1.0",
                    "repository": "file://../test-chart",
                }
            ],
        }

    def test_dependency_update_option_not_defined(self):
        set_module_args(
            {
                "release_name": "test",
                "release_namespace": "test",
                "chart_ref": "http://repo.example/charts/application.tgz",
            }
        )
        helm.get_release_status = MagicMock(return_value=None)
        helm.fetch_chart_info = MagicMock(return_value=self.chart_info_without_dep)
        with patch.object(basic.AnsibleModule, "run_command") as mock_run_command:
            mock_run_command.return_value = (
                0,
                "configuration updated",
                "",
            )  # successful execution
            with self.assertRaises(AnsibleExitJson) as result:
                helm.main()
        mock_run_command.assert_called_once_with(
            "/usr/bin/helm upgrade -i --reset-values test 'http://repo.example/charts/application.tgz'",
            environ_update={"HELM_NAMESPACE": "test"},
            data=None,
        )
        assert (
            result.exception.args[0]["command"]
            == "/usr/bin/helm upgrade -i --reset-values test 'http://repo.example/charts/application.tgz'"
        )

    def test_dependency_update_option_False(self):
        set_module_args(
            {
                "release_name": "test",
                "release_namespace": "test",
                "chart_ref": "http://repo.example/charts/application.tgz",
                "dependency_update": False,
            }
        )
        helm.get_release_status = MagicMock(return_value=None)
        helm.fetch_chart_info = MagicMock(return_value=self.chart_info_without_dep)
        with patch.object(basic.AnsibleModule, "run_command") as mock_run_command:
            mock_run_command.return_value = (
                0,
                "configuration updated",
                "",
            )  # successful execution
            with self.assertRaises(AnsibleExitJson) as result:
                helm.main()
        mock_run_command.assert_called_once_with(
            "/usr/bin/helm upgrade -i --reset-values test 'http://repo.example/charts/application.tgz'",
            environ_update={"HELM_NAMESPACE": "test"},
            data=None,
        )
        assert (
            result.exception.args[0]["command"]
            == "/usr/bin/helm upgrade -i --reset-values test 'http://repo.example/charts/application.tgz'"
        )

    def test_dependency_update_option_True_and_replace_option_disabled(self):
        set_module_args(
            {
                "release_name": "test",
                "release_namespace": "test",
                "chart_ref": "http://repo.example/charts/application.tgz",
                "dependency_update": True,
            }
        )
        helm.get_release_status = MagicMock(return_value=None)
        helm.fetch_chart_info = MagicMock(return_value=self.chart_info_with_dep)
        with patch.object(basic.AnsibleModule, "run_command") as mock_run_command:
            mock_run_command.return_value = (
                0,
                "configuration updated",
                "",
            )  # successful execution
            with self.assertRaises(AnsibleFailJson) as result:
                helm.main()
        # mock_run_command.assert_called_once_with('/usr/bin/helm --repo=http://repo.example/charts upgrade -i --reset-values test chart1',
        #                                          environ_update={'HELM_NAMESPACE': 'test'})
        assert result.exception.args[0]["msg"] == (
            "'--dependency-update' hasn't been supported yet with 'helm upgrade'. "
            "Please use 'helm install' instead by adding 'replace' option"
        )
        assert result.exception.args[0]["failed"]

    def test_dependency_update_option_True_and_replace_option_enabled(self):
        set_module_args(
            {
                "release_name": "test",
                "release_namespace": "test",
                "chart_ref": "http://repo.example/charts/application.tgz",
                "dependency_update": True,
                "replace": True,
            }
        )
        helm.get_release_status = MagicMock(return_value=None)
        helm.fetch_chart_info = MagicMock(return_value=self.chart_info_without_dep)
        with patch.object(basic.AnsibleModule, "run_command") as mock_run_command:
            mock_run_command.return_value = (
                0,
                "configuration updated",
                "",
            )  # successful execution
            with self.assertRaises(AnsibleExitJson) as result:
                helm.main()
        mock_run_command.assert_called_once_with(
            "/usr/bin/helm install --dependency-update --replace test 'http://repo.example/charts/application.tgz'",
            environ_update={"HELM_NAMESPACE": "test"},
            data=None,
        )
        assert (
            result.exception.args[0]["command"]
            == "/usr/bin/helm install --dependency-update --replace test 'http://repo.example/charts/application.tgz'"
        )
