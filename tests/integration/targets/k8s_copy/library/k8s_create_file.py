#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Aubin Bikouo <@abikouo>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""

module: k8s_create_file

short_description: Create large file with a defined size.

author:
    - Aubin Bikouo (@abikouo)

description:
  - This module is used to validate k8s_cp module.

options:
  path:
    description:
    - The destination path for the file to create.
    type: path
    required: yes
  size:
    description:
    - The size of the output file in MB.
    type: int
    default: 400
  binary:
    description:
    - If this flag is set to yes, the generated file content binary data.
    type: bool
    default: False
"""

EXAMPLES = r"""
- name: create 150MB file
  k8s_diff:
    path: large_file.txt
    size: 150
"""


RETURN = r"""
"""

import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def execute_module(module):
    try:
        size = module.params.get("size") * 1024 * 1024
        path = module.params.get("path")
        write_mode = "w"
        if module.params.get("binary"):
            content = os.urandom(size)
            write_mode = "wb"
        else:
            content = ""
            count = 0
            while len(content) < size:
                content += "This file has been generated using ansible: {0}\n".format(
                    count
                )
                count += 1

        with open(path, write_mode) as f:
            f.write(content)
        module.exit_json(changed=True, size=len(content))
    except Exception as e:
        module.fail_json(msg="failed to create file due to: {0}".format(to_native(e)))


def main():
    argument_spec = {}
    argument_spec["size"] = {"type": "int", "default": 400}
    argument_spec["path"] = {"type": "path", "required": True}
    argument_spec["binary"] = {"type": "bool", "default": False}
    module = AnsibleModule(argument_spec=argument_spec)

    execute_module(module)


if __name__ == "__main__":
    main()
