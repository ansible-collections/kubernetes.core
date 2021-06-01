#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2020, Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r'''

module: k8s_exec

short_description: Execute command in Pod

version_added: "0.10.0"

author: "Tristan de Cacqueray (@tristanC)"

description:
  - Use the Kubernetes Python client to execute command on K8s pods.

extends_documentation_fragment:
  - kubernetes.core.k8s_auth_options

requirements:
  - "python >= 2.7"
  - "openshift == 0.4.3"
  - "PyYAML >= 3.11"

notes:
  - Return code C(return_code) for the command executed is added in output in version 1.0.0.
  - The authenticated user must have at least read access to the pods resource and write access to the pods/exec resource.

options:
  proxy:
    description:
    - The URL of an HTTP proxy to use for the connection.
    - Can also be specified via I(K8S_AUTH_PROXY) environment variable.
    - Please note that this module does not pick up typical proxy settings from the environment (e.g. HTTP_PROXY).
    type: str
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
    - The name of the container in the pod to connect to.
    - Defaults to only container if there is only one container in the pod.
    type: str
    required: no
  command:
    description:
    - The command to execute
    type: str
    required: yes
'''

EXAMPLES = r'''
- name: Execute a command
  kubernetes.core.k8s_exec:
    namespace: myproject
    pod: zuul-scheduler
    command: zuul-scheduler full-reconfigure

- name: Check RC status of command executed
  kubernetes.core.k8s_exec:
    namespace: myproject
    pod: busybox-test
    command: cmd_with_non_zero_exit_code
  register: command_status
  ignore_errors: True

- name: Check last command status
  debug:
    msg: "cmd failed"
  when: command_status.return_code != 0
'''

RETURN = r'''
result:
  description:
  - The command object
  returned: success
  type: complex
  contains:
     stdout:
       description: The command stdout
       type: str
     stdout_lines:
       description: The command stdout
       type: str
     stderr:
       description: The command stderr
       type: str
     stderr_lines:
       description: The command stderr
       type: str
     return_code:
       description: The command status code
       type: int
'''

import copy
import shlex

try:
    import yaml
except ImportError:
    # ImportError are managed by the common module already.
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible_collections.kubernetes.core.plugins.module_utils.common import (
    K8sAnsibleMixin, AUTH_ARG_SPEC
)

try:
    from kubernetes.client.apis import core_v1_api
    from kubernetes.stream import stream
except ImportError:
    # ImportError are managed by the common module already.
    pass


class KubernetesExecCommand(K8sAnsibleMixin):

    def __init__(self):
        module = AnsibleModule(
            argument_spec=self.argspec,
            supports_check_mode=True,
        )
        self.module = module
        self.params = self.module.params
        self.fail_json = self.module.fail_json
        super(KubernetesExecCommand, self).__init__()

    @property
    def argspec(self):
        spec = copy.deepcopy(AUTH_ARG_SPEC)
        spec['namespace'] = dict(type='str', required=True)
        spec['pod'] = dict(type='str', required=True)
        spec['container'] = dict(type='str')
        spec['command'] = dict(type='str', required=True)
        return spec

    def execute_module(self):
        # Load kubernetes.client.Configuration
        self.get_api_client()
        api = core_v1_api.CoreV1Api()

        # hack because passing the container as None breaks things
        optional_kwargs = {}
        if self.params.get('container'):
            optional_kwargs['container'] = self.params['container']
        try:
            resp = stream(
                api.connect_get_namespaced_pod_exec,
                self.params["pod"],
                self.params["namespace"],
                command=shlex.split(self.params["command"]),
                stdout=True,
                stderr=True,
                stdin=False,
                tty=False,
                _preload_content=False, **optional_kwargs)
        except Exception as e:
            self.module.fail_json(msg="Failed to execute on pod %s"
                                      " due to : %s" % (self.params.get('pod'), to_native(e)))
        stdout, stderr, rc = [], [], 0
        while resp.is_open():
            resp.update(timeout=1)
            if resp.peek_stdout():
                stdout.append(resp.read_stdout())
            if resp.peek_stderr():
                stderr.append(resp.read_stderr())
        err = resp.read_channel(3)
        err = yaml.safe_load(err)
        if err['status'] == 'Success':
            rc = 0
        else:
            rc = int(err['details']['causes'][0]['message'])

        self.module.exit_json(
            # Some command might change environment, but ultimately failing at end
            changed=True,
            stdout="".join(stdout),
            stderr="".join(stderr),
            return_code=rc
        )


def main():
    KubernetesExecCommand().execute_module()


if __name__ == '__main__':
    main()
