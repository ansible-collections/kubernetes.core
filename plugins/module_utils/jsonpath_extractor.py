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

from ansible.module_utils._text import to_native


class JsonPathException(Exception):
    """ Error while parsing Json path structure """


def find_element(value, start):
    dot_idx = value.find(".", start)
    end = dot_idx if dot_idx != -1 else len(value)
    arr_idx = value.find("[", start, end)

    if dot_idx == -1 and arr_idx == -1:
        # last element of the json path
        if value[start] == '[':
            raise JsonPathException("unable to find array end string for array starting at index {0} '{1}'".format(start, value[start:]))
        return value[start:], None

    elif arr_idx != -1:
        if arr_idx == start:
            # array element (ex: "[0]" or "[*].ready" or "[*][0].ready" )
            arr_end = value.find("]", arr_idx)
            if arr_end == -1:
                raise JsonPathException("unable to find array end string for array starting at index {0} '{1}'".format(arr_idx, value[arr_idx:]))
            data = value[arr_idx + 1:arr_end]
            if data != "*" and not data.isnumeric():
                raise JsonPathException("wrong value specified into array starting at index {0} => '{1}'".format(arr_idx, data))
            return int(data) if data != "*" else -1, arr_end + 1 if arr_end < len(value) - 1 else None
        elif arr_idx > start:
            # single value found (ex: "containers[0]")
            return value[start:arr_idx], arr_idx

    else:  # dot_idx != -1
        return value[start:dot_idx], dot_idx + 1


def parse(expr):
    result = []
    if expr[0] == ".":
        expr = expr[1:]
    start = 0
    while start is not None:
        elt, next = find_element(expr, start)
        if elt == '':
            if not isinstance(result[-1], int):
                raise JsonPathException("empty element following non array element at index {0} '{1}'".format(start, expr[start:]))
        else:
            result.append(elt)
        start = next
    return result


def search_json_item(jsonpath_expr, json_doc):
    json_idx = 0
    json_item = jsonpath_expr[json_idx]
    if isinstance(json_item, int):
        if not isinstance(json_doc, list):
            # trying to parse list items, but current document is not a list
            return None
        elements = json_doc
        if json_item != -1:
            # looking for specific index from the list
            if json_item >= len(json_doc):
                return None
            else:
                elements = json_doc[json_item]

        # when we reach the end of the json path
        if len(jsonpath_expr) == 1:
            return elements
        elif json_item != -1 and (isinstance(elements, dict) or isinstance(elements, list)):
            return search_json_item(jsonpath_expr[1:], elements)
        elif json_item == -1:
            result = []
            for elt in elements:
                ret = search_json_item(jsonpath_expr[1:], elt)
                if ret is not None:
                    result.append(ret)
            return result if result != [] else None
    else:
        # looking for a specific field into the json document
        if not isinstance(json_doc, dict):
            return None
        if json_item not in json_doc:
            return None
        if len(jsonpath_expr) == 1:
            return json_doc.get(json_item)
        else:
            return search_json_item(jsonpath_expr[1:], json_doc.get(json_item))


def search(expr, data):
    jsonpath_expr = parse(expr)
    return search_json_item(jsonpath_expr, data)


def validate_with_jsonpath(module, data, expr, value=None):
    def _raise_or_fail(err, **kwargs):
        if module and hasattr(module, "fail_json"):
            module.fail_json(error=to_native(err), **kwargs)
        raise err

    def _match_value(buf, v):
        if isinstance(buf, list):
            # convert all values from bool to str and lowercase them
            return all([str(i).lower() == v.lower() for i in buf])
        elif isinstance(buf, str):
            return v.lower() == content.lower()
        elif isinstance(buf, bool):
            return v.lower() == str(content).lower()
        else:
            # unable to test single value against dict
            return False

    try:
        content = search(expr, data)
        if content is None or content == []:
            return False
        if value is None or _match_value(content, value):
            # looking for state present
            return True
        return False
    except Exception as err:
        _raise_or_fail(err, msg="Failed to extract path from Json: {0}".format(expr))
