# Copyright [2017] [Red Hat, Inc.]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from __future__ import absolute_import, division, print_function

__metaclass__ = type

import inspect

from ansible_collections.kubernetes.core.plugins.module_utils.apply import k8s_apply
from ansible_collections.kubernetes.core.plugins.module_utils.exceptions import (
    ApplyException,
)
from kubernetes.dynamic import DynamicClient


class _TimeoutApi:
    """Typed API (e.g. CoreV1Api) whose calls use a default request timeout."""

    def __init__(self, api, request_timeout):
        self._api = api
        self._request_timeout = request_timeout

    def __getattr__(self, name):
        attr = getattr(self._api, name)
        if name.startswith("_") or not inspect.ismethod(attr):
            return attr

        def call(*args, **kwargs):
            if kwargs.get("_request_timeout") is None and not kwargs.get("watch"):
                kwargs["_request_timeout"] = self._request_timeout
            return attr(*args, **kwargs)

        return call


class K8SDynamicClient(DynamicClient):
    def __init__(self, client, cache_file=None, discoverer=None, request_timeout=None):
        # Set before calling the parent: discovery already sends requests.
        # A (connect, read) tuple works with every supported kubernetes client;
        # older ones silently ignore a float.
        self.request_timeout = None
        if request_timeout is not None:
            self.request_timeout = (request_timeout, request_timeout)
        super().__init__(client, cache_file=cache_file, discoverer=discoverer)

    def request(self, method, path, body=None, **params):
        # Watch requests stream until their own timeout and stay untouched.
        if (
            self.request_timeout is not None
            and params.get("_request_timeout") is None
            and not params.get("watch")
        ):
            params["_request_timeout"] = self.request_timeout
        return super().request(method, path, body=body, **params)

    def typed_api(self, api_class):
        """Build a typed API client (e.g. CoreV1Api) that honours request_timeout.

        Calls made through typed APIs go straight to ApiClient and skip
        request(), so they need the timeout passed explicitly.
        """
        api = api_class(self.client)
        if self.request_timeout is None:
            return api
        return _TimeoutApi(api, self.request_timeout)

    def apply(self, resource, body=None, name=None, namespace=None, **kwargs):
        body = super().serialize_body(body)
        body["metadata"] = body.get("metadata", dict())
        name = name or body["metadata"].get("name")
        if not name:
            raise ValueError(
                "name is required to apply {0}.{1}".format(
                    resource.group_version, resource.kind
                )
            )
        if resource.namespaced:
            body["metadata"]["namespace"] = super().ensure_namespace(
                resource, namespace, body
            )
        try:
            return k8s_apply(resource, body, **kwargs)
        except ApplyException as e:
            raise ValueError(
                "Could not apply strategic merge to %s/%s: %s"
                % (body["kind"], body["metadata"]["name"], e)
            )
