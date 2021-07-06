#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Aubin Bikouo <@abikouo>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r'''

module: k8s_diff

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
  content:
    description:
    - local content to compare with remote file from pod.
    - mutually exclusive with option I(local_path).
    type: path
    required: yes
'''

EXAMPLES = r'''
- name: compare local /tmp/foo with /tmp/bar in a remote pod
  k8s_diff:
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
import tarfile
import yaml
import time
import gzip
from tempfile import NamedTemporaryFile
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
try:
    from kubernetes import config
    from kubernetes.client import Configuration
    from kubernetes.client.api import core_v1_api
    from kubernetes.client.rest import ApiException
    from kubernetes.stream import stream
    from kubernetes.stream.ws_client import ERROR_CHANNEL
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
        self._api_instance = core_v1_api.CoreV1Api()

        self._name = module.params.get('pod')
        self._namespace = module.params.get('namespace')

        try:
            self._api_instance.read_namespaced_pod(name=self._name, namespace=self._namespace)
        except ApiException as e:
            module.fail_json(msg="{0}/{1} Pod not found: {2}".format(self._name, self._namespace, to_native(e)))

        # interactive session to the pod
        self._container_arg = {}
        if module.params.get('container'):
            self._container_arg['container'] = module.params.get('container')

    def run_from_pod(self, command):
        response = stream(self._api_instance.connect_get_namespaced_pod_exec,
                          self._name,
                          self._namespace,
                          command=command,
                          stderr=True, stdin=False,
                          stdout=True, tty=False,
                          _preload_content=False, **self._container_arg)
        errors = []
        output = []
        while response.is_open():
            response.update(timeout=1)
            if response.peek_stderr():
                errors.append(response.read_stderr())
            if response.peek_stdout():
                output.append(response.read_stdout())
        err = response.read_channel(ERROR_CHANNEL)
        err = yaml.safe_load(err)
        response.close()
        if err['status'] != 'Success':
            self._module.fail_json(msg="Failed to run {0} on Pod.".format(command), errors=errors)
        if output:
            if isinstance(output[0], bytes):
                return output[0].decode("utf-8")
            return output[0]
        return None

    def get_file_content(self, file_path):
        return self.run_from_pod(['cat', file_path])

    def get_archive_content(self):
        archive_name = self._module.params.get('remote_path')
        # create directory to extract archive
        remote_dir = os.path.join("/{0}".format(int(time.time())), os.path.basename(archive_name.rstrip(".tar")))
        command = ['mkdir', '-p', remote_dir]
        self.run_from_pod(command)

        # unarchive data
        command = ['tar', 'xvf', archive_name, '-C', remote_dir]
        output = self.run_from_pod(command)

        # Get file content
        content = {}
        for file in output.rstrip("\n").split("\n"):
            content[file] = self.run_from_pod(['cat', os.path.join(remote_dir, file)])
        return content


def compare_archive(module):
    # Read local archive
    local_path = module.params.get('local_path')
    with tarfile.open(local_path, 'r:') as tar:
        local_content = {}
        for member in tar.getmembers():
            if member.isfile():
                local_content[member.name] = tar.extractfile(member).read().decode("utf-8")
        remote_content = KubernetesClient(module).get_archive_content()
        diffs = []
        for fname in local_content:
            local = local_content[fname]
            remote = remote_content[fname]
            if local != remote:
                diffs.append({'file': fname, 'pod': remote, 'local': local})
        if diffs:
            module.fail_json(msg="files differs", pod=remote_content, local=local_content)
        module.exit_json(msg="archive are the same.")


def compare_zipfile(module):
    # Read local zip file
    local_path = module.params.get('local_path')
    with gzip.open(local_path, 'rb') as zf:
        local = zf.read().decode("utf-8")
        # Get remote content
        command = ['zcat', module.params.get('remote_path')]
        remote = KubernetesClient(module).run_from_pod(command)
        if local != remote:
            module.fail_json(msg="files differs", pod=remote, local=local)
        module.exit_json(msg="zip file are the same.")


def compare_directory(module):
    k8s = KubernetesClient(module)
    remote_path = module.params.get('remote_path')
    local_path = module.params.get('local_path')
    local_file_list = []
    for root, dirs, files in os.walk(local_path):
        for f in files:
            local_file = os.path.join(root, f)
            local_file_list.append(local_file)
            with open(local_file) as fh:
                local = fh.read()
                remote_file = os.path.join(remote_path, os.path.relpath(os.path.join(root, f), start=local_path))
                remote = k8s.get_file_content(remote_file)
                if local != remote:
                    module.fail_json(msg="{0} and {1} differs".format(local_file, remote_file), pod=remote, local=local)
    module.exit_json(msg="directory are the same. {0} file(s) compared".format(len(local_file_list)))


def execute_module(module):
    # Create kubernetes client
    k8s_client = KubernetesClient(module)
    local_path = module.params.get('local_path')
    remote_path = module.params.get('remote_path')
    content = module.params.get('content')
    tmp_file = None
    if local_path:
        items = [{'local': local_path, 'remote': remote_path}]
        if not os.path.exists(local_path):
            module.fail_json(msg="{0} not found.".format(local_path))
        if os.path.isdir(local_path):
            compare_directory(module)
        elif local_path.endswith(".tar"):
            compare_archive(module)
        elif local_path.endswith(".gz"):
            compare_zipfile(module)
    else:
        tmp_file = NamedTemporaryFile(mode="w")
        tmp_file.write(content)
        tmp_file.flush()
        items = [{'local': tmp_file.name, 'remote': remote_path}]

    # compare files
    diffs = []
    errors = []
    for item in items:
        with open(item.get('local'), 'r') as fh:
            l_content = fh.read()
            r_content = k8s_client.get_file_content(item.get('remote'))
            diffs = {'before': l_content, 'after': r_content}
            if l_content != r_content:
                local_name = item.get('local') if local_path else "'defined content'"
                msg = "{0} and {1} differs".format(local_name, item.get('remote'))
                if module._diff:
                    errors.append(msg)
                else:
                    if tmp_file:
                        tmp_file.close()
                    module.fail_json(msg=msg)
    if tmp_file:
        tmp_file.close()
    result = dict()
    if module._diff and diffs:
        result['diff'] = diffs
    if errors:
        result['errors'] = errors
        module.fail_json(msg="{0} files differs between local and remote pod.".format(len(errors)), **result)
    result['msg'] = "{0} file(s) successfully compared.".format(len(items))
    module.exit_json(changed=False, **result)


def main():
    argument_spec = {}
    argument_spec['namespace'] = {'type': 'str', 'required': True}
    argument_spec['pod'] = {'type': 'str', 'required': True}
    argument_spec['container'] = {}
    argument_spec['remote_path'] = {'type': 'path', 'required': True}
    argument_spec['local_path'] = {'type': 'path'}
    argument_spec['content'] = {'type': 'str'}
    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=[('local_path', 'content')],
                           required_one_of=[['local_path', 'content']])

    execute_module(module)


if __name__ == '__main__':
    main()
