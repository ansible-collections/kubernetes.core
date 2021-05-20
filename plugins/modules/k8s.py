#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Chris Houseknecht <@chouseknecht>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r'''

module: k8s

short_description: Manage Kubernetes (K8s) objects

author:
    - "Chris Houseknecht (@chouseknecht)"
    - "Fabian von Feilitzsch (@fabianvf)"

description:
  - Use the OpenShift Python client to perform CRUD operations on K8s objects.
  - Pass the object definition from a source file or inline. See examples for reading
    files and using Jinja templates or vault-encrypted files.
  - Access to the full range of K8s APIs.
  - Use the M(kubernetes.core.k8s_info) module to obtain a list of items about an object of type C(kind)
  - Authenticate using either a config file, certificates, password or token.
  - Supports check mode.

extends_documentation_fragment:
  - kubernetes.core.k8s_state_options
  - kubernetes.core.k8s_name_options
  - kubernetes.core.k8s_resource_options
  - kubernetes.core.k8s_auth_options
  - kubernetes.core.k8s_wait_options
  - kubernetes.core.k8s_delete_options

notes:
  - If your OpenShift Python library is not 0.9.0 or newer and you are trying to
    remove an item from an associative array/dictionary, for example a label or
    an annotation, you will need to explicitly set the value of the item to be
    removed to `null`. Simply deleting the entry in the dictionary will not
    remove it from openshift or kubernetes.

