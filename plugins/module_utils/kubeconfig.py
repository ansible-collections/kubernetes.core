# Copyright (c) Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import hashlib
import os
import traceback

try:
    import yaml

    IMP_YAML = True
    IMP_YAML_ERR = None
except ImportError:
    IMP_YAML = False
    IMP_YAML_ERR = traceback.format_exc()


def load_yaml_file(path):
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def deep_merge(base, updates):
    result = base.copy()
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def merge_by_name(existing, new):
    merged = {}
    for item in existing:
        if isinstance(item, dict) and "name" in item:
            merged[item["name"]] = item

    for item in new:
        if not isinstance(item, dict) or "name" not in item:
            continue

        name = item["name"]
        behavior = item.get("behavior", "merge")
        item_copy = {k: v for k, v in item.items() if k != "behavior"}

        if name in merged:
            if behavior == "keep":
                continue
            elif behavior == "replace":
                merged[name] = item_copy
            else:
                result = {"name": name}
                for key in ["cluster", "user", "context"]:
                    if key in merged[name] or key in item_copy:
                        existing_config = merged[name].get(key, {})
                        new_config = item_copy.get(key, {})
                        result[key] = deep_merge(existing_config, new_config)
                for key in merged[name]:
                    if key not in ["name", "cluster", "user", "context"]:
                        result[key] = merged[name][key]
                for key in item_copy:
                    if (
                        key not in ["name", "cluster", "user", "context"]
                        and key not in result
                    ):
                        result[key] = item_copy[key]
                merged[name] = result
        else:
            merged[name] = item_copy

    return list(merged.values())


def hash_data(data):
    """Generate SHA-256 hash for idempotency checking."""
    return hashlib.sha256(yaml.safe_dump(data, sort_keys=True).encode()).hexdigest()


def write_file(dest, data):
    if not dest:
        return False
    with open(dest, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)
    return True
