#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2022, Aubin Bikouo <@abikouo>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""

module: k8s_secret

short_description: Create, update or delete a secret

version_added: "2.3.0"

author: Aubin Bikouo (@abikouo)

description:
  - Use Kubernetes Python SDK to create C(generic), C(tls), or C(docker-registry) secrets on Kubernetes.
  - Analogous to `kubectl create secret`.
  - A generic secret can be created using a file, directory, or specified literal value.
  - When creating a generic secret based on a file, the key will default to the basename of the file, and the value will default to
    the file content. If the basename is an invalid key or you wish to chose your own, you may specify an alternate key.
  - When creating a generic secret based on a directory, each file whose basename is a valid key in the directory will be packaged
    into the secret. Any directory entries except regular files are ignored (for example, subdirectories, symlinks, devices, pipes, and so on).
  - A TLS secret is created from a given public/private key pair.
    The public/private key pair must exist beforehand. The public key certificate must be .PEM encoded and match the given private key.
  - A C(docker-registry) secret is used to authenticate against Docker registries.

extends_documentation_fragment:
  - kubernetes.core.k8s_auth_options

options:
  state:
    description:
    - Determines if a secret should be created or deleted. When set to C(present), a secret will be
      created, if it does not already exist. If set to C(absent), an existing secret will be deleted.
    type: str
    default: present
    choices: [ absent, present ]
  force:
    description:
    - If set to C(yes), and I(state) is C(present), an existing secret will be replaced.
    type: bool
    default: false
  append_hash:
    description:
    - Append a hash of the secret to its name.
    type: bool
    default: false
  type:
    description:
    - Specifies the type of Secret to create.
    - When set to I(generic) one of C(literals) or C(from_path) should be set.
    - When set to I(docker-registry) one of C(docker-registry-credentials), C(literals) or C(from_path) should be set.
    - Ignored when C(state) is set to I(absent).
    - PyOpenSSL python library is required to create C(tls) secret.
    choices:
    - generic
    - docker-registry
    - tls
    type: str
    default: generic
  name:
    description:
      - Use to specify a Secret object name.
    required: true
    type: str
  namespace:
    description:
      - Use to specify a Secret object namespace.
    required: true
    type: str
  docker_registry_credentials:
    description:
      - Provide details for Docker registry authentication.
      - Ignores when C(type) is not set to I(docker-registry).
      - Required when C(type) is set to I(docker-registry).
    type: dict
    suboptions:
        server:
            description:
            - Server location for Docker registry.
            type: str
            required: true
        username:
            description:
            - Username for Docker registry authentication.
            type: str
            required: true
        password:
            description:
            - Password for Docker registry authentication.
            type: str
            required: true
        email:
            description:
            - Email for Docker registry.
            type: str
  from_path:
    description:
      - Specifies a file or directory defining key and value to insert in secret.
      - Key files can be specified using their file path, in which case a default name will be given to
        them, or a dictionary with a name and file path, in which case the given name will be used.
      - Specifying a directory will iterate each named file in the directory that is a valid secret key.
      - Ignored when C(type) is not set to I(generic).
    type: raw
  tls_certificate:
    description:
      - Provide TLS certificate along with the corresponding private key to create a new C(tls) secret.
      - Ignored when C(type) is not set to I(tls).
      - Required when C(type) is set to I(tls).
    type: dict
    suboptions:
        certificate:
            description:
            - Path to PEM encoded public key certificate.
            type: path
            required: true
        private_key:
            description:
            - Path to the private key associated with the given certificate.
            type: path
            required: true
  literals:
    description:
      - Dictionary of key and literal value to insert in secret data.
      - Ignored when C(type) is not set to I(generic).
    type: dict
  generic_secret_type:
    description:
      - Specifies the type of generic secret to create.
      - When set to I(kubernetes.io/service-account-token) you need to ensure that the C(annotations) contains
        key 'kubernetes.io/service-account.name' set to an existing service account name. The module may report that
        the secret has been created when the service account does not exist, but it is not.
      - Ignores when C(type) is not set to I(generic).
    type: str
    default: opaque
    choices:
    - opaque
    - kubernetes.io/service-account-token
    - kubernetes.io/dockerconfigjson
    - kubernetes.io/basic-auth
    - kubernetes.io/ssh-auth
    - bootstrap.kubernetes.io/token
  labels:
    description:
    - A dictionary of string keys and values is used as labels for the secret to be created.
    - see U(http://kubernetes.io/docs/user-guide/labels).
    - Ignored if C(state) is set to I(absent).
    type: dict
  annotations:
    description:
    - A dictionary of string keys and values is used as annotations for the secret to be created.
    - see U(http://kubernetes.io/docs/user-guide/annotations).
    - Ignored if C(state) is set to I(absent).
    type: dict

requirements:
  - python >= 3.6
  - kubernetes >= 12.0.0
  - PyOpenSSL
"""

EXAMPLES = r"""
- name: Create a generic secret with keys for each file in folder bar
  kubernetes.core.k8s_secret:
    name: my-secret
    namespace: my-secret-namespace
    from_path: path/to/bar

- name: Create a generic secret with specified keys instead of names on disk
  kubernetes.core.k8s_secret:
    name: my-secret
    namespace: my-secret-namespace
    from_path:
       name: ssh-privatekey
       path: path/to/id_rsa

- name: Create a generic secret with key1=supersecret and key2=topsecret
  kubernetes.core.k8s_secret:
    name: my-secret
    namespace: my-secret-namespace
    literals:
       key1: supersecret
       key2: topsecret

- name: Create a generic secret using a combination of a file and a literal
  kubernetes.core.k8s_secret:
    name: my-secret
    namespace: my-secret-namespace
    from_path:
       name: ssh-privatekey
       path: path/to/id_rsa
    literals:
        passphrase: topsecret

- name: Create a new TLS secret
  kubernetes.core.k8s_secret:
    name: my-tls-secret
    namespace: my-secret-namespace
    type: tls
    tls_certificate:
        certificate: path/to/tls.key
        private_key: path/to/tls.cert

- name: Create a Docker configuration secret
  kubernetes.core.k8s_secret:
    name: my-docker-secret
    namespace: my-secret-namespace
    type: docker-registry
    docker_registry_credentials:
        email: docker@ansible.com
        password: secret123
        username: admin
        server: my-private-registry.io

- name: Delete Secret
  kubernetes.core.k8s_secret:
    name: my-docker-secret
    namespace: my-secret-namespace
    state: absent

"""

RETURN = r"""
result:
  description:
  - The created or present Secret object. Will be empty in the case of a deletion.
  returned: success
  type: complex
  contains:
     api_version:
       description: The versioned schema of this representation of an object.
       returned: success
       type: str
     kind:
       description: Always 'Secret'.
       returned: success
       type: str
     metadata:
       description: Standard object metadata. Includes name, namespace, annotations, labels, etc.
       returned: success
       type: dict
     data:
       description: Encoded data of the secret.
       returned: success
       type: dict
     type:
       description: The type of secret. (e.g. kubernetes.io/service-account-token, kubernetes.io/dockerconfigjson, etc)
       returned: success
       type: str
"""

import copy
import os
import base64
import json
import re
import stat
import traceback

from ansible_collections.kubernetes.core.plugins.module_utils.ansiblemodule import (
    AnsibleModule,
)
from ansible_collections.kubernetes.core.plugins.module_utils.args_common import (
    AUTH_ARG_SPEC,
)
from ansible.module_utils.six import string_types
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils._text import to_native

try:
    from kubernetes.dynamic.exceptions import DynamicApiError
except ImportError:
    pass

try:
    from OpenSSL.crypto import (
        load_certificate,
        load_privatekey,
        dump_publickey,
        FILETYPE_PEM,
    )

    HAS_OPENSSL_MODULE = True
except ImportError as e:
    HAS_OPENSSL_MODULE = False
    openssl_import_exception = e
    IMPORT_OPENSSL_ERR = traceback.format_exc()


GENERIC_SECRET_TYPES = [
    "opaque",
    "kubernetes.io/service-account-token",
    "kubernetes.io/basic-auth",
    "kubernetes.io/ssh-auth",
    "bootstrap.kubernetes.io/token",
    "kubernetes.io/dockerconfigjson",
]

SECRET_ARG_SPEC = dict(
    state=dict(type="str", default="present", choices=["present", "absent"]),
    force=dict(type="bool", default=False),
    type=dict(
        type="str", default="generic", choices=["generic", "tls", "docker-registry"]
    ),
    name=dict(type="str", required=True),
    namespace=dict(type="str", required=True),
    from_path=dict(type="raw"),
    literals=dict(type="dict"),
    generic_secret_type=dict(
        type="str", default="opaque", choices=GENERIC_SECRET_TYPES
    ),
    append_hash=dict(type="bool", default=False),
    tls_certificate=dict(
        type="dict",
        options=dict(
            certificate=dict(type="path", required=True),
            private_key=dict(type="path", required=True),
        ),
    ),
    docker_registry_credentials=dict(
        type="dict",
        options=dict(
            server=dict(type="str", required=True),
            username=dict(type="str", required=True),
            password=dict(type="str", required=True, no_log=True),
            email=dict(type="str"),
        ),
    ),
    labels=dict(type="dict",),
    annotations=dict(type="dict",),
)


def argspec():
    args = copy.deepcopy(AUTH_ARG_SPEC)
    args.update(SECRET_ARG_SPEC)
    return args


def k8s_get_secret(name, namespace, k8s_ansible_mixin):
    params = dict(kind="Secret", api_version="v1", name=name, namespace=namespace)
    result = k8s_ansible_mixin.kubernetes_facts(**params)
    if len(result["resources"]) == 0:
        return None
    return result["resources"][0]


def is_valid_configmap_key(key):

    # DNS1123SubdomainMaxLength is a subdomain's max length in DNS (RFC 1123)
    if len(key) > 253:
        return "a valid config key must be no more than 253 characters"

    if not re.match(r"^[-._a-zA-Z0-9]+$", key):
        return "a valid config key must consist of alphanumeric characters, '-', '_' or '.'"

    if key in (".", ".."):
        return "a valid config key must not be '.' nor '..'"
    elif key.startswith(".."):
        return "a valid config key must not start with '..'"

    return None


def is_regular_file(path):
    """Returns true if the provided path is a regular file"""
    try:
        st = os.lstat(path)
        return stat.S_ISREG(st.st_mode)
    except OSError:
        return False


def is_private_key_matching_certificate(certificate_file, key_file):

    data = open(certificate_file).read()
    cert = load_certificate(FILETYPE_PEM, data)

    data = open(key_file).read()
    key = load_privatekey(FILETYPE_PEM, data)

    cert_pub = dump_publickey(FILETYPE_PEM, cert.get_pubkey())
    key_pub = dump_publickey(FILETYPE_PEM, key)
    return cert_pub == key_pub


def valide_secret_required_fields(definition):

    data = definition.get("data", {})
    error = None
    if definition["type"] == "kubernetes.io/basic-auth":
        if "username" not in data and "password" not in data:
            error = "the data field of must contain one of the following keys 'username', 'password' when creating 'kubernetes.io/basic-auth' secret type."
    elif definition["type"] == "kubernetes.io/ssh-auth":
        if "ssh-privatekey" not in data:
            error = "the data field of must contain the following key 'ssh-privatekey' when creating 'kubernetes.io/ssh-auth' secret type."
    elif definition["type"] == "kubernetes.io/dockerconfigjson":
        if ".dockerconfigjson" not in data:
            error = "the data field of must contain the following key '.dockerconfigjson' when creating 'kubernetes.io/dockerconfigjson' secret type."
    return error


class K8SSecret(object):
    def __init__(self, module, k8s_mixin):

        self.check_mode = module.check_mode
        self.fail_json = module.fail_json
        self.exit_json = module.exit_json
        self.params = module.params

        self.name = module.params.get("name")
        self.namespace = module.params.get("namespace")
        self.type = module.params.get("type")
        self.force = module.params.get("force")
        self.append_hash = module.params.get("append_hash")

        self.resource = k8s_mixin.find_resource(
            kind="Secret", api_version="v1", fail=True
        )
        self.existing = k8s_get_secret(self.name, self.namespace, k8s_mixin)

    def read_file(self, key, path):
        path = os.path.normpath(path)
        if not os.path.exists(path):
            self.fail_json(msg="Error accessing %s. Does the file exist?" % path)
        try:
            data = None
            with open(path, "rb") as f:
                data = f.read()
            return data
        except Exception as exc:
            self.fail_json(msg="Error loading %s: %s" % (key, exc))

    def create_secret(self, definition, append_hash=None):
        k8s_obj = definition
        labels = self.params.get("labels")
        annotations = self.params.get("annotations")
        if labels:
            definition["metadata"]["labels"] = labels
        if definition["type"] == "kubernetes.io/service-account-token" and (
            not annotations or "kubernetes.io/service-account.name" not in annotations
        ):
            msg = "the kubernetes.io/service-account.name annotation is required to create 'kubernetes.io/service-account-token' secret type."
            self.fail_json(msg=msg)
        if annotations:
            definition["metadata"]["annotations"] = annotations

        err = valide_secret_required_fields(definition)
        if err:
            self.fail_json(msg=err)

        if not self.check_mode:
            try:
                if self.existing:
                    params = dict(
                        name=self.name,
                        namespace=self.namespace,
                        append_hash=append_hash,
                    )
                    k8s_obj = self.resource.replace(definition, **params).to_dict()
                else:
                    k8s_obj = self.resource.create(
                        definition, namespace=self.namespace
                    ).to_dict()
            except DynamicApiError as exc:
                msg = "Failed to create secret: {0}".format(exc.body)
                self.fail_json(msg=msg, status=exc.status, reason=exc.reason)
            except Exception as exc:
                msg = "Failed to create secret: {0}".format(exc)
                self.fail_json(msg=msg)
        self.exit_json(changed=True, result=k8s_obj)

    def create_tls_secret(self):

        if not HAS_OPENSSL_MODULE:
            self.fail_json(
                msg=missing_required_lib("PyOpenSSL"),
                exception=IMPORT_OPENSSL_ERR,
                error=to_native(openssl_import_exception),
            )

        tls_certificate = self.params.get("tls_certificate", {})
        cert_file = tls_certificate.get("certificate")
        key_file = tls_certificate.get("private_key")

        if not tls_certificate or not cert_file or not key_file:
            msg = "key and cert must be specified when creating tls secret."
            self.fail_json(msg=msg)

        # Read cert file
        cert_data = base64.b64encode(
            self.read_file(key="secret_cert_file", path=cert_file)
        )

        # Read key file
        key_data = base64.b64encode(
            self.read_file(key="secret_key_file", path=key_file)
        )

        if not self.check_mode:
            cert_data = cert_data.decode()
            key_data = key_data.decode()

        if not is_private_key_matching_certificate(cert_file, key_file):
            msg = "failed to load key pair tls: private key does not match public key."
            self.fail_json(msg=msg)

        definition = {
            "kind": "Secret",
            "apiVersion": "v1",
            "metadata": {"name": self.name, "namespace": self.namespace},
            "data": {"tls.crt": cert_data, "tls.key": key_data},
            "type": "kubernetes.io/tls",
        }

        self.create_secret(definition)

    def add_key_from_literal_to_secret(self, definition, key, value):
        err = is_valid_configmap_key(key)
        if err:
            self.fail_json(msg="%s is not valid key name for a Secret: %s" % (key, err))

        if key in definition["data"]:
            self.fail_json(
                "cannot add key %s, another key by that name already exists" % key
            )
        if isinstance(value, dict):
            value = json.dumps(value)
        definition["data"][key] = base64.b64encode(value.encode()).decode()

    def handle_secret_from_literals(self, definition):
        literals = self.params.get("literals")
        for key in literals:
            self.add_key_from_literal_to_secret(definition, key, literals.get(key))

    def handle_secret_from_path(self, definition):

        src = self.params.get("from_path")
        keys = []

        if isinstance(src, string_types):
            # either a file or a directory
            src = os.path.abspath(src)
            if not os.path.exists(src):
                self.fail_json(msg="the following path %s does not exist." % src)

            if os.path.isdir(src):
                for file in os.listdir(src):
                    source_path = os.path.join(src, file)
                    if is_regular_file(source_path):
                        keys.append(dict(name=file, value=open(source_path).read()))
            elif os.path.isfile(src):
                keys.append(dict(name=os.path.basename(src), value=open(src).read()))
            else:
                msg = "Error while reading from_path parameter - a file or directory expected when parameter is string"
                self.fail_json(msg=msg)

        elif isinstance(src, dict):
            name = src.get("name")
            path = src.get("path")

            if name is None or path is None:
                self.fail_json(
                    msg="name and path should be specified when defining from_path as dict."
                )

            src = os.path.abspath(path)
            if not os.path.isfile(src) or not os.path.exists(src):
                self.fail_json(
                    msg="the following path %s does not exist or is not a valid file."
                    % path
                )

            keys.append(dict(name=name, value=open(path).read()))
        else:
            msg = (
                "Error while reading from_path parameter - a string or dict expected, but got %s instead"
                % type(src)
            )
            self.fail_json(msg=msg)

        for item in keys:
            self.add_key_from_literal_to_secret(definition, item["name"], item["value"])

    def create_docker_secret(self):
        docker_registry_credentials = self.params.get("docker_registry_credentials")

        literals = self.params.get("literals")
        from_path = self.params.get("from_path")

        if (
            literals is None
            and from_path is None
            and docker_registry_credentials is None
        ):
            msg = "one of literals, from_path or docker_registry_credentials parameters is required to create docker-registry secret."
            self.fail_json(msg=msg)

        definition = {
            "kind": "Secret",
            "apiVersion": "v1",
            "metadata": {"name": self.name, "namespace": self.namespace},
            "data": {},
            "type": "kubernetes.io/dockerconfigjson",
        }

        if docker_registry_credentials:

            server = docker_registry_credentials.get("server")
            username = docker_registry_credentials.get("username")
            password = docker_registry_credentials.get("password")
            email = docker_registry_credentials.get("email")

            payload = {"auths": {server: {"username": username, "password": password}}}
            if email:
                payload["auths"][server]["email"] = email
            definition["data"][".dockerconfigjson"] = base64.b64encode(
                json.dumps(payload).encode()
            ).decode()

        self.create_secret(definition)

    def create_generic_secret(self):

        generic_secret_type = self.params.get("generic_secret_type")
        definition = {
            "kind": "Secret",
            "apiVersion": "v1",
            "metadata": {"name": self.name, "namespace": self.namespace},
            "data": {},
            "type": generic_secret_type,
        }

        literals = self.params.get("literals")
        from_path = self.params.get("from_path")

        if literals:
            self.handle_secret_from_literals(definition)
        if from_path:
            self.handle_secret_from_path(definition)

        self.create_secret(definition)

    def delete(self):

        if not self.existing:
            self.exit_json(
                changed=False,
                msg="The secret %s/%s does not exist." % (self.namespace, self.name),
            )

        # Delete existing secret
        if not self.check_mode:
            try:
                self.resource.delete(name=self.name, namespace=self.namespace)
            except DynamicApiError as exc:
                msg = "Failed to delete Secret Object %s/%s: %s" % (
                    self.namespace,
                    self.name,
                    exc.body,
                )
                self.fail_json(msg=msg)

        self.exit_json(
            changed=True,
            msg="The secret %s/%s was successfully deleted."
            % (self.namespace, self.name),
        )

    def create(self):

        if self.existing and not self.force:
            msg = (
                "The secret %s/%s already exists, use option force to override it."
                % (self.namespace, self.name)
            )
            self.exit_json(changed=False, msg=msg)

        if self.type == "tls":
            self.create_tls_secret()
        elif self.type == "docker-registry":
            self.create_docker_secret()
        else:
            self.create_generic_secret()


def execute_module(module, k8s_ansible_mixin):

    state = module.params.get("state")
    k8s_obj = K8SSecret(module, k8s_ansible_mixin)

    if state == "absent":
        k8s_obj.delete()
    else:
        k8s_obj.create()


def main():
    required_if = [
        ("type", "tls", ["tls_certificate"]),
        ("type", "docker-registry", ["docker_registry_credentials"]),
    ]
    module = AnsibleModule(
        argument_spec=argspec(), required_if=required_if, supports_check_mode=True,
    )
    from ansible_collections.kubernetes.core.plugins.module_utils.common import (
        K8sAnsibleMixin,
        get_api_client,
    )

    k8s_ansible_mixin = K8sAnsibleMixin(module)
    k8s_ansible_mixin.client = get_api_client(module=module)
    execute_module(module, k8s_ansible_mixin)


if __name__ == "__main__":
    main()
