# Copyright: (c) 2021, Red Hat | Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from typing import Any, Dict, Optional, Tuple

from ansible_collections.kubernetes.core.plugins.module_utils.hashes import (
    generate_hash,
)
from ansible_collections.kubernetes.core.plugins.module_utils.selector import (
    LabelSelectorFilter,
)
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.waiter import (
    get_waiter,
)

from ansible.module_utils._text import to_native, to_bytes, to_text
from ansible.module_utils.common.dict_transformations import dict_merge

try:
    from kubernetes.dynamic.exceptions import (
        NotFoundError,
        ResourceNotFoundError,
        ResourceNotUniqueError,
        DynamicApiError,
        ConflictError,
        ForbiddenError,
        MethodNotAllowedError,
    )
    from kubernetes.dynamic.resource import Resource, ResourceInstance
except ImportError:
    # Handled in module setup
    pass

try:
    from ansible_collections.kubernetes.core.plugins.module_utils.apply import (
        apply_object,
    )
except ImportError:
    # Handled in module setup
    pass

try:
    from ansible_collections.kubernetes.core.plugins.module_utils.apply import (
        recursive_diff,
    )
except ImportError:
    from ansible.module_utils.common.dict_transformations import recursive_diff


try:
    from ansible_collections.kubernetes.core.plugins.module_utils.common import (
        _encode_stringdata,
    )
except ImportError:
    # Handled in module setup
    pass


def build_error_msg(kind: str, name: str, msg: str) -> str:
    return "%s %s: %s" % (kind, name, msg)


