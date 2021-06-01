#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2020, Abhijeet Kasurde
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
module: k8s_cluster_info

version_added: "0.11.1"

short_description: Describe Kubernetes (K8s) cluster, APIs available and their respective versions

author:
    - Abhijeet Kasurde (@Akasurde)

description:
  - Use the OpenShift Python client to perform read operations on K8s objects.
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
  - "python >= 2.7"
  - "openshift >= 0.6"
  - "PyYAML >= 3.11"
'''

EXAMPLES = r'''
- name: Get Cluster information
  kubernetes.core.k8s_cluster_info:
  register: api_status

- name: Do not invalidate cache before getting information
  kubernetes.core.k8s_cluster_info:
    invalidate_cache: False
  register: api_status
'''

RETURN = r'''
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
  - The API(s) that exists in dictionary
  returned: success
  type: dict
  contains:
    api_version:
      description: API version
      returned: success
      type: str
    categories:
      description: API categories
      returned: success
      type: list
    group_version:
      description: Resource Group version
      returned: success
      type: str
    kind:
      description: Resource kind
      returned: success
      type: str
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
    available_api_version:
      description: All available versions of the given API
      returned: success
      type: list
    preferred_api_version:
      description: Preferred version of the given API
      returned: success
      type: str
'''


import copy
import traceback

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.parsing.convert_bool import boolean
from ansible_collections.kubernetes.core.plugins.module_utils.common import K8sAnsibleMixin, AUTH_ARG_SPEC

try:
    try:
        from openshift import __version__ as version
        # >=0.10
        from openshift.dynamic.resource import ResourceList
    except ImportError:
        # <0.10
        from openshift.dynamic.client import ResourceList
    HAS_K8S_INSTANCE_HELPER = True
    k8s_import_exception = None
except ImportError:
    HAS_K8S_INSTANCE_HELPER = False
    k8s_import_exception = traceback.format_exc()


class KubernetesInfoModule(K8sAnsibleMixin):

    def __init__(self):
        module = AnsibleModule(
            argument_spec=self.argspec,
            supports_check_mode=True,
        )
        self.module = module
        self.params = self.module.params

        if not HAS_K8S_INSTANCE_HELPER:
            self.module.fail_json(msg=missing_required_lib("openshift >= 0.6.2", reason="for merge_type"),
                                  exception=k8s_import_exception)

        super(KubernetesInfoModule, self).__init__()

    def execute_module(self):
        self.client = self.get_api_client()
        invalidate_cache = boolean(self.module.params.get('invalidate_cache', True), strict=False)
        if invalidate_cache:
            self.client.resources.invalidate_cache()
        results = {}
        for resource in list(self.client.resources):
            resource = resource[0]
            if isinstance(resource, ResourceList):
                continue
            results[resource.group] = {
                'api_version': resource.group_version,
                'categories': resource.categories if resource.categories else [],
                'kind': resource.kind,
                'name': resource.name,
                'namespaced': resource.namespaced,
                'preferred': resource.preferred,
                'short_names': resource.short_names if resource.short_names else [],
                'singular_name': resource.singular_name,
            }
        configuration = self.client.configuration
        connection = {
            'cert_file': configuration.cert_file,
            'host': configuration.host,
            'password': configuration.password,
            'proxy': configuration.proxy,
            'ssl_ca_cert': configuration.ssl_ca_cert,
            'username': configuration.username,
            'verify_ssl': configuration.verify_ssl,
        }
        version_info = {
            'client': version,
            'server': self.client.version,
        }
        self.module.exit_json(changed=False, apis=results, connection=connection, version=version_info)

    @property
    def argspec(self):
        spec = copy.deepcopy(AUTH_ARG_SPEC)
        spec['invalidate_cache'] = dict(type='bool', default=True)
        return spec


def main():
    KubernetesInfoModule().execute_module()


if __name__ == '__main__':
    main()
