#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: helm

short_description: Manages Kubernetes packages with the Helm package manager

version_added: "0.11.0"

author:
  - Lucas Boisserie (@LucasBoisserie)
  - Matthieu Diehr (@d-matt)

requirements:
  - "helm (https://github.com/helm/helm/releases)"
  - "yaml (https://pypi.org/project/PyYAML/)"

description:
  - Install, upgrade, delete packages with the Helm package manager.

options:
  chart_ref:
    description:
      - chart_reference on chart repository.
      - path to a packaged chart.
      - path to an unpacked chart directory.
      - absolute URL.
      - Required when I(release_state) is set to C(present).
    required: false
    type: path
  chart_repo_url:
    description:
      - Chart repository URL where to locate the requested chart.
    required: false
    type: str
  chart_version:
    description:
      - Chart version to install. If this is not specified, the latest version is installed.
    required: false
    type: str
  release_name:
    description:
      - Release name to manage.
    required: true
    type: str
    aliases: [ name ]
  release_namespace:
    description:
      - Kubernetes namespace where the chart should be installed.
    required: true
    type: str
    aliases: [ namespace ]
  release_state:
    choices: ['present', 'absent']
    description:
      - Desirated state of release.
    required: false
    default: present
    aliases: [ state ]
    type: str
  release_values:
    description:
        - Value to pass to chart.
    required: false
    default: {}
    aliases: [ values ]
    type: dict
  values_files:
    description:
        - Value files to pass to chart.
        - Paths will be read from the target host's filesystem, not the host running ansible.
        - values_files option is evaluated before values option if both are used.
        - Paths are evaluated in the order the paths are specified.
    required: false
    default: []
    type: list
    elements: str
    version_added: '1.1.0'
  update_repo_cache:
    description:
      - Run C(helm repo update) before the operation. Can be run as part of the package installation or as a separate step.
    default: false
    type: bool

#Helm options
  disable_hook:
    description:
      - Helm option to disable hook on install/upgrade/delete.
    default: False
    type: bool
  force:
    description:
      - Helm option to force reinstall, ignore on new install.
    default: False
    type: bool
  purge:
    description:
      - Remove the release from the store and make its name free for later use.
    default: True
    type: bool
  wait:
    description:
      - Wait until all Pods, PVCs, Services, and minimum number of Pods of a Deployment are in a ready state before marking the release as successful.
    default: False
    type: bool
  wait_timeout:
    description:
      - Timeout when wait option is enabled (helm2 is a number of seconds, helm3 is a duration).
    type: str
  atomic:
    description:
      - If set, the installation process deletes the installation on failure.
    type: bool
    default: False
  create_namespace:
    description:
      - Create the release namespace if not present.
    type: bool
    default: False
    version_added: "0.11.1"
  replace:
    description:
      - Reuse the given name, only if that name is a deleted release which remains in the history.
      - This is unsafe in production environment.
    type: bool
    default: False
    version_added: "1.11.0"
  skip_crds:
    description:
      - Skip custom resource definitions when installing or upgrading.
    type: bool
    default: False
    version_added: "1.2.0"
extends_documentation_fragment:
  - kubernetes.core.helm_common_options
'''

EXAMPLES = r'''
- name: Deploy latest version of Prometheus chart inside monitoring namespace (and create it)
  kubernetes.core.helm:
    name: test
    chart_ref: stable/prometheus
    release_namespace: monitoring
    create_namespace: true

# From repository
- name: Add stable chart repo
  kubernetes.core.helm_repository:
    name: stable
    repo_url: "https://kubernetes.github.io/ingress-nginx"

- name: Deploy latest version of Grafana chart inside monitoring namespace with values
  kubernetes.core.helm:
    name: test
    chart_ref: stable/grafana
    release_namespace: monitoring
    values:
      replicas: 2

- name: Deploy Grafana chart on 5.0.12 with values loaded from template
  kubernetes.core.helm:
    name: test
    chart_ref: stable/grafana
    chart_version: 5.0.12
    values: "{{ lookup('template', 'somefile.yaml') | from_yaml }}"

- name: Deploy Grafana chart using values files on target
  kubernetes.core.helm:
    name: test
    chart_ref: stable/grafana
    release_namespace: monitoring
    values_files:
      - /path/to/values.yaml

