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
    changed = False
    client = get_api_client(module)
    svc = K8sService(client, module)
    definitions = create_definitions(module.params)

    for definition in definitions:
        result = {"changed": False, "result": {}, "warnings": []}
        warnings = []

        if module.params.get("validate") is not None:
            warnings = validate(client, module, definition)

        try:
            result = perform_action(svc, definition, module.params)
        except CoreException as e:
            msg = to_native(e)
            if warnings:
                msg += "\n" + "\n    ".join(warnings)
            if module.params.get("continue_on_error"):
                result["error"] = {"msg": msg}
            else:
                module.fail_json(msg=msg)

        if warnings:
            result.setdefault("warnings", [])
            result["warnings"] += warnings

        changed |= result["changed"]
        results.append(result)

    if len(results) == 1:
        module.exit_json(**results[0])

    module.exit_json(**{"changed": changed, "result": {"results": results}})


def perform_action(svc, definition: Dict, params: Dict) -> Dict:
    origin_name = definition["metadata"].get("name")
    namespace = definition["metadata"].get("namespace")
    label_selectors = params.get("label_selectors")
    state = params.get("state", None)
    kind = definition.get("kind")
    api_version = definition.get("apiVersion")
    result = {"changed": False, "result": {}}

    resource = svc.find_resource(kind, api_version, fail=True)
    definition["kind"] = resource.kind
    definition["apiVersion"] = resource.group_version
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
            if state == "patched":
                result.setdefault("warnings", []).append(
                    "resource 'kind={kind},name={name}' was not found but will not be "
                    "created as 'state' parameter has been set to '{state}'".format(
                        kind=kind, name=definition["metadata"].get("name"), state=state
                    )
                )
                return result
            result = svc.create(resource, definition)
            result["method"] = "create"
        elif params.get("force", False):
            result = svc.replace(resource, definition, existing)
            result["method"] = "replace"
        else:
            result = svc.update(resource, definition, existing)
            result["method"] = "update"

    return result
