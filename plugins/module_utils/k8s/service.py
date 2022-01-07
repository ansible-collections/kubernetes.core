# Copyright: (c) 2021, Red Hat | Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ansible_collections.kubernetes.core.plugins.module_utils.hashes import (
    generate_hash,
)
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.waiter import (
    get_waiter,
)

from ansible_collections.kubernetes.core.plugins.module_utils.k8s.exceptions import (
    CoreException,
    ResourceTimeout,
)

from ansible.module_utils.common.dict_transformations import dict_merge

try:
    from kubernetes.dynamic.exceptions import (
        NotFoundError,
        ResourceNotFoundError,
        ResourceNotUniqueError,
        ConflictError,
        ForbiddenError,
        MethodNotAllowedError,
        BadRequestError,
    )
except ImportError:
    # Handled in module setup
    pass

try:
    from kubernetes.dynamic.resource import Resource, ResourceInstance
except ImportError:
    # These are defined only for the sake of Ansible's checked import requirement
    Resource = Any  # type: ignore
    ResourceInstance = Any  # type: ignore

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


class K8sService:
    """A Service class for K8S modules.
    This class has the primary purpose is to perform work on the cluster (e.g., create, apply, replace, update, delete).
    """

    def __init__(self, client, module) -> None:
        self.client = client
        self.module = module

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
                self.module.fail(
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
            except Exception as e:
                reason = e.body if hasattr(e, "body") else e
                msg = "Failed to create object: {0}".format(reason)
                raise CoreException(msg) from e

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
            return k8s_obj, {}
        except Exception as e:
            reason = e.body if hasattr(e, "body") else e
            msg = "Failed to patch object: {0}".format(reason)
            raise CoreException(msg) from e

    def retrieve(self, resource: Resource, definition: Dict) -> Dict:
        state = self.module.params.get("state", None)
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
        except ForbiddenError as e:
            if (
                definition["kind"] in ["Project", "ProjectRequest"]
                and state != "absent"
            ):
                return self.create_project_request(definition)
            reason = e.body if hasattr(e, "body") else e
            msg = "Failed to retrieve requested object: {0}".format(reason)
            raise CoreException(msg) from e
        except Exception as e:
            reason = e.body if hasattr(e, "body") else e
            msg = "Failed to retrieve requested object: {0}".format(reason)
            raise CoreException(msg) from e

        if existing:
            results["result"] = existing.to_dict()

        return results

    def find(
        self,
        kind: str,
        api_version: str,
        name: str = None,
        namespace: Optional[str] = None,
        label_selectors: Optional[List[str]] = None,
        field_selectors: Optional[List[str]] = None,
        wait: Optional[bool] = False,
        wait_sleep: Optional[int] = 5,
        wait_timeout: Optional[int] = 120,
        state: Optional[str] = "present",
        condition: Optional[Dict] = None,
    ) -> Dict:
        resource = self.find_resource(kind, api_version)
        api_found = bool(resource)
        if not api_found:
            return dict(
                resources=[],
                msg='Failed to find API for resource with apiVersion "{0}" and kind "{1}"'.format(
                    api_version, kind
                ),
                api_found=False,
            )

        if not label_selectors:
            label_selectors = []
        if not field_selectors:
            field_selectors = []

        result = None

        try:
            result = self.client.get(
                resource,
                **dict(
                    name=name,
                    namespace=namespace,
                    label_selector=",".join(label_selectors),
                    field_selector=",".join(field_selectors),
                )
            )
        except BadRequestError:
            return dict(resources=[], api_found=True)
        except NotFoundError:
            if not wait or name is None:
                return dict(resources=[], api_found=True)

        if not wait:
            result = result.to_dict()
            if "items" in result:
                return dict(resources=result["items"], api_found=True)
            return dict(resources=[result], api_found=True)

        start = datetime.now()

        def _elapsed():
            return (datetime.now() - start).seconds

        if result is None:
            while _elapsed() < wait_timeout:
                try:
                    result = self.client.get(
                        resource,
                        **dict(
                            name=name,
                            namespace=namespace,
                            label_selector=",".join(label_selectors),
                            field_selector=",".join(field_selectors),
                        )
                    )
                    break
                except NotFoundError:
                    pass
                time.sleep(wait_sleep)
            if result is None:
                return dict(resources=[], api_found=True)

        if isinstance(result, ResourceInstance):
            satisfied_by = []
            # We have a list of ResourceInstance
            resource_list = result.get("items", [])
            if not resource_list:
                resource_list = [result]

            for resource_instance in resource_list:
                waiter = get_waiter(
                    self.client, resource_instance, state=state, condition=condition
                )
                success, res, duration = waiter.wait(
                    resource_instance, wait_timeout, wait_sleep
                )
                if not success:
                    raise CoreException(
                        "Failed to gather information about %s(s) even"
                        " after waiting for %s seconds" % (res.get("kind"), duration)
                    )
                satisfied_by.append(res)
            return dict(resources=satisfied_by, api_found=True)
        result = result.to_dict()

        if "items" in result:
            return dict(resources=result["items"], api_found=True)
        return dict(resources=[result], api_found=True)

    def create(self, resource: Resource, definition: Dict) -> Dict:
        origin_name = definition["metadata"].get("name")
        namespace = definition["metadata"].get("namespace")
        name = definition["metadata"].get("name")
        wait = self.module.params.get("wait")
        wait_sleep = self.module.params.get("wait_sleep")
        wait_timeout = self.module.params.get("wait_timeout")
        wait_condition = None
        if self.module.params.get("wait_condition") and self.module.params[
            "wait_condition"
        ].get("type"):
            wait_condition = self.module.params["wait_condition"]
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
            except Exception as e:
                reason = e.body if hasattr(e, "body") else e
                msg = "Failed to create object: {0}".format(reason)
                raise CoreException(msg) from e

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
            raise ResourceTimeout(
                '"{0}" "{1}": Resource creation timed out'.format(
                    definition["kind"], origin_name
                ),
                **results
            )

        return results

    def apply(
        self,
        resource: Resource,
        definition: Dict,
        existing: Optional[ResourceInstance] = None,
    ) -> Dict:
        apply = self.module.params.get("apply", False)
        origin_name = definition["metadata"].get("name")
        namespace = definition["metadata"].get("namespace")
        wait = self.module.params.get("wait")
        wait_sleep = self.module.params.get("wait_sleep")
        wait_condition = None
        if self.module.params.get("wait_condition") and self.module.params[
            "wait_condition"
        ].get("type"):
            wait_condition = self.module.params["wait_condition"]
        wait_timeout = self.module.params.get("wait_timeout")
        results = {"changed": False, "result": {}}

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
                except Exception as e:
                    reason = e.body if hasattr(e, "body") else e
                    msg = "Failed to apply object: {0}".format(reason)
                    raise CoreException(msg) from e

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
                raise ResourceTimeout(
                    '"{0}" "{1}": Resource apply timed out'.format(
                        definition["kind"], origin_name
                    ),
                    **results
                )

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
        if self.module.params.get("wait_condition") and self.module.params[
            "wait_condition"
        ].get("type"):
            wait_condition = self.module.params["wait_condition"]
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
            except Exception as e:
                reason = e.body if hasattr(e, "body") else e
                msg = "Failed to replace object: {0}".format(reason)
                raise CoreException(msg) from e

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
            raise ResourceTimeout(
                '"{0}" "{1}": Resource replacement timed out'.format(
                    definition["kind"], origin_name
                ),
                **results
            )

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
        if self.module.params.get("wait_condition") and self.module.params[
            "wait_condition"
        ].get("type"):
            wait_condition = self.module.params["wait_condition"]
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
                    resource, definition, name, namespace, merge_type=merge_type,
                )
                if not error:
                    break

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
            raise ResourceTimeout(
                '"{0}" "{1}": Resource update timed out'.format(
                    definition["kind"], origin_name
                ),
                **results
            )

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
                except Exception as e:
                    reason = e.body if hasattr(e, "body") else e
                    msg = "Failed to delete object: {0}".format(reason)
                    raise CoreException(msg) from e

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
                        raise ResourceTimeout(
                            '"{0}" "{1}": Resource deletion timed out'.format(
                                definition["kind"], origin_name
                            ),
                            **results
                        )

                return results
