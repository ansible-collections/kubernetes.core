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


import json
import os
from collections import defaultdict

import kubernetes.dynamic
import kubernetes.dynamic.discovery
from kubernetes import __version__
from kubernetes.dynamic.exceptions import ServiceUnavailableError

from ansible_collections.kubernetes.core.plugins.module_utils.client.resource import ResourceList


class Discoverer(kubernetes.dynamic.discovery.Discoverer):
    def __init__(self, client, cache_file):
        self.client = client
        self.__cache_file = cache_file
        self.__init_cache()

    def __init_cache(self, refresh=False):
        if refresh or not os.path.exists(self.__cache_file):
            self._cache = {'library_version': __version__}
            refresh = True
        else:
            try:
                with open(self.__cache_file, 'r') as f:
                    self._cache = json.load(f, cls=CacheDecoder(self.client))
                if self._cache.get('library_version') != __version__:
                    # Version mismatch, need to refresh cache
                    self.invalidate_cache()
            except Exception:
                self.invalidate_cache()
        self._load_server_info()
        self.discover()
        if refresh:
            self._write_cache()

    def get_resources_for_api_version(self, prefix, group, version, preferred):
        """ returns a dictionary of resources associated with provided (prefix, group, version)"""

        resources = defaultdict(list)
        subresources = {}

        path = '/'.join(filter(None, [prefix, group, version]))
        try:
            resources_response = self.client.request('GET', path).resources or []
        except ServiceUnavailableError:
            resources_response = []

        resources_raw = list(filter(lambda resource: '/' not in resource['name'], resources_response))
        subresources_raw = list(filter(lambda resource: '/' in resource['name'], resources_response))
        for subresource in subresources_raw:
            resource, name = subresource['name'].split('/')
            if not subresources.get(resource):
                subresources[resource] = {}
            subresources[resource][name] = subresource

        for resource in resources_raw:
            # Prevent duplicate keys
            for key in ('prefix', 'group', 'api_version', 'client', 'preferred'):
                resource.pop(key, None)

            resourceobj = kubernetes.dynamic.Resource(
                prefix=prefix,
                group=group,
                api_version=version,
                client=self.client,
                preferred=preferred,
                subresources=subresources.get(resource['name']),
                **resource
            )
            resources[resource['kind']].append(resourceobj)

            resource_lookup = {
                'prefix': prefix,
                'group': group,
                'api_version': version,
                'kind': resourceobj.kind,
                'name': resourceobj.name
            }
            resource_list = ResourceList(self.client, group=group, api_version=version, base_kind=resource['kind'], base_resource_lookup=resource_lookup)
            resources[resource_list.kind].append(resource_list)
        return resources


class LazyDiscoverer(Discoverer, kubernetes.dynamic.LazyDiscoverer):
    def __init__(self, client, cache_file):
        Discoverer.__init__(self, client, cache_file)
        self.__update_cache = False


class CacheDecoder(json.JSONDecoder):
    def __init__(self, client, *args, **kwargs):
        self.client = client
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        if '_type' not in obj:
            return obj
        _type = obj.pop('_type')
        if _type == 'Resource':
            return kubernetes.dynamic.Resource(client=self.client, **obj)
        elif _type == 'ResourceList':
            return ResourceList(self.client, **obj)
        elif _type == 'ResourceGroup':
            return kubernetes.dynamic.discovery.ResourceGroup(obj['preferred'], resources=self.object_hook(obj['resources']))
        return obj
