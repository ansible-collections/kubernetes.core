# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
from ansible_collections.kubernetes.core.plugins.modules.k8s_log import (
    get_exception_message,
)
from kubernetes.client.exceptions import ApiException

STATUS = '{"kind":"Status","message":"container foo is not valid for pod bar"}'


# kubernetes >= 37.0.0 decodes ApiException.body to str, older releases keep bytes.
@pytest.mark.parametrize("body", [STATUS, STATUS.encode("utf-8")])
def test_message_is_extracted_from_status_body(body):
    exc = ApiException(status=400, reason="Bad Request")
    exc.body = body

    assert get_exception_message(exc) == "container foo is not valid for pod bar"
