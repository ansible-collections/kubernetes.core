#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Will Thames <@willthames>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r'''
module: k8s_info

short_description: Describe Kubernetes (K8s) objects

author:
    - "Will Thames (@willthames)"

description:
  - Use the OpenShift Python client to perform read operations on K8s objects.
  - Access to the full range of K8s APIs.
  - Authenticate using either a config file, certificates, password or token.
  - Supports check mode.
  - This module was called C(k8s_facts) before Ansible 2.9. The usage did not change.

options:
  kind:
    description:
    - Use to specify an object model.
    - Use to create, delete, or discover an object without providing a full resource definition.
    - Use in conjunction with I(api_version), I(name), and I(namespace) to identify a specific object.
    - If I(resource definition) is provided, the I(kind) value from the I(resource_definition)
      will override this option.
    type: str
    required: True
  label_selectors:
    description: List of label selectors to use to filter results
    type: list
    elements: str
  field_selectors:
    description: List of field selectors to use to filter results
    type: list
    elements: str

extends_documentation_fragment:
  - kubernetes.core.k8s_auth_options
  - kubernetes.core.k8s_name_options
  - kubernetes.core.k8s_wait_options

requirements:
  - "python >= 2.7"
  - "openshift >= 0.6"
  - "PyYAML >= 3.11"
'''

EXAMPLES = r'''
- name: Get an existing Service object
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Service
    name: web
    namespace: testing
  register: web_service

- name: Get a list of all service objects
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Service
    namespace: testing
  register: service_list

- name: Get a list of all pods from any namespace
  kubernetes.core.k8s_info:
    kind: Pod
  register: pod_list

- name: Search for all Pods labelled app=web
  kubernetes.core.k8s_info:
    kind: Pod
    label_selectors:
      - app = web
      - tier in (dev, test)

- name: Using vars while using label_selectors
  kubernetes.core.k8s_info:
    kind: Pod
    label_selectors:
      - "app = {{ app_label_web }}"
  vars:
    app_label_web: web

- name: Search for all running pods
  kubernetes.core.k8s_info:
    kind: Pod
    field_selectors:
      - status.phase=Running

- name: List custom objects created using CRD
  kubernetes.core.k8s_info:
    kind: MyCustomObject
    api_version: "stable.example.com/v1"

- name: Wait till the Object is created
  kubernetes.core.k8s_info:
    kind: Pod
    wait: yes
    name: pod-not-yet-created
    namespace: default
    wait_sleep: 10
    wait_timeout: 360
'''

RETURN = r'''
api_found:
  description:
  - Whether the specified api_version and kind were successfully mapped to an existing API on the targeted cluster.
  - Version added 1.2.0.
  returned: always
  type: bool
resources:
  description:
  - The object(s) that exists
  returned: success
  type: complex
  contains:
    api_version:
      description: The versioned schema of this representation of an object.
      returned: success
      type: str
    kind:
      description: Represents the REST resource this object represents.
      returned: success
      type: str
    metadata:
      description: Standard object metadata. Includes name, namespace, annotations, labels, etc.
      returned: success
      type: dict
    spec:
      description: Specific attributes of the object. Will vary based on the I(api_version) and I(kind).
      returned: success
      type: dict
    status:
      description: Current status details for the object.
      returned: success
      type: dict
'''

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kubernetes.core.plugins.module_utils.common import (
    K8sAnsibleMixin, AUTH_ARG_SPEC, WAIT_ARG_SPEC)


class KubernetesInfoModule(K8sAnsibleMixin):

    def __init__(self, *args, **kwargs):
        module = AnsibleModule(
            argument_spec=self.argspec,
            supports_check_mode=True,
        )
        self.module = module
        self.params = self.module.params
        self.fail_json = self.module.fail_json
        self.exit_json = self.module.exit_json
        super(KubernetesInfoModule, self).__init__()

    def execute_module(self):
        self.client = self.get_api_client()

        self.exit_json(changed=False,
                       **self.kubernetes_facts(self.params['kind'],
                                               self.params['api_version'],
                                               name=self.params['name'],
                                               namespace=self.params['namespace'],
                                               label_selectors=self.params['label_selectors'],
                                               field_selectors=self.params['field_selectors'],
                                               wait=self.params['wait'],
                                               wait_sleep=self.params['wait_sleep'],
                                               wait_timeout=self.params['wait_timeout'],
                                               condition=self.params['wait_condition']))

    @property
    def argspec(self):
        args = copy.deepcopy(AUTH_ARG_SPEC)
        args.update(WAIT_ARG_SPEC)
        args.update(
            dict(
                kind=dict(required=True),
                api_version=dict(default='v1', aliases=['api', 'version']),
                name=dict(),
                namespace=dict(),
                label_selectors=dict(type='list', elements='str', default=[]),
                field_selectors=dict(type='list', elements='str', default=[]),
            )
        )
        return args


def main():
    KubernetesInfoModule().execute_module()


if __name__ == '__main__':
    main()
