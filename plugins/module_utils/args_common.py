from __future__ import absolute_import, division, print_function

import copy

from ansible.module_utils.six import string_types

__metaclass__ = type


def list_dict_str(value):
    if isinstance(value, (list, dict, string_types)):
        return value
    raise TypeError


def sanitize_kubeconfig_for_logging(kubeconfig):
    """
    Sanitize a kubeconfig dictionary by removing sensitive fields for logging purposes.

    This function creates a copy of the kubeconfig and replaces sensitive values
    with placeholder text to prevent credential exposure in logs.

    User-level sensitive fields:
    - token, password, client-certificate-data, client-key-data
    - refresh-token, id-token, access-token

    Cluster-level sensitive fields:
    - certificate-authority-data

    Args:
        kubeconfig: The kubeconfig dictionary to sanitize

    Returns:
        A sanitized copy of the kubeconfig dictionary safe for logging
    """
    if not isinstance(kubeconfig, dict):
        return kubeconfig

    # Create a deep copy to avoid modifying the original
    sanitized = copy.deepcopy(kubeconfig)

    # Define sensitive field names and their replacements
    sensitive_fields = {
        "token": "***TOKEN***",
        "password": "***PASSWORD***",
        "client-certificate-data": "***CLIENT_CERT_DATA***",
        "client-key-data": "***CLIENT_KEY_DATA***",
        "refresh-token": "***REFRESH_TOKEN***",
        "id-token": "***ID_TOKEN***",
        "access-token": "***ACCESS_TOKEN***",
        "certificate-authority-data": "***CA_CERT_DATA***",
        "client-secret": "***CLIENT_SECRET***",
    }

    def _sanitize_dict(data):
        """Recursively sanitize dictionary values"""
        if isinstance(data, dict):
            for key, value in data.items():
                if key in sensitive_fields:
                    data[key] = sensitive_fields[key]
                elif isinstance(value, (dict, list)):
                    _sanitize_dict(value)
        elif isinstance(data, list):
            for item in data:
                _sanitize_dict(item)

    _sanitize_dict(sanitized)
    return sanitized


AUTH_PROXY_HEADERS_SPEC = dict(
    proxy_basic_auth=dict(type="str", no_log=True),
    basic_auth=dict(type="str", no_log=True),
    user_agent=dict(type="str"),
)

AUTH_ARG_SPEC = {
    "kubeconfig": {"type": "raw"},
    "context": {},
    "host": {},
    "api_key": {"no_log": True},
    "username": {},
    "password": {"no_log": True},
    "validate_certs": {"type": "bool", "aliases": ["verify_ssl"]},
    "ca_cert": {"type": "path", "aliases": ["ssl_ca_cert"]},
    "client_cert": {"type": "path", "aliases": ["cert_file"]},
    "client_key": {"type": "path", "aliases": ["key_file"]},
    "proxy": {"type": "str"},
    "no_proxy": {"type": "str"},
    "proxy_headers": {"type": "dict", "options": AUTH_PROXY_HEADERS_SPEC},
    "persist_config": {"type": "bool"},
    "impersonate_user": {},
    "impersonate_groups": {"type": "list", "elements": "str"},
}

WAIT_ARG_SPEC = dict(
    wait=dict(type="bool", default=False),
    wait_sleep=dict(type="int", default=5),
    wait_timeout=dict(type="int", default=120),
    wait_condition=dict(
        type="dict",
        default=None,
        options=dict(
            type=dict(),
            status=dict(default=True, choices=[True, False, "Unknown"]),
            reason=dict(),
        ),
    ),
)

# Map kubernetes-client parameters to ansible parameters
AUTH_ARG_MAP = {
    "kubeconfig": "kubeconfig",
    "context": "context",
    "host": "host",
    "api_key": "api_key",
    "username": "username",
    "password": "password",
    "verify_ssl": "validate_certs",
    "ssl_ca_cert": "ca_cert",
    "cert_file": "client_cert",
    "key_file": "client_key",
    "proxy": "proxy",
    "no_proxy": "no_proxy",
    "proxy_headers": "proxy_headers",
    "persist_config": "persist_config",
}

NAME_ARG_SPEC = {
    "kind": {},
    "name": {},
    "namespace": {},
    "api_version": {"default": "v1", "aliases": ["api", "version"]},
}

COMMON_ARG_SPEC = {
    "state": {"default": "present", "choices": ["present", "absent"]},
    "force": {"type": "bool", "default": False},
}

RESOURCE_ARG_SPEC = {
    "resource_definition": {"type": list_dict_str, "aliases": ["definition", "inline"]},
    "src": {"type": "path"},
}

ARG_ATTRIBUTES_BLACKLIST = ("property_path",)

DELETE_OPTS_ARG_SPEC = {
    "propagationPolicy": {"choices": ["Foreground", "Background", "Orphan"]},
    "gracePeriodSeconds": {"type": "int"},
    "preconditions": {
        "type": "dict",
        "options": {"resourceVersion": {"type": "str"}, "uid": {"type": "str"}},
    },
}
