from __future__ import absolute_import, division, print_function

__metaclass__ = type


import os

from ansible.module_utils.ansible_release import __version__ as ansible_version
from ansible.module_utils.common.validation import check_type_bool
from ansible.module_utils.common.warnings import deprecate, warn
from ansible_collections.kubernetes.core.plugins.module_utils.version import (
    LooseVersion,
)

# cloud.common declares requires_ansible '>=2.15.0,<2.19'. On newer ansible-core the
# import still succeeds, so the version has to be checked explicitly: relying on
# ImportError alone lets turbo mode fail later with an unrelated traceback.
TURBO_UNSUPPORTED_CORE = "2.19.0"

try:
    enable_turbo_mode = check_type_bool(os.environ.get("ENABLE_TURBO_MODE"))
except TypeError:
    enable_turbo_mode = False

if enable_turbo_mode:
    deprecate(
        "ENABLE_TURBO_MODE is deprecated, as it relies on the cloud.common collection "
        "which is being retired. Setting this environment variable will have no effect "
        "once support is removed.",
        version="8.0.0",
        collection_name="kubernetes.core",
    )
    if LooseVersion(ansible_version) >= LooseVersion(TURBO_UNSUPPORTED_CORE):
        warn(
            "ENABLE_TURBO_MODE is ignored on ansible-core %s: Ansible Turbo mode requires "
            "the cloud.common collection, which supports ansible-core < %s only. "
            "Continuing without Turbo mode." % (ansible_version, TURBO_UNSUPPORTED_CORE)
        )
        enable_turbo_mode = False

if enable_turbo_mode:
    try:
        from ansible_collections.cloud.common.plugins.module_utils.turbo.module import (  # noqa: F401
            AnsibleTurboModule as AnsibleModule,
        )

        AnsibleModule.collection_name = "kubernetes.core"
    except ImportError:
        warn(
            "ENABLE_TURBO_MODE is set but the cloud.common collection is not installed. "
            "Continuing without Turbo mode."
        )
        from ansible.module_utils.basic import AnsibleModule  # noqa: F401
else:
    from ansible.module_utils.basic import AnsibleModule  # noqa: F401
