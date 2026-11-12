import base64
import os
import tempfile

import mock
import pytest
import yaml
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.client import (
    _create_auth_spec,
    _create_configuration,
    _get_request_timeout,
)
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.exceptions import (
    CoreException,
)
from ansible_collections.kubernetes.core.plugins.module_utils.k8sdynamicclient import (
    K8SDynamicClient,
)
from kubernetes.dynamic import DynamicClient
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


def _assert_configuration(actual, expected):
    for key, value in expected.items():
        assert getattr(actual, key) == value


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

    _assert_configuration(
        actual_configuration,
        {
            "host": TEST_HOST,
            "kubeconfig": config_file,
            "context": "simple_token",
        },
    )
    _remove_temp_file()


def test_load_kube_config_from_dict():
    auth_spec = {"kubeconfig": TEST_KUBE_CONFIG, "context": "simple_token"}
    actual_configuration = _create_configuration(auth_spec)

    _assert_configuration(
        actual_configuration,
        {
            "host": TEST_HOST,
            "kubeconfig": TEST_KUBE_CONFIG,
            "context": "simple_token",
        },
    )
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


def test_get_request_timeout_unset():
    module = MagicMock()
    module.params = {}
    with mock.patch.dict(os.environ, {}, clear=True):
        assert _get_request_timeout(module) is None


def test_get_request_timeout_from_module_params():
    module = MagicMock()
    module.params = {"request_timeout": 10.5}
    with mock.patch.dict(os.environ, {"K8S_AUTH_REQUEST_TIMEOUT": "99"}):
        assert _get_request_timeout(module) == 10.5


def test_get_request_timeout_from_kwargs():
    assert _get_request_timeout(None, request_timeout=7) == 7.0


@mock.patch.dict(os.environ, {"K8S_AUTH_REQUEST_TIMEOUT": "30"})
def test_get_request_timeout_from_env():
    module = MagicMock()
    module.params = {}
    assert _get_request_timeout(module) == 30.0


@pytest.mark.parametrize("value", ["abc", "0", "-5"])
def test_get_request_timeout_rejects_bad_values(value):
    module = MagicMock()
    module.params = {}
    with mock.patch.dict(os.environ, {"K8S_AUTH_REQUEST_TIMEOUT": value}):
        with pytest.raises(CoreException, match="request_timeout"):
            _get_request_timeout(module)


def _dynamic_client(request_timeout):
    seen = {}

    def fake_init(self, client, cache_file=None, discoverer=None):
        # Discovery runs in the parent constructor, so the timeout must be set already.
        seen["timeout"] = self.request_timeout
        self.client = client

    with mock.patch.object(DynamicClient, "__init__", fake_init):
        client = K8SDynamicClient(MagicMock(), request_timeout=request_timeout)
    return client, seen


@mock.patch.object(DynamicClient, "request")
def test_dynamic_client_sets_request_timeout(parent_request):
    client, seen = _dynamic_client(5.0)
    assert seen["timeout"] == (5.0, 5.0)

    client.request("get", "/api/v1/namespaces")

    parent_request.assert_called_once_with(
        "get", "/api/v1/namespaces", body=None, _request_timeout=(5.0, 5.0)
    )


@mock.patch.object(DynamicClient, "request")
def test_dynamic_client_keeps_explicit_request_timeout(parent_request):
    client, _ = _dynamic_client(5.0)

    client.request("get", "/api/v1/pods", _request_timeout=60)

    parent_request.assert_called_once_with(
        "get", "/api/v1/pods", body=None, _request_timeout=60
    )


@mock.patch.object(DynamicClient, "request")
def test_dynamic_client_skips_watch_requests(parent_request):
    client, _ = _dynamic_client(5.0)

    client.request("get", "/api/v1/pods", watch=True)

    parent_request.assert_called_once_with("get", "/api/v1/pods", body=None, watch=True)


@mock.patch.object(DynamicClient, "request")
def test_dynamic_client_without_request_timeout(parent_request):
    client, seen = _dynamic_client(None)
    assert seen["timeout"] is None

    client.request("get", "/api/v1/pods")

    parent_request.assert_called_once_with("get", "/api/v1/pods", body=None)


class _FakeCoreV1Api:
    def __init__(self, api_client):
        self.api_client = api_client
        self.calls = []

    def read_node(self, **kwargs):
        self.calls.append(kwargs)
        return "node"


def test_typed_api_applies_request_timeout():
    client, _ = _dynamic_client(5.0)

    api = client.typed_api(_FakeCoreV1Api)

    assert api.read_node(name="n1") == "node"
    assert api.read_node(name="n2", _request_timeout=60) == "node"
    assert api.read_node(name="n3", watch=True) == "node"
    assert api.calls == [
        {"name": "n1", "_request_timeout": (5.0, 5.0)},
        {"name": "n2", "_request_timeout": 60},
        {"name": "n3", "watch": True},
    ]
    assert api.api_client is client.client


def test_typed_api_without_request_timeout():
    client, _ = _dynamic_client(None)

    api = client.typed_api(_FakeCoreV1Api)

    assert isinstance(api, _FakeCoreV1Api)
    api.read_node(name="n1")
    assert api.calls == [{"name": "n1"}]


def test_get_api_client_reports_connection_errors():
    import urllib3
    from ansible_collections.kubernetes.core.plugins.module_utils.k8s import client

    module = MagicMock()
    module.params = {"host": TEST_HOST, "api_key": TEST_DATA, "request_timeout": 1}
    module.server_side_dry_run = False
    error = urllib3.exceptions.MaxRetryError(None, "/version", "connection refused")
    with mock.patch.object(client, "create_api_client", side_effect=error):
        with pytest.raises(CoreException, match="Could not connect to the API server"):
            client.get_api_client(module=module)


def test_get_api_client_reports_timeouts():
    import urllib3
    from ansible_collections.kubernetes.core.plugins.module_utils.k8s import client

    module = MagicMock()
    module.params = {"host": TEST_HOST, "api_key": TEST_DATA, "request_timeout": 1}
    module.server_side_dry_run = False
    error = urllib3.exceptions.MaxRetryError(
        None, "/version", urllib3.exceptions.ConnectTimeoutError(None, "timed out")
    )
    with mock.patch.object(client, "create_api_client", side_effect=error):
        with pytest.raises(CoreException, match="Timed out waiting for the API server"):
            client.get_api_client(module=module)
