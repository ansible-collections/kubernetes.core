# -*- coding: utf-8 -*-
# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


from contextlib import contextmanager
import os
import tempfile
import traceback
import re

from ansible.module_utils.basic import missing_required_lib


try:
    import yaml

    HAS_YAML = True
except ImportError:
    YAML_IMP_ERR = traceback.format_exc()
    HAS_YAML = False


@contextmanager
def prepare_helm_environ_update(module):
    environ_update = {}
    file_to_cleam_up = None
    kubeconfig_path = module.params.get("kubeconfig")
    if module.params.get("context") is not None:
        environ_update["HELM_KUBECONTEXT"] = module.params.get("context")
    if module.params.get("release_namespace"):
        environ_update["HELM_NAMESPACE"] = module.params.get("release_namespace")
    if module.params.get("api_key"):
        environ_update["HELM_KUBETOKEN"] = module.params["api_key"]
    if module.params.get("host"):
        environ_update["HELM_KUBEAPISERVER"] = module.params["host"]
    if module.params.get("validate_certs") is False or module.params.get("ca_cert"):
        kubeconfig_path = write_temp_kubeconfig(
            module.params["host"],
            validate_certs=module.params["validate_certs"],
            ca_cert=module.params["ca_cert"],
        )
        file_to_cleam_up = kubeconfig_path
    if kubeconfig_path is not None:
        environ_update["KUBECONFIG"] = kubeconfig_path

    try:
        yield environ_update
    finally:
        if file_to_cleam_up:
            os.remove(file_to_cleam_up)


def run_helm(module, command, fails_on_error=True):
    if not HAS_YAML:
        module.fail_json(msg=missing_required_lib("PyYAML"), exception=YAML_IMP_ERR)

    with prepare_helm_environ_update(module) as environ_update:
        rc, out, err = module.run_command(command, environ_update=environ_update)
    if fails_on_error and rc != 0:
        module.fail_json(
            msg="Failure when executing Helm command. Exited {0}.\nstdout: {1}\nstderr: {2}".format(
                rc, out, err
            ),
            stdout=out,
            stderr=err,
            command=command,
        )
    return rc, out, err


def get_values(module, command, release_name):
    """
    Get Values from deployed release
    """
    if not HAS_YAML:
        module.fail_json(msg=missing_required_lib("PyYAML"), exception=YAML_IMP_ERR)

    get_command = command + " get values --output=yaml " + release_name

    rc, out, err = run_helm(module, get_command)
    # Helm 3 return "null" string when no values are set
    if out.rstrip("\n") == "null":
        return {}
    return yaml.safe_load(out)


def write_temp_kubeconfig(server, validate_certs=True, ca_cert=None):
    # Workaround until https://github.com/helm/helm/pull/8622 is merged
    content = {
        "apiVersion": "v1",
        "kind": "Config",
        "clusters": [{"cluster": {"server": server}, "name": "generated-cluster"}],
        "contexts": [
            {"context": {"cluster": "generated-cluster"}, "name": "generated-context"}
        ],
        "current-context": "generated-context",
    }

    if not validate_certs:
        content["clusters"][0]["cluster"]["insecure-skip-tls-verify"] = True
    if ca_cert:
        content["clusters"][0]["cluster"]["certificate-authority"] = ca_cert

    _fd, file_name = tempfile.mkstemp()
    with os.fdopen(_fd, "w") as fp:
        yaml.dump(content, fp)
    return file_name


def get_helm_plugin_list(module, helm_bin=None):
    """
    Return `helm plugin list`
    """
    if not helm_bin:
        return []
    helm_plugin_list = helm_bin + " list"
    rc, out, err = run_helm(module, helm_plugin_list)
    if rc != 0 or (out == "" and err == ""):
        module.fail_json(
            msg="Failed to get Helm plugin info",
            command=helm_plugin_list,
            stdout=out,
            stderr=err,
            rc=rc,
        )
    return (rc, out, err)


def parse_helm_plugin_list(module, output=None):
    """
    Parse `helm plugin list`, return list of plugins
    """
    ret = []
    if not output:
        return ret

    for line in output:
        if line.startswith("NAME"):
            continue
        name, version, description = line.split("\t", 3)
        name = name.strip()
        version = version.strip()
        description = description.strip()
        if name == "":
            continue
        ret.append((name, version, description))

    return ret


def get_helm_version(module, helm_bin):

    helm_version_command = helm_bin + " version"
    rc, out, err = module.run_command(helm_version_command)
    if rc == 0:
        m = re.match(r'version.BuildInfo{Version:"v([0-9\.]*)",', out)
        if m:
            return m.group(1)
    return None
