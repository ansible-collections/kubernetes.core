#
#  Copyright 2021 Red Hat | Ansible
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = """
    name: kustomize

    short_description: Build a set of kubernetes resources using a 'kustomization.yaml' file.

    version_added: "2.2.0"

    author:
      - Aubin Bikouo (@abikouo)
    notes:
      - If both kustomize and kubectl are part of the PATH, kustomize will be used by the plugin.
    description:
      - Uses the kustomize or the kubectl tool.
      - Return the result of C(kustomize build) or C(kubectl kustomize).
    options:
      dir:
        description:
        - The directory path containing 'kustomization.yaml',
          or a git repository URL with a path suffix specifying same with respect to the repository root.
        - If omitted, '.' is assumed.
        default: "."
      binary_path:
        description:
        - The path of a kustomize or kubectl binary to use.
      opt_dirs:
        description:
        - An optional list of directories to search for the executable in addition to PATH.

    requirements:
      - "python >= 3.6"
"""

EXAMPLES = """
- name: Run lookup using kustomize
  set_fact:
    resources: "{{ lookup('kubernetes.core.kustomize', binary_path='/path/to/kustomize') }}"

- name: Run lookup using kubectl kustomize
  set_fact:
    resources: "{{ lookup('kubernetes.core.kustomize', binary_path='/path/to/kubectl') }}"

- name: Create kubernetes resources for lookup output
  k8s:
    definition: "{{ lookup('kubernetes.core.kustomize', dir='/path/to/kustomization') }}"
"""

RETURN = """
  _list:
    description:
      - YAML string for the object definitions returned from the tool execution.
    type: str
    sample:
      kind: ConfigMap
      apiVersion: v1
      metadata:
        name: my-config-map
        namespace: default
      data:
        key1: val1
"""

from ansible.errors import AnsibleLookupError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils.common.process import get_bin_path


import subprocess


def get_binary_from_path(name, opt_dirs=None):
    opt_arg = {}
    try:
        if opt_dirs is not None:
            if not isinstance(opt_dirs, list):
                opt_dirs = [opt_dirs]
            opt_arg["opt_dirs"] = opt_dirs
        bin_path = get_bin_path(name, **opt_arg)
        return bin_path
    except ValueError:
        return None


def run_command(command):
    cmd = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return cmd.communicate()


class LookupModule(LookupBase):
    def run(
        self, terms, variables=None, dir=".", binary_path=None, opt_dirs=None, **kwargs
    ):
        executable_path = binary_path
        if executable_path is None:
            executable_path = get_binary_from_path(name="kustomize", opt_dirs=opt_dirs)
            if executable_path is None:
                executable_path = get_binary_from_path(
                    name="kubectl", opt_dirs=opt_dirs
                )

            # validate that at least one tool was found
            if executable_path is None:
                raise AnsibleLookupError(
                    "Failed to find required executable 'kubectl' and 'kustomize' in paths"
                )

        # check input directory
        kustomization_dir = dir

        command = [executable_path]
        if executable_path.endswith("kustomize"):
            command += ["build", kustomization_dir]
        elif executable_path.endswith("kubectl"):
            command += ["kustomize", kustomization_dir]
        else:
            raise AnsibleLookupError(
                "unexpected tool provided as parameter {0}, expected one of kustomize, kubectl.".format(
                    executable_path
                )
            )

        (out, err) = run_command(command)
        if err:
            raise AnsibleLookupError(
                "kustomize command failed with: {0}".format(err.decode("utf-8"))
            )
        return [out.decode("utf-8")]
