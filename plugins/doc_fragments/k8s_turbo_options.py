# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Red Hat | Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Options for selecting or identifying a specific K8s object

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    DOCUMENTATION = r'''
options:
  enable_session_cache:
    description:
    - Enable the caching of the HTTP sessions.
    type: bool
    default: false
'''
