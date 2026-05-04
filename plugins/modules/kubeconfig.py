#!/usr/bin/python
#
# Copyright (c) Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: kubeconfig

short_description: Generate, update, and optionally write Kubernetes kubeconfig files

version_added: "6.5.0"

author: "Youssef Khalid Ali (@YoussefKhalidAli)"

description:
  - Build, update, and manage Kubernetes kubeconfig files using structured input.
  - Supports loading an existing kubeconfig file and merging clusters, users, and contexts.
  - Can optionally write the resulting kubeconfig to a destination path.
  - Ensures idempotent behavior by only updating files when changes occur.

requirements:
  - "PyYAML >= 5.1"

notes:
  - Input data is merged by resource name (cluster, user, context).
  - Updates under O(clusters), O(users), and O(contexts) are matched by C(name) against the kubeconfig loaded from O(path).
  - For an existing C(name), each entry's C(behavior) suboption controls the update.
  - The default is V(merge), which merges nested C(cluster), C(user), and C(context) data so unspecified keys are preserved.
  - With V(replace), the previous entry for that name is dropped and only the new definition is used.
  - With V(keep), the existing entry is left unchanged.
  - This can be used to move kubeconfig files to a different location with different content.
  - This module does not validate cluster connectivity or authentication.
  - The module supports C(check_mode) and will not write files when enabled.
  - The structure follows standard Kubernetes kubeconfig format as defined in the Kubernetes documentation.
  - Tokens and sensitive data should be protected using ansible-vault or environment variables.

