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

from ansible_collections.kubernetes.core.plugins.module_utils.jsonpath import match_json_property

import pytest
jmespath = pytest.importorskip("jmespath")


def test_property_present():
    data = {
        "containers": [
            {"name": "t0", "image": "nginx"},
            {"name": "t1", "image": "python"},
            {"name": "t2", "image": "mongo", "state": "running"}
        ]
    }
    assert match_json_property(None, data, "containers[*].state")
    assert not match_json_property(None, data, "containers[*].status")


def test_property_value():
    data = {
        "containers": [
            {"name": "t0", "image": "nginx"},
            {"name": "t1", "image": "python"},
            {"name": "t2", "image": "mongo", "state": "running"}
        ]
    }
    assert match_json_property(None, data, "containers[*].state", "running")
    assert match_json_property(None, data, "containers[*].state", "Running")
    assert not match_json_property(None, data, "containers[*].state", "off")


def test_boolean_value():
    data = {
        "containers": [
            {"image": "nginx", "poweron": False},
            {"image": "python"},
            {"image": "mongo", "connected": True}
        ]
    }
    assert match_json_property(None, data, "containers[*].connected", "true")
    assert match_json_property(None, data, "containers[*].connected", "True")
    assert match_json_property(None, data, "containers[*].connected", "TRUE")
    assert match_json_property(None, data, "containers[0].poweron", "false")


def test_valid_expression():
    data = dict(key="ansible", value="unit-test")
    with pytest.raises(jmespath.exceptions.ParseError) as parsing_err:
        match_json_property(None, data, ".ansible")
    assert "Parse error" in str(parsing_err.value)
