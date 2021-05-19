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

import traceback
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils._text import to_native

try:
    import jmespath
    HAS_JMESPATH_LIB = True
    jmespath_import_exception = None
except ImportError as e:
    HAS_JMESPATH_LIB = False
    jmespath_import_exception = e
    JMESPATH_IMP_ERR = traceback.format_exc()


def match_json_property(module, data, expr, value=None):
    """
    This function uses jmespath to validate json data
    - module: running the function (used to fail in case of error)
    - data: JSON document
    - expr: Specify how to extract elements from a JSON document (jmespath, http://jmespath.org)
    - value: the matching JSON element should have this value, if set to None this is ignored
    """
    def _raise_or_fail(err, **kwargs):
        if module and hasattr(module, "fail_json"):
            module.fail_json(error=to_native(err), **kwargs)
        raise err

    def _match_value(buf, v):
        # convert all values from bool to str and lowercase them
        return v.lower() in [str(i).lower() for i in buf]

    if not HAS_JMESPATH_LIB:
        _raise_or_fail(jmespath_import_exception, msg=missing_required_lib('jmespath'), exception=JMESPATH_IMP_ERR)

    jmespath.functions.REVERSE_TYPES_MAP['string'] = jmespath.functions.REVERSE_TYPES_MAP['string'] + ('AnsibleUnicode', 'AnsibleUnsafeText', )
    try:
        content = jmespath.search(expr, data)
        if not content:
            return False
        if not value or _match_value(content, value):
            return True
        return False
    except Exception as err:
        _raise_or_fail(err, msg="JMESPathError failed to extract from JSON document using expr: {}".format(expr))
