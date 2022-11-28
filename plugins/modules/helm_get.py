#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""

module: helm_get

short_description: Download extended information of a named release

version_added: "2.4.0"

author:
  - Aubin Bikouo (@abikouo)

description:
  - Gather information about the notes, hooks, supplied values, and generated manifest file of the given release.
  - Analogous to C(helm get).

options:
  binary_path:
    description:
      - The path of a helm binary to use.
    required: false
    type: path
  release_name:
    description:
      - Release name.
    required: true
    aliases: [ name ]
    type: str
  release_namespace:
    description:
      - namespace scope for this request.
    required: false
    aliases: [ namespace ]
    type: str
  release_revision:
    description:
      - Release revision
    required: false
    aliases: [ revision ]
    type: int
  release_info:
    description:
      - information to download for release.
      - if not provided, returns all information.
    type: list
    elements: str
    choices:
      - hooks
      - manifest
      - values
      - notes
  dump_all_values:
    description:
      - When I(release_info) is empty or contains C(values), this specifies
        whether to get user-specified values or all computed values.
    type: bool
    default: false
"""

EXAMPLES = r"""
- name: Get all hooks for a named release
  kubernetes.core.helm_get:
    release_name: my_release
    release_info:
        - hooks

- name: Get all values for a named release
  kubernetes.core.helm_get:
    release_name: my_release
    dump_all_values: true
    release_info:
        - hooks

- name: Get the manifest and the notes for helm release in namespace 'test'
  kubernetes.core.helm_get:
    release_name: my_release
    release_namespace: test
    release_info:
        - manifest
        - notes

- name: Get all information for a named release
  kubernetes.core.helm_get:
    release_name: my_release
"""

RETURN = r"""
hooks:
  type: list
  elements: dict
  description: the hooks for a named release.
  returned: If I(release_info) contains C(hooks) or is empty.
notes:
  type: str
  description: the notes for a named release.
  returned: If I(release_info) contains C(notes) or is empty.
manifest:
  type: list
  elements: dict
  description: the manifest for a named release.
  returned: If I(release_info) contains C(manifest) or is empty.
values:
  type: dict
  description: the values for a named release.
  returned: If I(release_info) contains C(values) or is empty.
"""


import json
import traceback

try:
    import yaml

    IMP_YAML = True
    IMP_YAML_ERR = None
except ImportError:
    IMP_YAML_ERR = traceback.format_exc()
    IMP_YAML = False

from ansible.module_utils.basic import missing_required_lib
from ansible_collections.kubernetes.core.plugins.module_utils.helm import (
    AnsibleHelmModule,
)


class HelmGet(object):

    HELM_GET_INFO = ("hooks", "values", "manifest", "notes")

    def __init__(self, module):

        self.module = module

        self.name = module.params.get("release_name")
        release_revision = module.params.get("release_revision")
        release_namespace = module.params.get("release_namespace")

        common_options = []
        if release_revision:
            common_options.append("--revision " + release_revision)

        if release_revision:
            common_options.append("--namespace " + release_namespace)

        self.common_options = " ".join(common_options)

    def parse_yaml_content(self, content):

        if not IMP_YAML:
            self.module.fail_json(
                msg=missing_required_lib("yaml"), exception=IMP_YAML_ERR
            )

        try:
            return list(yaml.safe_load_all(content))
        except (IOError, yaml.YAMLError) as exc:
            self.module.fail_json(
                msg="Error parsing YAML content: {0}".format(exc), raw_data=content
            )

    def hooks(self):

        command = [
            self.module.get_helm_binary(),
            "get",
            "hooks",
            self.name,
            self.common_options,
        ]
        rc, out, err = self.module.run_helm_command(" ".join(command))
        if rc != 0:
            self.module.fail_json(msg=err)
        return self.parse_yaml_content(out)

    def values(self):

        command = [
            self.module.get_helm_binary(),
            "get",
            "values",
            self.name,
            self.common_options,
            " --output json",
        ]
        if self.module.params.get("dump_all_values"):
            command.append("--all")

        rc, out, err = self.module.run_helm_command(" ".join(command))
        if rc != 0:
            self.module.fail_json(msg=err)
        if out.rstrip("\n") == "null":
            return None
        return json.loads(out)

    def manifest(self):

        command = [
            self.module.get_helm_binary(),
            "get",
            "manifest",
            self.name,
            self.common_options,
        ]
        rc, out, err = self.module.run_helm_command(" ".join(command))
        if rc != 0:
            self.module.fail_json(msg=err)
        return self.parse_yaml_content(out)

    def notes(self):

        command = [
            self.module.get_helm_binary(),
            "get",
            "notes",
            self.name,
            self.common_options,
        ]
        rc, out, err = self.module.run_helm_command(" ".join(command))
        if rc != 0:
            self.module.fail_json(msg=err)
        return out

    def execute(self):

        release_info = self.module.params.get("release_info") or self.HELM_GET_INFO

        result = {}
        for info in release_info:
            func = getattr(self, info)
            result[info] = func()

        return result


def main():
    module = AnsibleHelmModule(
        argument_spec=dict(
            binary_path=dict(type="path"),
            release_name=dict(required=True, aliases=["name"]),
            release_namespace=dict(aliases=["namespace"]),
            release_revision=dict(type="int", aliases=["revision"]),
            release_info=dict(
                type="list",
                elements="str",
                choices=["hooks", "manifest", "notes", "values"],
                default=[],
            ),
            dump_all_values=dict(type="bool", default=False),
        )
    )

    helm_get = HelmGet(module)

    module.exit_json(**helm_get.execute())


if __name__ == "__main__":
    main()
