# -*- coding: utf-8 -*-

import copy
from ansible_collections.kubernetes.core.plugins.module_utils.sanitize import (
    sanitize_kubeconfig_for_logging,
    sanitize_module_return_value,
    sanitize_kubeconfig_dict,
    SENSITIVE_USER_FIELDS,
    SENSITIVE_CLUSTER_FIELDS,
)


class TestKubeconfigSanitization:
    """Test cases for kubeconfig sanitization functions."""

    def test_sanitize_kubeconfig_string_path(self):
        """Test that string kubeconfig paths are preserved."""
        kubeconfig_path = "/home/user/.kube/config"
        result = sanitize_kubeconfig_for_logging(kubeconfig_path)
        assert result == kubeconfig_path

    def test_sanitize_kubeconfig_none(self):
        """Test that None kubeconfig is handled properly."""
        result = sanitize_kubeconfig_for_logging(None)
        assert result is None

    def test_sanitize_kubeconfig_unsupported_type(self):
        """Test that unsupported types are handled."""
        result = sanitize_kubeconfig_for_logging(123)
        assert result == "**UNSUPPORTED_TYPE**"

    def test_sanitize_kubeconfig_dict_with_sensitive_data(self):
        """Test that sensitive fields in kubeconfig dict are hidden."""
        kubeconfig = {
            "apiVersion": "v1",
            "kind": "Config",
            "current-context": "test-context",
            "contexts": [
                {
                    "name": "test-context",
                    "context": {"cluster": "test-cluster", "user": "test-user"},
                }
            ],
            "clusters": [
                {
                    "name": "test-cluster",
                    "cluster": {
                        "server": "https://kubernetes.example.com",
                        "certificate-authority-data": "LS0tLS1CRUdJTi...",
                    },
                }
            ],
            "users": [
                {
                    "name": "test-user",
                    "user": {
                        "token": "eyJhbGciOiJSUzI1NiIs...",
                        "client-certificate-data": "LS0tLS1CRUdJTi...",
                        "client-key-data": "LS0tLS1CRUdJTi...",
                    },
                }
            ],
        }

        result = sanitize_kubeconfig_for_logging(kubeconfig)

        # Check that structure is preserved
        assert result["apiVersion"] == "v1"
        assert result["kind"] == "Config"
        assert result["current-context"] == "test-context"

        # Check that non-sensitive cluster data is preserved
        assert (
            result["clusters"][0]["cluster"]["server"]
            == "https://kubernetes.example.com"
        )

        # Check that sensitive data is hidden
        assert (
            result["clusters"][0]["cluster"]["certificate-authority-data"]
            == "**HIDDEN**"
        )
        assert result["users"][0]["user"]["token"] == "**HIDDEN**"
        assert result["users"][0]["user"]["client-certificate-data"] == "**HIDDEN**"
        assert result["users"][0]["user"]["client-key-data"] == "**HIDDEN**"

    def test_sanitize_kubeconfig_dict_without_sensitive_data(self):
        """Test that kubeconfig without sensitive data is unchanged."""
        kubeconfig = {
            "apiVersion": "v1",
            "kind": "Config",
            "current-context": "test-context",
            "contexts": [
                {
                    "name": "test-context",
                    "context": {"cluster": "test-cluster", "user": "test-user"},
                }
            ],
            "clusters": [
                {
                    "name": "test-cluster",
                    "cluster": {"server": "https://kubernetes.example.com"},
                }
            ],
            "users": [{"name": "test-user", "user": {"username": "admin"}}],
        }

        result = sanitize_kubeconfig_for_logging(kubeconfig)

        # Should be unchanged since no sensitive data
        assert result == kubeconfig
        # But should be a copy, not the same object
        assert result is not kubeconfig

    def test_sanitize_all_sensitive_user_fields(self):
        """Test that all known sensitive user fields are properly hidden."""
        kubeconfig = {
            "users": [
                {
                    "name": "test-user",
                    "user": {
                        field: f"sensitive-{field}" for field in SENSITIVE_USER_FIELDS
                    },
                }
            ]
        }

        result = sanitize_kubeconfig_for_logging(kubeconfig)

        for field in SENSITIVE_USER_FIELDS:
            assert result["users"][0]["user"][field] == "**HIDDEN**"

    def test_sanitize_all_sensitive_cluster_fields(self):
        """Test that all known sensitive cluster fields are properly hidden."""
        kubeconfig = {
            "clusters": [
                {
                    "name": "test-cluster",
                    "cluster": {
                        field: f"sensitive-{field}"
                        for field in SENSITIVE_CLUSTER_FIELDS
                    },
                }
            ]
        }

        result = sanitize_kubeconfig_for_logging(kubeconfig)

        for field in SENSITIVE_CLUSTER_FIELDS:
            assert result["clusters"][0]["cluster"][field] == "**HIDDEN**"

    def test_sanitize_module_return_value_with_kubeconfig(self):
        """Test that module return values with kubeconfig are sanitized."""
        result = {
            "changed": False,
            "invocation": {
                "module_args": {
                    "kubeconfig": {
                        "users": [
                            {"name": "test-user", "user": {"token": "secret-token"}}
                        ]
                    },
                    "kind": "Pod",
                }
            },
        }

        sanitized = sanitize_module_return_value(result)

        assert sanitized["changed"] is False
        assert sanitized["invocation"]["module_args"]["kind"] == "Pod"
        assert (
            sanitized["invocation"]["module_args"]["kubeconfig"]["users"][0]["user"][
                "token"
            ]
            == "**HIDDEN**"
        )

    def test_sanitize_module_return_value_without_kubeconfig(self):
        """Test that module return values without kubeconfig are unchanged."""
        result = {
            "changed": True,
            "invocation": {"module_args": {"kind": "Pod", "name": "test-pod"}},
        }

        sanitized = sanitize_module_return_value(result)

        assert sanitized == result
        # Should be a copy
        assert sanitized is not result

    def test_sanitize_module_return_value_invalid_input(self):
        """Test that invalid input to sanitize_module_return_value is handled."""
        result = sanitize_module_return_value("not a dict")
        assert result == "not a dict"

    def test_original_kubeconfig_not_modified(self):
        """Test that the original kubeconfig dict is not modified during sanitization."""
        original_kubeconfig = {
            "users": [{"name": "test-user", "user": {"token": "secret-token"}}]
        }

        original_copy = copy.deepcopy(original_kubeconfig)

        # Sanitize the kubeconfig
        sanitize_kubeconfig_for_logging(original_kubeconfig)

        # Original should be unchanged
        assert original_kubeconfig == original_copy

    def test_sanitize_kubeconfig_dict_alias(self):
        """Test that sanitize_kubeconfig_dict works as an alias."""
        kubeconfig = {
            "users": [{"name": "test-user", "user": {"token": "secret-token"}}]
        }

        result = sanitize_kubeconfig_dict(kubeconfig)
        assert result["users"][0]["user"]["token"] == "**HIDDEN**"

    def test_empty_kubeconfig_sections(self):
        """Test handling of empty or missing kubeconfig sections."""
        kubeconfig = {"users": [], "clusters": []}

        result = sanitize_kubeconfig_for_logging(kubeconfig)
        assert result == kubeconfig

    def test_malformed_kubeconfig_structure(self):
        """Test handling of malformed kubeconfig structures."""
        kubeconfig = {
            "users": [
                {
                    "name": "test-user"
                    # Missing 'user' key
                }
            ],
            "clusters": [
                {
                    "name": "test-cluster"
                    # Missing 'cluster' key
                }
            ],
        }

        # Should not raise an exception
        result = sanitize_kubeconfig_for_logging(kubeconfig)
        assert result == kubeconfig
