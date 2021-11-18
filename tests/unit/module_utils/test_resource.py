import os
from pathlib import Path

from ansible_collections.kubernetes.core.plugins.module_utils.k8s.resource import (
    create_definitions,
    flatten_list_kind,
    from_file,
    from_yaml,
    merge_params,
)


def test_create_definitions_loads_from_definition():
    params = {
        "resource_definition": {
            "kind": "Pod",
            "apiVersion": "v1",
            "metadata": {"name": "foo", "namespace": "bar"},
        }
    }
    results = create_definitions(params)
    assert len(results) == 1
    assert results[0].kind == "Pod"
    assert results[0].api_version == "v1"
    assert results[0].name == "foo"
    assert results[0].namespace == "bar"


def test_create_definitions_loads_from_file():
    current = Path(os.path.dirname(os.path.abspath(__file__)))
    params = {"src": current / "fixtures/definitions.yml"}
    results = create_definitions(params)
    assert len(results) == 3
    assert results[0].kind == "Namespace"
    assert results[1].kind == "Pod"


def test_create_definitions_loads_from_params():
    params = {
        "kind": "Pod",
        "api_version": "v1",
        "name": "foo",
        "namespace": "foobar",
    }
    results = create_definitions(params)
    assert len(results) == 1
    assert results[0] == {
        "kind": "Pod",
        "apiVersion": "v1",
        "metadata": {"name": "foo", "namespace": "foobar"},
    }


def test_create_definitions_loads_list_kind():
    params = {
        "resource_definition": {
            "kind": "PodList",
            "apiVersion": "v1",
            "items": [
                {"kind": "Pod", "metadata": {"name": "foo"}},
                {"kind": "Pod", "metadata": {"name": "bar"}},
            ],
        }
    }
    results = create_definitions(params)
    assert len(results) == 2
    assert results[0].name == "foo"
    assert results[1].name == "bar"


def test_merge_params_does_not_overwrite():
    definition = {
        "kind": "Pod",
        "apiVersion": "v1",
        "metadata": {"name": "foo", "namespace": "bar"},
    }
    params = {
        "kind": "Service",
        "api_version": "v2",
        "name": "baz",
        "namespace": "gaz",
    }
    result = merge_params(definition, params)
    assert result == definition


def test_merge_params_adds_module_params():
    params = {
        "kind": "Pod",
        "api_version": "v1",
        "namespace": "bar",
        "generate_name": "foo-",
    }
    result = merge_params({}, params)
    assert result == {
        "kind": "Pod",
        "apiVersion": "v1",
        "metadata": {"generateName": "foo-", "namespace": "bar"},
    }


def test_from_yaml_loads_string_docs():
    definition = """
kind: Pod
apiVersion: v1
metadata:
  name: foo
  namespace: bar
---
kind: ConfigMap
apiVersion: v1
metadata:
  name: foo
  namespace: bar
"""
    result = list(from_yaml(definition))
    assert result[0]["kind"] == "Pod"
    assert result[1]["kind"] == "ConfigMap"


def test_from_yaml_loads_list():
    definition = [
        """
        kind: Pod
        apiVersion: v1
        metadata:
          name: foo
          namespace: bar
        """,
        """
        kind: ConfigMap
        apiVersion: v1
        metadata:
          name: foo
          namespace: bar
        """,
        {
            "kind": "Pod",
            "apiVersion": "v1",
            "metadata": {"name": "baz", "namespace": "bar"},
        },
    ]
    result = list(from_yaml(definition))
    assert len(result) == 3
    assert result[0]["kind"] == "Pod"
    assert result[1]["kind"] == "ConfigMap"
    assert result[2]["metadata"]["name"] == "baz"


def test_from_yaml_loads_dictionary():
    definition = {
        "kind": "Pod",
        "apiVersion": "v1",
        "metadata": {"name": "foo", "namespace": "bar"},
    }
    result = list(from_yaml(definition))
    assert result[0]["kind"] == "Pod"


def test_from_file_loads_definitions():
    current = Path(os.path.dirname(os.path.abspath(__file__)))
    result = list(from_file(current / "fixtures/definitions.yml"))
    assert result[0]["kind"] == "Namespace"
    assert result[1]["kind"] == "Pod"


def test_flatten_list_kind_flattens():
    definition = {
        "kind": "PodList",
        "apiVersion": "v1",
        "items": [
            {"kind": "Pod", "metadata": {"name": "foo"}},
            {"kind": "Pod", "metadata": {"name": "bar"}},
        ],
    }
    result = flatten_list_kind(definition, {"namespace": "foobar"})
    assert len(result) == 2

    assert result[0]["kind"] == "Pod"
    assert result[0]["apiVersion"] == "v1"
    assert result[0]["metadata"]["name"] == "foo"
    assert result[0]["metadata"]["namespace"] == "foobar"

    assert result[1]["kind"] == "Pod"
    assert result[1]["apiVersion"] == "v1"
    assert result[1]["metadata"]["name"] == "bar"
    assert result[1]["metadata"]["namespace"] == "foobar"