- name: Remove test release and waiting suppression ending
  kubernetes.core.helm:
    name: test
    state: absent
    wait: true

# From git
- name: Git clone stable repo on HEAD
  ansible.builtin.git:
    repo: "http://github.com/helm/charts.git"
    dest: /tmp/helm_repo

- name: Deploy Grafana chart from local path
  kubernetes.core.helm:
    name: test
    chart_ref: /tmp/helm_repo/stable/grafana
    release_namespace: monitoring

# From url
- name: Deploy Grafana chart on 5.6.0 from url
  kubernetes.core.helm:
    name: test
    chart_ref: "https://github.com/grafana/helm-charts/releases/download/grafana-5.6.0/grafana-5.6.0.tgz"
    release_namespace: monitoring
'''

RETURN = r"""
status:
  type: complex
  description: A dictionary of status output
  returned: on success Creation/Upgrade/Already deploy
  contains:
    appversion:
      type: str
      returned: always
      description: Version of app deployed
    chart:
      type: str
      returned: always
      description: Chart name and chart version
    name:
      type: str
      returned: always
      description: Name of the release
    namespace:
      type: str
      returned: always
      description: Namespace where the release is deployed
    revision:
      type: str
      returned: always
      description: Number of time where the release has been updated
    status:
      type: str
      returned: always
      description: Status of release (can be DEPLOYED, FAILED, ...)
    updated:
      type: str
      returned: always
      description: The Date of last update
    values:
      type: str
      returned: always
      description: Dict of Values used to deploy
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
  sample: helm upgrade ...
"""

import tempfile
import traceback

try:
    import yaml
    IMP_YAML = True
except ImportError:
    IMP_YAML_ERR = traceback.format_exc()
    IMP_YAML = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib, env_fallback
from ansible_collections.kubernetes.core.plugins.module_utils.helm import run_helm, get_values


def get_release(state, release_name):
    """
    Get Release from all deployed releases
    """

    if state is not None:
        for release in state:
            if release['name'] == release_name:
                return release
    return None


def get_release_status(module, command, release_name):
    """
    Get Release state from deployed release
    """

    list_command = command + " list --output=yaml --filter " + release_name

    rc, out, err = run_helm(module, list_command)

    release = get_release(yaml.safe_load(out), release_name)

    if release is None:  # not install
        return None

    release['values'] = get_values(module, command, release_name)

    return release


def run_repo_update(module, command):
    """
    Run Repo update
    """
    repo_update_command = command + " repo update"
    rc, out, err = run_helm(module, repo_update_command)


def fetch_chart_info(module, command, chart_ref):
    """
    Get chart info
    """
    inspect_command = command + " show chart " + chart_ref

    rc, out, err = run_helm(module, inspect_command)

    return yaml.safe_load(out)


def deploy(command, release_name, release_values, chart_name, wait,
           wait_timeout, disable_hook, force, values_files, atomic=False,
           create_namespace=False, replace=False, skip_crds=False):
    """
    Install/upgrade/rollback release chart
    """
    if replace:
        # '--replace' is not supported by 'upgrade -i'
        deploy_command = command + " install"
    else:
        deploy_command = command + " upgrade -i"  # install/upgrade

        # Always reset values to keep release_values equal to values released
        deploy_command += " --reset-values"

    if wait:
        deploy_command += " --wait"
        if wait_timeout is not None:
            deploy_command += " --timeout " + wait_timeout

    if atomic:
        deploy_command += " --atomic"

    if force:
        deploy_command += " --force"

    if replace:
        deploy_command += " --replace"

    if disable_hook:
        deploy_command += " --no-hooks"

    if create_namespace:
        deploy_command += " --create-namespace"

    if values_files:
        for value_file in values_files:
            deploy_command += " --values=" + value_file

    if release_values != {}:
        fd, path = tempfile.mkstemp(suffix='.yml')
        with open(path, 'w') as yaml_file:
            yaml.dump(release_values, yaml_file, default_flow_style=False)
        deploy_command += " -f=" + path

    if skip_crds:
        deploy_command += " --skip-crds"

    deploy_command += " " + release_name + " " + chart_name

    return deploy_command


def delete(command, release_name, purge, disable_hook):
    """
    Delete release chart
    """

    delete_command = command + " uninstall "

    if not purge:
        delete_command += " --keep-history"

    if disable_hook:
        delete_command += " --no-hooks"

    delete_command += " " + release_name

    return delete_command


def load_values_files(values_files):
    values = {}
    for values_file in values_files or []:
        with open(values_file, 'r') as fd:
            content = yaml.safe_load(fd)
            if not isinstance(content, dict):
                continue
            for k, v in content.items():
                values[k] = v
    return values


def has_plugin(command, plugin):
    """
    Check if helm plugin is installed.
    """

    cmd = command + " plugin list"
    rc, out, err = run_helm(module, cmd)
    for line in out.splitlines():
        if line.startswith("NAME"):
            continue
        name, _rest = line.split(None, 1)
        if name == plugin:
            return True
    return False


def helmdiff_check(module, helm_cmd, release_name, chart_ref, release_values,
                   values_files=None, chart_version=None, replace=False):
    """
    Use helm diff to determine if a release would change by upgrading a chart.
    """
    cmd = helm_cmd + " diff upgrade"
    cmd += " " + release_name
    cmd += " " + chart_ref

    if chart_version is not None:
        cmd += " " + "--version=" + chart_version
    if not replace:
        cmd += " " + "--reset-values"

    if release_values != {}:
        fd, path = tempfile.mkstemp(suffix='.yml')
        with open(path, 'w') as yaml_file:
            yaml.dump(release_values, yaml_file, default_flow_style=False)
        cmd += " -f=" + path

    if values_files:
        for values_file in values_files:
            cmd += " -f=" + values_file

    rc, out, err = run_helm(module, cmd)
    return len(out.strip()) > 0


def default_check(release_status, chart_info, values=None, values_files=None):
    """
    Use default check to determine if release would change by upgrading a chart.
    """
    # the 'appVersion' specification is optional in a chart
    chart_app_version = chart_info.get('appVersion', None)
    released_app_version = release_status.get('app_version', None)

    # when deployed without an 'appVersion' chart value the 'helm list' command will return the entry `app_version: ""`
    appversion_is_same = (chart_app_version == released_app_version) or (chart_app_version is None and released_app_version == "")

    if values_files:
        values_match = release_status['values'] == load_values_files(values_files)
    else:
        values_match = release_status['values'] == values
    return not values_match \
        or (chart_info['name'] + '-' + chart_info['version']) != release_status["chart"] \
        or not appversion_is_same


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            binary_path=dict(type='path'),
            chart_ref=dict(type='path'),
            chart_repo_url=dict(type='str'),
            chart_version=dict(type='str'),
            release_name=dict(type='str', required=True, aliases=['name']),
            release_namespace=dict(type='str', required=True, aliases=['namespace']),
            release_state=dict(default='present', choices=['present', 'absent'], aliases=['state']),
            release_values=dict(type='dict', default={}, aliases=['values']),
            values_files=dict(type='list', default=[], elements='str'),
            update_repo_cache=dict(type='bool', default=False),

            # Helm options
            disable_hook=dict(type='bool', default=False),
            force=dict(type='bool', default=False),
            context=dict(type='str', aliases=['kube_context'], fallback=(env_fallback, ['K8S_AUTH_CONTEXT'])),
            kubeconfig=dict(type='path', aliases=['kubeconfig_path'], fallback=(env_fallback, ['K8S_AUTH_KUBECONFIG'])),
            purge=dict(type='bool', default=True),
            wait=dict(type='bool', default=False),
            wait_timeout=dict(type='str'),
            atomic=dict(type='bool', default=False),
            create_namespace=dict(type='bool', default=False),
            replace=dict(type='bool', default=False),
            skip_crds=dict(type='bool', default=False),

            # Generic auth key
            host=dict(type='str', fallback=(env_fallback, ['K8S_AUTH_HOST'])),
            ca_cert=dict(type='path', aliases=['ssl_ca_cert'], fallback=(env_fallback, ['K8S_AUTH_SSL_CA_CERT'])),
            validate_certs=dict(type='bool', default=True, aliases=['verify_ssl'], fallback=(env_fallback, ['K8S_AUTH_VERIFY_SSL'])),
            api_key=dict(type='str', no_log=True, fallback=(env_fallback, ['K8S_AUTH_API_KEY']))
        ),
        required_if=[
            ('release_state', 'present', ['release_name', 'chart_ref']),
            ('release_state', 'absent', ['release_name'])
        ],
        mutually_exclusive=[
            ("context", "ca_cert"),
            ("context", "validate_certs"),
            ("kubeconfig", "ca_cert"),
            ("kubeconfig", "validate_certs")
        ],
        supports_check_mode=True,
    )

    if not IMP_YAML:
        module.fail_json(msg=missing_required_lib("yaml"), exception=IMP_YAML_ERR)

    changed = False

    bin_path = module.params.get('binary_path')
    chart_ref = module.params.get('chart_ref')
    chart_repo_url = module.params.get('chart_repo_url')
    chart_version = module.params.get('chart_version')
    release_name = module.params.get('release_name')
    release_state = module.params.get('release_state')
    release_values = module.params.get('release_values')
    values_files = module.params.get('values_files')
    update_repo_cache = module.params.get('update_repo_cache')

    # Helm options
    disable_hook = module.params.get('disable_hook')
    force = module.params.get('force')
    purge = module.params.get('purge')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')
    atomic = module.params.get('atomic')
    create_namespace = module.params.get('create_namespace')
    replace = module.params.get('replace')
    skip_crds = module.params.get('skip_crds')

    if bin_path is not None:
        helm_cmd_common = bin_path
    else:
        helm_cmd_common = module.get_bin_path('helm', required=True)

    if update_repo_cache:
        run_repo_update(module, helm_cmd_common)

    # Get real/deployed release status
    release_status = get_release_status(module, helm_cmd_common, release_name)

    # keep helm_cmd_common for get_release_status in module_exit_json
    helm_cmd = helm_cmd_common
    if release_state == "absent" and release_status is not None:
        if replace:
            module.fail_json(msg="replace is not applicable when state is absent")

        helm_cmd = delete(helm_cmd, release_name, purge, disable_hook)
        changed = True
    elif release_state == "present":

        if chart_version is not None:
            helm_cmd += " --version=" + chart_version

        if chart_repo_url is not None:
            helm_cmd += " --repo=" + chart_repo_url

        # Fetch chart info to have real version and real name for chart_ref from archive, folder or url
        chart_info = fetch_chart_info(module, helm_cmd, chart_ref)

        if release_status is None:  # Not installed
            helm_cmd = deploy(helm_cmd, release_name, release_values, chart_ref, wait, wait_timeout,
                              disable_hook, False, values_files=values_files, atomic=atomic,
                              create_namespace=create_namespace, replace=replace,
                              skip_crds=skip_crds)
            changed = True

        else:

            if has_plugin(helm_cmd_common, "diff") and not chart_repo_url:
                would_change = helmdiff_check(module, helm_cmd_common, release_name, chart_ref,
                                              release_values, values_files, chart_version, replace)
            else:
                module.warn("The default idempotency check can fail to report changes in certain cases. "
                            "Install helm diff for better results.")
                would_change = default_check(release_status, chart_info, release_values, values_files)

            if force or would_change:
                helm_cmd = deploy(helm_cmd, release_name, release_values, chart_ref, wait, wait_timeout,
                                  disable_hook, force, values_files=values_files, atomic=atomic,
                                  create_namespace=create_namespace, replace=replace,
                                  skip_crds=skip_crds)
                changed = True

    if module.check_mode:
        check_status = {
            'values': {
                "current": {},
                "declared": {},
            }
        }
        if release_status:
            check_status['values']['current'] = release_status['values']
            check_status['values']['declared'] = release_status

        module.exit_json(
            changed=changed,
            command=helm_cmd,
            status=check_status,
            stdout='',
            stderr='',
        )
    elif not changed:
        module.exit_json(
            changed=False,
            status=release_status,
            stdout='',
            stderr='',
            command=helm_cmd,
        )

    rc, out, err = run_helm(module, helm_cmd)

    module.exit_json(
        changed=changed,
        stdout=out,
        stderr=err,
        status=get_release_status(module, helm_cmd_common, release_name),
        command=helm_cmd,
    )


if __name__ == '__main__':
    main()
