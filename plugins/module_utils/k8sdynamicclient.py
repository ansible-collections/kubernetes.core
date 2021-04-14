from __future__ import absolute_import, division, print_function
__metaclass__ = type


from kubernetes.dynamic import DynamicClient

from ansible_collections.kubernetes.core.plugins.module_utils.apply import apply
from ansible_collections.kubernetes.core.plugins.module_utils.exceptions import ApplyException


class K8SDynamicClient(DynamicClient):
    def apply(self, resource, body=None, name=None, namespace=None):
        body = super().serialize_body(body)
        body['metadata'] = body.get('metadata', dict())
        name = name or body['metadata'].get('name')
        if not name:
            raise ValueError("name is required to apply {0}.{1}".format(resource.group_version, resource.kind))
        if resource.namespaced:
            body['metadata']['namespace'] = super().ensure_namespace(resource, namespace, body)
        try:
            return apply(resource, body)
        except ApplyException as e:
            raise ValueError("Could not apply strategic merge to %s/%s: %s" %
                             (body['kind'], body['metadata']['name'], e))
