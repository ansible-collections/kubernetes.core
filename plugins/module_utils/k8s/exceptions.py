# Copyright: (c) 2021, Red Hat | Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

try:
    from urllib3.exceptions import TimeoutError as _Urllib3TimeoutError
except ImportError:
    # Handled in module setup
    _Urllib3TimeoutError = ()


class CoreException(Exception):
    pass


class ResourceTimeout(CoreException):
    def __init__(self, message="", result=None):
        self.result = result or {}
        super().__init__(message)


def api_connection_error(error):
    """Build the CoreException for an urllib3 error raised while talking to the API server."""
    reason = getattr(error, "reason", None)
    if isinstance(error, _Urllib3TimeoutError) or isinstance(
        reason, _Urllib3TimeoutError
    ):
        msg = "Timed out waiting for the API server: {0}".format(error)
    else:
        msg = "Could not connect to the API server: {0}".format(error)
    return CoreException(msg)
