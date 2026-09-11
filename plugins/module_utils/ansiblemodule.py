from __future__ import absolute_import, division, print_function

__metaclass__ = type


import os

from ansible.module_utils.common.validation import check_type_bool

try:
    enable_turbo_mode = check_type_bool(os.environ.get("ENABLE_TURBO_MODE"))
except TypeError:
    enable_turbo_mode = False

if enable_turbo_mode:
    try:
        from ansible_collections.cloud.common.plugins.module_utils.turbo.module import (
            AnsibleTurboModule as _BaseAnsibleModule,
        )

        _BaseAnsibleModule.collection_name = "kubernetes.core"
    except ImportError:
        from ansible.module_utils.basic import AnsibleModule as _BaseAnsibleModule

    class AnsibleModule(_BaseAnsibleModule):
        def __init__(self, *args, **kwargs):
            super(AnsibleModule, self).__init__(*args, **kwargs)
            self.deprecate(
                "ENABLE_TURBO_MODE is deprecated, as it relies on the cloud.common "
                "collection which is being retired. Setting this environment "
                "variable will have no effect once support is removed.",
                version="8.0.0",
                collection_name="kubernetes.core",
            )

else:
    from ansible.module_utils.basic import AnsibleModule  # noqa: F401
