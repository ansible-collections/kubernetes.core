from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import sys
from io import BytesIO

import ansible.module_utils.basic
import pytest
from ansible.module_utils._text import to_bytes
from ansible.module_utils.common._collections_compat import MutableMapping
from ansible.module_utils.six import string_types


@pytest.fixture
def stdin(mocker, request):
    old_args = ansible.module_utils.basic._ANSIBLE_ARGS
    ansible.module_utils.basic._ANSIBLE_ARGS = None
    old_argv = sys.argv
    sys.argv = ["ansible_unittest"]

    if isinstance(request.param, string_types):
        args = request.param
    elif isinstance(request.param, MutableMapping):
        if "ANSIBLE_MODULE_ARGS" not in request.param:
            request.param = {"ANSIBLE_MODULE_ARGS": request.param}
        if "_ansible_remote_tmp" not in request.param["ANSIBLE_MODULE_ARGS"]:
            request.param["ANSIBLE_MODULE_ARGS"]["_ansible_remote_tmp"] = "/tmp"
        if "_ansible_keep_remote_files" not in request.param["ANSIBLE_MODULE_ARGS"]:
            request.param["ANSIBLE_MODULE_ARGS"]["_ansible_keep_remote_files"] = False
        args = json.dumps(request.param)
    else:
        raise Exception("Malformed data to the stdin pytest fixture")

    fake_stdin = BytesIO(to_bytes(args, errors="surrogate_or_strict"))
    mocker.patch("ansible.module_utils.basic.sys.stdin", mocker.MagicMock())
    mocker.patch("ansible.module_utils.basic.sys.stdin.buffer", fake_stdin)

    yield fake_stdin

    ansible.module_utils.basic._ANSIBLE_ARGS = old_args
    sys.argv = old_argv
