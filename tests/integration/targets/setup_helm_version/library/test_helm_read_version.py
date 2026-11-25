#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Aubin Bikouo <@abikouo>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""

module: test_helm_read_version

short_description: Retrieve helm version.

author:
    - Aubin Bikouo (@abikouo)

description:
  - This module is used for integration testing only for this collection.
  - The module runs the command to retrieve the helm version.

options:
  binary_path:
    description:
      - The path of a helm binary to use.
    required: false
    type: path
"""


RETURN = """
helm_version:
    description:
        - The helm version.
    returned: always
    type: str
"""

from ansible_collections.kubernetes.core.plugins.module_utils.helm import (
    AnsibleHelmModule,
)


def main():
    module = AnsibleHelmModule(
        argument_spec=dict(
            binary_path=dict(type="path"),
        ),
        supports_check_mode=True,
    )

    helm_version = module.get_helm_version()
    module.exit_json(changed=False, helm_version=helm_version)


if __name__ == "__main__":
    main()
