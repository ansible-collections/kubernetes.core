#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2020, Abhijeet Kasurde
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
module: k8s_cluster_info

version_added: "0.11.1"

short_description: Describe Kubernetes (K8s) cluster, APIs available and their respective versions

author:
    - Abhijeet Kasurde (@Akasurde)

description:
  - Use the Kubernetes Python client to perform read operations on K8s objects.
  - Authenticate using either a config file, certificates, password or token.
  - Supports check mode.

options:
  invalidate_cache:
    description:
    - Invalidate cache before retrieving information about cluster.
    type: bool
    default: True

extends_documentation_fragment:
  - kubernetes.core.k8s_auth_options

requirements:
  - "python >= 3.6"
  - "kubernetes >= 12.0.0"
  - "PyYAML >= 3.11"
"""

EXAMPLES = r"""
- name: Get Cluster information
  kubernetes.core.k8s_cluster_info:
  register: api_status

- name: Do not invalidate cache before getting information
  kubernetes.core.k8s_cluster_info:
    invalidate_cache: False
  register: api_status
"""

RETURN = r"""
connection:
  description:
  - Connection information
  returned: success
  type: dict
  contains:
    cert_file:
      description:
      - Path to client certificate.
      type: str
      returned: success
    host:
      description:
      - Host URL
      type: str
      returned: success
    password:
      description:
      - User password
      type: str
      returned: success
    proxy:
      description:
      - Proxy details
      type: str
      returned: success
    ssl_ca_cert:
      description:
      - Path to CA certificate
      type: str
      returned: success
    username:
      description:
      - Username
      type: str
      returned: success
    verify_ssl:
      description:
      - SSL verification status
      type: bool
      returned: success
version:
  description:
  - Information about server and client version
  returned: success
  type: dict
  contains:
    server:
      description: Server version
      returned: success
      type: dict
    client:
      description: Client version
      returned: success
      type: str
apis:
  description:
  - dictionary of group + version of resource found from cluster
  returned: success
  type: dict
  elements: dict
  contains:
    categories:
      description: API categories
      returned: success
      type: list
    name:
      description: Resource short name
      returned: success
      type: str
    namespaced:
      description: If resource is namespaced
      returned: success
      type: bool
    preferred:
      description: If resource version preferred
      returned: success
      type: bool
    short_names:
      description: Resource short names
      returned: success
      type: str
    singular_name:
      description: Resource singular name
      returned: success
      type: str
"""


import copy
import traceback
from collections import defaultdict

HAS_K8S = False
try:
    from ansible_collections.kubernetes.core.plugins.module_utils.client.resource import (
        ResourceList,
    )

    HAS_K8S = True
except ImportError as e:
    K8S_IMP_ERR = e
    K8S_IMP_EXC = traceback.format_exc()

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.parsing.convert_bool import boolean
from ansible_collections.kubernetes.core.plugins.module_utils.ansiblemodule import (
    AnsibleModule,
)
from ansible_collections.kubernetes.core.plugins.module_utils.args_common import (
    AUTH_ARG_SPEC,
)


def execute_module(module, client):
    invalidate_cache = boolean(
        module.params.get("invalidate_cache", True), strict=False
    )
    if invalidate_cache:
        client.resources.invalidate_cache()
    results = defaultdict(dict)
    for resource in list(client.resources):
        resource = resource[0]
        if isinstance(resource, ResourceList):
            continue
        key = (
            resource.group_version
            if resource.group == ""
            else "/".join([resource.group, resource.group_version.split("/")[-1]])
        )
        results[key][resource.kind] = {
            "categories": resource.categories if resource.categories else [],
            "name": resource.name,
            "namespaced": resource.namespaced,
            "preferred": resource.preferred,
            "short_names": resource.short_names if resource.short_names else [],
            "singular_name": resource.singular_name,
        }
    configuration = client.configuration
    connection = {
        "cert_file": configuration.cert_file,
        "host": configuration.host,
        "password": configuration.password,
        "proxy": configuration.proxy,
        "ssl_ca_cert": configuration.ssl_ca_cert,
        "username": configuration.username,
        "verify_ssl": configuration.verify_ssl,
    }
    from kubernetes import __version__ as version

    version_info = {
        "client": version,
        "server": client.version,
    }
    module.exit_json(
        changed=False, apis=results, connection=connection, version=version_info
    )


def argspec():
    spec = copy.deepcopy(AUTH_ARG_SPEC)
    spec["invalidate_cache"] = dict(type="bool", default=True)
    return spec


def main():
    module = AnsibleModule(argument_spec=argspec(), supports_check_mode=True)
    if not HAS_K8S:
        module.fail_json(
            msg=missing_required_lib("kubernetes"),
            exception=K8S_IMP_EXC,
            error=to_native(K8S_IMP_ERR),
        )
    from ansible_collections.kubernetes.core.plugins.module_utils.common import (
        get_api_client,
    )

    execute_module(module, client=get_api_client(module=module))


if __name__ == "__main__":
    main()
