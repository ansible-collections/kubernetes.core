# Copyright [2017] [Red Hat, Inc.]
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


import pytest
from ansible_collections.kubernetes.core.plugins.module_utils.client.discovery import (
    LazyDiscoverer,
)
from ansible_collections.kubernetes.core.plugins.module_utils.client.resource import (
    ResourceList,
)
from ansible_collections.kubernetes.core.plugins.module_utils.k8sdynamicclient import (
    K8SDynamicClient,
)
from kubernetes.client import ApiClient
from kubernetes.dynamic import Resource


@pytest.fixture(scope="module")
def mock_namespace():
    return Resource(
        api_version="v1",
        kind="Namespace",
        name="namespaces",
        namespaced=False,
        preferred=True,
        prefix="api",
        shorter_names=["ns"],
        shortNames=["ns"],
        singularName="namespace",
        verbs=["create", "delete", "get", "list", "patch", "update", "watch"],
    )


@pytest.fixture(scope="module")
def mock_templates():
    return Resource(
        api_version="v1",
        kind="Template",
        name="templates",
        namespaced=True,
        preferred=True,
        prefix="api",
        shorter_names=[],
        shortNames=[],
        verbs=["create", "delete", "get", "list", "patch", "update", "watch"],
    )


@pytest.fixture(scope="module")
def mock_processedtemplates():
    return Resource(
        api_version="v1",
        kind="Template",
        name="processedtemplates",
        namespaced=True,
        preferred=True,
        prefix="api",
        shorter_names=[],
        shortNames=[],
        verbs=["create", "delete", "get", "list", "patch", "update", "watch"],
    )


@pytest.fixture(scope="module")
def mock_namespace_list(mock_namespace):
    ret = ResourceList(
        mock_namespace.client,
        mock_namespace.group,
        mock_namespace.api_version,
        mock_namespace.kind,
    )
    ret._ResourceList__base_resource = mock_namespace
    return ret


@pytest.fixture(scope="function", autouse=True)
def setup_client_monkeypatch(
    monkeypatch,
    mock_namespace,
    mock_namespace_list,
    mock_templates,
    mock_processedtemplates,
):
    def mock_load_server_info(self):
        self.__version = {"kubernetes": "mock-k8s-version"}

    def mock_parse_api_groups(self, request_resources=False):
        return {
            "api": {
                "": {
                    "v1": {
                        "Namespace": [mock_namespace],
                        "NamespaceList": [mock_namespace_list],
                        "Template": [mock_templates, mock_processedtemplates],
                    }
                }
            }
        }

    monkeypatch.setattr(LazyDiscoverer, "_load_server_info", mock_load_server_info)
    monkeypatch.setattr(LazyDiscoverer, "parse_api_groups", mock_parse_api_groups)


@pytest.fixture
def client(request):
    return K8SDynamicClient(ApiClient(), discoverer=LazyDiscoverer)


@pytest.mark.parametrize(
    ("attribute", "value"),
    [("name", "namespaces"), ("singular_name", "namespace"), ("short_names", ["ns"])],
)
def test_search_returns_single_and_list(
    client, mock_namespace, mock_namespace_list, attribute, value
):
    resources = client.resources.search(**{"api_version": "v1", attribute: value})

    assert len(resources) == 2
    assert mock_namespace in resources
    assert mock_namespace_list in resources


@pytest.mark.parametrize(
    ("attribute", "value"),
    [
        ("kind", "Namespace"),
        ("name", "namespaces"),
        ("singular_name", "namespace"),
        ("short_names", ["ns"]),
    ],
)
def test_get_returns_only_single(client, mock_namespace, attribute, value):
    resource = client.resources.get(**{"api_version": "v1", attribute: value})

    assert resource == mock_namespace


def test_get_namespace_list_kind(client, mock_namespace_list):
    resource = client.resources.get(api_version="v1", kind="NamespaceList")

    assert resource == mock_namespace_list


def test_search_multiple_resources_for_template(
    client, mock_templates, mock_processedtemplates
):
    resources = client.resources.search(api_version="v1", kind="Template")

    assert len(resources) == 2
    assert mock_templates in resources
    assert mock_processedtemplates in resources
