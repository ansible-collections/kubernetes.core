# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

from ansible_collections.kubernetes.core.plugins.module_utils.args_common import (
    AUTH_ARG_SPEC,
    sanitize_kubeconfig_for_logging,
)


def test_sensitive_params_protected():
    """Test that truly sensitive parameters still have no_log=True."""
    # These should always have no_log=True
    sensitive_params = ["api_key", "password"]

    for param in sensitive_params:
        param_spec = AUTH_ARG_SPEC.get(param, {})
        assert (
            param_spec.get("no_log") is True
        ), f"{param} parameter should have no_log=True for security"


def test_non_sensitive_params_not_over_protected():
    """Test that non-sensitive parameters don't have no_log=True."""
    # These should not have no_log=True as they're not sensitive
    non_sensitive_params = ["host", "context", "validate_certs", "kubeconfig"]

    for param in non_sensitive_params:
        param_spec = AUTH_ARG_SPEC.get(param, {})
        assert (
            param_spec.get("no_log") is not True
        ), f"{param} parameter should not have no_log=True as it contains useful debugging info"


def test_sanitize_string_kubeconfig_passthrough():
    """Test that string kubeconfig values pass through unchanged."""
    kubeconfig_path = "/path/to/kubeconfig"
    result = sanitize_kubeconfig_for_logging(kubeconfig_path)
    assert result == kubeconfig_path


def test_sanitize_non_dict_passthrough():
    """Test that non-dict values pass through unchanged."""
    for value in [None, 123, [], "string"]:
        result = sanitize_kubeconfig_for_logging(value)
        assert result == value


def test_sanitize_user_level_sensitive_fields():
    """Test that user-level sensitive fields are properly sanitized."""
    kubeconfig = {
        "users": [
            {
                "name": "test-user",
                "user": {
                    "token": "secret-token-123",
                    "password": "secret-password",
                    "client-certificate-data": "base64-cert-data",
                    "client-key-data": "base64-key-data",
                    "username": "visible-username",  # Should remain visible
                },
            }
        ]
    }

    result = sanitize_kubeconfig_for_logging(kubeconfig)

    user_data = result["users"][0]["user"]
    assert user_data["token"] == "***TOKEN***"
    assert user_data["password"] == "***PASSWORD***"
    assert user_data["client-certificate-data"] == "***CLIENT_CERT_DATA***"
    assert user_data["client-key-data"] == "***CLIENT_KEY_DATA***"
    assert user_data["username"] == "visible-username"  # Should remain unchanged


def test_sanitize_cluster_level_sensitive_fields():
    """Test that cluster-level sensitive fields are properly sanitized."""
    kubeconfig = {
        "clusters": [
            {
                "name": "test-cluster",
                "cluster": {
                    "server": "https://kubernetes.example.com",  # Should remain visible
                    "certificate-authority-data": "base64-ca-cert-data",
                },
            }
        ]
    }

    result = sanitize_kubeconfig_for_logging(kubeconfig)

    cluster_data = result["clusters"][0]["cluster"]
    assert (
        cluster_data["server"] == "https://kubernetes.example.com"
    )  # Should remain unchanged
    assert cluster_data["certificate-authority-data"] == "***CA_CERT_DATA***"


def test_sanitize_auth_provider_fields():
    """Test that auth-provider sensitive fields are properly sanitized."""
    kubeconfig = {
        "users": [
            {
                "name": "oidc-user",
                "user": {
                    "auth-provider": {
                        "name": "oidc",
                        "config": {
                            "client-id": "my-client-id",  # Should remain visible
                            "client-secret": "secret-client-secret",
                            "refresh-token": "secret-refresh-token",
                            "id-token": "secret-id-token",
                            "access-token": "secret-access-token",
                        },
                    }
                },
            }
        ]
    }

    result = sanitize_kubeconfig_for_logging(kubeconfig)

    config = result["users"][0]["user"]["auth-provider"]["config"]
    assert config["client-id"] == "my-client-id"  # Should remain unchanged
    assert config["client-secret"] == "***CLIENT_SECRET***"
    assert config["refresh-token"] == "***REFRESH_TOKEN***"
    assert config["id-token"] == "***ID_TOKEN***"
    assert config["access-token"] == "***ACCESS_TOKEN***"


def test_sanitize_handles_missing_fields():
    """Test that sanitization handles kubeconfig with missing optional fields."""
    kubeconfig = {
        "users": [{"name": "test-user", "user": {}}],  # Empty user config
        "clusters": [
            {
                "name": "test-cluster",
                "cluster": {
                    "server": "https://kubernetes.example.com"
                    # Missing certificate-authority-data
                },
            }
        ],
    }

    # Should not raise any exceptions
    result = sanitize_kubeconfig_for_logging(kubeconfig)

    # Verify structure is preserved even with missing fields
    assert len(result["users"]) == 1
    assert len(result["clusters"]) == 1
    assert (
        result["clusters"][0]["cluster"]["server"] == "https://kubernetes.example.com"
    )
