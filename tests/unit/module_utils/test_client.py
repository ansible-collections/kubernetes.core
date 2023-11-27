import base64
import os
import tempfile

import mock
import yaml
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.client import (
    _create_auth_spec,
    _create_configuration,
)
from mock import MagicMock

TEST_HOST = "test-host"
TEST_SSL_HOST = "https://test-host"
TEST_CLIENT_CERT = "/dev/null"
TEST_CLIENT_KEY = "/dev/null"
TEST_CERTIFICATE_AUTH = "/dev/null"
TEST_DATA = "test-data"
TEST_BEARER_TOKEN = "Bearer %s" % base64.standard_b64encode(TEST_DATA.encode()).decode()
TEST_KUBE_CONFIG = {
    "current-context": "federal-context",
    "contexts": [
        {
            "name": "simple_token",
            "context": {"cluster": "default", "user": "simple_token"},
        }
    ],
    "clusters": [{"name": "default", "cluster": {"server": TEST_HOST}}],
    "users": [
        {
            "name": "ssl-no_file",
            "user": {
                "token": TEST_BEARER_TOKEN,
                "client-certificate": TEST_CLIENT_CERT,
                "client-key": TEST_CLIENT_KEY,
            },
        }
    ],
}

_temp_files = []


def _remove_temp_file():
    for f in _temp_files:
        try:
            os.remove(f)
        except FileNotFoundError:
            pass


def _create_temp_file(content=""):
    handler, name = tempfile.mkstemp()
    _temp_files.append(name)
    os.write(handler, str.encode(content))
    os.close(handler)
    return name


def test_create_auth_spec_ssl_no_options():
    module = MagicMock()
    module.params = {}
    actual_auth_spec = _create_auth_spec(module)

    assert "proxy_headers" in actual_auth_spec


def test_create_auth_spec_ssl_options():
    ssl_options = {
        "host": TEST_SSL_HOST,
        "token": TEST_BEARER_TOKEN,
        "client_cert": TEST_CLIENT_CERT,
        "client_key": TEST_CLIENT_KEY,
        "ca_cert": TEST_CERTIFICATE_AUTH,
        "validate_certs": True,
    }
    expected_auth_spec = {
        "host": TEST_SSL_HOST,
        "cert_file": TEST_CLIENT_CERT,
        "key_file": TEST_CLIENT_KEY,
        "ssl_ca_cert": TEST_CERTIFICATE_AUTH,
        "verify_ssl": True,
        "proxy_headers": {},
    }

    module = MagicMock()
    module.params = ssl_options
    actual_auth_spec = _create_auth_spec(module)

    assert expected_auth_spec.items() <= actual_auth_spec.items()


def test_create_auth_spec_ssl_options_no_verify():
    ssl_options = {
        "host": TEST_SSL_HOST,
        "token": TEST_BEARER_TOKEN,
        "client_cert": TEST_CLIENT_CERT,
        "client_key": TEST_CLIENT_KEY,
        "validate_certs": False,
    }

    expected_auth_spec = {
        "host": TEST_SSL_HOST,
        "cert_file": TEST_CLIENT_CERT,
        "key_file": TEST_CLIENT_KEY,
        "verify_ssl": False,
        "proxy_headers": {},
    }

    module = MagicMock()
    module.params = ssl_options
    actual_auth_spec = _create_auth_spec(module)

    assert expected_auth_spec.items() <= actual_auth_spec.items()


@mock.patch.dict(os.environ, {"K8S_AUTH_PROXY_HEADERS_PROXY_BASIC_AUTH": "foo:bar"})
@mock.patch.dict(os.environ, {"K8S_AUTH_PROXY_HEADERS_USER_AGENT": "foo/1.0"})
@mock.patch.dict(os.environ, {"K8S_AUTH_CERT_FILE": TEST_CLIENT_CERT})
def test_create_auth_spec_ssl_proxy():
    expected_auth_spec = {
        "kubeconfig": "~/.kube/customconfig",
        "verify_ssl": True,
        "cert_file": TEST_CLIENT_CERT,
        "proxy_headers": {"proxy_basic_auth": "foo:bar", "user_agent": "foo/1.0"},
    }
    module = MagicMock()
    options = {"validate_certs": True, "kubeconfig": "~/.kube/customconfig"}

    module.params = options
    actual_auth_spec = _create_auth_spec(module)

    assert expected_auth_spec.items() <= actual_auth_spec.items()


def test_load_kube_config_from_file_path():
    config_file = _create_temp_file(yaml.safe_dump(TEST_KUBE_CONFIG))
    auth = {"kubeconfig": config_file, "context": "simple_token"}
    actual_configuration = _create_configuration(auth)

    expected_configuration = {
        "host": TEST_HOST,
        "kubeconfig": config_file,
        "context": "simple_token",
    }

    assert expected_configuration.items() <= actual_configuration.__dict__.items()
    _remove_temp_file()


def test_load_kube_config_from_dict():
    auth_spec = {"kubeconfig": TEST_KUBE_CONFIG, "context": "simple_token"}
    actual_configuration = _create_configuration(auth_spec)

    expected_configuration = {
        "host": TEST_HOST,
        "kubeconfig": TEST_KUBE_CONFIG,
        "context": "simple_token",
    }

    assert expected_configuration.items() <= actual_configuration.__dict__.items()
    _remove_temp_file()


def test_create_auth_spec_with_aliases_in_kwargs():
    auth_options = {
        "host": TEST_HOST,
        "cert_file": TEST_CLIENT_CERT,
        "ssl_ca_cert": TEST_CERTIFICATE_AUTH,
        "key_file": TEST_CLIENT_KEY,
        "verify_ssl": True,
    }

    expected_auth_spec = {
        "host": TEST_HOST,
        "cert_file": TEST_CLIENT_CERT,
        "ssl_ca_cert": TEST_CERTIFICATE_AUTH,
        "key_file": TEST_CLIENT_KEY,
        "verify_ssl": True,
    }

    actual_auth_spec = _create_auth_spec(module=None, **auth_options)
    for key, value in expected_auth_spec.items():
        assert value == actual_auth_spec.get(key)
