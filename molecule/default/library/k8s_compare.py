#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Aubin Bikouo <@abikouo>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r'''

module: k8s_compare

short_description: Compare file and directories.

author:
    - Aubin Bikouo (@abikouo)

description:
  - This module is used to validate k8s_cp module.
  - Compare the local file/directory with the remote pod version

notes:
  - This module authenticates on kubernetes cluster using default kubeconfig only.

requirements:
  - "python >= 3.6"
  - "kubernetes >= 12.0.0"

options:
  namespace:
    description:
    - The pod namespace name
    type: str
    required: yes
  pod:
    description:
    - The pod name
    type: str
    required: yes
  container:
    description:
    - The container to retrieve files from.
    type: str
  remote_path:
    description:
    - Path of the file or directory on Pod.
    type: path
    required: yes
  local_path:
    description:
    - Path of the local file or directory.
    type: path
    required: yes
  display_content:
    description:
    - show file content which has been compared.
    type: bool
    default: false
'''

EXAMPLES = r'''
- name: compare local /tmp/foo with /tmp/bar in a remote pod
  k8s_compare:
    namespace: some-namespace
    pod: some-pod
    remote_path: /tmp/bar
    local_path: /tmp/foo
'''


RETURN = r'''
result:
  description:
  - message describing the copy operation successfully done.
  returned: success
  type: str
'''

import os
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
try:
    from kubernetes import config
    from kubernetes.client import Configuration
    from kubernetes.client.api import core_v1_api
    from kubernetes.client.rest import ApiException
    from kubernetes.stream import stream
except ImportError:
    # ImportError are managed by the common module already.
    pass


class KubernetesClient(object):

    def __init__(self, module):
        self._module = module
        config.load_kube_config()
        try:
            c = Configuration().get_default_copy()
        except AttributeError:
            c = Configuration()
            c.assert_hostname = False
        Configuration.set_default(c)
        api_instance = core_v1_api.CoreV1Api()

        pod_name = module.params.get('pod')
        pod_namespace = module.params.get('namespace')

        try:
            api_instance.read_namespaced_pod(name=pod_name, namespace=pod_namespace)
        except ApiException as e:
            module.fail_json(msg="{0}/{1} Pod not found: {2}".format(pod_name, pod_namespace, to_native(e)))

        # interactive session to the pod
        exec_command = ['/bin/sh']
        container_arg = {}
        if module.params.get('container'):
            container_arg['container'] = module.params.get('container')
        self._api_response = stream(api_instance.connect_get_namespaced_pod_exec,
                                    pod_name,
                                    pod_namespace,
                                    command=exec_command,
                                    stderr=True, stdin=True,
                                    stdout=True, tty=False,
                                    _preload_content=False, **container_arg)

    def close(self):
        self._api_response.close()

    def get_file_content(self, file_path):
        commands = ["cat {0}\n".format(file_path)]
        while self._api_response.is_open():
            self._api_response.update(timeout=1)
            if self._api_response.peek_stdout():
                return self._api_response.read_stdout()
            if self._api_response.peek_stderr():
                self._module.fail_json(msg="{0} not found from pod: {1}".format(file_path, self._api_response.read_stderr()))
            if commands:
                c = commands.pop(0)
                self._api_response.write_stdin(c + "\n")


def execute_module(module):
    # Create kubernetes client
    k8s_client = KubernetesClient(module)
    local_path = module.params.get('local_path')
    remote_path = module.params.get('remote_path')
    items = [{'local': local_path, 'remote': remote_path}]
    if not os.path.exists(local_path):
        module.fail_json(msg="{0} not found.".format(local_path))

    if os.path.isdir(local_path):
        items = []
        for root, dirs, files in os.walk(local_path):
            for local_file in files:
                items.append({'local': os.path.join(root, local_file),
                              'remote': os.path.join(remote_path, os.path.relpath(os.path.join(root, local_file), start=local_path))})

    # compare files
    content = []
    for item in items:
        r_content = k8s_client.get_file_content(item.get('remote'))
        with open(item.get('local'), 'r') as fh:
            l_content = fh.read()
            if l_content != r_content:
                module.fail_json(msg="local file {0} differs from remote file {1}".format(item.get('local'), item.get('remote')),
                                 local_content=l_content, remote_content=r_content)
                k8s_client.close()
            content.append({'local': item['local'], 'remote': item['remote'], 'content': l_content})
    k8s_client.close()
    result = {'result': "{0} file(s) successfully compared.".format(len(items))}
    if module.params.get('display_content'):
        result['content'] = content
    module.exit_json(changed=False, **result)


def main():
    argument_spec = {}
    argument_spec['namespace'] = {'type': 'str', 'required': True}
    argument_spec['pod'] = {'type': 'str', 'required': True}
    argument_spec['container'] = {}
    argument_spec['remote_path'] = {'type': 'path', 'required': True}
    argument_spec['local_path'] = {'type': 'path', 'required': True}
    argument_spec['display_content'] = {'type': 'bool', 'default': False}
    module = AnsibleModule(argument_spec=argument_spec)

    execute_module(module)


if __name__ == '__main__':
    main()
