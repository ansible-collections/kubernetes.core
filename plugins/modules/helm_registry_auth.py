#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2023, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: helm_registry_auth

short_description: login or logout to a registry.

version_added: "2.5.0"

author:
  - Aubin Bikouo (@abikouo)

requirements:
  - "helm (https://github.com/helm/helm/releases)"

description:
  -  Authenticate to a remote registry analogous to C(helm registry login)
    or Remove credentials stored for a remote registry analogous to C(helm registry logout).

options:
  state:
    description:
    - If set to I(present) attempt to log in to the remote registry server using the URL specified in C(host).
    - If set to I(absent) attempt to log out by removing credentials stored for the remote registry server specified in C(host).
    default: present
    choices:
    - present
    - absent
    type: str
  host:
    description:
    - Provide a URL for accessing the remote registry.
    type: str
    required: True
  validate_certs:
    description:
    - Whether or not to verify the Registry server's SSL certificates.
    type: bool
    aliases: [ verify_ssl ]
    default: True
  username:
    description:
    - Provide a username for authenticating with the remote registry.
    - Required when C(state) is set to I(present).
    type: str
  password:
    description:
    - Provide a password for authenticating with the remote registry.
    - Required when C(state) is set to I(present).
    type: str
  binary_path:
    description:
      - The path of a helm binary to use.
    type: path
"""

EXAMPLES = r"""
- hosts: localhost
  tasks:
  - block:
    # It's good practice to store login credentials in a secure vault and not
    # directly in playbooks.
    - include_vars: helm_registry_passwords.yml

    - name: Login to remote registry
      kubernetes.core.helm_registry_auth:
        username: admin
        password: "{{ helm_admin_password }}"
        host: localhost:5000

    - name: Download Chart from Registry
      kubernetes.core.helm_pull:
        chart_ref: mychart
        repo_url: oci://localhost:5000/helm-charts

    always:
    - name: Logout to Remote registry
      kubernetes.core.helm_registry_auth:
        host: localhost:5000
        state: absent
"""

RETURN = r"""
stdout:
  type: str
  description: Full `helm` command stdout, in case you want to display it or examine the event log
  returned: always
  sample: ''
stderr:
  type: str
  description: Full `helm` command stderr, in case you want to display it or examine the event log
  returned: always
  sample: ''
command:
  type: str
  description: Full `helm` command built by this module, in case you want to re-run the command outside the module or debug a problem.
  returned: always
  sample: helm registry login...
"""


from ansible_collections.kubernetes.core.plugins.module_utils.helm import (
    AnsibleHelmModule,
)
from ansible_collections.kubernetes.core.plugins.module_utils.version import (
    LooseVersion,
)


def argument_spec():
    arg_spec = {
        "state": {
            "type": "str",
            "default": "present",
            "choices": ["present", "absent"],
        },
        "host": {"type": "str", "required": True},
        "validate_certs": {"type": "bool", "default": True, "aliases": ["verify_ssl"]},
        "username": {},
        "password": {"no_log": True},
        "binary_path": {"type": "path"},
    }

    return arg_spec


def main():

    module = AnsibleHelmModule(
        argument_spec=argument_spec(),
        required_if=[
            ("state", "present", ["username", "password"]),
        ],
        supports_check_mode=True,
    )

    state = module.params.get("state")
    command = [module.get_helm_binary(), "registry"]
    if state == "present":
        command.extend(
            [
                "login",
                "--username",
                module.params.get("username"),
                "--password",
                module.params.get("password"),
            ]
        )
    else:
        command.append("logout")

    command.append(module.params.get("host"))
    command = " ".join(command)
    out, err = "", ""
    changed = True
    if not module.check_mode:
        env_update = {}
        if LooseVersion(module.get_helm_version()) < LooseVersion("3.0.0"):
            env_update["HELM_EXPERIMENTAL_OCI"] = "1"
        rc, out, err = module.run_helm_command(
            command, fails_on_error=False, add_env_update=env_update
        )
        if rc != 0:
            if state == "absent" and "Error: not logged in" in err:
                err = err.replace("Error: ", "")
                changed = False
            else:
                module.fail_json(
                    msg="Failure when executing Helm command. Exited {0}.\nstdout: {1}\nstderr: {2}".format(
                        rc, out, err
                    ),
                    stdout=out,
                    stderr=err,
                    command=command,
                )

    module.exit_json(changed=changed, stdout=out, stderr=err, command=command)


if __name__ == "__main__":
    main()
