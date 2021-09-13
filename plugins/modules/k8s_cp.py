#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Aubin Bikouo <@abikouo>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''

module: k8s_cp

short_description: Copy files and directories to and from pod.

version_added: "2.2.0"

author:
    - Aubin Bikouo (@abikouo)

description:
  - Use the Kubernetes Python client to copy files and directories to and from containers inside a pod.

extends_documentation_fragment:
  - kubernetes.core.k8s_auth_options

requirements:
  - "python >= 3.6"
  - "kubernetes >= 12.0.0"

options:
  namespace:
    description:
    - The pod namespace name.
    type: str
    required: yes
  pod:
    description:
    - The pod name.
    type: str
    required: yes
  container:
    description:
    - The name of the container in the pod to copy files/directories from/to.
    - Defaults to the only container if there is only one container in the pod.
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
    - For advanced formatting or if the content contains a variable, use the M(ansible.builtin.template) module.
    - Mutually exclusive with I(local_path).
    type: str
  state:
    description:
    - When set to C(to_pod), the local I(local_path) file or directory will be copied to I(remote_path) into the pod.
    - When set to C(from_pod), the remote file or directory I(remote_path) from pod will be copied locally to I(local_path).
    type: str
    default: to_pod
    choices: [ to_pod, from_pod ]
  no_preserve:
    description:
    - The copied file/directory's ownership and permissions will not be preserved in the container.
    - This option is ignored when I(content) is set or when I(state) is set to C(from_pod).
    type: bool
    default: False

notes:
    - the tar binary is required on the container when copying from local filesystem to pod.
'''

EXAMPLES = r'''
# kubectl cp /tmp/foo some-namespace/some-pod:/tmp/bar
- name: Copy /tmp/foo local file to /tmp/bar in a remote pod
  kubernetes.core.k8s_cp:
    namespace: some-namespace
    pod: some-pod
    remote_path: /tmp/bar
    local_path: /tmp/foo

# kubectl cp /tmp/foo_dir some-namespace/some-pod:/tmp/bar_dir
- name: Copy /tmp/foo_dir local directory to /tmp/bar_dir in a remote pod
  kubernetes.core.k8s_cp:
    namespace: some-namespace
    pod: some-pod
    remote_path: /tmp/bar_dir
    local_path: /tmp/foo_dir

# kubectl cp /tmp/foo some-namespace/some-pod:/tmp/bar -c some-container
- name: Copy /tmp/foo local file to /tmp/bar in a remote pod in a specific container
  kubernetes.core.k8s_cp:
    namespace: some-namespace
    pod: some-pod
    container: some-container
    remote_path: /tmp/bar
    local_path: /tmp/foo
    no_preserve: True
    state: to_pod

# kubectl cp some-namespace/some-pod:/tmp/foo /tmp/bar
- name: Copy /tmp/foo from a remote pod to /tmp/bar locally
  kubernetes.core.k8s_cp:
    namespace: some-namespace
    pod: some-pod
    remote_path: /tmp/foo
    local_path: /tmp/bar
    state: from_pod

# copy content into a file in the remote pod
- name: Copy /tmp/foo from a remote pod to /tmp/bar locally
  kubernetes.core.k8s_cp:
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
from tempfile import TemporaryFile, NamedTemporaryFile
from select import select
from abc import ABCMeta, abstractmethod
import tarfile

# from ansible_collections.kubernetes.core.plugins.module_utils.ansiblemodule import AnsibleModule
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible_collections.kubernetes.core.plugins.module_utils.common import K8sAnsibleMixin, get_api_client
from ansible_collections.kubernetes.core.plugins.module_utils.args_common import AUTH_ARG_SPEC

try:
    from kubernetes.client.api import core_v1_api
    from kubernetes.stream import stream
    from kubernetes.stream.ws_client import STDOUT_CHANNEL, STDERR_CHANNEL, ERROR_CHANNEL, ABNF
except ImportError:
    pass

try:
    import yaml
except ImportError:
    # ImportError are managed by the common module already.
    pass


class K8SCopy(metaclass=ABCMeta):

    def __init__(self, module, client):
        self.client = client
        self.module = module
        self.api_instance = core_v1_api.CoreV1Api(client.client)

        self.local_path = module.params.get('local_path')
        self.name = module.params.get('pod')
        self.namespace = module.params.get('namespace')
        self.remote_path = module.params.get('remote_path')
        self.content = module.params.get('content')

        self.no_preserve = module.params.get('no_preserve')
        self.container_arg = {}
        if module.params.get('container'):
            self.container_arg['container'] = module.params.get('container')

    @abstractmethod
    def run(self):
        pass


