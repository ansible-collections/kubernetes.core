# Copyright [2025] [Red Hat, Inc.]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import warnings

import pytest
from ansible_collections.kubernetes.core.plugins.module_utils.args_common import (
    extract_sensitive_values_from_kubeconfig,
)


@pytest.fixture
def mock_kubeconfig_with_sensitive_data():
    return {
        "apiVersion": "v1",
        "kind": "Config",
        "clusters": [
            {
                "name": "test-cluster",
                "cluster": {
                    "server": "https://test-cluster.example.com",
                    "certificate-authority-data": "LS0tLS1CRUdJTi...fake-cert-data",
                    "insecure-skip-tls-verify": False,
                },
            }
        ],
        "contexts": [
            {
                "name": "test-context",
                "context": {
                    "cluster": "test-cluster",
                    "user": "test-user",
                    "namespace": "default",
                },
            }
        ],
        "current-context": "test-context",
        "users": [
            {
                "name": "test-user",
                "user": {
                    "client-certificate-data": "LS0tLS1CRUdJTi...fake-client-cert",
                    "client-key-data": "LS0tLS1CRUdJTi...fake-client-key",
                    "token": "eyJhbGciOiJSUzI1NiIs...fake-token",
                    "password": "fake-password-123",
                    "username": "testuser",
                },
            },
            {
                "name": "service-account-user",
                "user": {
                    "token": "eyJhbGciOiJSUzI1NiIs...fake-service-token",
                },
            },
        ],
    }


@pytest.fixture
def mock_kubeconfig_with_nested_sensitive_data():
    return {
        "apiVersion": "v1",
        "kind": "Config",
        "clusters": [
            {
                "name": "cluster-1",
                "cluster": {
                    "certificate-authority-data": "fake-ca-data-1",
                },
            },
            {
                "name": "cluster-2",
                "cluster": {
                    "certificate-authority-data": "fake-ca-data-2",
                },
            },
        ],
        "users": [
            {
                "name": "user-1",
                "user": {
                    "client-certificate-data": "fake-cert-1",
                    "client-key-data": "fake-key-1",
                    "token": "fake-token-1",
                    "secret": "fake-secret-1",
                    "api_key": "fake-api-key-1",
                    "access-token": "fake-access-token-1",
                    "refresh-token": "fake-refresh-token-1",
                },
            },
        ],
    }


@pytest.fixture
def mock_kubeconfig_without_sensitive_data():
    return {
        "apiVersion": "v1",
        "kind": "Config",
        "clusters": [
            {
                "name": "test-cluster",
                "cluster": {
                    "server": "https://test-cluster.example.com",
                    "insecure-skip-tls-verify": True,
                },
            }
        ],
        "users": [
            {
                "name": "test-user",
                "user": {
                    "username": "testuser",
                },
            }
        ],
    }


@pytest.fixture
def mock_kubeconfig_v2():
    """Mock kubeconfig with API version v2 to test warning behavior."""
    return {
        "apiVersion": "v2",
        "kind": "Config",
        "clusters": [
            {
                "name": "test-cluster",
                "cluster": {
                    "server": "https://test-cluster.example.com",
                    "certificate-authority-data": "fake-ca-data-v2",
                },
            }
        ],
        "users": [
            {
                "name": "test-user",
                "user": {
                    "token": "fake-token-v2",
                    "password": "fake-password-v2",
                },
            }
        ],
    }


def test_extract_sensitive_values_basic(mock_kubeconfig_with_sensitive_data):
    result = extract_sensitive_values_from_kubeconfig(
        mock_kubeconfig_with_sensitive_data
    )

    # Should extract all sensitive string values
    expected_values = {
        "LS0tLS1CRUdJTi...fake-cert-data",  # certificate-authority-data
        "LS0tLS1CRUdJTi...fake-client-cert",  # client-certificate-data
        "LS0tLS1CRUdJTi...fake-client-key",  # client-key-data
        "eyJhbGciOiJSUzI1NiIs...fake-token",  # token
        "fake-password-123",  # password
        "eyJhbGciOiJSUzI1NiIs...fake-service-token",  # second token
    }

    assert result == expected_values