class K8sService:
    """A Service class for K8S modules.
    This class has the primary purpose is to perform work on the cluster (e.g., create, apply, replace, update, delete).
    """

    def __init__(self, client, module) -> None:
        self.client = client
        self.module = module
        self.warnings = []

    def find_resource(
        self, kind: str, api_version: str, fail: bool = False
    ) -> Optional[Any]:
        for attribute in ["kind", "name", "singular_name"]:
            try:
                return self.client.resources.get(
                    **{"api_version": api_version, attribute: kind}
                )
            except (ResourceNotFoundError, ResourceNotUniqueError):
                pass
        try:
            return self.client.resources.get(
                api_version=api_version, short_names=[kind]
            )
        except (ResourceNotFoundError, ResourceNotUniqueError):
            if fail:
                self.module.fail_json(
                    msg="Failed to find exact match for {0}.{1} by [kind, name, singularName, shortNames]".format(
                        api_version, kind
                    )
                )

    def create_project_request(self, definition: Dict) -> Dict:
        definition["kind"] = "ProjectRequest"
        results = {"changed": False, "result": {}}
        resource = self.find_resource(
            "ProjectRequest", definition["apiVersion"], fail=True
        )
        if not self.module.check_mode:
            try:
                k8s_obj = self.client.create(resource, definition)
                results["result"] = k8s_obj.to_dict()
            except DynamicApiError as exc:
                self.module.fail_json(
                    msg="Failed to create object: {0}".format(exc.body),
                    error=exc.status,
                    status=exc.status,
                    reason=exc.reason,
                )
        results["changed"] = True

        return results

    def diff_objects(self, existing: Dict, new: Dict) -> Tuple[bool, Dict]:
        result = dict()
        diff = recursive_diff(existing, new)
        if not diff:
            return True, result

        result["before"] = diff[0]
        result["after"] = diff[1]

        # If only metadata.generation and metadata.resourceVersion changed, ignore it
        ignored_keys = set(["generation", "resourceVersion"])

        if list(result["after"].keys()) != ["metadata"] or list(
            result["before"].keys()
        ) != ["metadata"]:
            return False, result

        if not set(result["after"]["metadata"].keys()).issubset(ignored_keys):
            return False, result
        if not set(result["before"]["metadata"].keys()).issubset(ignored_keys):
            return False, result

        if hasattr(self.module, "warn"):
            self.module.warn(
                "No meaningful diff was generated, but the API may not be idempotent (only metadata.generation or metadata.resourceVersion were changed)"
            )

        return True, result

    def patch_resource(
        self,
        resource: Resource,
        definition: Dict,
        name: str,
        namespace: str,
        merge_type: str = None,
    ) -> Tuple[bool, Dict]:
        if merge_type == "json":
            self.module.deprecate(
                msg="json as a merge_type value is deprecated. Please use the k8s_json_patch module instead.",
                version="3.0.0",
                collection_name="kubernetes.core",
            )
        try:
            params = dict(name=name, namespace=namespace)
            if self.module.check_mode:
                params["dry_run"] = "All"
            if merge_type:
                params["content_type"] = "application/{0}-patch+json".format(merge_type)
            k8s_obj = self.client.patch(resource, definition, **params).to_dict()
            error = {}
            return k8s_obj, {}
        except DynamicApiError as exc:
            msg = "Failed to patch object: {0}".format(exc.body)
            if self.warnings:
                msg += "\n" + "\n    ".join(self.warnings)
            error = dict(
                msg=msg,
                error=exc.status,
                status=exc.status,
                reason=exc.reason,
                warnings=self.warnings,
            )
            return None, error
        except Exception as exc:
            msg = "Failed to patch object: {0}".format(exc)
            if self.warnings:
                msg += "\n" + "\n    ".join(self.warnings)
            error = dict(
                msg=msg,
                error=to_native(exc),
                status="",
                reason="",
                warnings=self.warnings,
            )
            return None, error

    def retrieve(self, resource: Resource, definition: Dict) -> Dict:
        state = self.module.params.get("state", None)
        origin_name = definition["metadata"].get("name")
        append_hash = self.module.params.get("append_hash", False)
        name = definition["metadata"].get("name")
        namespace = definition["metadata"].get("namespace")
        label_selectors = self.module.params.get("label_selectors")
        results = {
            "changed": False,
            "result": {},
        }
        existing = None

        try:
            # ignore append_hash for resources other than ConfigMap and Secret
            if append_hash and definition["kind"] in ["ConfigMap", "Secret"]:
                name = "%s-%s" % (name, generate_hash(definition))
                definition["metadata"]["name"] = name
            params = dict(name=name)
            if namespace:
                params["namespace"] = namespace
            if label_selectors:
                params["label_selector"] = ",".join(label_selectors)
            existing = self.client.get(resource, **params)
        except (NotFoundError, MethodNotAllowedError):
            pass
        except ForbiddenError as exc:
            if (
                definition["kind"] in ["Project", "ProjectRequest"]
                and state != "absent"
            ):
                return self.create_project_request(definition)
            msg = "Failed to retrieve requested object: {0}".format(exc.body)
            results["error"] = dict(
                msg=build_error_msg(definition["kind"], origin_name, msg),
                error=exc.status,
                status=exc.status,
                reason=exc.reason,
            )
            return results
        except DynamicApiError as exc:
            msg = "Failed to retrieve requested object: {0}".format(exc.body)
            results["error"] = dict(
                msg=build_error_msg(definition["kind"], origin_name, msg),
                error=exc.status,
                status=exc.status,
                reason=exc.reason,
            )
            return results
        except ValueError as value_exc:
            msg = "Failed to retrieve requested object: {0}".format(
                to_native(value_exc)
            )
            results["error"] = dict(
                msg=build_error_msg(definition["kind"], origin_name, msg),
                error="",
                status="",
                reason="",
            )
            return results

        if existing:
            results["result"] = existing.to_dict()

        return results

    def create(self, resource: Resource, definition: Dict) -> Dict:
        origin_name = definition["metadata"].get("name")
        namespace = definition["metadata"].get("namespace")
        name = definition["metadata"].get("name")
        wait = self.module.params.get("wait")
        wait_sleep = self.module.params.get("wait_sleep")
        wait_timeout = self.module.params.get("wait_timeout")
        wait_condition = None
        if self.params.get("wait_condition") and self.params["wait_condition"].get(
            "type"
        ):
            wait_condition = self.params["wait_condition"]
        results = {"changed": False, "result": {}}

        if self.module.check_mode and not self.client.dry_run:
            k8s_obj = _encode_stringdata(definition)
        else:
            params = {}
            if self.module.check_mode:
                params["dry_run"] = "All"
            try:
                k8s_obj = self.client.create(
                    resource, definition, namespace=namespace, **params
                ).to_dict()
            except ConflictError:
                # Some resources, like ProjectRequests, can't be created multiple times,
                # because the resources that they create don't match their kind
                # In this case we'll mark it as unchanged and warn the user
                self.module.warn(
                    "{0} was not found, but creating it returned a 409 Conflict error. This can happen \
                            if the resource you are creating does not directly create a resource of the same kind.".format(
                        name
                    )
                )
                return results
            except DynamicApiError as exc:
                msg = "Failed to create object: {0}".format(exc.body)
                if self.warnings:
                    msg += "\n" + "\n    ".join(self.warnings)
                results["error"] = dict(
                    msg=build_error_msg(definition["kind"], origin_name, msg),
                    error=exc.status,
                    status=exc.status,
                    reason=exc.reason,
                )
                return results
            except Exception as exc:
                msg = "Failed to create object: {0}".format(exc)
                if self.warnings:
                    msg += "\n" + "\n    ".join(self.warnings)
                results["error"] = dict(
                    msg=build_error_msg(definition["kind"], origin_name, msg),
                    error="",
                    status="",
                    reason="",
                )
                return results

        success = True
        results["result"] = k8s_obj

        if wait and not self.module.check_mode:
            definition["metadata"].update({"name": k8s_obj["metadata"]["name"]})
            waiter = get_waiter(self.client, resource, condition=wait_condition)
            success, results["result"], results["duration"] = waiter.wait(
                definition, wait_timeout, wait_sleep,
            )

        results["changed"] = True

        if not success:
            msg = "Resource creation timed out"
            results["error"] = dict(
                msg=build_error_msg(definition["kind"], origin_name, msg), **results
            )
            return results

        return results

    def apply(
        self,
        resource: Resource,
        definition: Dict,
        existing: Optional[ResourceInstance] = None,
    ) -> Dict:
        apply = self.module.params.get("apply", False)
        label_selectors = self.module.params.get("label_selectors")
        origin_name = definition["metadata"].get("name")
        namespace = definition["metadata"].get("namespace")
        wait = self.module.params.get("wait")
        wait_sleep = self.module.params.get("wait_sleep")
        wait_condition = None
        if self.params.get("wait_condition") and self.params["wait_condition"].get(
            "type"
        ):
            wait_condition = self.params["wait_condition"]
        wait_timeout = self.module.params.get("wait_timeout")
        results = {"changed": False, "result": {}}

        if label_selectors:
            filter_selector = LabelSelectorFilter(label_selectors)
            if not filter_selector.isMatching(definition):
                results["changed"] = False
                results["msg"] = (
                    "resource 'kind={kind},name={name},namespace={namespace}' "
                    "filtered by label_selectors.".format(
                        kind=definition["kind"], name=origin_name, namespace=namespace,
                    )
                )
                return results
        if apply:
            if self.module.check_mode and not self.client.dry_run:
                ignored, patch = apply_object(resource, _encode_stringdata(definition))
                if existing:
                    k8s_obj = dict_merge(existing.to_dict(), patch)
                else:
                    k8s_obj = patch
            else:
                try:
                    params = {}
                    if self.module.check_mode:
                        params["dry_run"] = "All"
                    k8s_obj = self.client.apply(
                        resource, definition, namespace=namespace, **params
                    ).to_dict()
                except DynamicApiError as exc:
                    msg = "Failed to apply object: {0}".format(exc.body)
                    if self.warnings:
                        msg += "\n" + "\n    ".join(self.warnings)
                    results["error"] = dict(
                        msg=build_error_msg(definition["kind"], origin_name, msg),
                        error=exc.status,
                        status=exc.status,
                        reason=exc.reason,
                    )
                    return results

            success = True
            results["result"] = k8s_obj

            if wait and not self.module.check_mode:
                waiter = get_waiter(self.client, resource, condition=wait_condition)
                success, results["result"], results["duration"] = waiter.wait(
                    definition, wait_timeout, wait_sleep,
                )

            if existing:
                existing = existing.to_dict()
            else:
                existing = {}

            match, diffs = self.diff_objects(existing, results["result"])
            results["changed"] = not match

            if self.module._diff:
                results["diff"] = diffs

            if not success:
                msg = "Resource apply timed out"
                results["error"] = dict(
                    msg=build_error_msg(definition["kind"], origin_name, msg), **results
                )
                return results

        return results

    def replace(
        self, resource: Resource, definition: Dict, existing: ResourceInstance,
    ) -> Dict:
        append_hash = self.module.params.get("append_hash", False)
        name = definition["metadata"].get("name")
        origin_name = definition["metadata"].get("name")
        namespace = definition["metadata"].get("namespace")
        wait = self.module.params.get("wait")
        wait_sleep = self.module.params.get("wait_sleep")
        wait_timeout = self.module.params.get("wait_timeout")
        wait_condition = None
        if self.params.get("wait_condition") and self.params["wait_condition"].get(
            "type"
        ):
            wait_condition = self.params["wait_condition"]
        results = {"changed": False, "result": {}}
        match = False
        diffs = []

        if self.module.check_mode and not self.module.client.dry_run:
            k8s_obj = _encode_stringdata(definition)
        else:
            params = {}
            if self.module.check_mode:
                params["dry_run"] = "All"
            try:
                k8s_obj = self.client.replace(
                    resource,
                    definition,
                    name=name,
                    namespace=namespace,
                    append_hash=append_hash,
                    **params
                ).to_dict()
            except DynamicApiError as exc:
                msg = "Failed to replace object: {0}".format(exc.body)
                if self.warnings:
                    msg += "\n" + "\n    ".join(self.warnings)
                results["error"] = dict(
                    msg=build_error_msg(definition["kind"], origin_name, msg),
                    error=exc.status,
                    status=exc.status,
                    reason=exc.reason,
                )
                return results

        match, diffs = self.diff_objects(existing.to_dict(), k8s_obj)
        success = True
        results["result"] = k8s_obj

        if wait and not self.module.check_mode:
            waiter = get_waiter(self.client, resource, condition=wait_condition)
            success, results["result"], results["duration"] = waiter.wait(
                definition, wait_timeout, wait_sleep
            )
        match, diffs = self.diff_objects(existing.to_dict(), results["result"])
        results["changed"] = not match

        if self.module._diff:
            results["diff"] = diffs

        if not success:
            msg = "Resource replacement timed out"
            results["error"] = dict(
                msg=build_error_msg(definition["kind"], origin_name, msg), **results
            )
            return results

        return results

    def update(
        self, resource: Resource, definition: Dict, existing: ResourceInstance
    ) -> Dict:
        name = definition["metadata"].get("name")
        origin_name = definition["metadata"].get("name")
        namespace = definition["metadata"].get("namespace")
        wait = self.module.params.get("wait")
        wait_sleep = self.module.params.get("wait_sleep")
        wait_timeout = self.module.params.get("wait_timeout")
        wait_condition = None
        if self.params.get("wait_condition") and self.params["wait_condition"].get(
            "type"
        ):
            wait_condition = self.params["wait_condition"]
        results = {"changed": False, "result": {}}
        match = False
        diffs = []

        if self.module.check_mode and not self.module.client.dry_run:
            k8s_obj = dict_merge(existing.to_dict(), _encode_stringdata(definition))
        else:
            for merge_type in self.module.params.get("merge_type") or [
                "strategic-merge",
                "merge",
            ]:
                k8s_obj, error = self.patch_resource(
                    resource,
                    definition,
                    existing,
                    name,
                    namespace,
                    merge_type=merge_type,
                )
                if not error:
                    break
            if error:
                results["error"] = error
                results["error"]["msg"] = build_error_msg(
                    definition["kind"], origin_name, results["error"].get("msg")
                )
                return results

        success = True
        results["result"] = k8s_obj

        if wait and not self.module.check_mode:
            waiter = get_waiter(self.client, resource, condition=wait_condition)
            success, results["result"], results["duration"] = waiter.wait(
                definition, wait_timeout, wait_sleep,
            )

        match, diffs = self.diff_objects(existing.to_dict(), results["result"])
        results["changed"] = not match

        if self.module._diff:
            results["diff"] = diffs

        if not success:
            msg = "Resource update timed out"
            results["error"] = dict(
                msg=build_error_msg(definition["kind"], origin_name, msg), **results
            )
            return results

        return results

    def delete(
        self,
        resource: Resource,
        definition: Dict,
        existing: Optional[ResourceInstance] = None,
    ) -> Dict:
        delete_options = self.module.params.get("delete_options")
        label_selectors = self.module.params.get("label_selectors")
        origin_name = definition["metadata"].get("name")
        wait = self.module.params.get("wait")
        wait_sleep = self.module.params.get("wait_sleep")
        wait_timeout = self.module.params.get("wait_timeout")
        wait_condition = None
        if self.params.get("wait_condition") and self.params["wait_condition"].get(
            "type"
        ):
            wait_condition = self.params["wait_condition"]
        results = {"changed": False, "result": {}}
        params = {}

        def _empty_resource_list() -> bool:
            if existing and existing.kind.endswith("List"):
                return existing.items == []
            return False

        if not existing or _empty_resource_list():
            # The object already does not exist
            return results
        else:
            # Delete the object
            results["changed"] = True
            if self.module.check_mode and not self.client.dry_run:
                return results
            else:
                if delete_options:
                    body = {
                        "apiVersion": "v1",
                        "kind": "DeleteOptions",
                    }
                    body.update(delete_options)
                    params["body"] = body

                if self.module.check_mode:
                    params["dry_run"] = "All"
                try:
                    k8s_obj = self.client.delete(resource, **params)
                    results["result"] = k8s_obj.to_dict()
                except DynamicApiError as exc:
                    msg = "Failed to delete object: {0}".format(exc.body)
                    results["error"] = dict(
                        msg=build_error_msg(definition["kind"], origin_name, msg),
                        error=exc.status,
                        status=exc.status,
                        reason=exc.reason,
                    )
                    return results

                if wait and not self.module.check_mode:
                    waiter = get_waiter(self.client, resource, state="absent")
                    success, resource, duration = waiter.wait(
                        definition,
                        wait_timeout,
                        wait_sleep,
                        label_selectors=label_selectors,
                    )
                    results["duration"] = duration
                    if not success:
                        msg = "Resource deletion timed out"
                        results["error"] = dict(
                            msg=build_error_msg(definition["kind"], origin_name, msg),
                            **results
                        )
                        return results

                return results
