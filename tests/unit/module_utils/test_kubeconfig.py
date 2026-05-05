# Copyright (c) Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import yaml
from ansible_collections.kubernetes.core.plugins.module_utils.kubeconfig import (
    deep_merge,
    hash_data,
    load_yaml_file,
    merge_by_name,
    write_file,
)


# load_yaml_file
def test_load_yaml_file_returns_empty_dict_for_missing_file():
    assert load_yaml_file("/nonexistent/path/config") == {}


def test_load_yaml_file_returns_empty_dict_for_none():
    assert load_yaml_file(None) == {}


def test_load_yaml_file_returns_empty_dict_for_empty_string():
    assert load_yaml_file("") == {}


def test_load_yaml_file_loads_valid_yaml(tmp_path):
    config = {"apiVersion": "v1", "kind": "Config", "clusters": []}
    f = tmp_path / "config"
    f.write_text(yaml.safe_dump(config))
    assert load_yaml_file(str(f)) == config


def test_load_yaml_file_returns_empty_dict_for_empty_file(tmp_path):
    f = tmp_path / "config"
    f.write_text("")
    assert load_yaml_file(str(f)) == {}


# deep_merge
def test_deep_merge_adds_new_keys():
    base = {"a": 1}
    updates = {"b": 2}
    assert deep_merge(base, updates) == {"a": 1, "b": 2}


def test_deep_merge_overwrites_scalar():
    base = {"a": 1}
    updates = {"a": 99}
    assert deep_merge(base, updates) == {"a": 99}


def test_deep_merge_recursively_merges_dicts():
    base = {
        "cluster": {
            "server": "https://old.example.com",
            "insecure-skip-tls-verify": True,
        }
    }
    updates = {"cluster": {"server": "https://new.example.com"}}
    result = deep_merge(base, updates)
    assert result["cluster"]["server"] == "https://new.example.com"
    assert result["cluster"]["insecure-skip-tls-verify"] is True


def test_deep_merge_does_not_mutate_base():
    base = {"a": {"b": 1}}
    updates = {"a": {"c": 2}}
    deep_merge(base, updates)
    assert base == {"a": {"b": 1}}


def test_deep_merge_overwrites_dict_with_scalar():
    base = {"a": {"nested": 1}}
    updates = {"a": "flat"}
    assert deep_merge(base, updates) == {"a": "flat"}


# merge_by_name
def test_merge_by_name_adds_new_entry():
    existing = []
    new = [{"name": "cluster-a", "cluster": {"server": "https://a.example.com"}}]
    result = merge_by_name(existing, new)
    assert len(result) == 1
    assert result[0]["name"] == "cluster-a"


def test_merge_by_name_preserves_existing_when_no_new():
    existing = [{"name": "cluster-a", "cluster": {"server": "https://a.example.com"}}]
    result = merge_by_name(existing, [])
    assert len(result) == 1
    assert result[0]["name"] == "cluster-a"


def test_merge_by_name_default_behavior_merges_fields():
    existing = [
        {
            "name": "cluster-a",
            "cluster": {"server": "https://old.com", "insecure-skip-tls-verify": True},
        }
    ]
    new = [{"name": "cluster-a", "cluster": {"server": "https://new.com"}}]
    result = merge_by_name(existing, new)
    assert len(result) == 1
    assert result[0]["cluster"]["server"] == "https://new.com"
    assert result[0]["cluster"]["insecure-skip-tls-verify"] is True


def test_merge_by_name_replace_behavior_replaces_entire_entry():
    existing = [
        {
            "name": "cluster-a",
            "cluster": {"server": "https://old.com", "insecure-skip-tls-verify": True},
        }
    ]
    new = [
        {
            "name": "cluster-a",
            "behavior": "replace",
            "cluster": {"server": "https://new.com"},
        }
    ]
    result = merge_by_name(existing, new)
    assert result[0]["cluster"] == {"server": "https://new.com"}
    assert "insecure-skip-tls-verify" not in result[0]["cluster"]


def test_merge_by_name_keep_behavior_preserves_existing():
    existing = [{"name": "cluster-a", "cluster": {"server": "https://old.com"}}]
    new = [
        {
            "name": "cluster-a",
            "behavior": "keep",
            "cluster": {"server": "https://new.com"},
        }
    ]
    result = merge_by_name(existing, new)
    assert result[0]["cluster"]["server"] == "https://old.com"


def test_merge_by_name_behavior_key_not_in_output():
    existing = []
    new = [
        {
            "name": "cluster-a",
            "behavior": "replace",
            "cluster": {"server": "https://a.com"},
        }
    ]
    result = merge_by_name(existing, new)
    assert "behavior" not in result[0]


def test_merge_by_name_skips_items_without_name():
    existing = []
    new = [{"cluster": {"server": "https://a.com"}}]
    result = merge_by_name(existing, new)
    assert result == []


def test_merge_by_name_skips_non_dict_items():
    existing = []
    new = ["not-a-dict", 42]
    result = merge_by_name(existing, new)
    assert result == []


def test_merge_by_name_adds_multiple_new_entries():
    existing = []
    new = [
        {"name": "cluster-a", "cluster": {"server": "https://a.com"}},
        {"name": "cluster-b", "cluster": {"server": "https://b.com"}},
    ]
    result = merge_by_name(existing, new)
    names = [r["name"] for r in result]
    assert "cluster-a" in names
    assert "cluster-b" in names


def test_merge_by_name_existing_non_dict_items_are_skipped():
    existing = ["not-a-dict", {"cluster": {"server": "https://a.com"}}]
    new = [{"name": "cluster-b", "cluster": {"server": "https://b.com"}}]
    result = merge_by_name(existing, new)
    assert len(result) == 1
    assert result[0]["name"] == "cluster-b"


# hash_data
def test_hash_data_returns_string():
    assert isinstance(hash_data({}), str)


def test_hash_data_different_input_different_hash():
    assert hash_data({"a": 1}) != hash_data({"a": 2})


def test_hash_data_order_independent():
    a = {"x": 1, "y": 2}
    b = {"y": 2, "x": 1}
    assert hash_data(a) == hash_data(b)


# write_file
def test_write_file_returns_false_for_empty_dest():
    assert write_file("", {"apiVersion": "v1"}) is False


def test_write_file_returns_false_for_none_dest():
    assert write_file(None, {"apiVersion": "v1"}) is False


def test_write_file_writes_valid_yaml(tmp_path):
    dest = str(tmp_path / "config")
    data = {"apiVersion": "v1", "kind": "Config"}
    result = write_file(dest, data)
    assert result is True
    with open(dest, "r") as f:
        written = yaml.safe_load(f)
    assert written == data


def test_write_file_overwrites_existing_file(tmp_path):
    dest = str(tmp_path / "config")
    write_file(dest, {"apiVersion": "v1"})
    write_file(dest, {"apiVersion": "v2"})
    with open(dest, "r") as f:
        written = yaml.safe_load(f)
    assert written["apiVersion"] == "v2"