def test_extract_sensitive_values_nested(mock_kubeconfig_with_nested_sensitive_data):
    result = extract_sensitive_values_from_kubeconfig(
        mock_kubeconfig_with_nested_sensitive_data
    )

    # Should extract all sensitive values from multiple clusters and users
    expected_values = {
        "fake-ca-data-1",
        "fake-ca-data-2",
        "fake-cert-1",
        "fake-key-1",
        "fake-token-1",
        "fake-secret-1",
        "fake-api-key-1",
        "fake-access-token-1",
        "fake-refresh-token-1",
    }

    assert result == expected_values


def test_extract_sensitive_values_no_sensitive_data(
    mock_kubeconfig_without_sensitive_data,
):
    result = extract_sensitive_values_from_kubeconfig(
        mock_kubeconfig_without_sensitive_data
    )

    # Should return empty set since there is no sensitive data
    assert result == set()


def test_redaction_placeholder_appears_in_output(mock_kubeconfig_with_sensitive_data):
    """Test that sensitive values are replaced with VALUE_SPECIFIED_IN_NO_LOG_PARAMETER in output."""
    sensitive_values = extract_sensitive_values_from_kubeconfig(
        mock_kubeconfig_with_sensitive_data
    )

    # Create a mock module output that would contain sensitive data
    mock_output = {
        "kubeconfig": mock_kubeconfig_with_sensitive_data,
        "result": "success",
        "sensitive_token": "eyJhbGciOiJSUzI1NiIs...fake-token",
        "sensitive_password": "fake-password-123",
    }

    # Simulate what Ansible does when no_log_values is set
    json_str = json.dumps(mock_output)
    for sensitive_value in sensitive_values:
        json_str = json_str.replace(
            f'"{sensitive_value}"', '"VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"'
        )
    redacted_output = json.loads(json_str)

    # Verify that sensitive values are replaced with the redaction placeholder
    assert redacted_output["sensitive_token"] == "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
    assert (
        redacted_output["sensitive_password"] == "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
    )

    # Verify that non-sensitive data remains unchanged
    assert redacted_output["result"] == "success"
    assert redacted_output["kubeconfig"]["users"][0]["user"]["username"] == "testuser"


