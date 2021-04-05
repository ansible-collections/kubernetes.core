# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


from ansible_collections.kubernetes.core.plugins.module_utils.common import (
    _encode_stringdata,
)


def test_encode_stringdata_modifies_definition():
    definition = {
        "apiVersion": "v1",
        "kind": "Secret",
        "type": "Opaque",
        "stringData": {
            "mydata": "ansiβle"
        }
    }
    res = _encode_stringdata(definition)
    assert "stringData" not in res
    assert res["data"]["mydata"] == "YW5zac6ybGU="


def test_encode_stringdata_does_not_modify_data():
    definition = {
        "apiVersion": "v1",
        "kind": "Secret",
        "type": "Opaque",
        "data": {
            "mydata": "Zm9vYmFy"
        }
    }
    res = _encode_stringdata(definition)
    assert res["data"]["mydata"] == "Zm9vYmFy"
