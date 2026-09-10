# Copyright (c) 2026 Yuriy Novostavskiy
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.
#
# This file is licensed permissively rather than under the collection's
# GPL-3.0-or-later because it lives outside plugins/ and imports no
# GPL-licensed code: membership is read statically with ast, so nothing from
# ansible-core or plugins/ is imported. See the collection requirements,
# "Licensing" section.

# Guards the action groups declared in meta/runtime.yml.
#
# A module belongs in an action group if and only if it accepts that group's
# shared authentication options, because module_defaults set on a group is
# applied to every member. A member that does not accept the options fails with
# "Unsupported parameters"; a non-member that does accept them silently ignores
# the defaults the user set. Both directions are bugs, so both are asserted.
#
# Membership is derived from whether a module builds its argument spec from the
# shared constant, which is how every module in the collection does it today.

import ast
import os

import pytest
import yaml

COLLECTION_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
MODULES_DIR = os.path.join(COLLECTION_ROOT, "plugins", "modules")
RUNTIME_YML = os.path.join(COLLECTION_ROOT, "meta", "runtime.yml")

# action group -> the module_utils file defining its shared spec, and the constant name
SHARED_ARG_SPECS = {
    "k8s": {"module_utils": "args_common", "constant": "AUTH_ARG_SPEC"},
    "helm": {"module_utils": "helm_args_common", "constant": "HELM_AUTH_ARG_SPEC"},
}

# Modules that intentionally stay out of the groups, with the reason. Listed
# explicitly so that adding one back is a deliberate decision rather than an
# oversight. See https://github.com/ansible-collections/kubernetes.core/issues/577
EXCLUDED_FROM_GROUPS = {
    "helm_pull": "accepts only binary_path, not the shared helm auth options",
    "helm_template": "accepts only binary_path, not the shared helm auth options",
    "helm_registry_auth": "its 'host' is an OCI registry URL, not a Kubernetes API server",
    "kubeconfig": "writes a kubeconfig file locally, takes no cluster connection options",
}


def _module_names():
    return sorted(
        name[:-3]
        for name in os.listdir(MODULES_DIR)
        if name.endswith(".py") and name != "__init__.py"
    )


def _shared_specs_used_by(module_name):
    """Return the shared arg-spec constants a module imports."""
    path = os.path.join(MODULES_DIR, module_name + ".py")
    with open(path, "rb") as handle:
        tree = ast.parse(handle.read(), filename=path)

    group_of_constant = {
        spec["constant"]: group for group, spec in SHARED_ARG_SPECS.items()
    }
    modules_of_interest = {spec["module_utils"] for spec in SHARED_ARG_SPECS.values()}

    used = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or not node.module:
            continue
        if node.module.rsplit(".", 1)[-1] not in modules_of_interest:
            continue
        for alias in node.names:
            if alias.name in group_of_constant:
                used.add(group_of_constant[alias.name])
    return used


@pytest.fixture(scope="module")
def action_groups():
    with open(RUNTIME_YML) as handle:
        return yaml.safe_load(handle)["action_groups"]


def test_runtime_declares_expected_action_groups(action_groups):
    assert set(action_groups) == set(SHARED_ARG_SPECS), (
        "meta/runtime.yml declares action groups this test does not know about. "
        "Add the new group and its shared arg-spec constant to SHARED_ARG_SPECS."
    )


@pytest.mark.parametrize("group", sorted(SHARED_ARG_SPECS))
def test_action_group_members_exist(action_groups, group):
    known = set(_module_names())
    missing = sorted(set(action_groups[group]) - known)
    assert not missing, (
        "meta/runtime.yml lists modules in the '%s' action group that do not exist "
        "under plugins/modules/: %s" % (group, ", ".join(missing))
    )


@pytest.mark.parametrize("group", sorted(SHARED_ARG_SPECS))
def test_action_group_matches_shared_arg_spec_users(action_groups, group):
    constant = SHARED_ARG_SPECS[group]["constant"]
    declared = set(action_groups[group])
    actual = {name for name in _module_names() if group in _shared_specs_used_by(name)}

    missing_from_group = sorted(actual - declared)
    assert not missing_from_group, (
        "%s build their argument spec from %s but are not listed in the '%s' action "
        "group, so module_defaults set on that group silently does not reach them. "
        "Add them to meta/runtime.yml."
        % (", ".join(missing_from_group), constant, group)
    )

    not_shared = sorted(declared - actual)
    assert not not_shared, (
        "%s are listed in the '%s' action group but do not build their argument spec "
        "from %s, so module_defaults set on that group will fail for them with "
        "'Unsupported parameters'. Remove them from meta/runtime.yml."
        % (", ".join(not_shared), group, constant)
    )


@pytest.mark.parametrize("module_name,reason", sorted(EXCLUDED_FROM_GROUPS.items()))
def test_excluded_modules_stay_out_of_action_groups(action_groups, module_name, reason):
    assert module_name in _module_names(), (
        "%s is listed in EXCLUDED_FROM_GROUPS but no longer exists; drop the entry."
        % module_name
    )

    for group, members in action_groups.items():
        assert module_name not in members, (
            "%s was added to the '%s' action group, but it %s. If it now accepts the "
            "group's shared authentication options, remove it from EXCLUDED_FROM_GROUPS "
            "in this test as well." % (module_name, group, reason)
        )

    assert not _shared_specs_used_by(module_name), (
        "%s now builds its argument spec from a shared auth spec, so the reason it was "
        "excluded (%s) no longer holds. Add it to the matching action group and remove "
        "it from EXCLUDED_FROM_GROUPS." % (module_name, reason)
    )
