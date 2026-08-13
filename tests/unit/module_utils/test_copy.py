# Copyright [2026] [Red Hat, Inc.]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Tests for the to_pod streaming path of K8SCopyToPod. The v4 exec protocol
# cannot half-close stdin, so the archive is bounded with `head -c` to give the
# remote tar a clean EOF; the module must then keep reading until the API server
# closes the connection and check the status reported on the error channel. See
# https://github.com/ansible-collections/kubernetes.core/issues/776

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import io

import pytest

from ansible_collections.kubernetes.core.plugins.module_utils.copy import K8SCopyToPod

ERROR_CHANNEL = 3

SUCCESS = '{"metadata":{},"status":"Success"}'
FAILURE = (
    '{"metadata":{},"status":"Failure","message":"command terminated with'
    ' non-zero exit code","reason":"NonZeroExitCode"}'
)


class FakeModuleFailure(Exception):
    """Stands in for the SystemExit that AnsibleModule.fail_json raises."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        super(FakeModuleFailure, self).__init__(kwargs.get("msg"))


class FakeModule:
    def __init__(self, **params):
        params.setdefault("copy_timeout", 300)
        self.params = params
        self.check_mode = False
        self.warnings = []

    def fail_json(self, **kwargs):
        raise FakeModuleFailure(**kwargs)

    def warn(self, warning):
        self.warnings.append(warning)


class FakeWSClient:
    """Minimal stand-in for kubernetes.stream.ws_client.WSClient.

    ``close_after`` is the number of ``update()`` calls the connection stays
    open for once the last chunk has been written, modelling the remote tar
    consuming the archive and exiting.
    """

    def __init__(self, close_after=2, error=SUCCESS, stderr=None, drop_after=None):
        self.written = []
        self.closed = False
        self._open = True
        self._updates = 0
        self._close_after = close_after
        self._error = error
        self._pending_stderr = stderr
        self._drop_after = drop_after
        self.writes_done = False

    def is_open(self):
        return self._open

    def update(self, timeout=0):
        self._updates += 1
        if self.writes_done and self._updates > self._close_after:
            self._open = False

    def write_stdin(self, data):
        if self._drop_after is not None and len(self.written) >= self._drop_after:
            self._open = False
            return
        self.written.append(data)

    def peek_stdout(self):
        return ""

    def read_stdout(self):
        return ""

    def peek_stderr(self):
        # tar only complains once it has started extracting, i.e. after the
        # whole archive has been handed over.
        if not self.writes_done:
            return ""
        return self._pending_stderr or ""

    def read_stderr(self):
        out, self._pending_stderr = self._pending_stderr, None
        return out

    def read_channel(self, channel):
        assert channel == ERROR_CHANNEL
        return self._error

    def close(self):
        self.closed = True
        self._open = False


def make_copier(has_shell=True, no_preserve=False, **params):
    module = FakeModule(**params)
    copier = K8SCopyToPod.__new__(K8SCopyToPod)
    copier.module = module
    copier.namespace = "testing"
    copier.name = "some-pod"
    copier.named_temp_file = None
    copier.no_preserve = no_preserve
    copier.copy_timeout = module.params["copy_timeout"]
    copier.can_bound_stream = lambda: has_shell
    return copier


def stream_archive(copier, response, size, wait_for_exit=True):
    """Drive _stream_tar_to_pod, marking the writes finished for the fake."""
    payload = io.BytesIO(b"x" * size)
    original_read = payload.read

    def read(n):
        data = original_read(n)
        if not data:
            response.writes_done = True
        return data

    payload.read = read
    return copier._stream_tar_to_pod(response, payload, wait_for_exit)


def test_waits_for_tar_to_exit_before_closing():
    """The connection must not be closed until the remote process is done."""
    copier = make_copier()
    response = FakeWSClient(close_after=5)

    error, stdout, stderr = stream_archive(
        copier, response, 3 * K8SCopyToPod.CHUNK_SIZE
    )

    assert error["status"] == "Success"
    assert stdout == []
    assert stderr == []
    # Whole archive sent, in CHUNK_SIZE pieces.
    assert len(response.written) == 3
    assert sum(len(c) for c in response.written) == 3 * K8SCopyToPod.CHUNK_SIZE
    # Closed only after the server hung up, not right after the last write.
    assert response.closed
    assert response._updates > 3


def test_partial_write_is_not_reported_as_success():
    """A connection dropped mid-archive must fail, not silently truncate."""
    copier = make_copier()
    response = FakeWSClient(drop_after=2)

    with pytest.raises(FakeModuleFailure) as exc:
        stream_archive(copier, response, 5 * K8SCopyToPod.CHUNK_SIZE)

    assert "the remote file is incomplete" in exc.value.kwargs["msg"]
    assert len(response.written) == 2
    assert response.closed


def test_non_zero_tar_exit_is_surfaced():
    """A Failure status on the error channel must reach the caller."""
    copier = make_copier()
    response = FakeWSClient(error=FAILURE)

    error, _stdout, _stderr = stream_archive(copier, response, K8SCopyToPod.CHUNK_SIZE)

    assert error["status"] == "Failure"
    assert error["reason"] == "NonZeroExitCode"


def test_stderr_is_collected_while_draining():
    """Output tar writes after the last chunk must still be captured."""
    copier = make_copier()
    response = FakeWSClient(stderr="tar: /foo: Cannot utime: Operation not permitted")

    _error, _stdout, stderr = stream_archive(copier, response, K8SCopyToPod.CHUNK_SIZE)

    assert stderr == ["tar: /foo: Cannot utime: Operation not permitted"]


def test_drain_honours_copy_timeout(monkeypatch):
    """A remote tar that never exits must time out instead of hanging."""
    copier = make_copier(copy_timeout=30)
    response = FakeWSClient(close_after=10**6)

    # Time only moves past the deadline once the archive has been sent, so the
    # timeout is exercised in the drain loop rather than the write loop.
    monkeypatch.setattr("time.monotonic", lambda: 10**6 if response.writes_done else 0)

    with pytest.raises(FakeModuleFailure) as exc:
        stream_archive(copier, response, K8SCopyToPod.CHUNK_SIZE)

    assert "waiting for tar to finish extracting" in exc.value.kwargs["msg"]
    assert response.closed


def test_archive_is_bounded_with_head():
    """head -c gives the remote tar a clean EOF the v4 protocol cannot."""
    copier = make_copier()

    command, wait_for_exit = copier.remote_command("/tmp/foo", 1003520)

    assert wait_for_exit is True
    assert command == ["/bin/sh", "-c", "head -c 1003520 | tar -xmf - -C /"]
    assert copier.module.warnings == []


def test_bounded_command_carries_no_preserve():
    copier = make_copier(no_preserve=True)

    command, _wait = copier.remote_command("/tmp/foo", 512)

    assert command[2] == (
        "head -c 512 | tar --no-same-permissions --no-same-owner -xmf - -C /"
    )


def test_relative_destination_is_not_anchored():
    """Only absolute destinations get -C /, as before."""
    copier = make_copier()

    command, _wait = copier.remote_command("tmp/foo", 512)

    assert command[2] == "head -c 512 | tar -xmf -"


def test_shell_less_container_falls_back_and_warns():
    """Without a shell the copy still runs, but completion is unverifiable."""
    copier = make_copier(has_shell=False)

    command, wait_for_exit = copier.remote_command("/tmp/foo", 512)

    assert wait_for_exit is False
    assert command == ["tar", "-xmf", "-", "-C", "/"]
    assert len(copier.module.warnings) == 1
    assert "cannot confirm the copy" in copier.module.warnings[0]


def test_fallback_path_does_not_wait_for_exit():
    """The legacy path must not block on a tar that will never exit."""
    copier = make_copier(has_shell=False)
    response = FakeWSClient(close_after=10**6)

    error, _stdout, _stderr = stream_archive(
        copier, response, K8SCopyToPod.CHUNK_SIZE, wait_for_exit=False
    )

    # No exit status is available on this path.
    assert error is None
    assert response.closed
    assert sum(len(c) for c in response.written) == K8SCopyToPod.CHUNK_SIZE
