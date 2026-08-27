# Copyright [2021] [Red Hat, Inc.]
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


from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os
import shlex
import tarfile
import time
from abc import ABCMeta, abstractmethod
from select import select
from tempfile import NamedTemporaryFile, TemporaryFile

from ansible.module_utils.common.text.converters import to_native

# from ansible_collections.kubernetes.core.plugins.module_utils.ansiblemodule import AnsibleModule
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.exceptions import (
    CoreException,
)

try:
    from kubernetes.client.api import core_v1_api
    from kubernetes.stream import stream
    from kubernetes.stream.ws_client import (
        ABNF,
        ERROR_CHANNEL,
        STDERR_CHANNEL,
        STDOUT_CHANNEL,
    )
except ImportError:
    pass

try:
    import yaml
except ImportError:
    # ImportError are managed by the common module already.
    pass


class K8SCopy(metaclass=ABCMeta):
    def __init__(self, module, client):
        self.client = client
        self.module = module
        self.api_instance = core_v1_api.CoreV1Api(client.client)

        self.local_path = module.params.get("local_path")
        self.name = module.params.get("pod")
        self.namespace = module.params.get("namespace")
        self.remote_path = module.params.get("remote_path")
        self.content = module.params.get("content")

        self.no_preserve = module.params.get("no_preserve")
        self.container_arg = {}
        if module.params.get("container"):
            self.container_arg["container"] = module.params.get("container")
        self.check_mode = self.module.check_mode

    def _run_from_pod(self, cmd):
        try:
            resp = stream(
                self.api_instance.connect_get_namespaced_pod_exec,
                self.name,
                self.namespace,
                command=cmd,
                async_req=False,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
                _preload_content=False,
                **self.container_arg,
            )

            stderr, stdout = [], []
            while resp.is_open():
                resp.update(timeout=1)
                if resp.peek_stdout():
                    stdout.extend(resp.read_stdout().rstrip("\n").split("\n"))
                if resp.peek_stderr():
                    stderr.extend(resp.read_stderr().rstrip("\n").split("\n"))
            error = resp.read_channel(ERROR_CHANNEL)
            resp.close()
            error = yaml.safe_load(error)
            return error, stdout, stderr
        except Exception as e:
            self.module.fail_json(
                msg="Error while running/parsing from pod {0}/{1} command='{2}' : {3}".format(
                    self.namespace, self.name, cmd, to_native(e)
                )
            )

    def is_directory_path_from_pod(self, file_path, failed_if_not_exists=True):
        # check if file exists
        error, out, err = self._run_from_pod(cmd=["test", "-e", file_path])
        if error.get("status") != "Success":
            if failed_if_not_exists:
                return None, "%s does not exist in remote pod filesystem" % file_path
            return False, None
        error, out, err = self._run_from_pod(cmd=["test", "-d", file_path])
        return error.get("status") == "Success", None

    @abstractmethod
    def run(self):
        pass


