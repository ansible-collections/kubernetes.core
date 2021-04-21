# Copyright [2017] [Red Hat, Inc.]
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

from ansible.module_utils.six import PY3


def get_user():
    if hasattr(os, 'getlogin'):
        try:
            user = os.getlogin()
            if user:
                return str(user)
        except OSError:
            pass
    if hasattr(os, 'getuid'):
        try:
            user = os.getuid()
            if user:
                return str(user)
        except OSError:
            pass
    user = os.environ.get("USERNAME")
    if user:
        return str(user)
    return None


def get_default_cache_id(client):
    user = get_user()
    if user:
        cache_id = "{0}-{1}".format(client.configuration.host, user)
    else:
        cache_id = client.configuration.host

    if PY3:
        return cache_id.encode('utf-8')

    return cache_id
