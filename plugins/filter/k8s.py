# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""

name: k8s_config_resource_name
short_description: Generate resource name for the given resource of type ConfigMap, Secret
description:
  - Generate resource name for the given resource of type ConfigMap, Secret.
  - Resource must have a C(metadata.name) key to generate a resource name
options:
  _input:
    description:
      - A valid YAML definition for a ConfigMap or a Secret.
    type: dict
    required: true
author:
  - ansible cloud team

"""

EXAMPLES = r"""
# Dump generated name for a configmap into a variable
- set_fact:
    generated_name: '{{ definition | kubernetes.core.k8s_config_resource_name }}'
  vars:
    definition:
      apiVersion: v1
      kind: ConfigMap
      metadata:
        name: myconfigmap
        namespace: mynamespace
"""

RETURN = r"""
  _value:
    description: Generated resource name.
    type: str
"""


from ansible.errors import AnsibleFilterError
from ansible_collections.kubernetes.core.plugins.module_utils.hashes import (
    generate_hash,
)


def k8s_config_resource_name(resource):
    """
    Generate resource name for the given resource of type ConfigMap, Secret
    """
    try:
        return resource["metadata"]["name"] + "-" + generate_hash(resource)
    except KeyError:
        raise AnsibleFilterError(
            "resource must have a metadata.name key to generate a resource name"
        )


# ---- Ansible filters ----
class FilterModule(object):
    def filters(self):
        return {"k8s_config_resource_name": k8s_config_resource_name}