class K8SCopyFromPod(K8SCopy):
    """
    Copy files/directory from Pod into local filesystem
    """

    def __init__(self, module, client):
        super(K8SCopyFromPod, self).__init__(module, client)
        self.is_remote_path_dir = None
        self.files_to_copy = []
        self._shellname = None

    @property
    def pod_shell(self):
        if self._shellname is None:
            for s in ("/bin/sh", "/bin/bash"):
                error, out, err = self._run_from_pod(s)
                if error.get("status") == "Success":
                    self._shellname = s
                    break
        return self._shellname

    def listfiles_with_find(self, path):
        find_cmd = ["find", path, "-type", "f"]
        error, files, err = self._run_from_pod(cmd=find_cmd)
        if error.get("status") != "Success":
            self.module.fail_json(msg=error.get("message"))
        return files

    def listfile_with_echo(self, path):
        echo_cmd = [
            self.pod_shell,
            "-c",
            "echo {path}/* {path}/.*".format(
                path=path.translate(str.maketrans({" ": r"\ "}))
            ),
        ]
        error, out, err = self._run_from_pod(cmd=echo_cmd)
        if error.get("status") != "Success":
            self.module.fail_json(msg=error.get("message"))

        files = []
        if out:
            output = out[0] + " "
            files = [
                os.path.join(path, p[:-1])
                for p in output.split(f"{path}/")
                if p and p[:-1] not in (".", "..")
            ]

        result = []
        for f in files:
            is_dir, err = self.is_directory_path_from_pod(f)
            if err:
                continue
            if not is_dir:
                result.append(f)
                continue
            result += self.listfile_with_echo(f)
        return result

    def list_remote_files(self):
        """
        This method will check if the remote path is a dir or file
        if it is a directory the file list will be updated accordingly
        """
        # check is remote path exists and is a file or directory
        is_dir, error = self.is_directory_path_from_pod(self.remote_path)
        if error:
            self.module.fail_json(msg=error)

        if not is_dir:
            return [self.remote_path]
        else:
            # find executable to list dir with
            executables = dict(
                find=self.listfiles_with_find,
                echo=self.listfile_with_echo,
            )
            for item in executables:
                error, out, err = self._run_from_pod(item)
                if error.get("status") == "Success":
                    return executables.get(item)(self.remote_path)

    def read(self):
        self.stdout = None
        self.stderr = None

        if self.response.is_open():
            if not self.response.sock.connected:
                self.response._connected = False
            else:
                ret, out, err = select((self.response.sock.sock,), (), (), 0)
                if ret:
                    code, frame = self.response.sock.recv_data_frame(True)
                    if code == ABNF.OPCODE_CLOSE:
                        self.response._connected = False
                    elif (
                        code in (ABNF.OPCODE_BINARY, ABNF.OPCODE_TEXT)
                        and len(frame.data) > 1
                    ):
                        channel = frame.data[0]
                        content = frame.data[1:]
                        if content:
                            if channel == STDOUT_CHANNEL:
                                self.stdout = content
                            elif channel == STDERR_CHANNEL:
                                self.stderr = content.decode("utf-8", "replace")

    def copy(self):
        is_remote_path_dir = (
            len(self.files_to_copy) > 1 or self.files_to_copy[0] != self.remote_path
        )
        relpath_start = self.remote_path
        if is_remote_path_dir and os.path.isdir(self.local_path):
            relpath_start = os.path.dirname(self.remote_path)

        if not self.check_mode:
            for remote_file in self.files_to_copy:
                dest_file = self.local_path
                if is_remote_path_dir:
                    dest_file = os.path.join(
                        self.local_path,
                        os.path.relpath(remote_file, start=relpath_start),
                    )
                    # create directory to copy file in
                    os.makedirs(os.path.dirname(dest_file), exist_ok=True)

                pod_command = ["cat", remote_file]
                self.response = stream(
                    self.api_instance.connect_get_namespaced_pod_exec,
                    self.name,
                    self.namespace,
                    command=pod_command,
                    stderr=True,
                    stdin=True,
                    stdout=True,
                    tty=False,
                    _preload_content=False,
                    **self.container_arg,
                )
                errors = []
                with open(dest_file, "wb") as fh:
                    while self.response._connected:
                        self.read()
                        if self.stdout:
                            fh.write(self.stdout)
                        if self.stderr:
                            errors.append(self.stderr)
                if errors:
                    self.module.fail_json(
                        msg="Failed to copy file from Pod: {0}".format("".join(errors))
                    )
        self.module.exit_json(
            changed=True,
            result="{0} successfully copied locally into {1}".format(
                self.remote_path, self.local_path
            ),
        )

    def run(self):
        self.files_to_copy = self.list_remote_files()
        if self.files_to_copy == []:
            # Using warn method instead of passing warnings to exit_json as it is
            # deprecated in ansible-core>=2.19.0
            self._module.warn(
                "No file found from directory '{0}' into remote Pod.".format(
                    self.remote_path
                )
            )
            self.module.exit_json(
                changed=False,
            )
        self.copy()


