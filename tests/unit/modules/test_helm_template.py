# -*- coding: utf-8 -*-
# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os.path

import argparse

from ansible_collections.kubernetes.core.plugins.modules.helm_template import (
    template,
)


def test_template_with_release_values_and_values_files():
    my_chart_ref = "testref"
    helm_cmd = "helm"
    parser = argparse.ArgumentParser()

    parser.add_argument('cmd')
    parser.add_argument('template')
# to "simulate" helm template options, include two optional parameters NAME and CHART.
# if parsed string contains only one parameter, the value will be passed
# to CHART and NAME will be set to default value "release-name" as in helm template
    parser.add_argument('NAME', nargs='?', default="release-name")
    parser.add_argument('CHART', nargs='+')
    parser.add_argument('-f', action='append')

    rv = {
        "v1": {
            "enabled": True
        }
    }
    vf = [
        "values1.yml",
        "values2.yml"
    ]
    mytemplate = template(cmd=helm_cmd, chart_ref=my_chart_ref, release_values=rv, values_files=vf)

    args, unknown = parser.parse_known_args(mytemplate.split())

    # helm_template writes release_values to temporary file with changing name
    # these tests should insure
    # - correct order values_files
    # - unknown being included as last
    assert args.f[0] == "values1.yml"
    assert args.f[1] == "values2.yml"
    assert len(args.f) == 3
