# Copyright [2025] [Red Hat, Inc.]
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

import pytest
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.service import (
    build_hidden_field_tree,
    hide_fields,
)


def test_hiding_missing_field_does_nothing():
    output = dict(
        kind="ConfigMap", metadata=dict(name="foo"), data=dict(one="1", two="2")
    )
    hidden_fields = ["doesnotexist"]
    assert hide_fields(output, hidden_fields) == output


def test_hiding_simple_field():
    output = dict(
        kind="ConfigMap", metadata=dict(name="foo"), data=dict(one="1", two="2")
    )
    hidden_fields = ["metadata"]
    expected = dict(kind="ConfigMap", data=dict(one="1", two="2"))
    assert hide_fields(output, hidden_fields) == expected


def test_hiding_only_key_in_dict_removes_dict():
    output = dict(kind="ConfigMap", metadata=dict(name="foo"), data=dict(one="1"))
    hidden_fields = ["data.one"]
    expected = dict(kind="ConfigMap", metadata=dict(name="foo"))
    assert hide_fields(output, hidden_fields) == expected


def test_hiding_all_keys_in_dict_removes_dict():
    output = dict(
        kind="ConfigMap", metadata=dict(name="foo"), data=dict(one="1", two="2")
    )
    hidden_fields = ["data.one", "data.two"]
    expected = dict(kind="ConfigMap", metadata=dict(name="foo"))
    assert hide_fields(output, hidden_fields) == expected


def test_hiding_multiple_fields():
    output = dict(
        kind="ConfigMap", metadata=dict(name="foo"), data=dict(one="1", two="2")
    )
    hidden_fields = ["metadata", "data.one"]
    expected = dict(kind="ConfigMap", data=dict(two="2"))
    assert hide_fields(output, hidden_fields) == expected


def test_hiding_dict_key():
    output = dict(
        kind="ConfigMap",
        metadata=dict(
            name="foo",
            annotations={
                "kubectl.kubernetes.io/last-applied-configuration": '{"testvalue"}'
            },
        ),
        data=dict(one="1", two="2"),
    )
    hidden_fields = [
        "metadata.annotations[kubectl.kubernetes.io/last-applied-configuration]",
    ]
    expected = dict(
        kind="ConfigMap", metadata=dict(name="foo"), data=dict(one="1", two="2")
    )
    assert hide_fields(output, hidden_fields) == expected


def test_hiding_list_value_key():
    output = dict(
        kind="Pod",
        metadata=dict(name="foo"),
        spec=dict(
            containers=[
                dict(
                    name="containers",
                    image="busybox",
                    env=[
                        dict(name="ENV1", value="env1"),
                        dict(name="ENV2", value="env2"),
                        dict(name="ENV3", value="env3"),
                    ],
                )
            ]
        ),
    )
    hidden_fields = ["spec.containers[0].env[1].value"]
    expected = dict(
        kind="Pod",
        metadata=dict(name="foo"),
        spec=dict(
            containers=[
                dict(
                    name="containers",
                    image="busybox",
                    env=[
                        dict(name="ENV1", value="env1"),
                        dict(name="ENV2"),
                        dict(name="ENV3", value="env3"),
                    ],
                )
            ]
        ),
    )
    assert hide_fields(output, hidden_fields) == expected


def test_hiding_last_list_item():
    output = dict(
        kind="Pod",
        metadata=dict(name="foo"),
        spec=dict(
            containers=[
                dict(
                    name="containers",
                    image="busybox",
                    env=[
                        dict(name="ENV1", value="env1"),
                    ],
                )
            ]
        ),
    )
    hidden_fields = ["spec.containers[0].env[0]"]
    expected = dict(
        kind="Pod",
        metadata=dict(name="foo"),
        spec=dict(
            containers=[
                dict(
                    name="containers",
                    image="busybox",
                )
            ]
        ),
    )
    assert hide_fields(output, hidden_fields) == expected


def test_hiding_nested_dicts_using_brackets():
    output = dict(
        kind="Pod",
        metadata=dict(name="foo"),
        spec=dict(
            containers=[
                dict(
                    name="containers",
                    image="busybox",
                    securityContext=dict(runAsUser=101),
                )
            ]
        ),
    )
    hidden_fields = ["spec.containers[0][securityContext][runAsUser]"]
    expected = dict(
        kind="Pod",
        metadata=dict(name="foo"),
        spec=dict(
            containers=[
                dict(
                    name="containers",
                    image="busybox",
                )
            ]
        ),
    )
    assert hide_fields(output, hidden_fields) == expected


def test_using_jinja_syntax():
    output = dict(
        kind="ConfigMap", metadata=dict(name="foo"), data=["0", "1", "2", "3"]
    )
    hidden_fields = ["data.2"]
    expected = dict(kind="ConfigMap", metadata=dict(name="foo"), data=["0", "1", "3"])
    assert hide_fields(output, hidden_fields) == expected


def test_remove_multiple_items_from_list():
    output = dict(
        kind="ConfigMap", metadata=dict(name="foo"), data=["0", "1", "2", "3"]
    )
    hidden_fields = ["data[0]", "data[2]"]
    expected = dict(kind="ConfigMap", metadata=dict(name="foo"), data=["1", "3"])
    assert hide_fields(output, hidden_fields) == expected


def test_hide_dict_and_nested_dict():
    output = {
        "kind": "Pod",
        "metadata": {
            "labels": {
                "control-plane": "controller-manager",
                "pod-template-hash": "687b856498",
            },
            "annotations": {
                "kubectl.kubernetes.io/default-container": "awx-manager",
                "creationTimestamp": "2025-01-16T12:40:43Z",
            },
        },
    }
    hidden_fields = ["metadata.labels.pod-template-hash", "metadata.labels"]
    expected = {
        "kind": "Pod",
        "metadata": {
            "annotations": {
                "kubectl.kubernetes.io/default-container": "awx-manager",
                "creationTimestamp": "2025-01-16T12:40:43Z",
            }
        },
    }
    assert hide_fields(output, hidden_fields) == expected


@pytest.mark.parametrize(
    "hidden_fields,expected",
    [
        (
            [
                "data[0]",
                "data[1]",
                "metadata.annotation",
                "metadata.annotation[0].name",
            ],
            {"data": {"0": None, "1": None}, "metadata": {"annotation": None}},
        ),
        (
            [
                "data[0]",
                "data[1]",
                "metadata.annotation[0].name",
                "metadata.annotation",
            ],
            {"data": {"0": None, "1": None}, "metadata": {"annotation": None}},
        ),
        (
            [
                "data[0]",
                "data[1]",
                "data",
                "metadata.annotation[0].name",
                "metadata.annotation",
            ],
            {"data": None, "metadata": {"annotation": None}},
        ),
    ],
)
def test_build_hidden_field_tree(hidden_fields, expected):
    assert build_hidden_field_tree(hidden_fields) == expected
