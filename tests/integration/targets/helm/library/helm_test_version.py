#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: helm_test_version
short_description: check helm executable version
author:
  - Aubin Bikouo (@abikouo)
requirements:
  - "helm (https://github.com/helm/helm/releases)"
description:
  -  validate version of helm binary is lower than the specified version.
options:
  binary_path:
    description:
      - The path of a helm binary to use.
    required: false
    type: path
  version:
    description:
      - version to test against helm binary.
    type: str
    default: 3.7.0
"""

EXAMPLES = r"""
- name: validate helm binary version is lower than 3.5.0
  helm_test_version:
    binary_path: path/to/helm
    version: "3.5.0"
"""

RETURN = r"""
message:
  type: str
  description: Text message describing the test result.
  returned: always
  sample: 'version installed: 3.4.5 is lower than version 3.5.0'
result:
  type: bool
  description: Test result.
  returned: always
  sample: 1
"""

import re

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kubernetes.core.plugins.module_utils.version import (
    LooseVersion,
)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            binary_path=dict(type="path"),
            version=dict(type="str", default="3.7.0"),
        ),
    )

    bin_path = module.params.get("binary_path")
    version = module.params.get("version")

    if bin_path is not None:
        helm_cmd_common = bin_path
    else:
        helm_cmd_common = "helm"

    helm_cmd_common = module.get_bin_path(helm_cmd_common, required=True)
    rc, out, err = module.run_command([helm_cmd_common, "version"])
    if rc != 0:
        module.fail_json(msg="helm version failed.", err=err, out=out, rc=rc)

    m = re.match(r'version.BuildInfo{Version:"v([0-9\.]*)",', out)
    installed_version = m.group(1)

    message = "version installed: %s" % installed_version
    if LooseVersion(installed_version) < LooseVersion(version):
        message += " is lower than version %s" % version
        module.exit_json(changed=False, result=True, message=message)
    else:
        message += " is greater than version %s" % version
        module.exit_json(changed=False, result=False, message=message)


if __name__ == "__main__":
    main()
