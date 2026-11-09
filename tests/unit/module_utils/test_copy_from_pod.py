# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# kubernetes >= 37.0.0 validates API call arguments with pydantic, and the exec
# endpoint's ``command`` is a list of strings, so a bare string is rejected
# before the request is sent. See
# https://github.com/ansible-collections/kubernetes.core/issues/1273

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from types import SimpleNamespace

from ansible_collections.kubernetes.core.plugins.module_utils import copy as copy_utils
from ansible_collections.kubernetes.core.plugins.module_utils.copy import (
    K8SCopyFromPod,
)

SUCCESS = '{"metadata":{},"status":"Success"}'


class FakeModule:
    def fail_json(self, **kwargs):
        raise AssertionError(kwargs["msg"])


class FakeWSClient:
    """Exec response that reports success and closes on the first update."""

    def __init__(self):
        self._open = True

    def is_open(self):
        return self._open

    def update(self, timeout=0):
        self._open = False

    def peek_stdout(self):
        return ""

    def peek_stderr(self):
        return ""

    def read_channel(self, channel):
        return SUCCESS

    def close(self):
        self._open = False


def make_copier(monkeypatch):
    """K8SCopyFromPod whose exec calls all succeed, recording each command."""
    commands = []

    def fake_stream(*args, **kwargs):
        commands.append(kwargs["command"])
        return FakeWSClient()

    monkeypatch.setattr(copy_utils, "stream", fake_stream, raising=False)
    copier = K8SCopyFromPod.__new__(K8SCopyFromPod)
    copier.module = FakeModule()
    copier.namespace = "testing"
    copier.name = "some-pod"
    copier.api_instance = SimpleNamespace(connect_get_namespaced_pod_exec=None)
    copier.container_arg = {}
    copier.remote_path = "/data"
    copier._shellname = None
    return copier, commands


def test_directory_listing_probe_is_a_list(monkeypatch):
    copier, commands = make_copier(monkeypatch)

    assert copier.list_remote_files() == []
    assert commands == [
        ["test", "-e", "/data"],
        ["test", "-d", "/data"],
        ["find"],
        ["find", "/data", "-type", "f"],
    ]


def test_shell_probe_is_a_list(monkeypatch):
    copier, commands = make_copier(monkeypatch)

    assert copier.pod_shell == "/bin/sh"
    assert commands == [["/bin/sh"]]
