# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.kubernetes.core.plugins.modules import k8s_exec


def test_core_v1_api_is_imported():
    # The module swallows ImportError, so a broken import only shows up at run
    # time as a NameError. See
    # https://github.com/ansible-collections/kubernetes.core/issues/1273
    assert hasattr(k8s_exec, "core_v1_api")
