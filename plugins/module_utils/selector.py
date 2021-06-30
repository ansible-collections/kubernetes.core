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


class Selector(object):

    def __init__(self, data):
        self._operator = None
        self._data = ''
        for sep in ('==', '!=', '='):
            pos = data.find(sep)
            if pos != -1:
                break
        if pos == -1:
            self._key = data
        else:
            self._key = data[0:pos]
            self._operator = sep
            self._data = data[pos + len(sep):]

    def isMatch(self, labels):
        if self._key not in labels:
            return False
        if self._operator in ('=', '=='):
            return self._data == labels.get(self._key)
        elif self._operator == '!=':
            print("'{}' and {} (differs)".format(self._data, labels.get(self._key)))
            return self._data != labels.get(self._key)
        # operator not defined
        return True


class LabelSelectorFilter(object):

    def __init__(self, label_selectors):
        self.selectors = [Selector(data) for data in label_selectors]

    def isMatching(self, definition):
        if "metadata" not in definition or "labels" not in definition['metadata']:
            return False
        labels = definition['metadata']['labels']
        if not isinstance(labels, dict):
            return None
        return all([sel.isMatch(labels) for sel in self.selectors])
