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

import re


class Selector(object):

    equality_based_operators = ('==', '!=', '=')

    def __init__(self, data):
        self._operator = None
        self._data = ''
        self.define_set_based_requirement(data)
        if not self._set_based_requirement:
            self.define_equality_based_requirement(data)

    def define_set_based_requirement(self, data):
        self._set_based_requirement = False
        m = re.match(r'( *)([a-z0-9A-Z][a-z0-9A-Z\._-]*[a-z0-9A-Z])( *)(notin|in)( *)\((.*)\)( *)', data)
        if m:
            self._set_based_requirement = True
            self._key = m.group(2)
            self._operator = m.group(4)
            self._data = [x.replace(' ', '') for x in m.group(6).split(',') if x != '']
        elif all([x not in data for x in self.equality_based_operators]):
            self._set_based_requirement = True
            data = data.replace(" ", "")
            self._key = data
            if data.startswith("!"):
                self._key = data[1:]
                self._operator = "!"

    def define_equality_based_requirement(self, data):
        data_selector = data.replace(" ", "")
        for sep in self.equality_based_operators:
            pos = data_selector.find(sep)
            if pos != -1:
                break
        if pos == -1:
            self._key = data_selector
        else:
            self._key = data_selector[0:pos]
            self._operator = sep
            self._data = data_selector[pos + len(sep):]

    def filter_equality_based_requirement(self, labels):
        if self._key not in labels:
            return False
        if self._operator in ('=', '=='):
            return self._data == labels.get(self._key)
        elif self._operator == '!=':
            return self._data != labels.get(self._key)
        return True

    def filter_set_based_requirement(self, labels):
        if self._operator == "in":
            return self._key in labels and labels.get(self._key) in self._data
        elif self._operator == "notin":
            return self._key not in labels or labels.get(self._key) not in self._data
        else:
            return self._key not in labels if self._operator == "!" else self._key in labels

    def isMatch(self, labels):
        if self._set_based_requirement:
            return self.filter_set_based_requirement(labels)
        return self.filter_equality_based_requirement(labels)


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
