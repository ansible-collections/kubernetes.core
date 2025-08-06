from __future__ import absolute_import, division, print_function

import copy

from ansible.module_utils.six import string_types

__metaclass__ = type

# Define sensitive fields that should be hidden in kubeconfig
SENSITIVE_USER_FIELDS = {
    "token",
    "password",
    "client-certificate-data",
    "client-key-data",
    "refresh-token",
    "id-token",
    "access-token",
}

SENSITIVE_CLUSTER_FIELDS = {"certificate-authority-data"}


def sanitize_kubeconfig_for_logging(kubeconfig):
    """
    Sanitize kubeconfig for logging purposes.
    Removes sensitive fields while preserving structure for debugging.

    Args:
        kubeconfig (str|dict): The kubeconfig to sanitize

    Returns:
        str|dict: Sanitized version safe for logging
    """
    if not kubeconfig:
        return kubeconfig

    if isinstance(kubeconfig, string_types):
        # For file paths, show just the path (which is not sensitive)
        return kubeconfig

    if not isinstance(kubeconfig, dict):
        return "**UNSUPPORTED_TYPE**"

    # Create a deep copy to avoid modifying the original
    sanitized = copy.deepcopy(kubeconfig)

    # Sanitize users section
    if "users" in sanitized:
        for user in sanitized["users"]:
            if "user" in user:
                for field in SENSITIVE_USER_FIELDS:
                    if field in user["user"]:
                        user["user"][field] = "**HIDDEN**"

    # Sanitize clusters section
    if "clusters" in sanitized:
        for cluster in sanitized["clusters"]:
            if "cluster" in cluster:
                for field in SENSITIVE_CLUSTER_FIELDS:
                    if field in cluster["cluster"]:
                        cluster["cluster"][field] = "**HIDDEN**"

    return sanitized


def sanitize_module_return_value(result):
    """
    Sanitize module return values to remove sensitive kubeconfig data.

    Args:
        result (dict): Module result dictionary

    Returns:
        dict: Sanitized result dictionary
    """
    if not isinstance(result, dict):
        return result

    # Create a copy to avoid modifying the original
    sanitized_result = copy.deepcopy(result)

    # Look for kubeconfig in invocation arguments
    if "invocation" in sanitized_result and isinstance(
        sanitized_result["invocation"], dict
    ):
        invocation = sanitized_result["invocation"]

        # Check module_args
        if "module_args" in invocation and isinstance(invocation["module_args"], dict):
            if "kubeconfig" in invocation["module_args"]:
                invocation["module_args"][
                    "kubeconfig"
                ] = sanitize_kubeconfig_for_logging(
                    invocation["module_args"]["kubeconfig"]
                )

        # Check direct args
        if "kubeconfig" in invocation:
            invocation["kubeconfig"] = sanitize_kubeconfig_for_logging(
                invocation["kubeconfig"]
            )

    return sanitized_result


def sanitize_kubeconfig_dict(kubeconfig_dict):
    """
    Sanitize a kubeconfig dictionary by replacing sensitive values.
    This is for situations where the kubeconfig needs to be processed
    but sensitive data should be removed first.

    Args:
        kubeconfig_dict (dict): The kubeconfig dictionary

    Returns:
        dict: Sanitized kubeconfig dictionary
    """
    if not isinstance(kubeconfig_dict, dict):
        return kubeconfig_dict

    return sanitize_kubeconfig_for_logging(kubeconfig_dict)
