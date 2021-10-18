#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, Fabian von Feilitzsch <@fabianvf>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
module: k8s_log

short_description: Fetch logs from Kubernetes resources

version_added: "0.10.0"

author:
    - "Fabian von Feilitzsch (@fabianvf)"

description:
  - Use the Kubernetes Python client to perform read operations on K8s log endpoints.
  - Authenticate using either a config file, certificates, password or token.
  - Supports check mode.
  - Analogous to `kubectl logs` or `oc logs`
extends_documentation_fragment:
  - kubernetes.core.k8s_auth_options
  - kubernetes.core.k8s_name_options
options:
  kind:
    description:
    - Use to specify an object model.
    - Use in conjunction with I(api_version), I(name), and I(namespace) to identify a specific object.
    - If using I(label_selectors), cannot be overridden.
    type: str
    default: Pod
  name:
    description:
    - Use to specify an object name.
    - Use in conjunction with I(api_version), I(kind) and I(namespace) to identify a specific object.
    - Only one of I(name) or I(label_selectors) may be provided.
    type: str
  label_selectors:
    description:
    - List of label selectors to use to filter results
    - Only one of I(name) or I(label_selectors) may be provided.
    type: list
    elements: str
  container:
    description:
    - Use to specify the container within a pod to grab the log from.
    - If there is only one container, this will default to that container.
    - If there is more than one container, this option is required.
    required: no
    type: str
  since_seconds:
    description:
    - A relative time in seconds before the current time from which to show logs.
    required: no
    type: str
    version_added: '2.2.0'

requirements:
  - "python >= 3.6"
  - "kubernetes >= 12.0.0"
  - "PyYAML >= 3.11"
"""

EXAMPLES = r"""
- name: Get a log from a Pod
  kubernetes.core.k8s_log:
    name: example-1
    namespace: testing
  register: log

# This will get the log from the first Pod found matching the selector
- name: Log a Pod matching a label selector
  kubernetes.core.k8s_log:
    namespace: testing
    label_selectors:
    - app=example
  register: log

# This will get the log from a single Pod managed by this Deployment
- name: Get a log from a Deployment
  kubernetes.core.k8s_log:
    api_version: apps/v1
    kind: Deployment
    namespace: testing
    name: example
    since_seconds: "4000"
  register: log

# This will get the log from a single Pod managed by this DeploymentConfig
- name: Get a log from a DeploymentConfig
  kubernetes.core.k8s_log:
    api_version: apps.openshift.io/v1
    kind: DeploymentConfig
    namespace: testing
    name: example
  register: log
"""

RETURN = r"""
log:
  type: str
  description:
  - The text log of the object
  returned: success
log_lines:
  type: list
  description:
  - The log of the object, split on newlines
  returned: success
"""


import copy

from ansible_collections.kubernetes.core.plugins.module_utils.ansiblemodule import (
    AnsibleModule,
)
from ansible.module_utils.six import PY2

from ansible_collections.kubernetes.core.plugins.module_utils.args_common import (
    AUTH_ARG_SPEC,
    NAME_ARG_SPEC,
)


def argspec():
    args = copy.deepcopy(AUTH_ARG_SPEC)
    args.update(NAME_ARG_SPEC)
    args.update(
        dict(
            kind=dict(type="str", default="Pod"),
            container=dict(),
            since_seconds=dict(),
            label_selectors=dict(type="list", elements="str", default=[]),
        )
    )
    return args


def execute_module(module, k8s_ansible_mixin):
    name = module.params.get("name")
    namespace = module.params.get("namespace")
    label_selector = ",".join(module.params.get("label_selectors", {}))
    if name and label_selector:
        module.fail(msg="Only one of name or label_selectors can be provided")

    resource = k8s_ansible_mixin.find_resource(
        module.params["kind"], module.params["api_version"], fail=True
    )
    v1_pods = k8s_ansible_mixin.find_resource("Pod", "v1", fail=True)

    if "log" not in resource.subresources:
        if not name:
            module.fail(
                msg="name must be provided for resources that do not support the log subresource"
            )
        instance = resource.get(name=name, namespace=namespace)
        label_selector = ",".join(extract_selectors(module, instance))
        resource = v1_pods

    if label_selector:
        instances = v1_pods.get(namespace=namespace, label_selector=label_selector)
        if not instances.items:
            module.fail(
                msg="No pods in namespace {0} matched selector {1}".format(
                    namespace, label_selector
                )
            )
        # This matches the behavior of kubectl when logging pods via a selector
        name = instances.items[0].metadata.name
        resource = v1_pods

    kwargs = {}
    if module.params.get("container"):
        kwargs["query_params"] = dict(container=module.params["container"])

    if module.params.get("since_seconds"):
        kwargs.setdefault("query_params", {}).update(
            {"sinceSeconds": module.params["since_seconds"]}
        )

    log = serialize_log(
        resource.log.get(name=name, namespace=namespace, serialize=False, **kwargs)
    )

    module.exit_json(changed=False, log=log, log_lines=log.split("\n"))


def extract_selectors(module, instance):
    # Parses selectors on an object based on the specifications documented here:
    # https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/#label-selectors
    selectors = []
    if not instance.spec.selector:
        module.fail(
            msg="{0} {1} does not support the log subresource directly, and no Pod selector was found on the object".format(
                "/".join(instance.group, instance.apiVersion), instance.kind
            )
        )

    if not (
        instance.spec.selector.matchLabels or instance.spec.selector.matchExpressions
    ):
        # A few resources (like DeploymentConfigs) just use a simple key:value style instead of supporting expressions
        for k, v in dict(instance.spec.selector).items():
            selectors.append("{0}={1}".format(k, v))
        return selectors

    if instance.spec.selector.matchLabels:
        for k, v in dict(instance.spec.selector.matchLabels).items():
            selectors.append("{0}={1}".format(k, v))

    if instance.spec.selector.matchExpressions:
        for expression in instance.spec.selector.matchExpressions:
            operator = expression.operator

            if operator == "Exists":
                selectors.append(expression.key)
            elif operator == "DoesNotExist":
                selectors.append("!{0}".format(expression.key))
            elif operator in ["In", "NotIn"]:
                selectors.append(
                    "{key} {operator} {values}".format(
                        key=expression.key,
                        operator=operator.lower(),
                        values="({0})".format(", ".join(expression.values)),
                    )
                )
            else:
                module.fail(
                    msg="The k8s_log module does not support the {0} matchExpression operator".format(
                        operator.lower()
                    )
                )

    return selectors


def serialize_log(response):
    if PY2:
        return response.data
    return response.data.decode("utf8")


def main():
    module = AnsibleModule(argument_spec=argspec(), supports_check_mode=True)
    from ansible_collections.kubernetes.core.plugins.module_utils.common import (
        K8sAnsibleMixin,
        get_api_client,
    )

    k8s_ansible_mixin = K8sAnsibleMixin(module)
    k8s_ansible_mixin.client = get_api_client(module=module)
    execute_module(module, k8s_ansible_mixin)


if __name__ == "__main__":
    main()
