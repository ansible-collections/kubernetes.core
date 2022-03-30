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

# Test ConfigMap and Secret marshalling
# tests based on https://github.com/kubernetes/kubernetes/pull/49961

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.kubernetes.core.plugins.module_utils.hashes import (
    marshal,
    sorted_dict,
)

tests = [
    dict(
        resource=dict(
            kind="ConfigMap",
            name="",
            data=dict(),
        ),
        expected=b'{"data":{},"kind":"ConfigMap","name":""}',
    ),
    dict(
        resource=dict(
            kind="ConfigMap",
            name="",
            data=dict(one=""),
        ),
        expected=b'{"data":{"one":""},"kind":"ConfigMap","name":""}',
    ),
    dict(
        resource=dict(
            kind="ConfigMap",
            name="",
            data=dict(
                two="2",
                one="",
                three="3",
            ),
        ),
        expected=b'{"data":{"one":"","three":"3","two":"2"},"kind":"ConfigMap","name":""}',
    ),
    dict(
        resource=dict(
            kind="Secret",
            type="my-type",
            name="",
            data=dict(),
        ),
        expected=b'{"data":{},"kind":"Secret","name":"","type":"my-type"}',
    ),
    dict(
        resource=dict(
            kind="Secret",
            type="my-type",
            name="",
            data=dict(one=""),
        ),
        expected=b'{"data":{"one":""},"kind":"Secret","name":"","type":"my-type"}',
    ),
    dict(
        resource=dict(
            kind="Secret",
            type="my-type",
            name="",
            data=dict(
                two="Mg==",
                one="",
                three="Mw==",
            ),
        ),
        expected=b'{"data":{"one":"","three":"Mw==","two":"Mg=="},"kind":"Secret","name":"","type":"my-type"}',
    ),
]


def test_marshal():
    for test in tests:
        assert (
            marshal(
                sorted_dict(test["resource"]), sorted(list(test["resource"].keys()))
            )
            == test["expected"]
        )
