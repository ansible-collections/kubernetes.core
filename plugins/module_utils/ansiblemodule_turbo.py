from __future__ import (absolute_import, division, print_function)

__metaclass__ = type


try:
    from ansible_collections.cloud.common.plugins.module_utils.turbo.module import (
        AnsibleTurboModule as AnsibleModule,
    )  # noqa: F401
    AnsibleModule.collection_name = "community.kubernetes"
except (ImportError, ModuleNotFoundError):
    from ansible.module_utils.basic import AnsibleModule  # noqa: F401
from ansible.module_utils.basic import AnsibleModule  # noqa: F401
