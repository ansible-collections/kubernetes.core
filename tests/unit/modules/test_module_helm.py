# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import unittest
from unittest.mock import MagicMock, patch

from ansible.module_utils import basic
from ansible_collections.kubernetes.core.plugins.module_utils.helm import (
    AnsibleHelmModule,
)
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
            # Mock responses: first call is helm version, second is the actual command
            mock_run_command.side_effect = [
                (
                    0,
                    'version.BuildInfo{Version:"v3.10.0", GitCommit:"", GoVersion:"go1.18"}',
                    "",
                ),
                (0, "configuration updated", ""),
            ]
            with self.assertRaises(AnsibleExitJson) as result:
                helm.main()
        helm.run_dep_update.assert_not_called()
        # Check the last call (actual helm command, after version check)
        assert (
            mock_run_command.call_args_list[-1][0][0]
            == "/usr/bin/helm upgrade -i --reset-values test '/tmp/path'"
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
            # Mock responses: first call is helm version, second is the actual command
            mock_run_command.side_effect = [
                (
                    0,
                    'version.BuildInfo{Version:"v3.10.0", GitCommit:"", GoVersion:"go1.18"}',
                    "",
                ),
                (0, "configuration updated", ""),
            ]
            with self.assertRaises(AnsibleExitJson) as result:
                helm.main()
        helm.run_dep_update.assert_not_called()
        # Check the last call (actual helm command, after version check)
        assert (
            mock_run_command.call_args_list[-1][0][0]
            == "/usr/bin/helm upgrade -i --reset-values test '/tmp/path'"
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
            # Mock responses: first call is helm version, second is the actual command
            mock_run_command.side_effect = [
                (
                    0,
                    'version.BuildInfo{Version:"v3.10.0", GitCommit:"", GoVersion:"go1.18"}',
                    "",
                ),
                (0, "configuration updated", ""),
            ]
            with patch.object(basic.AnsibleModule, "warn") as mock_warn:
                with self.assertRaises(AnsibleExitJson) as result:
                    helm.main()
        mock_warn.assert_not_called()
        # Check calls include the actual helm command (after version check)
        assert any(
            "/usr/bin/helm upgrade -i --reset-values test '/tmp/path'" in str(call)
            for call in mock_run_command.call_args_list
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
            # Mock responses: first call is helm version, second is the actual command
            mock_run_command.side_effect = [
                (
                    0,
                    'version.BuildInfo{Version:"v3.10.0", GitCommit:"", GoVersion:"go1.18"}',
                    "",
                ),
                (0, "configuration updated", ""),
            ]
            with patch.object(basic.AnsibleModule, "warn") as mock_warn:
                with self.assertRaises(AnsibleExitJson) as result:
                    helm.main()
        mock_warn.assert_called_once()
        # Check calls include the actual helm command (after version check)
        assert any(
            "/usr/bin/helm upgrade -i --reset-values test '/tmp/path'" in str(call)
            for call in mock_run_command.call_args_list
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
            # Mock responses: first call is helm version, second is the actual command
            mock_run_command.side_effect = [
                (
                    0,
                    'version.BuildInfo{Version:"v3.10.0", GitCommit:"", GoVersion:"go1.18"}',
                    "",
                ),
                (0, "configuration updated", ""),
            ]
            with self.assertRaises(AnsibleExitJson) as result:
                helm.main()
        # Check the last call (actual helm command, after version check)
        assert (
            mock_run_command.call_args_list[-1][0][0]
            == "/usr/bin/helm --repo=http://repo.example/charts upgrade -i --reset-values test 'chart1'"
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
            # Mock responses: first call is helm version, second is the actual command
            mock_run_command.side_effect = [
                (
                    0,
                    'version.BuildInfo{Version:"v3.10.0", GitCommit:"", GoVersion:"go1.18"}',
                    "",
                ),
                (0, "configuration updated", ""),
            ]
            with self.assertRaises(AnsibleExitJson) as result:
                helm.main()
        # Check the last call (actual helm command, after version check)
        assert (
            mock_run_command.call_args_list[-1][0][0]
            == "/usr/bin/helm --repo=http://repo.example/charts upgrade -i --reset-values test 'chart1'"
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
            # Mock responses: first call is helm version, second is the actual command
            mock_run_command.side_effect = [
                (
                    0,
                    'version.BuildInfo{Version:"v3.10.0", GitCommit:"", GoVersion:"go1.18"}',
                    "",
                ),
                (0, "configuration updated", ""),
            ]
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
            # Mock responses: first call is helm version, second is the actual command
            mock_run_command.side_effect = [
                (
                    0,
                    'version.BuildInfo{Version:"v3.10.0", GitCommit:"", GoVersion:"go1.18"}',
                    "",
                ),
                (0, "configuration updated", ""),
            ]
            with self.assertRaises(AnsibleExitJson) as result:
                helm.main()
        # Check the last call (actual helm command, after version check)
        assert (
            mock_run_command.call_args_list[-1][0][0]
            == "/usr/bin/helm --repo=http://repo.example/charts install --dependency-update --replace test 'chart1'"
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
            # Mock responses: first call is helm version, second is the actual command
            mock_run_command.side_effect = [
                (
                    0,
                    'version.BuildInfo{Version:"v3.10.0", GitCommit:"", GoVersion:"go1.18"}',
                    "",
                ),
                (0, "configuration updated", ""),
            ]
            with self.assertRaises(AnsibleExitJson) as result:
                helm.main()
        # Check the last call (actual helm command, after version check)
        assert (
            mock_run_command.call_args_list[-1][0][0]
            == "/usr/bin/helm upgrade -i --reset-values test 'http://repo.example/charts/application.tgz'"
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
            # Mock responses: first call is helm version, second is the actual command
            mock_run_command.side_effect = [
                (
                    0,
                    'version.BuildInfo{Version:"v3.10.0", GitCommit:"", GoVersion:"go1.18"}',
                    "",
                ),
                (0, "configuration updated", ""),
            ]
            with self.assertRaises(AnsibleExitJson) as result:
                helm.main()
        # Check the last call (actual helm command, after version check)
        assert (
            mock_run_command.call_args_list[-1][0][0]
            == "/usr/bin/helm upgrade -i --reset-values test 'http://repo.example/charts/application.tgz'"
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
            # Mock responses: first call is helm version, second is the actual command
            mock_run_command.side_effect = [
                (
                    0,
                    'version.BuildInfo{Version:"v3.10.0", GitCommit:"", GoVersion:"go1.18"}',
                    "",
                ),
                (0, "configuration updated", ""),
            ]
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
            # Mock responses: first call is helm version, second is the actual command
            mock_run_command.side_effect = [
                (
                    0,
                    'version.BuildInfo{Version:"v3.10.0", GitCommit:"", GoVersion:"go1.18"}',
                    "",
                ),
                (0, "configuration updated", ""),
            ]
            with self.assertRaises(AnsibleExitJson) as result:
                helm.main()
        # Check the last call (actual helm command, after version check)
        assert (
            mock_run_command.call_args_list[-1][0][0]
            == "/usr/bin/helm install --dependency-update --replace test 'http://repo.example/charts/application.tgz'"
        )
        assert (
            result.exception.args[0]["command"]
            == "/usr/bin/helm install --dependency-update --replace test 'http://repo.example/charts/application.tgz'"
        )


class TestForceFlagHelmVersion(unittest.TestCase):
    def setUp(self):
        self.mock_module_helper = patch.multiple(
            basic.AnsibleModule,
            exit_json=exit_json,
            fail_json=fail_json,
            get_bin_path=get_bin_path,
        )
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

        self.chart_info = {
            "apiVersion": "v2",
            "appVersion": "default",
            "description": "A chart used in molecule tests",
            "name": "test-chart",
            "type": "application",
            "version": "0.1.0",
        }

    def _deploy_command(self, params, helm_version, release_status=None):
        """Run helm.main() with mocked dependencies and return the helm command."""
        set_module_args(
            {
                "release_name": "test",
                "release_namespace": "test",
                "chart_ref": "/tmp/path",
                **params,
            }
        )
        helm.get_release_status = MagicMock(return_value=release_status)
        helm.fetch_chart_info = MagicMock(return_value=self.chart_info)
        # Force the default (non helm-diff) idempotency check path for upgrades.
        helm.get_plugin_version = MagicMock(return_value=None)
        helm.default_check = MagicMock(return_value=False)
        with patch.object(
            AnsibleHelmModule, "get_helm_version", return_value=helm_version
        ):
            with patch.object(basic.AnsibleModule, "run_command") as mock_run_command:
                mock_run_command.return_value = (0, "deployed", "")
                try:
                    helm.main()
                except AnsibleExitJson:
                    pass
                return mock_run_command.call_args_list[-1][0][0]

    # --- force flag (existing release, so the upgrade path is exercised) ---

    def test_force_uses_force_on_helm_v3(self):
        cmd = self._deploy_command(
            {"force": True}, "3.10.0", release_status={"status": "deployed"}
        )
        assert " --force" in cmd
        assert "--force-replace" not in cmd

    def test_force_uses_force_replace_on_helm_v4(self):
        cmd = self._deploy_command(
            {"force": True}, "4.0.0", release_status={"status": "deployed"}
        )
        assert " --server-side=false --force-replace" in cmd
        assert " --force " not in cmd

    # --- server_side option (fresh install path) ---

    def test_server_side_on_helm_v4(self):
        cmd = self._deploy_command({"server_side": "true"}, "4.0.0")
        assert " --server-side=true" in cmd

    def test_server_side_requires_helm_v4(self):
        set_module_args(
            {
                "release_name": "test",
                "release_namespace": "test",
                "chart_ref": "/tmp/path",
                "server_side": "true",
            }
        )
        helm.get_release_status = MagicMock(return_value=None)
        helm.fetch_chart_info = MagicMock(return_value=self.chart_info)
        with patch.object(AnsibleHelmModule, "get_helm_version", return_value="3.10.0"):
            with patch.object(basic.AnsibleModule, "run_command") as mock_run_command:
                mock_run_command.return_value = (0, "deployed", "")
                with self.assertRaises(AnsibleFailJson):
                    helm.main()

    # --- force_conflicts option (fresh install path) ---

    def test_force_conflicts_on_helm_v4(self):
        cmd = self._deploy_command({"force_conflicts": True}, "4.0.0")
        assert " --force-conflicts" in cmd

    def test_force_conflicts_with_server_side(self):
        cmd = self._deploy_command(
            {"force_conflicts": True, "server_side": "auto"}, "4.0.0"
        )
        assert " --server-side=auto --force-conflicts" in cmd

    def test_force_conflicts_requires_helm_v4(self):
        set_module_args(
            {
                "release_name": "test",
                "release_namespace": "test",
                "chart_ref": "/tmp/path",
                "force_conflicts": True,
            }
        )
        helm.get_release_status = MagicMock(return_value=None)
        helm.fetch_chart_info = MagicMock(return_value=self.chart_info)
        with patch.object(AnsibleHelmModule, "get_helm_version", return_value="3.10.0"):
            with patch.object(basic.AnsibleModule, "run_command") as mock_run_command:
                mock_run_command.return_value = (0, "deployed", "")
                with self.assertRaises(AnsibleFailJson):
                    helm.main()

    def test_force_conflicts_conflicts_with_server_side_false(self):
        set_module_args(
            {
                "release_name": "test",
                "release_namespace": "test",
                "chart_ref": "/tmp/path",
                "force_conflicts": True,
                "server_side": "false",
            }
        )
        helm.get_release_status = MagicMock(return_value=None)
        helm.fetch_chart_info = MagicMock(return_value=self.chart_info)
        with patch.object(AnsibleHelmModule, "get_helm_version", return_value="4.0.0"):
            with patch.object(basic.AnsibleModule, "run_command") as mock_run_command:
                mock_run_command.return_value = (0, "deployed", "")
                with self.assertRaises(AnsibleFailJson):
                    helm.main()

    # --- mutually exclusive combinations (rejected at module init) ---

    def test_force_and_server_side_are_mutually_exclusive(self):
        with self.assertRaises(AnsibleFailJson):
            set_module_args(
                {
                    "release_name": "test",
                    "chart_ref": "/tmp/path",
                    "force": True,
                    "server_side": "true",
                }
            )
            helm.main()

    def test_force_and_force_conflicts_are_mutually_exclusive(self):
        with self.assertRaises(AnsibleFailJson):
            set_module_args(
                {
                    "release_name": "test",
                    "chart_ref": "/tmp/path",
                    "force": True,
                    "force_conflicts": True,
                }
            )
            helm.main()


class TestAtomicFlagHelmVersion(unittest.TestCase):
    """Helm v4 renamed '--atomic' to '--rollback-on-failure' (issue #1143)."""

    def setUp(self):
        self.mock_module_helper = patch.multiple(
            basic.AnsibleModule,
            exit_json=exit_json,
            fail_json=fail_json,
            get_bin_path=get_bin_path,
        )
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

        self.chart_info = {
            "apiVersion": "v2",
            "appVersion": "default",
            "description": "A chart used in molecule tests",
            "name": "test-chart",
            "type": "application",
            "version": "0.1.0",
        }

    def _run_with_version(self, args, helm_version):
        set_module_args(args)
        helm.get_release_status = MagicMock(return_value=None)
        helm.fetch_chart_info = MagicMock(return_value=self.chart_info)
        with patch.object(
            helm.AnsibleHelmModule, "get_helm_version", return_value=helm_version
        ):
            with patch.object(basic.AnsibleModule, "run_command") as mock_run_command:
                mock_run_command.return_value = (0, "configuration updated", "")
                with self.assertRaises(AnsibleExitJson) as result:
                    helm.main()
        return result.exception.args[0]["command"]

    def test_atomic_uses_atomic_flag_on_helm_v3(self):
        command = self._run_with_version(
            {
                "release_name": "test",
                "release_namespace": "test",
                "chart_ref": "chart1",
                "atomic": True,
            },
            "3.17.0",
        )
        assert "--atomic" in command
        assert "--rollback-on-failure" not in command

    def test_atomic_uses_rollback_on_failure_on_helm_v4(self):
        command = self._run_with_version(
            {
                "release_name": "test",
                "release_namespace": "test",
                "chart_ref": "chart1",
                "atomic": True,
            },
            "4.0.0",
        )
        assert "--rollback-on-failure" in command
        assert "--atomic" not in command

    def test_atomic_with_replace_uses_rollback_on_failure_on_helm_v4(self):
        # 'replace' uses 'helm install', where '--atomic' is removed in v4.
        command = self._run_with_version(
            {
                "release_name": "test",
                "release_namespace": "test",
                "chart_ref": "chart1",
                "atomic": True,
                "replace": True,
            },
            "4.0.0",
        )
        assert " install " in command
        assert "--rollback-on-failure" in command
        assert "--atomic" not in command
