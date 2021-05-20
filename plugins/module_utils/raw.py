#
#  Copyright 2018 Red Hat | Ansible
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kubernetes.core.plugins.module_utils.common import (
    K8sAnsibleMixin, AUTH_ARG_SPEC, COMMON_ARG_SPEC, RESOURCE_ARG_SPEC, NAME_ARG_SPEC)


class KubernetesRawModule(K8sAnsibleMixin):
    # NOTE: This class KubernetesRawModule is deprecated in favor of
    #       class K8sAnsibleMixin and will be removed 2.0.0 release.
    #       Please use K8sAnsibleMixin instead.
    @property
    def validate_spec(self):
        return dict(
            fail_on_error=dict(type='bool'),
            version=dict(),
            strict=dict(type='bool', default=True)
        )

    @property
    def condition_spec(self):
        return dict(
            type=dict(),
            status=dict(default=True, choices=[True, False, "Unknown"]),
            reason=dict()
        )

    @property
    def argspec(self):
        argument_spec = copy.deepcopy(COMMON_ARG_SPEC)
        argument_spec.update(copy.deepcopy(NAME_ARG_SPEC))
        argument_spec.update(copy.deepcopy(RESOURCE_ARG_SPEC))
        argument_spec.update(copy.deepcopy(AUTH_ARG_SPEC))
        argument_spec['merge_type'] = dict(type='list', elements='str', choices=['json', 'merge', 'strategic-merge'])
        argument_spec['wait'] = dict(type='bool', default=False)
        argument_spec['wait_sleep'] = dict(type='int', default=5)
        argument_spec['wait_timeout'] = dict(type='int', default=120)
        argument_spec['wait_condition'] = dict(type='dict', default=None, options=self.condition_spec)
        argument_spec['validate'] = dict(type='dict', default=None, options=self.validate_spec)
        argument_spec['append_hash'] = dict(type='bool', default=False)
        argument_spec['apply'] = dict(type='bool', default=False)
        return argument_spec

    def __init__(self, k8s_kind=None, *args, **kwargs):
        mutually_exclusive = [
            ('resource_definition', 'src'),
            ('merge_type', 'apply'),
        ]

        module = AnsibleModule(
            argument_spec=self.argspec,
            mutually_exclusive=mutually_exclusive,
            supports_check_mode=True,
        )

        self.module = module
        self.check_mode = self.module.check_mode
        self.params = self.module.params
        self.fail_json = self.module.fail_json
        self.fail = self.module.fail_json
        self.exit_json = self.module.exit_json

        self.module.warn("class KubernetesRawModule is deprecated"
                         " and will be removed in 2.0.0. Please use K8sAnsibleMixin instead.")
        super(KubernetesRawModule, self).__init__(*args, **kwargs)

        self.client = None
        self.warnings = []

        self.kind = k8s_kind or self.params.get('kind')
        self.api_version = self.params.get('api_version')
        self.name = self.params.get('name')
        self.namespace = self.params.get('namespace')

        self.check_library_version()
        self.set_resource_definitions()
