# Copyright: (c) 2021, Red Hat | Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from typing import Dict

from ansible.module_utils._text import to_native

from ansible_collections.kubernetes.core.plugins.module_utils.k8s.client import (
    get_api_client,
)
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.resource import (
    create_definitions,
)
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.service import (
    K8sService,
)
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.exceptions import (
    CoreException,
)
from ansible_collections.kubernetes.core.plugins.module_utils.selector import (
    LabelSelectorFilter,
)


def validate(client, module, resource):
    def _prepend_resource_info(resource, msg):
        return "%s %s: %s" % (resource["kind"], resource["metadata"]["name"], msg)

    module.requires("kubernetes-validate")

    warnings, errors = client.validate(
        resource,
        module.params["validate"].get("version"),
        module.params["validate"].get("strict"),
    )

    if errors and module.params["validate"]["fail_on_error"]:
        module.fail_json(
            msg="\n".join([_prepend_resource_info(resource, error) for error in errors])
        )
    return [_prepend_resource_info(resource, msg) for msg in warnings + errors]


def run_module(module) -> None:
    results = []

    client = get_api_client(module)
    svc = K8sService(client, module)
    definitions = create_definitions(module.params)

    for definition in definitions:
        module.warnings = []

        if module.params["validate"] is not None:
            module.warnings = validate(client, module, definition)

        try:
            result = perform_action(svc, definition, module.params)
        except CoreException as e:
            if module.warnings:
                e["msg"] += "\n" + "\n    ".join(module.warnings)
            if module.params.get("continue_on_error"):
                result = {"error": "{0}".format(e)}
            else:
                module.fail_json(msg=to_native(e))

        if module.warnings:
            result["warnings"] = module.warnings

        results.append(result)

    if len(results) == 1:
        module.exit_json(**results[0])

    module.exit_json(result=results)


def perform_action(svc, definition: Dict, params: Dict) -> Dict:
    origin_name = definition["metadata"].get("name")
    namespace = definition["metadata"].get("namespace")
    label_selectors = params.get("label_selectors")
    state = params.get("state", None)
    kind = definition.get("kind")
    api_version = definition.get("apiVersion")
    result = {}

    resource = svc.find_resource(kind, api_version, fail=True)
    existing = svc.retrieve(resource, definition)

    if state == "absent":
        result = svc.delete(resource, definition, existing)
        result["method"] = "delete"
    else:
        if label_selectors:
            filter_selector = LabelSelectorFilter(label_selectors)
            if not filter_selector.isMatching(definition):
                result["changed"] = False
                result["msg"] = (
                    "resource 'kind={kind},name={name},namespace={namespace}' "
                    "filtered by label_selectors.".format(
                        kind=kind, name=origin_name, namespace=namespace,
                    )
                )
                return result

        if params.get("apply"):
            result = svc.apply(resource, definition, existing)
            result["method"] = "apply"
        elif not existing:
            result = svc.create(resource, definition)
            result["method"] = "create"
        elif params.get("force", False):
            result = svc.replace(resource, definition, existing)
            result["method"] = "replace"
        else:
            result = svc.update(resource, definition, existing)
            result["method"] = "update"

    return result