def test_redaction_placeholder_appears_in_nested_output(
    mock_kubeconfig_with_nested_sensitive_data,
):
    # Extract sensitive values
    sensitive_values = extract_sensitive_values_from_kubeconfig(
        mock_kubeconfig_with_nested_sensitive_data
    )

    # Create a mock module output that would contain nested sensitive data
    mock_output = {
        "kubeconfig": mock_kubeconfig_with_nested_sensitive_data,
        "result": "success",
        "cluster_ca_data": "fake-ca-data-1",
        "user_cert_data": "fake-cert-1",
        "user_key_data": "fake-key-1",
        "user_token": "fake-token-1",
        "user_secret": "fake-secret-1",
        "api_key": "fake-api-key-1",
        "access_token": "fake-access-token-1",
        "refresh_token": "fake-refresh-token-1",
    }

    # Simulate what Ansible does when no_log_values is set
    json_str = json.dumps(mock_output)
    for sensitive_value in sensitive_values:
        json_str = json_str.replace(
            f'"{sensitive_value}"', '"VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"'
        )
    redacted_output = json.loads(json_str)

    # Verify that sensitive values are replaced with the redaction placeholder
    assert redacted_output["cluster_ca_data"] == "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
    assert redacted_output["user_cert_data"] == "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
    assert redacted_output["user_key_data"] == "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
    assert redacted_output["user_token"] == "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
    assert redacted_output["user_secret"] == "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
    assert redacted_output["api_key"] == "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
    assert redacted_output["access_token"] == "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
    assert redacted_output["refresh_token"] == "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"

    # Verify that non-sensitive data remains unchanged
    assert redacted_output["result"] == "success"
    assert redacted_output["kubeconfig"]["apiVersion"] == "v1"
    assert redacted_output["kubeconfig"]["kind"] == "Config"
    assert redacted_output["kubeconfig"]["clusters"][0]["name"] == "cluster-1"
    assert redacted_output["kubeconfig"]["clusters"][1]["name"] == "cluster-2"
    assert redacted_output["kubeconfig"]["users"][0]["name"] == "user-1"

    # Verify that sensitive values within the nested kubeconfig structure are also redacted
    assert (
        redacted_output["kubeconfig"]["clusters"][0]["cluster"][
            "certificate-authority-data"
        ]
        == "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
    )
    assert (
        redacted_output["kubeconfig"]["clusters"][1]["cluster"][
            "certificate-authority-data"
        ]
        == "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
    )
    assert (
        redacted_output["kubeconfig"]["users"][0]["user"]["client-certificate-data"]
        == "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
    )
    assert (
        redacted_output["kubeconfig"]["users"][0]["user"]["client-key-data"]
        == "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
    )
    assert (
        redacted_output["kubeconfig"]["users"][0]["user"]["token"]
        == "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
    )
    assert (
        redacted_output["kubeconfig"]["users"][0]["user"]["secret"]
        == "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
    )
    assert (
        redacted_output["kubeconfig"]["users"][0]["user"]["api_key"]
        == "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
    )
    assert (
        redacted_output["kubeconfig"]["users"][0]["user"]["access-token"]
        == "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
    )
    assert (
        redacted_output["kubeconfig"]["users"][0]["user"]["refresh-token"]
        == "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
    )


def test_warning_for_non_v1_api_version(mock_kubeconfig_v2):
    with pytest.warns(UserWarning) as warning_list:
        result = extract_sensitive_values_from_kubeconfig(mock_kubeconfig_v2)

    # Verify that exactly one warning was raised
    assert len(warning_list) == 1

    # Verify the warning message content
    warning = warning_list[0]
    assert "Kubeconfig API version 'v2' is not 'v1'" in str(warning.message)

    # Verify that the function still works and extracts sensitive values
    expected_values = {
        "fake-ca-data-v2",
        "fake-token-v2",
        "fake-password-v2",
    }
    assert result == expected_values


def test_no_warning_for_v1_api_version(mock_kubeconfig_with_sensitive_data):
    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")  # Capture all warnings
        result = extract_sensitive_values_from_kubeconfig(
            mock_kubeconfig_with_sensitive_data
        )

    # Filter for UserWarning specifically (our warning type)
    user_warnings = [w for w in warning_list if issubclass(w.category, UserWarning)]
    assert len(user_warnings) == 0

    # Verify that the function still works normally
    assert len(result) > 0


def test_no_warning_for_missing_api_version():
    """Test that no warning is raised when apiVersion field is missing (defaults to v1)."""
    kubeconfig_no_version = {
        "kind": "Config",
        "clusters": [
            {
                "name": "test-cluster",
                "cluster": {
                    "server": "https://test-cluster.example.com",
                    "certificate-authority-data": "fake-ca-data",
                },
            }
        ],
        "users": [
            {
                "name": "test-user",
                "user": {
                    "token": "fake-token",
                },
            }
        ],
    }

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")  # Capture all warnings
        result = extract_sensitive_values_from_kubeconfig(kubeconfig_no_version)

    # Filter for UserWarning specifically (our warning type)
    user_warnings = [w for w in warning_list if issubclass(w.category, UserWarning)]
    assert len(user_warnings) == 0

    # Verify that the function still works normally
    expected_values = {"fake-ca-data", "fake-token"}
    assert result == expected_values
