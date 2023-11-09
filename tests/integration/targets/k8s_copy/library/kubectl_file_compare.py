#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Aubin Bikouo <@abikouo>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""

module: kubectl_file_compare

short_description: Compare file and directory using kubectl

author:
    - Aubin Bikouo (@abikouo)

description:
  - This module is used to validate k8s_cp module.
  - Compare the local file/directory with the remote pod version

notes:
  - This module authenticates on kubernetes cluster using default kubeconfig only.

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
  args:
    description:
    - The file is considered to be an executable.
    - The tool will be run locally and on pod and compare result from output and stderr.
    type: list
  kubectl_path:
    description:
    - Path to the kubectl executable, if not specified it will be download.
    type: path
"""

EXAMPLES = r"""
- name: compare local /tmp/foo with /tmp/bar in a remote pod
  kubectl_file_compare:
    namespace: some-namespace
    pod: some-pod
    remote_path: /tmp/bar
    local_path: /tmp/foo
    kubectl_path: /tmp/test/kubectl

- name: Compare executable running help command
  kubectl_file_compare:
    namespace: some-namespace
    pod: some-pod
    remote_path: /tmp/test/kubectl
    local_path: kubectl
    kubectl_path: /tmp/test/kubectl
    args:
    - "--help"
"""


RETURN = r"""
"""

import filecmp
import os
from tempfile import NamedTemporaryFile, TemporaryDirectory

from ansible.module_utils.basic import AnsibleModule


def kubectl_get_content(module, dest_dir):
    kubectl_path = module.params.get("kubectl_path")
    if kubectl_path is None:
        kubectl_path = module.get_bin_path("kubectl", required=True)

    namespace = module.params.get("namespace")
    pod = module.params.get("pod")
    file = module.params.get("remote_path")

    cmd = [kubectl_path, "cp", "{0}/{1}:{2}".format(namespace, pod, file)]
    container = module.params.get("container")
    if container:
        cmd += ["-c", container]
    local_file = os.path.join(
        dest_dir, os.path.basename(module.params.get("remote_path"))
    )
    cmd.append(local_file)
    rc, out, err = module.run_command(cmd)
    return local_file, err, rc, out


def kubectl_run_from_pod(module):
    kubectl_path = module.params.get("kubectl_path")
    if kubectl_path is None:
        kubectl_path = module.get_bin_path("kubectl", required=True)

    cmd = [
        kubectl_path,
        "exec",
        module.params.get("pod"),
        "-n",
        module.params.get("namespace"),
    ]
    container = module.params.get("container")
    if container:
        cmd += ["-c", container]
    cmd += ["--", module.params.get("remote_path")]
    cmd += module.params.get("args")
    return module.run_command(cmd)


def compare_directories(dir1, dir2):
    test = filecmp.dircmp(dir1, dir2)
    if any(
        [len(test.left_only) > 0, len(test.right_only) > 0, len(test.funny_files) > 0]
    ):
        return False
    (t, mismatch, errors) = filecmp.cmpfiles(
        dir1, dir2, test.common_files, shallow=False
    )
    if len(mismatch) > 0 or len(errors) > 0:
        return False
    for common_dir in test.common_dirs:
        new_dir1 = os.path.join(dir1, common_dir)
        new_dir2 = os.path.join(dir2, common_dir)
        if not compare_directories(new_dir1, new_dir2):
            return False
    return True


def execute_module(module):
    args = module.params.get("args")
    local_path = module.params.get("local_path")
    namespace = module.params.get("namespace")
    pod = module.params.get("pod")
    file = module.params.get("remote_path")
    content = module.params.get("content")
    if args:
        pod_rc, pod_out, pod_err = kubectl_run_from_pod(module)
        rc, out, err = module.run_command([module.params.get("local_path")] + args)
        if rc == pod_rc and out == pod_out:
            module.exit_json(
                msg="{0} and {1}/{2}:{3} are same.".format(
                    local_path, namespace, pod, file
                ),
                rc=rc,
                stderr=err,
                stdout=out,
            )
        result = dict(
            local=dict(rc=rc, out=out, err=err),
            remote=dict(rc=pod_rc, out=pod_out, err=pod_err),
        )
        module.fail_json(
            msg=f"{local_path} and {namespace}/{pod}:{file} are same.", **result
        )
    else:
        with TemporaryDirectory() as tmpdirname:
            file_from_pod, err, rc, out = kubectl_get_content(
                module=module, dest_dir=tmpdirname
            )
            if not os.path.exists(file_from_pod):
                module.fail_json(
                    msg="failed to copy content from pod", error=err, output=out
                )

            if content is not None:
                with NamedTemporaryFile(mode="w") as tmp_file:
                    tmp_file.write(content)
                    tmp_file.flush()
                    if filecmp.cmp(file_from_pod, tmp_file.name):
                        module.exit_json(
                            msg=f"defined content and {namespace}/{pod}:{file} are same."
                        )
                    module.fail_json(
                        msg=f"defined content and {namespace}/{pod}:{file} are same."
                    )

            if os.path.isfile(local_path):
                if filecmp.cmp(file_from_pod, local_path):
                    module.exit_json(
                        msg=f"{local_path} and {namespace}/{pod}:{file} are same."
                    )
                module.fail_json(
                    msg=f"{local_path} and {namespace}/{pod}:{file} are same."
                )

            if os.path.isdir(local_path):
                if compare_directories(file_from_pod, local_path):
                    module.exit_json(
                        msg=f"{local_path} and {namespace}/{pod}:{file} are same."
                    )
                module.fail_json(
                    msg=f"{local_path} and {namespace}/{pod}:{file} are same."
                )


def main():
    argument_spec = {}
    argument_spec["namespace"] = {"type": "str", "required": True}
    argument_spec["pod"] = {"type": "str", "required": True}
    argument_spec["container"] = {}
    argument_spec["remote_path"] = {"type": "path", "required": True}
    argument_spec["local_path"] = {"type": "path"}
    argument_spec["content"] = {"type": "str"}
    argument_spec["kubectl_path"] = {"type": "path"}
    argument_spec["args"] = {"type": "list"}
    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[("local_path", "content")],
        required_one_of=[["local_path", "content"]],
    )

    execute_module(module)


if __name__ == "__main__":
    main()
