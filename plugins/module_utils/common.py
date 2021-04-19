# Copyright 2018 Red Hat | Ansible
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

import base64
import time
import os
import traceback
import sys
from datetime import datetime
from distutils.version import LooseVersion

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.six import iteritems, string_types
from ansible.module_utils._text import to_native, to_bytes, to_text
from ansible.module_utils.common.dict_transformations import dict_merge
from ansible.module_utils.parsing.convert_bool import boolean
from ansible_collections.community.kubernetes.plugins.module_utils.exceptions import K8sInventoryException


K8S_IMP_ERR = None
try:
    import kubernetes
    import openshift
    from openshift.dynamic import DynamicClient
    from openshift.dynamic.exceptions import (
        ResourceNotFoundError, ResourceNotUniqueError, NotFoundError, DynamicApiError,
        ConflictError, ForbiddenError, MethodNotAllowedError)
    HAS_K8S_MODULE_HELPER = True
    k8s_import_exception = None
except ImportError as e:
    HAS_K8S_MODULE_HELPER = False
    k8s_import_exception = e
    K8S_IMP_ERR = traceback.format_exc()

YAML_IMP_ERR = None
try:
    import yaml
    HAS_YAML = True
except ImportError:
    YAML_IMP_ERR = traceback.format_exc()
    HAS_YAML = False

K8S_CONFIG_HASH_IMP_ERR = None
try:
    from openshift.helper.hashes import generate_hash
    from openshift.dynamic.exceptions import KubernetesValidateMissing
    HAS_K8S_CONFIG_HASH = True
except ImportError:
    K8S_CONFIG_HASH_IMP_ERR = traceback.format_exc()
    HAS_K8S_CONFIG_HASH = False

HAS_K8S_APPLY = None
try:
    from openshift.dynamic.apply import apply_object
    HAS_K8S_APPLY = True
except ImportError:
    HAS_K8S_APPLY = False

try:
    import urllib3
    urllib3.disable_warnings()
except ImportError:
    pass

try:
    from openshift.dynamic.apply import recursive_diff
except ImportError:
    from ansible.module_utils.common.dict_transformations import recursive_diff

try:
    try:
        # >=0.10
        from openshift.dynamic.resource import ResourceInstance
    except ImportError:
        # <0.10
        from openshift.dynamic.client import ResourceInstance
    HAS_K8S_INSTANCE_HELPER = True
    k8s_import_exception = None
except ImportError as e:
    HAS_K8S_INSTANCE_HELPER = False
    k8s_import_exception = e
    K8S_IMP_ERR = traceback.format_exc()


def list_dict_str(value):
    if isinstance(value, (list, dict, string_types)):
        return value
    raise TypeError


ARG_ATTRIBUTES_BLACKLIST = ('property_path',)

COMMON_ARG_SPEC = {
    'state': {
        'default': 'present',
        'choices': ['present', 'absent'],
    },
    'force': {
        'type': 'bool',
        'default': False,
    },
}

RESOURCE_ARG_SPEC = {
    'resource_definition': {
        'type': list_dict_str,
        'aliases': ['definition', 'inline']
    },
    'src': {
        'type': 'path',
    },
}

NAME_ARG_SPEC = {
    'kind': {},
    'name': {},
    'namespace': {},
    'api_version': {
        'default': 'v1',
        'aliases': ['api', 'version'],
    },
}

AUTH_ARG_SPEC = {
    'kubeconfig': {
        'type': 'path',
    },
    'context': {},
    'host': {},
    'api_key': {
        'no_log': True,
    },
    'username': {},
    'password': {
        'no_log': True,
    },
    'validate_certs': {
        'type': 'bool',
        'aliases': ['verify_ssl'],
    },
    'ca_cert': {
        'type': 'path',
        'aliases': ['ssl_ca_cert'],
    },
    'client_cert': {
        'type': 'path',
        'aliases': ['cert_file'],
    },
    'client_key': {
        'type': 'path',
        'aliases': ['key_file'],
    },
    'proxy': {
        'type': 'str',
    },
    'persist_config': {
        'type': 'bool',
    },
}