options:
  path:
    description:
      - Path to an existing kubeconfig file to load and merge from.
      - If the file does not exist, a new kubeconfig will be created.
      - This becomes the default destination if O(dest) is not specified.
    type: str
    required: true

  dest:
    description:
      - Destination path where the final kubeconfig should be written.
      - If not specified, the kubeconfig will be saved to O(path).
      - Allows copying and modifying a kubeconfig to a new location.
    type: str
    required: false

  clusters:
    description:
      - List of cluster definitions to merge into the kubeconfig.
      - Each cluster is identified by its C(name).
      - When C(name) matches an existing cluster, the default C(behavior) is V(merge).
      - See the C(behavior) suboption for V(replace) and V(keep).
    type: list
    elements: dict
    required: false
    default: []
    suboptions:
      name:
        description:
          - Unique name identifier for the cluster.
        type: str
        required: true
      behavior:
        description:
          - How to handle merging if a cluster with this name already exists.
          - C(merge) - Update only the specified fields, preserve others (default).
          - C(replace) - Replace the entire cluster definition.
          - C(keep) - Keep existing cluster, skip this entry.
        type: str
        choices: ['merge', 'replace', 'keep']
        default: merge
      cluster:
        description:
          - Cluster configuration details.
        type: dict
        required: true
        suboptions:
          server:
            description:
              - Kubernetes API server URL (e.g., C(https://k8s.example.com:6443)).
            type: str
            required: true
          certificate-authority:
            description:
              - Path to a CA certificate file for validating the API server certificate.
            type: str
          certificate-authority-data:
            description:
              - Base64 encoded CA certificate data.
              - Use this instead of C(certificate-authority) for embedded certificates.
            type: str
          insecure-skip-tls-verify:
            description:
              - If true, the server's certificate will not be validated.
            type: bool
          proxy-url:
            description:
              - Optional proxy URL for cluster connections.
            type: str
          tls-server-name:
            description:
              - Server name to use for server certificate validation.
            type: str

  users:
    description:
      - List of user authentication configurations.
      - Each user is identified by its C(name).
      - When C(name) matches an existing user, the default C(behavior) is V(merge).
      - See the C(behavior) suboption for V(replace) and V(keep).
    type: list
    elements: dict
    required: false
    default: []
    suboptions:
      name:
        description:
          - Unique name identifier for the user.
        type: str
        required: true
      behavior:
        description:
          - How to handle merging if a user with this name already exists.
          - C(merge) - Update only the specified fields, preserve others (default).
          - C(replace) - Replace the entire user definition.
          - C(keep) - Keep existing user, skip this entry.
        type: str
        choices: ['merge', 'replace', 'keep']
        default: merge
      user:
        description:
          - User authentication configuration.
        type: dict
        required: true
        suboptions:
          token:
            description:
              - Bearer token for authentication.
            type: str
          username:
            description:
              - Username for basic authentication.
            type: str
          password:
            description:
              - Password for basic authentication.
            type: str
          client-certificate:
            description:
              - Path to client certificate file.
              - Used for certificate-based authentication.
            type: str
          client-key:
            description:
              - Path to client private key file.
              - Must be provided with C(client-certificate).
            type: str
          client-certificate-data:
            description:
              - Base64 encoded client certificate.
              - Use instead of C(client-certificate) for embedded certificates.
            type: str
          client-key-data:
            description:
              - Base64 encoded client private key.
              - Use instead of C(client-key) for embedded keys.
            type: str
          auth-provider:
            description:
              - Authentication provider configuration (e.g., for GCP, Azure).
            type: dict
          exec:
            description:
              - Exec-based credential plugin configuration.
              - Used for external authentication providers.
            type: dict

  contexts:
    description:
      - List of context definitions linking users and clusters.
      - Each context is identified by its C(name).
      - When C(name) matches an existing context, the default C(behavior) is V(merge).
      - See the C(behavior) suboption for V(replace) and V(keep).
    type: list
    elements: dict
    required: false
    default: []
    suboptions:
      name:
        description:
          - Unique name identifier for the context.
        type: str
        required: true
      behavior:
        description:
          - How to handle merging if a context with this name already exists.
          - C(merge) - Update only the specified fields, preserve others (default).
          - C(replace) - Replace the entire context definition.
          - C(keep) - Keep existing context, skip this entry.
        type: str
        choices: ['merge', 'replace', 'keep']
        default: merge
      context:
        description:
          - Context configuration linking cluster and user.
        type: dict
        required: true
        suboptions:
          cluster:
            description:
              - Name of the cluster to use (must match a cluster name in O(clusters)).
            type: str
            required: true
          user:
            description:
              - Name of the user to authenticate as (must match a user name in O(users)).
            type: str
            required: true
          namespace:
            description:
              - Default namespace to use for this context.
              - If not specified, defaults to C(default).
            type: str

  preferences:
    description:
      - Kubeconfig preferences.
      - Used for client-side settings like color output, default editor, etc.
    type: dict
    required: false
    default: {}

  current_context:
    description:
      - Name of the context to set as current/active.
      - This context will be used by default when using kubectl.
      - Must match one of the context names defined in O(contexts).
    type: str
    required: false

seealso:
  - name: Kubernetes kubeconfig documentation
    description: Official Kubernetes documentation for kubeconfig files
    link: https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/
  - name: kubectl config documentation
    description: kubectl commands for working with kubeconfig files
    link: https://kubernetes.io/docs/reference/kubectl/generated/kubectl_config/
"""

EXAMPLES = r"""
# Create a new kubeconfig file with a single cluster
- name: Create basic kubeconfig
  kubernetes.core.kubeconfig:
    path: /home/user/.kube/config
    clusters:
      - name: production-cluster
        cluster:
          server: https://prod.k8s.example.com:6443
          certificate-authority-data: LS0tLS1CRUdJTi...
    users:
      - name: admin-user
        user:
          token: eyJhbGciOiJSUzI1NiIsImtpZCI6IiJ9...
    contexts:
      - name: prod-admin
        context:
          cluster: production-cluster
          user: admin-user
          namespace: production
    current_context: prod-admin

- name: Copy and modify kubeconfig
  kubernetes.core.kubeconfig:
    path: /home/user/.kube/config
    dest: /home/user/.kube/config-backup
    clusters:
      - name: new-cluster
        cluster:
          server: https://new.example.com:6443

- name: Switch current context
  kubernetes.core.kubeconfig:
    path: ~/.kube/config
    current_context: prod-context

- name: Update user credentials
  kubernetes.core.kubeconfig:
    path: ~/.kube/config
    users:
      - name: admin-user
        user:
          token: "{{ new_admin_token }}"
"""

RETURN = r"""
kubeconfig:
  description: The complete kubeconfig data structure.
  type: dict
  returned: always

dest:
  description: The path where the kubeconfig was written.
  type: str
  returned: always
  sample: /home/user/.kube/config
"""
import os
import traceback

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.common.text.converters import to_native
from ansible_collections.kubernetes.core.plugins.module_utils.args_common import (
    extract_sensitive_values_from_kubeconfig,
)
from ansible_collections.kubernetes.core.plugins.module_utils.kubeconfig import (
    hash_data,
    load_yaml_file,
    merge_by_name,
    write_file,
)

try:
    import yaml

    IMP_YAML = True
    IMP_YAML_ERR = None
except ImportError:
    IMP_YAML = False
    IMP_YAML_ERR = traceback.format_exc()


def run_module():
    module_args = dict(
        path=dict(type="str", required=True),
        dest=dict(type="str", required=False),
        clusters=dict(type="list", elements="dict", required=False, default=[]),
        users=dict(type="list", elements="dict", required=False, default=[]),
        contexts=dict(type="list", elements="dict", required=False, default=[]),
        preferences=dict(type="dict", required=False, default={}),
        current_context=dict(type="str", required=False),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    path = module.params["path"]
    dest = module.params["dest"] or path

    clusters_input = module.params["clusters"]
    users_input = module.params["users"]
    contexts_input = module.params["contexts"]

    preferences = module.params["preferences"]
    current_context = module.params["current_context"]

    # Load existing kubeconfig
    try:
        if not IMP_YAML:
            module.fail_json(
                msg=missing_required_lib("pyyaml"),
                exception=IMP_YAML_ERR,
            )
        existing = load_yaml_file(path) if path else {}
    except Exception as e:
        module.fail_json(
            msg="Failed to load existing kubeconfig: %s" % to_native(e),
            exception=traceback.format_exc(),
        )

    clusters = merge_by_name(existing.get("clusters", []), clusters_input)
    users = merge_by_name(existing.get("users", []), users_input)
    contexts = merge_by_name(existing.get("contexts", []), contexts_input)

    # Build final kubeconfig
    kubeconfig = {
        "apiVersion": "v1",
        "kind": "Config",
        "preferences": preferences or existing.get("preferences", {}),
        "clusters": clusters,
        "users": users,
        "contexts": contexts,
        "current-context": current_context or existing.get("current-context") or "",
    }

    changed = False
    old_data = {}

    if os.path.exists(dest):
        try:
            with open(dest, "r") as f:
                old_data = yaml.safe_load(f) or {}
        except Exception as e:
            module.fail_json(
                msg="Failed to read destination file: %s" % to_native(e),
                exception=traceback.format_exc(),
            )

    old_hash = hash_data(old_data)
    new_hash = hash_data(kubeconfig)

    if old_hash != new_hash:
        if not module.check_mode:
            try:
                write_file(dest, kubeconfig)
            except Exception as e:
                module.fail_json(
                    msg="Failed to write kubeconfig: %s" % to_native(e),
                    exception=traceback.format_exc(),
                )
        changed = True

    if isinstance(kubeconfig, dict):
        module.no_log_values.update(
            extract_sensitive_values_from_kubeconfig(kubeconfig)
        )

    module.exit_json(
        changed=changed,
        kubeconfig=kubeconfig,
        dest=dest,
        msg=(
            "Kubeconfig file has been updated."
            if changed
            else "Kubeconfig file is already up to date."
        ),
    )


def main():
    run_module()


if __name__ == "__main__":
    main()
