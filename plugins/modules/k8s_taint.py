#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2021, Alina Buzachis <@alinabuzachis>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
module: k8s_taint
short_description: Taint a node in a Kubernetes/OpenShift cluster
version_added: "2.1.0"
author: Alina Buzachis (@alinabuzachis)
description:
    - Taint allows a node to refuse Pod to be scheduled unless that Pod has a matching toleration.
    - Untaint will remove taints from nodes as needed.
extends_documentation_fragment:
  - kubernetes.core.k8s_auth_options
options:
    state:
        description:
            - Determines whether to add or remove taints.
        type: str
        default: present
        choices: [ present, absent ]
    name:
        description:
            - The name of the node.
        required: true
        type: str
    taints:
        description:
            - List containing the taints.
        type: list
        required: true
        elements: dict
        suboptions:
            key:
                description:
                    - The taint key to be applied to a node.
                type: str
            value:
                description:
                    - The taint value corresponding to the taint key.
                type: str
            effect:
                description:
                    - The effect of the taint on Pods that do not tolerate the taint.
                    - Required when I(state=present).
                type: str
                choices: [ NoSchedule, NoExecute, PreferNoSchedule ]
    overwrite:
        description:
            - If true, allow taints to be overwritten, otherwise reject taint updates that overwrite existing taints.
        required: false
        default: false
        type: bool
requirements:
  - python >= 3.6
  - kubernetes >= 12.0.0
"""

EXAMPLES = r"""
- name: Taint node "foo"
  kubernetes.core.k8s_taint:
    state: present
    name: foo
    taints:
        - effect: NoExecute
          key: "key1"
          value: "value1"

- name: Taint node "foo"
  kubernetes.core.k8s_taint:
    state: present
    name: foo
    taints:
        - effect: NoExecute
          key: "key1"
          value: "value1"
        - effect: NoSchedule
          key: "key1"
          value: "value1"

- name: Remove all taints from "foo" with "key=key1".
  kubernetes.core.k8s_taint:
    state: absent
    name: foo
    taints: "key1"

- name: Remove taint from "foo".
  kubernetes.core.k8s_taint:
    state: absent
    name: foo
    taints:
        - effect: NoExecute
          key: "key1"
          value: "value1"
"""

RETURN = r"""
result:
   description:
        -  Shows if the node has been successfully tainted/untained.
   type: str
   returned: success
   sample: "node/ip-10-0-152-161.eu-central-1.compute.internal untainted"
