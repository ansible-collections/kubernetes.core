# Test ConfigMapHash and SecretHash equivalents
# tests based on https://github.com/kubernetes/kubernetes/pull/49961

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.kubernetes.core.plugins.module_utils.hashes import generate_hash

tests = [
    dict(
        resource=dict(
            kind="ConfigMap",
            metadata=dict(name="foo"),
            data=dict()
        ),
        expected="867km9574f",
    ),
    dict(
        resource=dict(
            kind="ConfigMap",
            metadata=dict(name="foo"),
            type="my-type",
            data=dict()
        ),
        expected="867km9574f",
    ),
    dict(
        resource=dict(
            kind="ConfigMap",
            metadata=dict(name="foo"),
            data=dict(
                key1="value1",
                key2="value2")
        ),
        expected="gcb75dd9gb",
    ),
    dict(
        resource=dict(
            kind="Secret",
            metadata=dict(name="foo"),
            data=dict()
        ),
        expected="949tdgdkgg",
    ),
    dict(
        resource=dict(
            kind="Secret",
            metadata=dict(name="foo"),
            type="my-type",
            data=dict()
        ),
        expected="dg474f9t76",
    ),

    dict(
        resource=dict(
            kind="Secret",
            metadata=dict(name="foo"),
            data=dict(
                key1="dmFsdWUx",
                key2="dmFsdWUy")
        ),
        expected="tf72c228m4",
    )

]


def test_hashes():
    for test in tests:
        assert(generate_hash(test['resource']) == test['expected'])
