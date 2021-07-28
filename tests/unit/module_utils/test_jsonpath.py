# Copyright [2021] [Red Hat, Inc.]
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

from ansible_collections.kubernetes.core.plugins.module_utils.jsonpath_extractor import validate_with_jsonpath


def test_property_present():
    data = {
        "containers": [
            {"name": "t0", "image": "nginx"},
            {"name": "t1", "image": "python"},
            {"name": "t2", "image": "mongo", "state": "running"}
        ]
    }
    assert validate_with_jsonpath(None, data, "containers[*].state")
    assert not validate_with_jsonpath(None, data, "containers[*].status")


def test_property_value():
    data = {
        "containers": [
            {"name": "t0", "image": "nginx"},
            {"name": "t1", "image": "python"},
            {"name": "t2", "image": "mongo", "state": "running"}
        ]
    }
    assert validate_with_jsonpath(None, data, "containers[*].state", "running")
    assert validate_with_jsonpath(None, data, "containers[*].state", "Running")
    assert not validate_with_jsonpath(None, data, "containers[*].state", "off")


def test_boolean_value():
    data = {
        "containers": [
            {"image": "nginx", "poweron": False},
            {"image": "python"},
            {"image": "mongo", "connected": True}
        ]
    }
    assert validate_with_jsonpath(None, data, "containers[*].connected", "true")
    assert validate_with_jsonpath(None, data, "containers[*].connected", "True")
    assert validate_with_jsonpath(None, data, "containers[*].connected", "TRUE")
    assert validate_with_jsonpath(None, data, "containers[0].poweron", "false")

    data = {
        "containers": [
            {"image": "nginx", "ready": False},
            {"image": "python", "ready": False},
            {"image": "mongo", "ready": True}
        ]
    }
    assert not validate_with_jsonpath(None, data, "containers[*].ready", "true")

    data = {
        "containers": [
            {"image": "nginx", "ready": True},
            {"image": "python", "ready": True},
            {"image": "mongo", "ready": True}
        ]
    }
    assert validate_with_jsonpath(None, data, "containers[*].ready", "true")