class K8SCopyFromPod(K8SCopy):
    """
    Copy files/directory from Pod into local filesystem
    """
    def __init__(self, module, client):
        super(K8SCopyFromPod, self).__init__(module, client)
        self.is_remote_path_dir = None
        self.files_to_copy = list()

    def list_remote_files(self):
        """
        This method will check if the remote path is a dir or file
        if it is a directory the file list will be updated accordingly
        """
        try:
            find_cmd = ['find', self.remote_path, '-type', 'f', '-name', '*']
            response = stream(self.api_instance.connect_get_namespaced_pod_exec,
                              self.name,
                              self.namespace,
                              command=find_cmd,
                              stdout=True, stderr=True,
                              stdin=False, tty=False,
                              _preload_content=False, **self.container_arg)
        except Exception as e:
            self.module.fail_json(msg="Failed to execute on pod {0}/{1} due to : {2}".format(self.namespace, self.name, to_native(e)))
        stderr = []
        while response.is_open():
            response.update(timeout=1)
            if response.peek_stdout():
                self.files_to_copy.extend(response.read_stdout().rstrip('\n').split('\n'))
            if response.peek_stderr():
                err = response.read_stderr()
                if "No such file or directory" in err:
                    self.module.fail_json(msg="{0} does not exist in remote pod filesystem".format(self.remote_path))
                stderr.append(err)
        error = response.read_channel(ERROR_CHANNEL)
        response.close()
        error = yaml.safe_load(error)
        if error['status'] != 'Success':
            self.module.fail_json(msg="Failed to execute on Pod due to: {0}".format(error))

    def read(self):
        self.stdout = None
        self.stderr = None

        if self.response.is_open():
            if not self.response.sock.connected:
                self.response._connected = False
            else:
                ret, out, err = select((self.response.sock.sock, ), (), (), 0)
                if ret:
                    code, frame = self.response.sock.recv_data_frame(True)
                    if code == ABNF.OPCODE_CLOSE:
                        self.response._connected = False
                    elif code in (ABNF.OPCODE_BINARY, ABNF.OPCODE_TEXT) and len(frame.data) > 1:
                        channel = frame.data[0]
                        content = frame.data[1:]
                        if content:
                            if channel == STDOUT_CHANNEL:
                                self.stdout = content
                            elif channel == STDERR_CHANNEL:
                                self.stderr = content.decode("utf-8", "replace")

    def copy(self):
        is_remote_path_dir = len(self.files_to_copy) > 1 or self.files_to_copy[0] != self.remote_path
        relpath_start = self.remote_path
        if is_remote_path_dir and os.path.isdir(self.local_path):
            relpath_start = os.path.dirname(self.remote_path)

        for remote_file in self.files_to_copy:
            dest_file = self.local_path
            if is_remote_path_dir:
                dest_file = os.path.join(self.local_path, os.path.relpath(remote_file, start=relpath_start))
                # create directory to copy file in
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)

            pod_command = ['cat', remote_file]
            self.response = stream(self.api_instance.connect_get_namespaced_pod_exec,
                                   self.name,
                                   self.namespace,
                                   command=pod_command,
                                   stderr=True, stdin=True,
                                   stdout=True, tty=False,
                                   _preload_content=False, **self.container_arg)
            errors = []
            with open(dest_file, 'wb') as fh:
                while self.response._connected:
                    self.read()
                    if self.stdout:
                        fh.write(self.stdout)
                    if self.stderr:
                        errors.append(self.stderr)
            if errors:
                self.module.fail_json(msg="Failed to copy file from Pod: {0}".format(''.join(errors)))
        self.module.exit_json(changed=True, result="{0} successfully copied locally into {1}".format(self.remote_path, self.local_path))

    def run(self):
        try:
            self.list_remote_files()
            if self.files_to_copy == []:
                self.module.exit_json(changed=False, warning="No file found from directory '{0}' into remote Pod.".format(self.remote_path))
            self.copy()
        except Exception as e:
            self.module.fail_json(msg="Failed to copy file/directory from Pod due to: {0}".format(to_native(e)))


