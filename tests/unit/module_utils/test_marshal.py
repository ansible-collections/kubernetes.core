# Test ConfigMap and Secret marshalling
# tests based on https://github.com/kubernetes/kubernetes/pull/49961

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.kubernetes.core.plugins.module_utils.hashes import marshal, sorted_dict

tests = [
    dict(
        resource=dict(
            kind="ConfigMap",
            name="",
            data=dict(),
        ),
        expected=b'{"data":{},"kind":"ConfigMap","name":""}'
    ),
    dict(
        resource=dict(
            kind="ConfigMap",
            name="",
            data=dict(
                one=""
            ),
        ),
        expected=b'{"data":{"one":""},"kind":"ConfigMap","name":""}'
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
        expected=b'{"data":{"one":"","three":"3","two":"2"},"kind":"ConfigMap","name":""}'
    ),
    dict(
        resource=dict(
            kind="Secret",
            type="my-type",
            name="",
            data=dict(),
        ),
        expected=b'{"data":{},"kind":"Secret","name":"","type":"my-type"}'
    ),
    dict(
        resource=dict(
            kind="Secret",
            type="my-type",
            name="",
            data=dict(
                one=""
            ),
        ),
        expected=b'{"data":{"one":""},"kind":"Secret","name":"","type":"my-type"}'
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
        expected=b'{"data":{"one":"","three":"Mw==","two":"Mg=="},"kind":"Secret","name":"","type":"my-type"}'
    ),
]


def test_marshal():
    for test in tests:
        assert(marshal(sorted_dict(test['resource']), sorted(list(test['resource'].keys()))) == test['expected'])
