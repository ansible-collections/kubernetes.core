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

# Test ConfigMapHash and SecretHash equivalents
# tests based on https://github.com/kubernetes/kubernetes/pull/49961

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.kubernetes.core.plugins.module_utils.hashes import (
    generate_hash,
)

tests = [
    dict(
        resource=dict(kind="ConfigMap", metadata=dict(name="foo"), data=dict()),
        expected="867km9574f",
    ),
    dict(
        resource=dict(
            kind="ConfigMap", metadata=dict(name="foo"), type="my-type", data=dict()
        ),
        expected="867km9574f",
    ),
    dict(
        resource=dict(
            kind="ConfigMap",
            metadata=dict(name="foo"),
            data=dict(key1="value1", key2="value2"),
        ),
        expected="gcb75dd9gb",
    ),
    dict(
        resource=dict(kind="Secret", metadata=dict(name="foo"), data=dict()),
        expected="949tdgdkgg",
    ),
    dict(
        resource=dict(
            kind="Secret", metadata=dict(name="foo"), type="my-type", data=dict()
        ),
        expected="dg474f9t76",
    ),
    dict(
        resource=dict(
            kind="Secret",
            metadata=dict(name="foo"),
            data=dict(key1="dmFsdWUx", key2="dmFsdWUy"),
        ),
        expected="tf72c228m4",
    ),
    dict(
        # an empty binaryData must not change the hash compared to a
        # ConfigMap without any binaryData at all
        resource=dict(
            kind="ConfigMap",
            metadata=dict(name="foo"),
            data=dict(),
            binaryData=dict(),
        ),
        expected="867km9574f",
    ),
    dict(
        resource=dict(
            kind="ConfigMap",
            metadata=dict(name="foo"),
            data=dict(),
            binaryData=dict(key1="dmFsdWUx"),
        ),
        expected="228tffgk4b",
    ),
    dict(
        resource=dict(
            kind="ConfigMap",
            metadata=dict(name="foo"),
            data=dict(),
            binaryData=dict(key1="dmFsdWUx", key2="dmFsdWUy"),
        ),
        expected="kkf4dk7gh2",
    ),
    dict(
        # an empty stringData must not change the hash compared to a
        # Secret without any stringData at all
        resource=dict(
            kind="Secret",
            metadata=dict(name="foo"),
            data=dict(),
            stringData=dict(),
        ),
        expected="949tdgdkgg",
    ),
    dict(
        resource=dict(
            kind="Secret",
            metadata=dict(name="foo"),
            data=dict(),
            stringData=dict(key1="value1"),
        ),
        expected="kc6cmgf942",
    ),
    dict(
        resource=dict(
            kind="Secret",
            metadata=dict(name="foo"),
            data=dict(),
            stringData=dict(key1="value1", key2="value2"),
        ),
        expected="hkg957m978",
    ),
]


def test_hashes():
    for test in tests:
        assert generate_hash(test["resource"]) == test["expected"]


def test_different_binary_data_produce_different_hashes():
    # https://github.com/ansible-collections/kubernetes.core/issues/666
    one_file = dict(
        kind="ConfigMap",
        metadata=dict(name="test-tgz"),
        binaryData=dict(**{"test.tgz": "SDRzSUFBQUFBQUFBQQo="}),
    )
    two_files = dict(
        kind="ConfigMap",
        metadata=dict(name="test-tgz"),
        binaryData=dict(
            **{"test.tgz": "SDRzSUFBQUFBQUFBQQo=", "test2.tgz": "SDRzSUFBQUFBQUFBQQo="}
        ),
    )
    assert generate_hash(one_file) != generate_hash(two_files)


def test_different_string_data_produce_different_hashes():
    # https://github.com/ansible-collections/kubernetes.core/issues/666
    one_key = dict(
        kind="Secret",
        metadata=dict(name="foo"),
        stringData=dict(key1="value1"),
    )
    two_keys = dict(
        kind="Secret",
        metadata=dict(name="foo"),
        stringData=dict(key1="value1", key2="value2"),
    )
    assert generate_hash(one_key) != generate_hash(two_keys)
