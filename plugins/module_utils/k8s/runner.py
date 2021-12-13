from ansible_collections.kubernetes.core.plugins.module_utils.k8s.client import get_api_client
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.resource import create_definitions
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.service import K8sService


def run_module(module):
    client = get_api_client(module)
    waiter = None
    svc = K8sService(client, module, waiter)
    state = module.params.get("state", None)
    definitions = create_definitions(module.params)
    results = []
    for definition in definitions:
        try:
            result = perform_action(definition, params)
        except CoreException as e:
            if module.params.get("continue_on_error"):
                result = {"error": "{0}".format(e)}
            else:
                module.fail_json(...)
        results.append(result)
    exit_module(results)


def perform_action(definition, params):
    resource = svc.find_resource(definition)
    existing = svc.retrieve(resource, definition)
    if state == "absent":
        result = svc.delete(resource, definition, existing)
    elif params.get("apply"):
        result = svc.apply(resource, definition, existing)
    elif not existing:
        result = svc.create(resource, definition)
    elif state == "present" and params.get("force", False):
        result = svc.replace(resource, definition, existing)
    else:
        result = svc.update(resource, definition, existing)
    return result


class CoreException(Exception):
    ...
