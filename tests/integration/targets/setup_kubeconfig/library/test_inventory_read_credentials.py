#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Aubin Bikouo <@abikouo>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""

module: test_inventory_read_credentials

short_description: Generate cert_file, key_file, host and server certificate

author:
    - Aubin Bikouo (@abikouo)

description:
  - This module is used for integration testing only for this collection
  - The module load a kube_config file and generate parameters used to authenticate the client.

options:
  kube_config:
    description:
    - Path to a valid kube config file to test.
    type: path
    required: yes
  dest_dir:
    description:
    - Path to a directory where file will be generated.
    type: path
    required: yes
"""

EXAMPLES = r"""
- name: Generate authentication parameters for current context
  test_inventory_read_credentials:
    kube_config: ~/.kube/config
    dest_dir: /tmp
"""


RETURN = """
auth:
    description:
        - User information used to authenticate to the cluster.
    returned: always
    type: complex
    contains:
        cert_file:
            description:
                - Path to the generated user certificate file.
            type: str
        key_file:
            description:
                - Path to the generated user key file.
            type: str
        ssl_ca_cert:
            description:
                - Path to the generated server certificate file.
            type: str
        host:
            description:
                - Path to the file containing cluster host.
            type: str
"""

import os
import shutil

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.client import (
    get_api_client,
)


class K8SInventoryTestModule(AnsibleModule):
    def __init__(self):
        argument_spec = dict(
            kube_config=dict(required=True, type="path"),
            dest_dir=dict(required=True, type="path"),
        )

        super(K8SInventoryTestModule, self).__init__(argument_spec=argument_spec)
        self.execute_module()

    def execute_module(self):
        dest_dir = os.path.abspath(self.params.get("dest_dir"))
        kubeconfig_path = self.params.get("kube_config")
        if not os.path.isdir(dest_dir):
            self.fail_json(
                msg="The following {0} does not exist or is not a directory.".format(
                    dest_dir
                )
            )
        if not os.path.isfile(kubeconfig_path):
            self.fail_json(
                msg="The following {0} does not exist or is not a valid file.".format(
                    kubeconfig_path
                )
            )

        client = get_api_client(kubeconfig=kubeconfig_path)

        result = dict(host=os.path.join(dest_dir, "host_data.txt"))
        # create file containing host information
        with open(result["host"], "w") as fd:
            fd.write(client.configuration.host)
        for key in ("cert_file", "key_file", "ssl_ca_cert"):
            dest_file = os.path.join(dest_dir, "{0}_data.txt".format(key))
            shutil.copyfile(getattr(client.configuration, key), dest_file)
            result[key] = dest_file

        self.exit_json(auth=result)


def main():
    K8SInventoryTestModule()


if __name__ == "__main__":
    main()