"""


import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kubernetes.core.plugins.module_utils.args_common import (
    AUTH_ARG_SPEC,
)
from ansible.module_utils._text import to_native

try:
    from kubernetes.client.api import core_v1_api
    from kubernetes.dynamic.exceptions import ApiException
except ImportError:
    # ImportError are managed by the common module already.
    pass


def _equal_dicts(a, b):
    ignore_keys = ("time_added", "value")
    ka = set(a).difference(ignore_keys)
    kb = set(b).difference(ignore_keys)

    return all(a[k] == b[k] for k in ka if k in kb)


def _get_difference(a, b):
    return [
        a_item for a_item in a if not any(_equal_dicts(a_item, b_item) for b_item in b)
    ]


def _get_intersection(a, b):
    return [a_item for a_item in a if any(_equal_dicts(a_item, b_item) for b_item in b)]


def if_failed(function):
    def wrapper(self, *args):
        result = {}
        res = _get_difference(*args)
        if (
            not res
            and self.module.params.get("state") == "present"
            and not self.module.params.get("overwrite")
        ):
            result["result"] = "node/{0} already has ".format(
                self.module.params.get("name")
            ) + "{0} taint(s) with same effect(s) and overwrite is false".format(
                ", ".join(
                    map(
                        lambda t: "%s" % t["key"],
                        _get_intersection(*args),
                    )
                )
            )

            self.module.exit_json(changed=self.changed, **result)

        if res and self.module.params.get("state") == "absent":
            self.module.fail_json(
                msg="{0} not found".format(
                    ", ".join(map(lambda t: "%s" % t["key"], res))
                )
            )

        return function(self, *args)

    return wrapper


def if_check_mode(function):
    def wrapper(self, *args):
        result = {}
        if self.module.check_mode:
            self.changed = True
            result[
                "result"
            ] = "Would have tainted node/{0} if not in check mode".format(
                self.module.params.get("name")
            )
            self.module.exit_json(changed=self.changed, **result)
        return function(self, *args)

    return wrapper


def argspec():
    argument_spec = copy.deepcopy(AUTH_ARG_SPEC)
    argument_spec.update(
        dict(
            state=dict(type="str", choices=["present", "absent"], default="present"),
            name=dict(type="str", required=True),
            taints=dict(type="list", required=True, elements="dict"),
            overwrite=dict(type="bool", default=False),
        )
    )

    return argument_spec


class K8sTaintAnsible:
    def __init__(self, module):
        from ansible_collections.kubernetes.core.plugins.module_utils.common import (
            K8sAnsibleMixin,
            get_api_client,
        )

        self.module = module
        self.k8s_ansible_mixin = K8sAnsibleMixin(module=self.module)
        self.k8s_ansible_mixin.client = get_api_client(module=self.module)
        self.k8s_ansible_mixin.module = self.module
        self.k8s_ansible_mixin.argspec = self.module.argument_spec
        self.k8s_ansible_mixin.check_mode = self.module.check_mode
        self.k8s_ansible_mixin.params = self.module.params
        self.k8s_ansible_mixin.fail_json = self.module.fail_json
        self.k8s_ansible_mixin.fail = self.module.fail_json
        self.k8s_ansible_mixin.exit_json = self.module.exit_json
        self.k8s_ansible_mixin.warn = self.module.warn
        self.k8s_ansible_mixin.warnings = []

        self.api_instance = core_v1_api.CoreV1Api(self.k8s_ansible_mixin.client.client)
        self.k8s_ansible_mixin.check_library_version()
        self.changed = False

    def get_current_taints(self, name):
        try:
            node = self.api_instance.read_node(name=name)
        except ApiException as exc:
            if exc.reason == "Not Found":
                self.module.fail_json(msg="Node '{0}' has not been found.".format(name))
            self.module.fail_json(
                msg="Failed to retrieve node '{0}' due to: {1}".format(
                    name, exc.reason
                ),
                status=exc.status,
            )
        except Exception as exc:
            self.module.fail_json(
                msg="Failed to retrieve node '{0}' due to: {1}".format(
                    name, to_native(exc)
                )
            )

        return node.spec.to_dict()["taints"] or []

    def patch_node(self, taints):
        body = {"spec": {"taints": taints}}

        try:
            self.api_instance.patch_node(name=self.module.params.get("name"), body=body)
        except Exception as exc:
            self.module.fail_json(
                msg="Failed to patch node due to: {0}".format(to_native(exc))
            )

    @if_failed
    @if_check_mode
    def _taint(self, new_taints, current_taints):
        if not self.module.params.get("overwrite"):
            self.patch_node(taints=[*current_taints, *new_taints])
        else:
            self.patch_node(taints=new_taints)

    @if_failed
    @if_check_mode
    def _untaint(self, new_taints, current_taints):
        self.patch_node(taints=_get_difference(current_taints, new_taints))

    def execute_module(self):
        result = {}
        state = self.module.params.get("state")
        taints = self.module.params.get("taints")
        name = self.module.params.get("name")

        current_taints = self.get_current_taints(name)

        def _ensure_dict(a):
            for item_a in a:
                if not isinstance(item_a, dict):
                    a.remove(item_a)
                    a.append({"key": item_a})

        def _ensure_effect_defined(a):
            return all(
                elem.get("effect") in ("NoExecute", "NoSchedule", "PreferNoSchedule")
                for elem in a
            )

        if state == "present":
            if not _ensure_effect_defined:
                self.module.fail_json(
                    msg="An effect must be specified. Valid values: {0}".format(
                        t for t in ("NoExecute", "NoSchedule", "PreferNoSchedule")
                    )
                )
            self._taint(taints, current_taints)
            result["result"] = "node/{0} tainted".format(name)
            self.changed = True

        if state == "absent":
            _ensure_dict(taints)
            self._untaint(taints, current_taints)
            result["result"] = "node/{0} untainted".format(name)
            self.changed = True

        self.module.exit_json(changed=self.changed, **result)


def main():
    module = AnsibleModule(
        argument_spec=argspec(),
        supports_check_mode=True,
    )
    k8s_taint = K8sTaintAnsible(module)
    k8s_taint.execute_module()


if __name__ == "__main__":
    main()
