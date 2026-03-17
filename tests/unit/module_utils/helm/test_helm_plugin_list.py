# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
from ansible_collections.kubernetes.core.plugins.module_utils.helm import (
    parse_helm_plugin_list,
)


def test_parse_helm_plugin_list_empty():
    assert parse_helm_plugin_list() == []


@pytest.mark.parametrize(
    "output,expected",
    [
        (
            """
NAME	VERSION	TYPE	APIVERSION	PROVENANCE	SOURCE
diff	3.4.1  	cli/v1	legacy    	unknown   	unknown

        """,
            [
                dict(
                    name="diff",
                    version="3.4.1",
                    type="cli/v1",
                    apiversion="legacy",
                    provenance="unknown",
                    source="unknown",
                )
            ],
        ),
        (
            """
NAME	VERSION	DESCRIPTION
diff	3.4.1  	Preview helm upgrade changes as a diff
        """,
            [
                dict(
                    name="diff",
                    version="3.4.1",
                    description="Preview helm upgrade changes as a diff",
                )
            ],
        ),
    ],
)
def test_parse_helm_plugin_list_values(output, expected):
    assert parse_helm_plugin_list(output.split("\n")) == expected
