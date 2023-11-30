#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2023, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: helm_test_pending
short_description: created pending-install release
author:
  - Aubin Bikouo (@abikouo)
requirements:
  - "helm (https://github.com/helm/helm/releases)"
description:
  - This module is used to create a pending install release for integration testing
  - The scope of this module is the integration testing of the kubernetes.core collection only.
options:
  binary_path:
    description:
      - The path of a helm binary to use.
    required: true
    type: path
  chart_ref:
    description:
      - chart reference on chart repository (e.g. my-repo/my-chart-ref)
    required: true
    type: str
  chart_release:
    description:
      - Release name to manage.
    required: true
    type: str
  chart_release_namespace:
    description:
      - Kubernetes namespace where the chart should be installed.
    required: true
    type: str
"""

EXAMPLES = r"""
"""

RETURN = r"""
"""

import json
import subprocess
import time

from ansible.module_utils.basic import AnsibleModule


class HelmReleaseNotFoundError(Exception):
    def __init__(self, message):
        super().__init__(message)


def create_pending_install_release(helm_binary, chart_ref, chart_release, namespace):
    # create pending-install release
    command = [
        helm_binary,
        "install",
        chart_release,
        chart_ref,
        "--namespace",
        namespace,
        "--wait",
    ]
    proc = subprocess.Popen(command)
    time.sleep(2)
    proc.kill()
    # ensure release status is pending-install
    command = [
        helm_binary,
        "list",
        "--all",
        "--output=json",
        "--namespace",
        namespace,
        "--filter",
        chart_release,
    ]
    cmd = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = cmd.communicate()

    data = json.loads(out)
    if not data:
        error = "Release %s not found." % chart_release
        raise HelmReleaseNotFoundError(message=error)
    return data[0]["status"] == "pending-install", data[0]["status"]


def main():
    module = AnsibleModule(
        argument_spec=dict(
            binary_path=dict(type="path", required=True),
            chart_ref=dict(type="str", required=True),
            chart_release=dict(type="str", required=True),
            chart_release_namespace=dict(type="str", required=True),
        ),
    )

    params = dict(
        helm_binary=module.params.get("binary_path"),
        chart_release=module.params.get("chart_release"),
        chart_ref=module.params.get("chart_ref"),
        namespace=module.params.get("chart_release_namespace"),
    )

    try:
        result, status = create_pending_install_release(**params)
        if not result:
            module.fail_json(
                msg="unable to create pending-install release, current status is %s"
                % status
            )
        module.exit_json(changed=True, msg="Release created with status '%s'" % status)
    except HelmReleaseNotFoundError as err:
        module.fail_json(
            msg="Error while trying to create pending-install release due to '%s'" % err
        )


if __name__ == "__main__":
    main()