WAIT_ARG_SPEC = dict(
    wait=dict(type='bool', default=False),
    wait_sleep=dict(type='int', default=5),
    wait_timeout=dict(type='int', default=120),
    wait_condition=dict(
        type='dict',
        default=None,
        options=dict(
            type=dict(),
            status=dict(type='str', default="True", choices=["True", "False", "Unknown"]),
            reason=dict()
        )
    )
)

DELETE_OPTS_ARG_SPEC = {
    'propagationPolicy': {
        'choices': ['Foreground', 'Background', 'Orphan'],
    },
    'gracePeriodSeconds': {
        'type': 'int',
    },
    'preconditions': {
        'type': 'dict',
        'options': {
            'resourceVersion': {
                'type': 'str',
            },
            'uid': {
                'type': 'str',
            }
        }
    }
}


# Map kubernetes-client parameters to ansible parameters
AUTH_ARG_MAP = {
    'kubeconfig': 'kubeconfig',
    'context': 'context',
    'host': 'host',
    'api_key': 'api_key',
    'username': 'username',
    'password': 'password',
    'verify_ssl': 'validate_certs',
    'ssl_ca_cert': 'ca_cert',
    'cert_file': 'client_cert',
    'key_file': 'client_key',
    'proxy': 'proxy',
    'persist_config': 'persist_config',
}


