#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2021, Aubin Bikouo <@abikouo>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r'''

module: k8s_cp

short_description: Copy files and directories to and from pod.

version_added: "2.1.0"

author:
    - Aubin Bikouo (@abikouo)

description:
  - Use the Kubernetes Python client to copy files and directories to and from containers inside a pod.

extends_documentation_fragment:
  - kubernetes.core.k8s_auth_options

notes:
  - This module does not support copy of tar file or zip file.

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
    - The name of the container in the pod to copy files/directories from/to.
    - Defaults to only container if there is only one container in the pod.
    type: str
  remote_path:
    description:
    - Path of the file or directory to copy.
    type: path
    required: yes
  local_path:
    description:
    - Path of the local file or directory.
    - Required when I(state) is set to C(from_pod).
    - Mutually exclusive with I(content).
    type: path
  content:
    description:
    - When used instead of I(local_path), sets the contents of a local file directly to the specified value.
    - Works only when I(remote_path) is a file. Creates the file if it does not exist.
    - For advanced formatting or if content contains a variable, use the ansible.builtin.template module.
    - Mutually exclusive with I(local_path).
    type: str
  state:
    description:
    - When set to C(to_pod), the local I(local_path) file or directory will be copied to I(remote_path) into pod.
    - When set to C(from_pod), the remote file or directory I(remote_path) from pod will be copied locally to I(local_path).
    type: str
    default: to_pod
    choices: [ to_pod, from_pod ]
'''

EXAMPLES = r'''
# kubectl cp /tmp/foo some-namespace/some-pod:/tmp/bar
- name: Copy /tmp/foo local file to /tmp/bar in a remote pod
  kubernetes.core.k8s:
    namespace: some-namespace
    pod: some-pod
    remote_path: /tmp/bar
    local_path: /tmp/foo

# kubectl cp /tmp/foo_dir some-namespace/some-pod:/tmp/bar_dir
- name: Copy /tmp/foo_dir local directory to /tmp/bar_dir in a remote pod
  kubernetes.core.k8s:
    namespace: some-namespace
    pod: some-pod
    remote_path: /tmp/bar_dir
    local_path: /tmp/foo_dir

# kubectl cp /tmp/foo some-namespace/some-pod:/tmp/bar -c some-container
- name: Copy /tmp/foo local file to /tmp/bar in a remote pod in a specific container
  kubernetes.core.k8s:
    namespace: some-namespace
    pod: some-pod
    container: some-container
    remote_path: /tmp/bar
    local_path: /tmp/foo

# kubectl cp some-namespace/some-pod:/tmp/foo /tmp/bar
- name: Copy /tmp/foo from a remote pod to /tmp/bar locally
  kubernetes.core.k8s:
    namespace: some-namespace
    pod: some-pod
    remote_path: /tmp/foo
    local_path: /tmp/bar
    state: from_pod

# copy content into a file in the remote pod
- name: Copy /tmp/foo from a remote pod to /tmp/bar locally
  kubernetes.core.k8s:
    state: to_pod
    namespace: some-namespace
    pod: some-pod
    remote_path: /tmp/foo.txt
    content: "This content will be copied into remote file"
'''


RETURN = r'''
result:
  description:
  - message describing the copy operation successfully done.
  returned: success
  type: str