class K8SCopyToPod(K8SCopy):
    """
    Copy files/directory from local filesystem into remote Pod
    """

    # Size of the chunks the tar archive is written to stdin with.
    CHUNK_SIZE = 1024 * 1024
    SHELL = "/bin/sh"

    def __init__(self, module, client):
        super(K8SCopyToPod, self).__init__(module, client)
        self.files_to_copy = list()
        self.named_temp_file = None
        self.copy_timeout = module.params.get("copy_timeout")

    def close_temp_file(self):
        if self.named_temp_file:
            self.named_temp_file.close()

    def _fail(self, response, msg, stderr=(), **kwargs):
        """Fail, keeping whatever the remote already wrote to stderr.

        An early close or a stall is usually the symptom, not the cause: tar
        has typically said why on stderr first.
        """
        if stderr:
            msg = "{0}: {1}".format(msg, "".join(stderr))
        response.close()
        self.close_temp_file()
        self.module.fail_json(
            msg="Failed to copy local file/directory into Pod: {0}".format(msg),
            **kwargs,
        )

    def tar_command(self, dest_file):
        if self.no_preserve:
            command = [
                "tar",
                "--no-same-permissions",
                "--no-same-owner",
                "-xmf",
                "-",
            ]
        else:
            command = ["tar", "-xmf", "-"]

        if dest_file.startswith("/"):
            command.extend(["-C", "/"])
        return command

    def can_bound_stream(self):
        """Whether the container can run ``sh -c 'head -c ...'``."""
        error, _out, _err = self._run_from_pod(
            cmd=[self.SHELL, "-c", "command -v head"]
        )
        return (error or {}).get("status") == "Success"

    def remote_command(self, dest_file, archive_size):
        """Build the command that extracts the archive inside the container.

        The websocket exec protocol the kubernetes client speaks (v4) cannot
        half-close stdin, so the only EOF the remote process can get is the
        connection going away. Relying on that races with tar finishing and
        truncates the file (issue #776), and tar cannot be relied on to stop at
        the end-of-archive marker either -- busybox tar blocks for EOF.

        Piping through ``head -c`` bounds the stream at the exact archive size,
        so tar sees a clean EOF, exits on its own, and the API server reports
        its exit status on the error channel. Only where the container has no
        shell do we fall back to feeding tar directly, which cannot confirm
        that the copy completed.
        """
        command = self.tar_command(dest_file)
        if not self.can_bound_stream():
            self.module.warn(
                "Container has no '{0}' with 'head', falling back to writing the"
                " archive straight to tar. The module cannot confirm the copy"
                " completed; verify the file after copying.".format(self.SHELL)
            )
            return command, False

        return [
            self.SHELL,
            "-c",
            "head -c {0} | {1}".format(
                archive_size, " ".join(shlex.quote(arg) for arg in command)
            ),
        ], True

    def _stream_tar_to_pod(self, response, tar_buffer, wait_for_exit):
        """Feed the archive to the remote extractor and wait for it to finish.

        Writing the last chunk only hands the bytes to the local socket; they
        still have to cross the API server and reach the container. Closing the
        connection at that point kills the extractor mid-write and silently
        truncates the file, which is what issue #776 reports.
        """
        stdout, stderr = [], []

        def drain(timeout):
            response.update(timeout=timeout)
            if response.peek_stdout():
                stdout.append(response.read_stdout().rstrip("\n"))
            if response.peek_stderr():
                stderr.append(response.read_stderr().rstrip("\n"))

        deadline = time.monotonic() + self.copy_timeout

        chunk = tar_buffer.read(self.CHUNK_SIZE)
        while chunk:
            if not response.is_open():
                self._fail(
                    response,
                    "connection to Pod {0}/{1} closed before the whole archive was"
                    " sent, the remote file is incomplete".format(
                        self.namespace, self.name
                    ),
                    stderr,
                )
            if time.monotonic() > deadline:
                self._fail(
                    response,
                    "timed out after {0}s sending the archive to Pod {1}/{2}".format(
                        self.copy_timeout, self.namespace, self.name
                    ),
                    stderr,
                )
            # Non-blocking, keeps the receive buffer clear while we write.
            drain(0)
            response.write_stdin(chunk)
            chunk = tar_buffer.read(self.CHUNK_SIZE)

        if not wait_for_exit:
            # No way to make the extractor exit, so no status to collect: read
            # whatever it has already said and close, as the module always did.
            drain(0)
            response.close()
            return None, stdout, stderr

        # The archive is on the wire; wait for the extractor to consume it,
        # exit, and have its status reported on the error channel.
        while response.is_open():
            if time.monotonic() > deadline:
                self._fail(
                    response,
                    "timed out after {0}s waiting for tar to finish extracting on Pod"
                    " {1}/{2}".format(self.copy_timeout, self.namespace, self.name),
                    stderr,
                )
            drain(1)

        error = yaml.safe_load(response.read_channel(ERROR_CHANNEL)) or {}
        response.close()
        return error, stdout, stderr

    def run(self):
        # remove trailing slash from destination path
        dest_file = self.remote_path.rstrip("/")
        src_file = self.local_path
        self.named_temp_file = None
        if self.content:
            self.named_temp_file = NamedTemporaryFile(mode="w")
            self.named_temp_file.write(self.content)
            self.named_temp_file.flush()
            src_file = self.named_temp_file.name
        else:
            if not os.path.exists(self.local_path):
                self.module.fail_json(
                    msg="{0} does not exist in local filesystem".format(self.local_path)
                )
            if not os.access(self.local_path, os.R_OK):
                self.module.fail_json(msg="{0} not readable".format(self.local_path))

        is_dir, err = self.is_directory_path_from_pod(
            self.remote_path, failed_if_not_exists=False
        )
        if err:
            self.module.fail_json(msg=err)
        if is_dir:
            if self.content:
                self.module.fail_json(
                    msg="When content is specified, remote path should not be an existing directory"
                )
            else:
                dest_file = os.path.join(dest_file, os.path.basename(src_file))

        if not self.check_mode:
            with TemporaryFile() as tar_buffer:
                # Build the archive first: bounding the remote read needs its
                # exact size.
                with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
                    tar.add(src_file, dest_file)
                archive_size = tar_buffer.tell()
                tar_buffer.seek(0)

                command, wait_for_exit = self.remote_command(dest_file, archive_size)
                response = stream(
                    self.api_instance.connect_get_namespaced_pod_exec,
                    self.name,
                    self.namespace,
                    command=command,
                    stderr=True,
                    stdin=True,
                    stdout=True,
                    tty=False,
                    _preload_content=False,
                    **self.container_arg,
                )
                error, stdout, stderr = self._stream_tar_to_pod(
                    response, tar_buffer, wait_for_exit
                )

            if error is not None and error.get("status") != "Success":
                self._fail(
                    response,
                    "".join(stderr) or error.get("message", "unknown error"),
                    command=command,
                )
            if error is None and stderr:
                # Legacy path: no exit status to go on, so any output is fatal.
                self._fail(response, "".join(stderr), command=command)
            if stderr:
                self.module.warn(
                    "tar wrote to stderr while extracting into Pod {0}/{1}: {2}".format(
                        self.namespace, self.name, "".join(stderr)
                    )
                )
            self.close_temp_file()
        if self.content:
            self.module.exit_json(
                changed=True,
                result="Content successfully copied into {0} on remote Pod".format(
                    self.remote_path
                ),
            )
        self.module.exit_json(
            changed=True,
            result="{0} successfully copied into remote Pod into {1}".format(
                self.local_path, self.remote_path
            ),
        )