options:
  merge_type:
    description:
    - Whether to override the default patch merge approach with a specific type. By default, the strategic
      merge will typically be used.
    - For example, Custom Resource Definitions typically aren't updatable by the usual strategic merge. You may
      want to use C(merge) if you see "strategic merge patch format is not supported"
    - See U(https://kubernetes.io/docs/tasks/run-application/update-api-object-kubectl-patch/#use-a-json-merge-patch-to-update-a-deployment)
    - Requires openshift >= 0.6.2
    - If more than one merge_type is given, the merge_types will be tried in order
    - If openshift >= 0.6.2, this defaults to C(['strategic-merge', 'merge']), which is ideal for using the same parameters
      on resource kinds that combine Custom Resources and built-in resources. For openshift < 0.6.2, the default
      is simply C(strategic-merge).
    - mutually exclusive with C(apply)
    choices:
    - json
    - merge
    - strategic-merge
    type: list
    elements: str
  validate:
    description:
      - how (if at all) to validate the resource definition against the kubernetes schema.
        Requires the kubernetes-validate python module and openshift >= 0.8.0
    suboptions:
      fail_on_error:
        description: whether to fail on validation errors.
        type: bool
      version:
        description: version of Kubernetes to validate against. defaults to Kubernetes server version
        type: str
      strict:
        description: whether to fail when passing unexpected properties
        default: True
        type: bool
    type: dict
  append_hash:
    description:
    - Whether to append a hash to a resource name for immutability purposes
    - Applies only to ConfigMap and Secret resources
    - The parameter will be silently ignored for other resource kinds
    - The full definition of an object is needed to generate the hash - this means that deleting an object created with append_hash
      will only work if the same object is passed with state=absent (alternatively, just use state=absent with the name including
      the generated hash and append_hash=no)
    - Requires openshift >= 0.7.2
    default: False
    type: bool
  apply:
    description:
    - C(apply) compares the desired resource definition with the previously supplied resource definition,
      ignoring properties that are automatically generated
    - C(apply) works better with Services than 'force=yes'
    - Requires openshift >= 0.9.2
    - mutually exclusive with C(merge_type)
    default: False
    type: bool
  template:
    description:
    - Provide a valid YAML template definition file for an object when creating or updating.
    - Value can be provided as string or dictionary.
    - Mutually exclusive with C(src) and C(resource_definition).
    - Template files needs to be present on the Ansible Controller's file system.
    - Additional parameters can be specified using dictionary.
    - 'Valid additional parameters - '
    - 'C(newline_sequence) (str): Specify the newline sequence to use for templating files.
      valid choices are "\n", "\r", "\r\n". Default value "\n".'
    - 'C(block_start_string) (str): The string marking the beginning of a block.
      Default value "{%".'
    - 'C(block_end_string) (str): The string marking the end of a block.
      Default value "%}".'
    - 'C(variable_start_string) (str): The string marking the beginning of a print statement.
      Default value "{{".'
    - 'C(variable_end_string) (str): The string marking the end of a print statement.
      Default value "}}".'
    - 'C(trim_blocks) (bool): Determine when newlines should be removed from blocks. When set to C(yes) the first newline
       after a block is removed (block, not variable tag!). Default value is true.'
    - 'C(lstrip_blocks) (bool): Determine when leading spaces and tabs should be stripped.
      When set to C(yes) leading spaces and tabs are stripped from the start of a line to a block.
      This functionality requires Jinja 2.7 or newer. Default value is false.'
    type: raw

requirements:
  - "python >= 2.7"
  - "openshift >= 0.6"
  - "PyYAML >= 3.11"
'''

EXAMPLES = r'''
- name: Create a k8s namespace
  kubernetes.core.k8s:
    name: testing
    api_version: v1
    kind: Namespace
    state: present

- name: Create a Service object from an inline definition
  kubernetes.core.k8s:
    state: present
    definition:
      apiVersion: v1
      kind: Service
      metadata:
        name: web
        namespace: testing
        labels:
          app: galaxy
          service: web
      spec:
        selector:
          app: galaxy
          service: web
        ports:
        - protocol: TCP
          targetPort: 8000
          name: port-8000-tcp
          port: 8000

- name: Remove an existing Service object
  kubernetes.core.k8s:
    state: absent
    api_version: v1
    kind: Service
    namespace: testing
    name: web

# Passing the object definition from a file

- name: Create a Deployment by reading the definition from a local file
  kubernetes.core.k8s:
    state: present
    src: /testing/deployment.yml

- name: >-
    Read definition file from the Ansible controller file system.
    If the definition file has been encrypted with Ansible Vault it will automatically be decrypted.
  kubernetes.core.k8s:
    state: present
    definition: "{{ lookup('file', '/testing/deployment.yml') | from_yaml }}"

- name: Read definition template file from the Ansible controller file system
  kubernetes.core.k8s:
    state: present
    template: '/testing/deployment.j2'

- name: Read definition template file from the Ansible controller file system that uses custom start/end strings
  kubernetes.core.k8s:
    state: present
    template:
      path: '/testing/deployment.j2'
      variable_start_string: '[['
      variable_end_string: ']]'

- name: fail on validation errors
  kubernetes.core.k8s:
    state: present
    definition: "{{ lookup('template', '/testing/deployment.yml') | from_yaml }}"
    validate:
      fail_on_error: yes

- name: warn on validation errors, check for unexpected properties
  kubernetes.core.k8s:
    state: present
    definition: "{{ lookup('template', '/testing/deployment.yml') | from_yaml }}"
    validate:
      fail_on_error: no
      strict: yes

# Download and apply manifest
- name: Download metrics-server manifest to the cluster.
  ansible.builtin.get_url:
    url: https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
    dest: ~/metrics-server.yaml
    mode: '0664'

- name: Apply metrics-server manifest to the cluster.
  kubernetes.core.k8s:
    state: present
    src: ~/metrics-server.yaml
'''

RETURN = r'''
result:
  description:
  - The created, patched, or otherwise present object. Will be empty in the case of a deletion.
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
       type: complex
     spec:
       description: Specific attributes of the object. Will vary based on the I(api_version) and I(kind).
       returned: success
       type: complex
     status:
       description: Current status details for the object.
       returned: success
       type: complex
     items:
       description: Returned only when multiple yaml documents are passed to src or resource_definition
       returned: when resource_definition or src contains list of objects
       type: list
     duration:
       description: elapsed time of task in seconds
       returned: when C(wait) is true
       type: int
       sample: 48
'''

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kubernetes.core.plugins.module_utils.common import (
    K8sAnsibleMixin, COMMON_ARG_SPEC, NAME_ARG_SPEC, RESOURCE_ARG_SPEC, AUTH_ARG_SPEC,
    WAIT_ARG_SPEC, DELETE_OPTS_ARG_SPEC)


class KubernetesModule(K8sAnsibleMixin):

    @property
    def validate_spec(self):
        return dict(
            fail_on_error=dict(type='bool'),
            version=dict(),
            strict=dict(type='bool', default=True)
        )

    @property
    def argspec(self):
        argument_spec = copy.deepcopy(COMMON_ARG_SPEC)
        argument_spec.update(copy.deepcopy(NAME_ARG_SPEC))
        argument_spec.update(copy.deepcopy(RESOURCE_ARG_SPEC))
        argument_spec.update(copy.deepcopy(AUTH_ARG_SPEC))
        argument_spec.update(copy.deepcopy(WAIT_ARG_SPEC))
        argument_spec['merge_type'] = dict(type='list', elements='str', choices=['json', 'merge', 'strategic-merge'])
        argument_spec['validate'] = dict(type='dict', default=None, options=self.validate_spec)
        argument_spec['append_hash'] = dict(type='bool', default=False)
        argument_spec['apply'] = dict(type='bool', default=False)
        argument_spec['template'] = dict(type='raw', default=None)
        argument_spec['delete_options'] = dict(type='dict', default=None, options=copy.deepcopy(DELETE_OPTS_ARG_SPEC))
        return argument_spec

    def __init__(self, k8s_kind=None, *args, **kwargs):
        mutually_exclusive = [
            ('resource_definition', 'src'),
            ('merge_type', 'apply'),
            ('template', 'resource_definition'),
            ('template', 'src'),
        ]

        module = AnsibleModule(
            argument_spec=self.argspec,
            mutually_exclusive=mutually_exclusive,
            supports_check_mode=True,
        )

        self.module = module
        self.check_mode = self.module.check_mode
        self.params = self.module.params
        self.fail_json = self.module.fail_json
        self.fail = self.module.fail_json
        self.exit_json = self.module.exit_json

        super(KubernetesModule, self).__init__(*args, **kwargs)

        self.client = None
        self.warnings = []

        self.kind = k8s_kind or self.params.get('kind')
        self.api_version = self.params.get('api_version')
        self.name = self.params.get('name')
        self.namespace = self.params.get('namespace')

        self.check_library_version()
        self.set_resource_definitions()


def main():
    KubernetesModule().execute_module()


if __name__ == '__main__':
    main()
