from __future__ import absolute_import, division, print_function

__metaclass__ = type

import sys
from unittest.mock import MagicMock, patch

import pytest
from ansible.plugins.lookup import LookupBase as StandardLookupBase


class TestK8sTurboMode:
    """Test turbo mode version checking in k8s lookup plugin."""

    @pytest.fixture(autouse=True)
    def cleanup_k8s_module(self):
        """Ensure clean module state before each test."""
        sys.modules.pop('ansible_collections.kubernetes.core.plugins.lookup.k8s', None)
        yield

    @pytest.mark.parametrize("ansible_version", ["2.19.0", "2.21.4"])
    def test_turbo_mode_disabled_on_newer_ansible(self, monkeypatch, ansible_version):
        """Test that turbo mode is disabled on ansible-core >= 2.19.0."""
        monkeypatch.setenv("ENABLE_TURBO_MODE", "true")
        mock_display = MagicMock()

        with patch.dict('sys.modules', {
            'ansible.module_utils.ansible_release': MagicMock(__version__=ansible_version),
            'ansible.utils.display': MagicMock(Display=lambda: mock_display),
        }):
            from ansible_collections.kubernetes.core.plugins.lookup import k8s

            mock_display.deprecated.assert_called()
            assert "ENABLE_TURBO_MODE is deprecated" in mock_display.deprecated.call_args[0][0]

            mock_display.warning.assert_called()
            assert f"ENABLE_TURBO_MODE is ignored on ansible-core {ansible_version}" in mock_display.warning.call_args[0][0]
            assert "ansible-core < 2.19.0 only" in mock_display.warning.call_args[0][0]

            assert k8s.LookupBase == StandardLookupBase

    def test_turbo_mode_enabled_on_ansible_core_2_18(self, monkeypatch):
        """Test that turbo mode is still enabled on ansible-core < 2.19.0."""
        monkeypatch.setenv("ENABLE_TURBO_MODE", "true")
        mock_display = MagicMock()
        mock_turbo_lookup = MagicMock()

        with patch.dict('sys.modules', {
            'ansible.module_utils.ansible_release': MagicMock(__version__='2.18.0'),
            'ansible.utils.display': MagicMock(Display=lambda: mock_display),
            'ansible_collections.cloud.common.plugins.plugin_utils.turbo.lookup': mock_turbo_lookup,
        }):
            from ansible_collections.kubernetes.core.plugins.lookup import k8s

            mock_display.deprecated.assert_called()
            assert not mock_display.warning.called

    def test_turbo_mode_disabled_when_env_not_set(self, monkeypatch):
        """Test that turbo mode is disabled when ENABLE_TURBO_MODE is not set."""
        monkeypatch.delenv("ENABLE_TURBO_MODE", raising=False)
        mock_display = MagicMock()

        with patch.dict('sys.modules', {
            'ansible.module_utils.ansible_release': MagicMock(__version__='2.18.0'),
            'ansible.utils.display': MagicMock(Display=lambda: mock_display),
        }):
            from ansible_collections.kubernetes.core.plugins.lookup import k8s

            mock_display.deprecated.assert_not_called()
            mock_display.warning.assert_not_called()
            assert k8s.LookupBase == StandardLookupBase
