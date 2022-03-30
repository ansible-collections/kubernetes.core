#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: helm_plugin_info
short_description: Gather information about Helm plugins
version_added: "1.0.0"
author:
  - Abhijeet Kasurde (@Akasurde)
requirements:
  - "helm (https://github.com/helm/helm/releases)"
description:
  -  Gather information about Helm plugins installed in namespace.
options:
#Helm options
  plugin_name:
    description:
      - Name of Helm plugin, to gather particular plugin info.
    type: str
extends_documentation_fragment:
  - kubernetes.core.helm_common_options
"""

EXAMPLES = r"""
- name: Gather Helm plugin info
  kubernetes.core.helm_plugin_info:

- name: Gather Helm env plugin info
  kubernetes.core.helm_plugin_info:
    plugin_name: env
"""

RETURN = r"""
stdout:
  type: str
  description: Full `helm` command stdout, in case you want to display it or examine the event log
  returned: always
  sample: ''
stderr:
  type: str
  description: Full `helm` command stderr, in case you want to display it or examine the event log
  returned: always
  sample: ''
command:
  type: str
  description: Full `helm` command built by this module, in case you want to re-run the command outside the module or debug a problem.
  returned: always
  sample: helm plugin list ...
plugin_list:
  type: list
  description: Helm plugin dict inside a list
  returned: always
  sample: {
      "name": "env",
      "version": "0.1.0",
      "description": "Print out the helm environment."
  }
rc:
  type: int
  description: Helm plugin command return code
  returned: always
  sample: 1
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_collections.kubernetes.core.plugins.module_utils.helm import (
    get_helm_plugin_list,
    parse_helm_plugin_list,
)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            binary_path=dict(type="path"),
            plugin_name=dict(
                type="str",
            ),
            # Helm options
            context=dict(
                type="str",
                aliases=["kube_context"],
                fallback=(env_fallback, ["K8S_AUTH_CONTEXT"]),
            ),
            kubeconfig=dict(
                type="path",
                aliases=["kubeconfig_path"],
                fallback=(env_fallback, ["K8S_AUTH_KUBECONFIG"]),
            ),
            # Generic auth key
            host=dict(type="str", fallback=(env_fallback, ["K8S_AUTH_HOST"])),
            ca_cert=dict(
                type="path",
                aliases=["ssl_ca_cert"],
                fallback=(env_fallback, ["K8S_AUTH_SSL_CA_CERT"]),
            ),
            validate_certs=dict(
                type="bool",
                default=True,
                aliases=["verify_ssl"],
                fallback=(env_fallback, ["K8S_AUTH_VERIFY_SSL"]),
            ),
            api_key=dict(
                type="str", no_log=True, fallback=(env_fallback, ["K8S_AUTH_API_KEY"])
            ),
        ),
        mutually_exclusive=[
            ("context", "ca_cert"),
            ("context", "validate_certs"),
            ("kubeconfig", "ca_cert"),
            ("kubeconfig", "validate_certs"),
        ],
        supports_check_mode=True,
    )

    bin_path = module.params.get("binary_path")

    if bin_path is not None:
        helm_cmd_common = bin_path
    else:
        helm_cmd_common = "helm"

    helm_cmd_common = module.get_bin_path(helm_cmd_common, required=True)

    helm_cmd_common += " plugin"

    plugin_name = module.params.get("plugin_name")

    plugin_list = []

    rc, output, err = get_helm_plugin_list(module, helm_bin=helm_cmd_common)

    out = parse_helm_plugin_list(module, output=output.splitlines())

    for line in out:
        if plugin_name is None:
            plugin_list.append(
                {"name": line[0], "version": line[1], "description": line[2]}
            )
            continue

        if plugin_name == line[0]:
            plugin_list.append(
                {"name": line[0], "version": line[1], "description": line[2]}
            )
            break

    module.exit_json(
        changed=True,
        command=helm_cmd_common + " list",
        stdout=output,
        stderr=err,
        rc=rc,
        plugin_list=plugin_list,
    )


if __name__ == "__main__":
    main()