def check_pod(svc):
    module = svc.module
    namespace = module.params.get("namespace")
    name = module.params.get("pod")
    container = module.params.get("container")

    try:
        resource = svc.find_resource("Pod", None, True)
    except CoreException as e:
        module.fail_json(msg=to_native(e))

    def _fail(exc):
        arg = {}
        if hasattr(exc, "body"):
            msg = (
                "Namespace={0} Kind=Pod Name={1}: Failed requested object: {2}".format(
                    namespace, name, exc.body
                )
            )
        else:
            msg = to_native(exc)
        for attr in ["status", "reason"]:
            if hasattr(exc, attr):
                arg[attr] = getattr(exc, attr)
        module.fail_json(msg=msg, **arg)

    try:
        result = svc.client.get(resource, name=name, namespace=namespace)
        containers = dict(
            {
                c["name"]: c
                for cl in ["initContainerStatuses", "containerStatuses"]
                for c in result.to_dict()["status"].get(cl, [])
            }
        )
        if container and container not in containers.keys():
            module.fail_json(msg="Pod has no container {0}".format(container))
        if (
            container
            and container in containers
            and not bool(containers[container].get("started", False))
        ):
            module.fail_json(msg="Pod container {0} is not started".format(container))
        return containers.keys()
    except Exception as exc:
        _fail(exc)
