# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from datetime import datetime

from ansible_collections.kubernetes.core.plugins.action.k8s_info import RemoveOmit


def get_omit_token():
    return "__omit_place_holder__%s" % datetime.now().strftime("%Y%m%d%H%M%S")


def test_remove_omit_from_str():
    omit_token = get_omit_token()
    src = """
        project: ansible
        collection: {omit}
    """.format(
        omit=omit_token
    )
    result = RemoveOmit(src, omit_value=omit_token).output()
    assert len(result) == 1
    assert result[0] == dict(project="ansible")


def test_remove_omit_from_list():
    omit_token = get_omit_token()
    src = """
        items:
          - {omit}
    """.format(
        omit=omit_token
    )
    result = RemoveOmit(src, omit_value=omit_token).output()
    assert len(result) == 1
    assert result[0] == dict(items=[])


def test_remove_omit_from_list_of_dict():
    omit_token = get_omit_token()
    src = """
        items:
          - owner: ansible
            team: {omit}
          - simple_list_item
    """.format(
        omit=omit_token
    )
    result = RemoveOmit(src, omit_value=omit_token).output()
    assert len(result) == 1
    assert result[0] == dict(items=[dict(owner="ansible"), "simple_list_item"])


def test_remove_omit_combined():
    omit_token = get_omit_token()
    src = """
        items:
          - {omit}
          - list_item_a
          - list_item_b
        parent:
          child:
            subchilda: {omit}
            subchildb:
                name: {omit}
                age: 3
    """.format(
        omit=omit_token
    )
    result = RemoveOmit(src, omit_value=omit_token).output()
    assert len(result) == 1
    assert result[0] == dict(
        items=["list_item_a", "list_item_b"],
        parent=dict(child=dict(subchildb=dict(age=3))),
    )


def test_remove_omit_mutiple_documents():
    omit_token = get_omit_token()
    src = [
        """
    project: ansible
    collection: {omit}
    """.format(
            omit=omit_token
        ),
        "---",
        """
    project: kubernetes
    environment: production
    collection: {omit}""".format(
            omit=omit_token
        ),
    ]
    src = "\n".join(src)
    print(src)
    result = RemoveOmit(src, omit_value=omit_token).output()
    assert len(result) == 2
    assert result[0] == dict(project="ansible")
    assert result[1] == dict(project="kubernetes", environment="production")
