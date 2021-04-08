#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Chris Houseknecht <@chouseknecht>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function


__metaclass__ = type


DOCUMENTATION = r'''

module: k8s_scale

short_description: Set a new size for a Deployment, ReplicaSet, Replication Controller, or Job.

author:
    - "Chris Houseknecht (@chouseknecht)"
    - "Fabian von Feilitzsch (@fabianvf)"

description:
  - Similar to the kubectl scale command. Use to set the number of replicas for a Deployment, ReplicaSet,
    or Replication Controller, or the parallelism attribute of a Job. Supports check mode.

extends_documentation_fragment:
  - kubernetes.core.k8s_name_options
  - kubernetes.core.k8s_auth_options
  - kubernetes.core.k8s_resource_options
  - kubernetes.core.k8s_scale_options

requirements:
    - "python >= 2.7"
    - "openshift >= 0.6"
    - "PyYAML >= 3.11"
'''

EXAMPLES = r'''
- name: Scale deployment up, and extend timeout
  community.kubernetes.k8s_scale:
    api_version: v1
    kind: Deployment
    name: elastic
    namespace: myproject
    replicas: 3
    wait_timeout: 60

- name: Scale deployment down when current replicas match
  community.kubernetes.k8s_scale:
    api_version: v1
    kind: Deployment
    name: elastic
    namespace: myproject
    current_replicas: 3
    replicas: 2

- name: Increase job parallelism
  community.kubernetes.k8s_scale:
    api_version: batch/v1
    kind: job
    name: pi-with-timeout
    namespace: testing
    replicas: 2

# Match object using local file or inline definition

- name: Scale deployment based on a file from the local filesystem
  community.kubernetes.k8s_scale:
    src: /myproject/elastic_deployment.yml
    replicas: 3
    wait: no

- name: Scale deployment based on a template output
  community.kubernetes.k8s_scale:
    resource_definition: "{{ lookup('template', '/myproject/elastic_deployment.yml') | from_yaml }}"
    replicas: 3
    wait: no

- name: Scale deployment based on a file from the Ansible controller filesystem
  community.kubernetes.k8s_scale:
    resource_definition: "{{ lookup('file', '/myproject/elastic_deployment.yml') | from_yaml }}"
    replicas: 3
    wait: no
'''

RETURN = r'''
result:
  description:
  - If a change was made, will return the patched object, otherwise returns the existing object.
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
     duration:
       description: elapsed time of task in seconds
       returned: when C(wait) is true
       type: int
       sample: 48
'''

import copy

from ansible_collections.community.kubernetes.plugins.module_utils.ansiblemodule import AnsibleModule
from ansible_collections.community.kubernetes.plugins.module_utils.args_common import (
    AUTH_ARG_SPEC, RESOURCE_ARG_SPEC, NAME_ARG_SPEC)


SCALE_ARG_SPEC = {
    'replicas': {'type': 'int', 'required': True},
    'current_replicas': {'type': 'int'},
    'resource_version': {},
    'wait': {'type': 'bool', 'default': True},
    'wait_timeout': {'type': 'int', 'default': 20},
}


def execute_module(module, k8s_ansible_mixin,):
    k8s_ansible_mixin.set_resource_definitions(module)

    definition = k8s_ansible_mixin.resource_definitions[0]

    name = definition['metadata']['name']
    namespace = definition['metadata'].get('namespace')
    api_version = definition['apiVersion']
    kind = definition['kind']
    current_replicas = module.params.get('current_replicas')
    replicas = module.params.get('replicas')
    resource_version = module.params.get('resource_version')

    wait = module.params.get('wait')
    wait_time = module.params.get('wait_timeout')
    existing = None
    existing_count = None
    return_attributes = dict(changed=False, result=dict(), diff=dict())
    if wait:
        return_attributes['duration'] = 0

    resource = k8s_ansible_mixin.find_resource(kind, api_version, fail=True)

    from ansible_collections.community.kubernetes.plugins.module_utils.common import NotFoundError

    try:
        existing = resource.get(name=name, namespace=namespace)
        return_attributes['result'] = existing.to_dict()
    except NotFoundError as exc:
        module.fail_json(msg='Failed to retrieve requested object: {0}'.format(exc),
                         error=exc.value.get('status'))

    if module.params['kind'] == 'job':
        existing_count = existing.spec.parallelism
    elif hasattr(existing.spec, 'replicas'):
        existing_count = existing.spec.replicas

    if existing_count is None:
        module.fail_json(msg='Failed to retrieve the available count for the requested object.')

    if resource_version and resource_version != existing.metadata.resourceVersion:
        module.exit_json(**return_attributes)

    if current_replicas is not None and existing_count != current_replicas:
        module.exit_json(**return_attributes)

    if existing_count != replicas:
        return_attributes['changed'] = True
        if not module.check_mode:
            if module.params['kind'] == 'job':
                existing.spec.parallelism = replicas
                return_attributes['result'] = resource.patch(existing.to_dict()).to_dict()
            else:
                return_attributes = scale(module, k8s_ansible_mixin, resource, existing, replicas, wait, wait_time)

    module.exit_json(**return_attributes)


def argspec():
    args = copy.deepcopy(SCALE_ARG_SPEC)
    args.update(RESOURCE_ARG_SPEC)
    args.update(NAME_ARG_SPEC)
    args.update(AUTH_ARG_SPEC)
    return args


def scale(module, k8s_ansible_mixin, resource, existing_object, replicas, wait, wait_time):
    name = existing_object.metadata.name
    namespace = existing_object.metadata.namespace
    kind = existing_object.kind

    if not hasattr(resource, 'scale'):
        module.fail_json(
            msg="Cannot perform scale on resource of kind {0}".format(resource.kind)
        )

    scale_obj = {'kind': kind, 'metadata': {'name': name, 'namespace': namespace}, 'spec': {'replicas': replicas}}

    existing = resource.get(name=name, namespace=namespace)

    try:
        resource.scale.patch(body=scale_obj)
    except Exception as exc:
        module.fail_json(msg="Scale request failed: {0}".format(exc))

    k8s_obj = resource.get(name=name, namespace=namespace).to_dict()
    match, diffs = k8s_ansible_mixin.diff_objects(existing.to_dict(), k8s_obj)
    result = dict()
    result['result'] = k8s_obj
    result['changed'] = not match
    result['diff'] = diffs

    if wait:
        success, result['result'], result['duration'] = k8s_ansible_mixin.wait(resource, scale_obj, 5, wait_time)
        if not success:
            module.fail_json(msg="Resource scaling timed out", **result)
    return result


def main():
    module = AnsibleModule(argument_spec=argspec(), supports_check_mode=True)
    from ansible_collections.community.kubernetes.plugins.module_utils.common import (
        K8sAnsibleMixin, get_api_client)

    k8s_ansible_mixin = K8sAnsibleMixin(module)
    k8s_ansible_mixin.client = get_api_client(module=module)
    execute_module(module, k8s_ansible_mixin)


if __name__ == '__main__':
    main()