class K8sAnsibleMixin(object):

    def __init__(self, *args, **kwargs):
        if not HAS_K8S_MODULE_HELPER:
            self.fail_json(msg=missing_required_lib('openshift'), exception=K8S_IMP_ERR,
                           error=to_native(k8s_import_exception))
        self.openshift_version = openshift.__version__

        if not HAS_YAML:
            self.fail_json(msg=missing_required_lib("PyYAML"), exception=YAML_IMP_ERR)

    def get_api_client(self, **auth_params):
        auth_params = auth_params or getattr(self, 'params', {})
        auth = {}

        # If authorization variables aren't defined, look for them in environment variables
        for true_name, arg_name in AUTH_ARG_MAP.items():
            if auth_params.get(arg_name) is None:
                env_value = os.getenv('K8S_AUTH_{0}'.format(arg_name.upper()), None) or os.getenv('K8S_AUTH_{0}'.format(true_name.upper()), None)
                if env_value is not None:
                    if AUTH_ARG_SPEC[arg_name].get('type') == 'bool':
                        env_value = env_value.lower() not in ['0', 'false', 'no']
                    auth[true_name] = env_value
            else:
                auth[true_name] = auth_params[arg_name]

        def auth_set(*names):
            return all([auth.get(name) for name in names])

        if auth_set('username', 'password', 'host') or auth_set('api_key', 'host'):
            # We have enough in the parameters to authenticate, no need to load incluster or kubeconfig
            pass
        elif auth_set('kubeconfig') or auth_set('context'):
            try:
                kubernetes.config.load_kube_config(auth.get('kubeconfig'), auth.get('context'), persist_config=auth.get('persist_config'))
            except Exception as err:
                self.fail(msg='Failed to load kubeconfig due to %s' % to_native(err))
        else:
            # First try to do incluster config, then kubeconfig
            try:
                kubernetes.config.load_incluster_config()
            except kubernetes.config.ConfigException:
                try:
                    kubernetes.config.load_kube_config(auth.get('kubeconfig'), auth.get('context'), persist_config=auth.get('persist_config'))
                except Exception as err:
                    self.fail(msg='Failed to load kubeconfig due to %s' % to_native(err))

        # Override any values in the default configuration with Ansible parameters
        # As of kubernetes-client v12.0.0, get_default_copy() is required here
        try:
            configuration = kubernetes.client.Configuration().get_default_copy()
        except AttributeError:
            configuration = kubernetes.client.Configuration()

        for key, value in iteritems(auth):
            if key in AUTH_ARG_MAP.keys() and value is not None:
                if key == 'api_key':
                    setattr(configuration, key, {'authorization': "Bearer {0}".format(value)})
                else:
                    setattr(configuration, key, value)

        kubernetes.client.Configuration.set_default(configuration)
        try:
            return DynamicClient(kubernetes.client.ApiClient(configuration))
        except Exception as err:
            self.fail(msg='Failed to get client due to %s' % to_native(err))

    def find_resource(self, kind, api_version, fail=False):
        for attribute in ['kind', 'name', 'singular_name']:
            try:
                return self.client.resources.get(**{'api_version': api_version, attribute: kind})
            except (ResourceNotFoundError, ResourceNotUniqueError):
                pass
        try:
            return self.client.resources.get(api_version=api_version, short_names=[kind])
        except (ResourceNotFoundError, ResourceNotUniqueError):
            if fail:
                self.fail(msg='Failed to find exact match for {0}.{1} by [kind, name, singularName, shortNames]'.format(api_version, kind))

    def kubernetes_facts(self, kind, api_version, name=None, namespace=None, label_selectors=None, field_selectors=None,
                         wait=False, wait_sleep=5, wait_timeout=120, state='present', condition=None):
        resource = self.find_resource(kind, api_version)
        api_found = bool(resource)
        if not api_found:
            return dict(resources=[], msg='Failed to find API for resource with apiVersion "{0}" and kind "{1}"'.format(api_version, kind), api_found=False)

        if not label_selectors:
            label_selectors = []
        if not field_selectors:
            field_selectors = []

        result = None
        try:
            result = resource.get(name=name, namespace=namespace,
                                  label_selector=','.join(label_selectors),
                                  field_selector=','.join(field_selectors))
        except openshift.dynamic.exceptions.BadRequestError:
            return dict(resources=[], api_found=True)
        except openshift.dynamic.exceptions.NotFoundError:
            if not wait or name is None:
                return dict(resources=[], api_found=True)

        if not wait:
            result = result.to_dict()
            if 'items' in result:
                return dict(resources=result['items'], api_found=True)
            return dict(resources=[result], api_found=True)

        start = datetime.now()

        def _elapsed():
            return (datetime.now() - start).seconds

        if result is None:
            while _elapsed() < wait_timeout:
                try:
                    result = resource.get(name=name, namespace=namespace,
                                          label_selector=','.join(label_selectors),
                                          field_selector=','.join(field_selectors))
                    break
                except NotFoundError:
                    pass
                time.sleep(wait_sleep)
            if result is None:
                return dict(resources=[], api_found=True)

        if isinstance(result, ResourceInstance):
            satisfied_by = []
            # We have a list of ResourceInstance
            resource_list = result.get('items', [])
            if not resource_list:
                resource_list = [result]

            for resource_instance in resource_list:
                success, res, duration = self.wait(resource, resource_instance,
                                                   sleep=wait_sleep, timeout=wait_timeout,
                                                   state=state, condition=condition)
                if not success:
                    self.fail(msg="Failed to gather information about %s(s) even"
                                  " after waiting for %s seconds" % (res.get('kind'), duration))
                satisfied_by.append(res)
            return dict(resources=satisfied_by, api_found=True)
        result = result.to_dict()

        if 'items' in result:
            return dict(resources=result['items'], api_found=True)
        return dict(resources=[result], api_found=True)

    def remove_aliases(self):
        """
        The helper doesn't know what to do with aliased keys
        """
        for k, v in iteritems(self.argspec):
            if 'aliases' in v:
                for alias in v['aliases']:
                    if alias in self.params:
                        self.params.pop(alias)

    def load_resource_definitions(self, src):
        """ Load the requested src path """
        result = None
        path = os.path.normpath(src)
        if not os.path.exists(path):
            self.fail(msg="Error accessing {0}. Does the file exist?".format(path))
        try:
            with open(path, 'r') as f:
                result = list(yaml.safe_load_all(f))
        except (IOError, yaml.YAMLError) as exc:
            self.fail(msg="Error loading resource_definition: {0}".format(exc))
        return result

    def diff_objects(self, existing, new):
        result = dict()
        diff = recursive_diff(existing, new)
        if not diff:
            return True, result

        result['before'] = diff[0]
        result['after'] = diff[1]

        # If only metadata.generation and metadata.resourceVersion changed, ignore it
        ignored_keys = set(['generation', 'resourceVersion'])

        if list(result['after'].keys()) != ['metadata'] or list(result['before'].keys()) != ['metadata']:
            return False, result

        if not set(result['after']['metadata'].keys()).issubset(ignored_keys):
            return False, result
        if not set(result['before']['metadata'].keys()).issubset(ignored_keys):
            return False, result

        if hasattr(self, 'warn'):
            self.warn('No meaningful diff was generated, but the API may not be idempotent (only metadata.generation or metadata.resourceVersion were changed)')

        return True, result

    def fail(self, msg=None):
        if hasattr(self, 'fail_json'):
            self.fail_json(msg=msg)
        raise K8sInventoryException(msg)

    def _wait_for(self, resource, name, namespace, predicate, sleep, timeout, state):
        start = datetime.now()

        def _wait_for_elapsed():
            return (datetime.now() - start).seconds

        response = None
        while _wait_for_elapsed() < timeout:
            try:
                response = resource.get(name=name, namespace=namespace)
                if predicate(response):
                    if response:
                        return True, response.to_dict(), _wait_for_elapsed()
                    return True, {}, _wait_for_elapsed()
                time.sleep(sleep)
            except NotFoundError:
                if state == 'absent':
                    return True, {}, _wait_for_elapsed()
        if response:
            response = response.to_dict()
        return False, response, _wait_for_elapsed()

    def wait(self, resource, definition, sleep, timeout, state='present', condition=None):

        def _deployment_ready(deployment):
            # FIXME: frustratingly bool(deployment.status) is True even if status is empty
            # Furthermore deployment.status.availableReplicas == deployment.status.replicas == None if status is empty
            # deployment.status.replicas is None is perfectly ok if desired replicas == 0
            # Scaling up means that we also need to check that we're not in a
            # situation where status.replicas == status.availableReplicas
            # but spec.replicas != status.replicas
            return (deployment.status
                    and deployment.spec.replicas == (deployment.status.replicas or 0)
                    and deployment.status.availableReplicas == deployment.status.replicas
                    and deployment.status.observedGeneration == deployment.metadata.generation
                    and not deployment.status.unavailableReplicas)

        def _pod_ready(pod):
            return (pod.status and pod.status.containerStatuses is not None
                    and all([container.ready for container in pod.status.containerStatuses]))

        def _daemonset_ready(daemonset):
            return (daemonset.status and daemonset.status.desiredNumberScheduled is not None
                    and daemonset.status.numberReady == daemonset.status.desiredNumberScheduled
                    and daemonset.status.observedGeneration == daemonset.metadata.generation
                    and not daemonset.status.unavailableReplicas)

        def _custom_condition(resource):
            if not resource.status or not resource.status.conditions:
                return False
            match = [x for x in resource.status.conditions if x.type == condition['type']]
            if not match:
                return False
            # There should never be more than one condition of a specific type
            match = match[0]
            if match.status == 'Unknown':
                if match.status == condition['status']:
                    if 'reason' not in condition:
                        return True
                    if condition['reason']:
                        return match.reason == condition['reason']
                return False
            status = True if match.status == 'True' else False
            if status == boolean(condition['status'], strict=False):
                if condition.get('reason'):
                    return match.reason == condition['reason']
                return True
            return False

        def _resource_absent(resource):
            return not resource

        waiter = dict(
            Deployment=_deployment_ready,
            DaemonSet=_daemonset_ready,
            Pod=_pod_ready
        )
        kind = definition['kind']
        if state == 'present' and not condition:
            predicate = waiter.get(kind, lambda x: x)
        elif state == 'present' and condition:
            predicate = _custom_condition
        else:
            predicate = _resource_absent
        return self._wait_for(resource, definition['metadata']['name'], definition['metadata'].get('namespace'), predicate, sleep, timeout, state)

    def set_resource_definitions(self):
        resource_definition = self.params.get('resource_definition')

        self.resource_definitions = []

        if resource_definition:
            if isinstance(resource_definition, string_types):
                try:
                    self.resource_definitions = yaml.safe_load_all(resource_definition)
                except (IOError, yaml.YAMLError) as exc:
                    self.fail(msg="Error loading resource_definition: {0}".format(exc))
            elif isinstance(resource_definition, list):
                self.resource_definitions = resource_definition
            else:
                self.resource_definitions = [resource_definition]

        src = self.params.get('src')
        if src:
            self.resource_definitions = self.load_resource_definitions(src)
        try:
            self.resource_definitions = [item for item in self.resource_definitions if item]
        except AttributeError:
            pass

        if not resource_definition and not src:
            implicit_definition = dict(
                kind=self.kind,
                apiVersion=self.api_version,
                metadata=dict(name=self.name)
            )
            if self.namespace:
                implicit_definition['metadata']['namespace'] = self.namespace
            self.resource_definitions = [implicit_definition]

    def check_library_version(self):
        validate = self.params.get('validate')
        if validate and LooseVersion(self.openshift_version) < LooseVersion("0.8.0"):
            self.fail_json(msg="openshift >= 0.8.0 is required for validate")
        self.append_hash = self.params.get('append_hash')
        if self.append_hash and not HAS_K8S_CONFIG_HASH:
            self.fail_json(msg=missing_required_lib("openshift >= 0.7.2", reason="for append_hash"),
                           exception=K8S_CONFIG_HASH_IMP_ERR)
        if self.params['merge_type'] and LooseVersion(self.openshift_version) < LooseVersion("0.6.2"):
            self.fail_json(msg=missing_required_lib("openshift >= 0.6.2", reason="for merge_type"))
        self.apply = self.params.get('apply', False)
        if self.apply and not HAS_K8S_APPLY:
            self.fail_json(msg=missing_required_lib("openshift >= 0.9.2", reason="for apply"))
        wait = self.params.get('wait', False)
        if wait and not HAS_K8S_INSTANCE_HELPER:
            self.fail_json(msg=missing_required_lib("openshift >= 0.4.0", reason="for wait"))

    def flatten_list_kind(self, list_resource, definitions):
        flattened = []
        parent_api_version = list_resource.group_version if list_resource else None
        parent_kind = list_resource.kind[:-4] if list_resource else None
        for definition in definitions.get('items', []):
            resource = self.find_resource(definition.get('kind', parent_kind), definition.get('apiVersion', parent_api_version), fail=True)
            flattened.append((resource, self.set_defaults(resource, definition)))
        return flattened

    def execute_module(self):
        changed = False
        results = []
        try:
            self.client = self.get_api_client()
        # Hopefully the kubernetes client will provide its own exception class one day
        except (urllib3.exceptions.RequestError) as e:
            self.fail_json(msg="Couldn't connect to Kubernetes: %s" % str(e))

        flattened_definitions = []
        for definition in self.resource_definitions:
            if definition is None:
                continue
            kind = definition.get('kind', self.kind)
            api_version = definition.get('apiVersion', self.api_version)
            if kind and kind.endswith('List'):
                resource = self.find_resource(kind, api_version, fail=False)
                flattened_definitions.extend(self.flatten_list_kind(resource, definition))
            else:
                resource = self.find_resource(kind, api_version, fail=True)
                flattened_definitions.append((resource, definition))

        for (resource, definition) in flattened_definitions:
            kind = definition.get('kind', self.kind)
            api_version = definition.get('apiVersion', self.api_version)
            definition = self.set_defaults(resource, definition)
            self.warnings = []
            if self.params['validate'] is not None:
                self.warnings = self.validate(definition)
            result = self.perform_action(resource, definition)
            result['warnings'] = self.warnings
            changed = changed or result['changed']
            results.append(result)

        if len(results) == 1:
            self.exit_json(**results[0])

        self.exit_json(**{
            'changed': changed,
            'result': {
                'results': results
            }
        })

    def validate(self, resource):
        def _prepend_resource_info(resource, msg):
            return "%s %s: %s" % (resource['kind'], resource['metadata']['name'], msg)

        try:
            warnings, errors = self.client.validate(resource, self.params['validate'].get('version'), self.params['validate'].get('strict'))
        except KubernetesValidateMissing:
            self.fail_json(msg="kubernetes-validate python library is required to validate resources")

        if errors and self.params['validate']['fail_on_error']:
            self.fail_json(msg="\n".join([_prepend_resource_info(resource, error) for error in errors]))
        else:
            return [_prepend_resource_info(resource, msg) for msg in warnings + errors]

    def set_defaults(self, resource, definition):
        definition['kind'] = resource.kind
        definition['apiVersion'] = resource.group_version
        metadata = definition.get('metadata', {})
        if self.name and not metadata.get('name'):
            metadata['name'] = self.name
        if resource.namespaced and self.namespace and not metadata.get('namespace'):
            metadata['namespace'] = self.namespace
        definition['metadata'] = metadata
        return definition

    def perform_action(self, resource, definition):
        delete_options = self.params.get('delete_options')
        result = {'changed': False, 'result': {}}
        state = self.params.get('state', None)
        force = self.params.get('force', False)
        name = definition['metadata'].get('name')
        namespace = definition['metadata'].get('namespace')
        existing = None
        wait = self.params.get('wait')
        wait_sleep = self.params.get('wait_sleep')
        wait_timeout = self.params.get('wait_timeout')
        wait_condition = None
        if self.params.get('wait_condition') and self.params['wait_condition'].get('type'):
            wait_condition = self.params['wait_condition']

        self.remove_aliases()

        try:
            # ignore append_hash for resources other than ConfigMap and Secret
            if self.append_hash and definition['kind'] in ['ConfigMap', 'Secret']:
                name = '%s-%s' % (name, generate_hash(definition))
                definition['metadata']['name'] = name
            params = dict(name=name)
            if namespace:
                params['namespace'] = namespace
            existing = resource.get(**params)
        except (NotFoundError, MethodNotAllowedError):
            # Remove traceback so that it doesn't show up in later failures
            try:
                sys.exc_clear()
            except AttributeError:
                # no sys.exc_clear on python3
                pass
        except ForbiddenError as exc:
            if definition['kind'] in ['Project', 'ProjectRequest'] and state != 'absent':
                return self.create_project_request(definition)
            self.fail_json(msg='Failed to retrieve requested object: {0}'.format(exc.body),
                           error=exc.status, status=exc.status, reason=exc.reason)
        except DynamicApiError as exc:
            self.fail_json(msg='Failed to retrieve requested object: {0}'.format(exc.body),
                           error=exc.status, status=exc.status, reason=exc.reason)
        except ValueError as value_exc:
            self.fail_json(msg='Failed to retrieve requested object: {0}'.format(to_native(value_exc)),
                           error='', status='', reason='')

        if state == 'absent':
            result['method'] = "delete"
            if not existing:
                # The object already does not exist
                return result
            else:
                # Delete the object
                result['changed'] = True
                if not self.check_mode:
                    if delete_options:
                        body = {
                            'apiVersion': 'v1',
                            'kind': 'DeleteOptions',
                        }
                        body.update(delete_options)
                        params['body'] = body
                    try:
                        k8s_obj = resource.delete(**params)
                        result['result'] = k8s_obj.to_dict()
                    except DynamicApiError as exc:
                        self.fail_json(msg="Failed to delete object: {0}".format(exc.body),
                                       error=exc.status, status=exc.status, reason=exc.reason)
                    if wait:
                        success, resource, duration = self.wait(resource, definition, wait_sleep, wait_timeout, 'absent')
                        result['duration'] = duration
                        if not success:
                            self.fail_json(msg="Resource deletion timed out", **result)
                return result
        else:
            if self.apply:
                if self.check_mode:
                    ignored, patch = apply_object(resource, _encode_stringdata(definition))
                    if existing:
                        k8s_obj = dict_merge(existing.to_dict(), patch)
                    else:
                        k8s_obj = patch
                else:
                    try:
                        k8s_obj = resource.apply(definition, namespace=namespace).to_dict()
                    except DynamicApiError as exc:
                        msg = "Failed to apply object: {0}".format(exc.body)
                        if self.warnings:
                            msg += "\n" + "\n    ".join(self.warnings)
                        self.fail_json(msg=msg, error=exc.status, status=exc.status, reason=exc.reason)
                success = True
                result['result'] = k8s_obj
                if wait and not self.check_mode:
                    success, result['result'], result['duration'] = self.wait(resource, definition, wait_sleep, wait_timeout, condition=wait_condition)
                if existing:
                    existing = existing.to_dict()
                else:
                    existing = {}
                match, diffs = self.diff_objects(existing, result['result'])
                result['changed'] = not match
                result['diff'] = diffs
                result['method'] = 'apply'
                if not success:
                    self.fail_json(msg="Resource apply timed out", **result)
                return result

            if not existing:
                if self.check_mode:
                    k8s_obj = _encode_stringdata(definition)
                else:
                    try:
                        k8s_obj = resource.create(definition, namespace=namespace).to_dict()
                    except ConflictError:
                        # Some resources, like ProjectRequests, can't be created multiple times,
                        # because the resources that they create don't match their kind
                        # In this case we'll mark it as unchanged and warn the user
                        self.warn("{0} was not found, but creating it returned a 409 Conflict error. This can happen \
                                  if the resource you are creating does not directly create a resource of the same kind.".format(name))
                        return result
                    except DynamicApiError as exc:
                        msg = "Failed to create object: {0}".format(exc.body)
                        if self.warnings:
                            msg += "\n" + "\n    ".join(self.warnings)
                        self.fail_json(msg=msg, error=exc.status, status=exc.status, reason=exc.reason)
                    except Exception as exc:
                        msg = "Failed to create object: {0}".format(exc)
                        if self.warnings:
                            msg += "\n" + "\n    ".join(self.warnings)
                        self.fail_json(msg=msg, error='', status='', reason='')
                success = True
                result['result'] = k8s_obj
                if wait and not self.check_mode:
                    success, result['result'], result['duration'] = self.wait(resource, definition, wait_sleep, wait_timeout, condition=wait_condition)
                result['changed'] = True
                result['method'] = 'create'
                if not success:
                    self.fail_json(msg="Resource creation timed out", **result)
                return result

            match = False
            diffs = []

            if existing and force:
                if self.check_mode:
                    k8s_obj = _encode_stringdata(definition)
                else:
                    try:
                        k8s_obj = resource.replace(definition, name=name, namespace=namespace, append_hash=self.append_hash).to_dict()
                    except DynamicApiError as exc:
                        msg = "Failed to replace object: {0}".format(exc.body)
                        if self.warnings:
                            msg += "\n" + "\n    ".join(self.warnings)
                        self.fail_json(msg=msg, error=exc.status, status=exc.status, reason=exc.reason)
                match, diffs = self.diff_objects(existing.to_dict(), k8s_obj)
                success = True
                result['result'] = k8s_obj
                if wait and not self.check_mode:
                    success, result['result'], result['duration'] = self.wait(resource, definition, wait_sleep, wait_timeout, condition=wait_condition)
                match, diffs = self.diff_objects(existing.to_dict(), result['result'])
                result['changed'] = not match
                result['method'] = 'replace'
                result['diff'] = diffs
                if not success:
                    self.fail_json(msg="Resource replacement timed out", **result)
                return result

            # Differences exist between the existing obj and requested params
            if self.check_mode:
                k8s_obj = dict_merge(existing.to_dict(), _encode_stringdata(definition))
            else:
                if LooseVersion(self.openshift_version) < LooseVersion("0.6.2"):
                    k8s_obj, error = self.patch_resource(resource, definition, existing, name,
                                                         namespace)
                else:
                    for merge_type in self.params['merge_type'] or ['strategic-merge', 'merge']:
                        k8s_obj, error = self.patch_resource(resource, definition, existing, name,
                                                             namespace, merge_type=merge_type)
                        if not error:
                            break
                if error:
                    self.fail_json(**error)

            success = True
            result['result'] = k8s_obj
            if wait and not self.check_mode:
                success, result['result'], result['duration'] = self.wait(resource, definition, wait_sleep, wait_timeout, condition=wait_condition)
            match, diffs = self.diff_objects(existing.to_dict(), result['result'])
            result['changed'] = not match
            result['method'] = 'patch'
            result['diff'] = diffs

            if not success:
                self.fail_json(msg="Resource update timed out", **result)
            return result

    def patch_resource(self, resource, definition, existing, name, namespace, merge_type=None):
        try:
            params = dict(name=name, namespace=namespace)
            if merge_type:
                params['content_type'] = 'application/{0}-patch+json'.format(merge_type)
            k8s_obj = resource.patch(definition, **params).to_dict()
            match, diffs = self.diff_objects(existing.to_dict(), k8s_obj)
            error = {}
            return k8s_obj, {}
        except DynamicApiError as exc:
            msg = "Failed to patch object: {0}".format(exc.body)
            if self.warnings:
                msg += "\n" + "\n    ".join(self.warnings)
            error = dict(msg=msg, error=exc.status, status=exc.status, reason=exc.reason, warnings=self.warnings)
            return None, error
        except Exception as exc:
            msg = "Failed to patch object: {0}".format(exc)
            if self.warnings:
                msg += "\n" + "\n    ".join(self.warnings)
            error = dict(msg=msg, error=to_native(exc), status='', reason='', warnings=self.warnings)
            return None, error

    def create_project_request(self, definition):
        definition['kind'] = 'ProjectRequest'
        result = {'changed': False, 'result': {}}
        resource = self.find_resource('ProjectRequest', definition['apiVersion'], fail=True)
        if not self.check_mode:
            try:
                k8s_obj = resource.create(definition)
                result['result'] = k8s_obj.to_dict()
            except DynamicApiError as exc:
                self.fail_json(msg="Failed to create object: {0}".format(exc.body),
                               error=exc.status, status=exc.status, reason=exc.reason)
        result['changed'] = True
        result['method'] = 'create'
        return result


class KubernetesAnsibleModule(AnsibleModule, K8sAnsibleMixin):
    # NOTE: This class KubernetesAnsibleModule is deprecated in favor of
    #       class K8sAnsibleMixin and will be removed 2.0.0 release.
    #       Please use K8sAnsibleMixin instead.

    def __init__(self, *args, **kwargs):
        kwargs['argument_spec'] = self.argspec
        AnsibleModule.__init__(self, *args, **kwargs)
        K8sAnsibleMixin.__init__(self, *args, **kwargs)

        self.warn("class KubernetesAnsibleModule is deprecated"
                  " and will be removed in 2.0.0. Please use K8sAnsibleMixin instead.")


def _encode_stringdata(definition):
    if definition['kind'] == 'Secret' and 'stringData' in definition:
        for k, v in definition['stringData'].items():
            encoded = base64.b64encode(to_bytes(v))
            definition.setdefault('data', {})[k] = to_text(encoded)
        del definition['stringData']
    return definition