'''

import copy
import os
import yaml
from tempfile import TemporaryFile, NamedTemporaryFile
import tarfile

# from ansible_collections.kubernetes.core.plugins.module_utils.ansiblemodule import AnsibleModule
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kubernetes.core.plugins.module_utils.args_common import AUTH_ARG_SPEC
from ansible.module_utils._text import to_native
from ansible_collections.kubernetes.core.plugins.module_utils.common import K8sAnsibleMixin, get_api_client
try:
    from kubernetes.client.apis import core_v1_api
    from kubernetes.stream import stream
except ImportError:
    pass


def check_pod(k8s_ansible_mixin, module):
    resource = k8s_ansible_mixin.find_resource("Pod", None, True)
    namespace = module.params.get('namespace')
    name = module.params.get('pod')
    container = module.params.get('container')

    def _fail(exc):
        arg = {}
        if hasattr(exc, 'body'):
            msg = "Namespace={0} Kind=Pod Name={1}: Failed requested object: {2}".format(namespace, name, exc.body)
        else:
            msg = to_native(exc)
        for attr in ['status', 'reason']:
            if hasattr(exc, attr):
                arg[attr] = getattr(exc, attr)
        module.fail_json(msg=msg, **arg)

    try:
        result = resource.get(name=name, namespace=namespace)
        containers = [c['name'] for c in result.to_dict()['status']['containerStatuses']]
        if container and container not in containers:
            module.fail_json(msg="Pod '{0}' from Namespace '{1}' has no container named '{2}'.".format(
                name, namespace, container
            ))
        return containers
    except Exception as exc:
        _fail(exc)


class K8SCopyModule(object):

    def __init__(self, module, client):
        self.client = client
        self.module = module
        self.api_instance = core_v1_api.CoreV1Api(client.client)

        self.local_path = module.params.get('local_path')
        self.name = module.params.get('pod')
        self.namespace = module.params.get('namespace')
        self.remote_path = module.params.get('remote_path')
        self.content = module.params.get('content')

        self.container_arg = {}
        if module.params.get('container'):
            self.container_arg['container'] = module.params.get('container')

    def test_remote_path(self, as_dir=True):
        """
            When 'as_dir' is set to True, we check if the resource exist as a directory inside the remote pod
            When 'as_dir' is set to False, we check if the resource exist as a file inside the remote pod
        """
        try:
            test_arg = '-d' if as_dir else '-f'
            test_cmd = ['test', test_arg, self.remote_path]
            resp = stream(self.api_instance.connect_get_namespaced_pod_exec,
                          self.name,
                          self.namespace,
                          command=test_cmd,
                          stdout=True, stderr=True,
                          stdin=False, tty=False,
                          _preload_content=False, **self.container_arg)
        except Exception as e:
            self.module.fail_json(msg="Failed to execute on pod {0}/{1} due to : {2}".format(self.namespace, self.name, to_native(e)))
        stdout, stderr = [], []
        while resp.is_open():
            resp.update(timeout=1)
            if resp.peek_stdout():
                stdout.append(resp.read_stdout())
            if resp.peek_stderr():
                stderr.append(resp.read_stderr())
        err = resp.read_channel(3)
        err = yaml.safe_load(err)
        resp.close()
        if err['status'] == 'Success':
            return True
        return False

    def copy_local_file_to_remote(self, local_file, remote_file):
        tar_command = ['tar', 'xvf', '-', '-C', '/']
        response = stream(self.api_instance.connect_get_namespaced_pod_exec,
                          self.name,
                          self.namespace,
                          command=tar_command,
                          stderr=True, stdin=True,
                          stdout=True, tty=False,
                          _preload_content=False, **self.container_arg)
        with TemporaryFile() as tar_buffer:
            with tarfile.open(fileobj=tar_buffer, mode='w') as tar:
                tar.add(local_file, remote_file)
            tar_buffer.seek(0)
            commands = []
            commands.append(tar_buffer.read())

            stderr, stdout = [], []
            while response.is_open():
                response.update(timeout=1)
                if response.peek_stdout():
                    stdout.append(response.read_stdout().rstrip("\n"))
                if response.peek_stderr():
                    stderr.append(response.read_stderr().rstrip("\n"))
                if commands:
                    cmd = commands.pop(0)
                    response.write_stdin(cmd.decode())
                else:
                    break
            response.close()
            if stderr:
                self.module.fail_json(msg="copy operation failed: {}".format(stderr))
            else:
                self.module.exit_json(changed=True, result="content successfully copied into file {} on remote pod".format(self.remote_path))

    def copy_to_remote(self):
        if self.local_path:
            if not os.path.exists(self.local_path):
                self.module.fail_json(msg="{} does not exist in local filesystem".format(self.local_path))
            if not os.access(self.local_path, os.R_OK):
                self.module.fail_json(msg="{} not readable".format(self.local_path))
            is_remote_path_dir = self.test_remote_path()
            if os.path.isfile(self.local_path):
                dest_file = self.remote_path
                if is_remote_path_dir:
                    dest_file = os.path.join(self.remote_path, os.path.basename(self.local_path))
                self.copy_local_file_to_remote(self.local_path, dest_file)
            else:
                self.copy_local_file_to_remote(self.local_path, self.remote_path)
        else:
            if self.test_remote_path():
                self.module.fail_json(msg="content option is set, remote_path should be a file instead of a directory.")
            # create file on remote pod using content
            with NamedTemporaryFile(mode="w") as tmp_f:
                tmp_f.write(self.content)
                tmp_f.flush()
                self.copy_local_file_to_remote(tmp_f.name, self.remote_path)

    def copy_to_local(self):
        is_remote_path_dir = self.test_remote_path()
        is_remote_path_file = self.test_remote_path(as_dir=False)

        if not is_remote_path_dir and not is_remote_path_file:
            self.module.fail_json(msg="{} does not exist in remote pod filesystem".format(self.remote_path))

        is_local_path_dir = os.path.isdir(self.local_path)
        if is_remote_path_dir and not is_local_path_dir:
            self.module.fail_json(msg="{} does not exist in local filesystem".format(self.local_path))

        exec_command = ['tar', 'cf', '-', '-C', os.path.dirname(self.remote_path), os.path.basename(self.remote_path)]
        with TemporaryFile() as tar_buffer:
            response = stream(self.api_instance.connect_get_namespaced_pod_exec,
                              self.name,
                              self.namespace,
                              command=exec_command,
                              stderr=True, stdin=True,
                              stdout=True, tty=False,
                              _preload_content=False, **self.container_arg)
            stderr = []
            while response.is_open():
                response.update(timeout=1)
                if response.peek_stdout():
                    tar_buffer.write(response.read_stdout().encode('utf-8'))
                if response.peek_stderr():
                    stderr.append(response.read_stderr().rstrip("\n"))
            response.close()

            tar_buffer.flush()
            tar_buffer.seek(0)
            with tarfile.open(fileobj=tar_buffer, mode='r:') as tar:
                for member in tar.getmembers():
                    dest_file = os.path.join(self.local_path, member.name)
                    if member.isdir():
                        os.makedirs(dest_file, exist_ok=True)
                    else:
                        if is_remote_path_file:
                            if is_local_path_dir:
                                dest_file = os.path.join(self.local_path, os.path.basename(member.name))
                            else:
                                dest_file = self.local_path
                        tar.makefile(member, dest_file)
        self.module.exit_json(changed=True, result="{} successfully copied locally into {}".format(self.remote_path, self.local_path))


def execute_module(module):

    k8s_ansible_mixin = K8sAnsibleMixin(module)
    k8s_ansible_mixin.check_library_version()

    k8s_ansible_mixin.module = module
    k8s_ansible_mixin.argspec = module.argument_spec
    k8s_ansible_mixin.check_mode = k8s_ansible_mixin.module.check_mode
    k8s_ansible_mixin.params = k8s_ansible_mixin.module.params
    k8s_ansible_mixin.fail_json = k8s_ansible_mixin.module.fail_json
    k8s_ansible_mixin.fail = k8s_ansible_mixin.module.fail_json

    k8s_ansible_mixin.client = get_api_client(module=module)
    containers = check_pod(k8s_ansible_mixin, module)
    if len(containers) > 1 and module.params.get('container') is None:
        module.fail_json(msg="Pod contains more than 1 container, option 'container' should be set.")

    try:
        k8s_copy = K8SCopyModule(module, k8s_ansible_mixin.client)
        if module.params.get('state') == 'to_pod':
            # copy local file/directory to remote pod
            k8s_copy.copy_to_remote()
        else:
            # copy remote file/directory to local file system
            k8s_copy.copy_to_local()
    except Exception as e:
        import traceback
        module.fail_json("Failed to copy object due to: {}".format(to_native(e)), trace=traceback.format_exc(), embbeded=AnsibleModule.embedded_in_server)


def main():
    argument_spec = copy.deepcopy(AUTH_ARG_SPEC)
    argument_spec['namespace'] = {'type': 'str', 'required': True}
    argument_spec['pod'] = {'type': 'str', 'required': True}
    argument_spec['container'] = {}
    argument_spec['remote_path'] = {'type': 'path', 'required': True}
    argument_spec['local_path'] = {'type': 'path'}
    argument_spec['content'] = {'type': 'str'}
    argument_spec['state'] = {'type': 'str', 'default': 'to_pod', 'choices': ['to_pod', 'from_pod']}

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=[('local_path', 'content')],
                           required_if=[('state', 'from_pod', ['local_path'])],
                           required_one_of=[['local_path', 'content']],
                           supports_check_mode=True)

    execute_module(module)


if __name__ == '__main__':
    main()