class K8SCopyToPod(K8SCopy):
    """
    Copy files/directory from local filesystem into remote Pod
    """
    def __init__(self, module, client):
        super(K8SCopyToPod, self).__init__(module, client)
        self.files_to_copy = list()

    def run_from_pod(self, command):
        response = stream(self.api_instance.connect_get_namespaced_pod_exec,
                          self.name,
                          self.namespace,
                          command=command,
                          stderr=True, stdin=False,
                          stdout=True, tty=False,
                          _preload_content=False, **self.container_arg)
        errors = []
        while response.is_open():
            response.update(timeout=1)
            if response.peek_stderr():
                errors.append(response.read_stderr())
        response.close()
        err = response.read_channel(ERROR_CHANNEL)
        err = yaml.safe_load(err)
        response.close()
        if err['status'] != 'Success':
            self.module.fail_json(msg="Failed to run {0} on Pod.".format(command), errors=errors)

    def is_remote_path_dir(self):
        pod_command = ['test', '-d', self.remote_path]
        response = stream(self.api_instance.connect_get_namespaced_pod_exec,
                          self.name,
                          self.namespace,
                          command=pod_command,
                          stdout=True, stderr=True,
                          stdin=False, tty=False,
                          _preload_content=False, **self.container_arg)
        while response.is_open():
            response.update(timeout=1)
        err = response.read_channel(ERROR_CHANNEL)
        err = yaml.safe_load(err)
        response.close()
        if err['status'] == 'Success':
            return True
        return False

    def close_temp_file(self):
        if self.named_temp_file:
            self.named_temp_file.close()

    def run(self):
        try:
            # remove trailing slash from destination path
            dest_file = self.remote_path.rstrip("/")
            src_file = self.local_path
            self.named_temp_file = None
            if self.content:
                self.named_temp_file = NamedTemporaryFile(mode="w")
                self.named_temp_file.write(self.content)
                self.named_temp_file.flush()
                src_file = self.named_temp_file.name
            else:
                if not os.path.exists(self.local_path):
                    self.module.fail_json(msg="{0} does not exist in local filesystem".format(self.local_path))
                if not os.access(self.local_path, os.R_OK):
                    self.module.fail_json(msg="{0} not readable".format(self.local_path))

            if self.is_remote_path_dir():
                if self.content:
                    self.module.fail_json(msg="When content is specified, remote path should not be an existing directory")
                else:
                    dest_file = os.path.join(dest_file, os.path.basename(src_file))

            if self.no_preserve:
                tar_command = ['tar', '--no-same-permissions', '--no-same-owner', '-xmf', '-']
            else:
                tar_command = ['tar', '-xmf', '-']

            if dest_file.startswith("/"):
                tar_command.extend(['-C', '/'])

            response = stream(self.api_instance.connect_get_namespaced_pod_exec,
                              self.name,
                              self.namespace,
                              command=tar_command,
                              stderr=True, stdin=True,
                              stdout=True, tty=False,
                              _preload_content=False, **self.container_arg)
            with TemporaryFile() as tar_buffer:
                with tarfile.open(fileobj=tar_buffer, mode='w') as tar:
                    tar.add(src_file, dest_file)
                tar_buffer.seek(0)
                commands = []
                # push command in chunk mode
                size = 1024 * 1024
                while True:
                    data = tar_buffer.read(size)
                    if not data:
                        break
                    commands.append(data)

                stderr, stdout = [], []
                while response.is_open():
                    if response.peek_stdout():
                        stdout.append(response.read_stdout().rstrip("\n"))
                    if response.peek_stderr():
                        stderr.append(response.read_stderr().rstrip("\n"))
                    if commands:
                        cmd = commands.pop(0)
                        response.write_stdin(cmd)
                    else:
                        break
                response.close()
                if stderr:
                    self.close_temp_file()
                    self.module.fail_json(command=tar_command, msg="Failed to copy local file/directory into Pod due to: {0}".format(''.join(stderr)))
            self.close_temp_file()
            if self.content:
                self.module.exit_json(changed=True, result="Content successfully copied into {0} on remote Pod".format(self.remote_path))
            self.module.exit_json(changed=True, result="{0} successfully copied into remote Pod into {1}".format(self.local_path, self.remote_path))

        except Exception as e:
            self.module.fail_json(msg="Failed to copy local file/directory into Pod due to: {0}".format(to_native(e)))


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
            module.fail_json(msg="Pod has no container {0}".format(container))
        return containers
    except Exception as exc:
        _fail(exc)


def execute_module(module):

    k8s_ansible_mixin = K8sAnsibleMixin(module, pyyaml_required=False)
    k8s_ansible_mixin.check_library_version()

    k8s_ansible_mixin.module = module
    k8s_ansible_mixin.argspec = module.argument_spec
    k8s_ansible_mixin.params = k8s_ansible_mixin.module.params
    k8s_ansible_mixin.fail_json = k8s_ansible_mixin.module.fail_json
    k8s_ansible_mixin.fail = k8s_ansible_mixin.module.fail_json

    k8s_ansible_mixin.client = get_api_client(module=module)
    containers = check_pod(k8s_ansible_mixin, module)
    if len(containers) > 1 and module.params.get('container') is None:
        module.fail_json(msg="Pod contains more than 1 container, option 'container' should be set")

    try:
        load_class = {'to_pod': K8SCopyToPod, 'from_pod': K8SCopyFromPod}
        state = module.params.get('state')
        k8s_copy = load_class.get(state)(module, k8s_ansible_mixin.client)
        k8s_copy.run()
    except Exception as e:
        module.fail_json("Failed to copy object due to: {0}".format(to_native(e)))


def main():
    argument_spec = copy.deepcopy(AUTH_ARG_SPEC)
    argument_spec['namespace'] = {'type': 'str', 'required': True}
    argument_spec['pod'] = {'type': 'str', 'required': True}
    argument_spec['container'] = {}
    argument_spec['remote_path'] = {'type': 'path', 'required': True}
    argument_spec['local_path'] = {'type': 'path'}
    argument_spec['content'] = {'type': 'str'}
    argument_spec['state'] = {'type': 'str', 'default': 'to_pod', 'choices': ['to_pod', 'from_pod']}
    argument_spec['no_preserve'] = {'type': 'bool', 'default': False}

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=[('local_path', 'content')],
                           required_if=[('state', 'from_pod', ['local_path'])],
                           required_one_of=[['local_path', 'content']],
                           supports_check_mode=True)

    execute_module(module)


if __name__ == '__main__':
    main()
