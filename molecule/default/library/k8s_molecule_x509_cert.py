#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Aubin Bikouo <@abikouo>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r'''

module: k8s_molecule_x509_cert.py

short_description: Generate x509 certificate and private key pair.

author:
    - Aubin Bikouo (@abikouo)

description:
  - This module is used to generate x509 certificate and private key for molecule
    testing for the kubernetes.core collection.
  - This module is not supported outside of this context.

options:
  path:
    description:
    - The destination path where files will be created.
    - The following files will be created certificate.pem and private_key.pem with the prefix on the file name.
    type: path
    required: yes
  prefix:
    description:
    - generated files prefix.
    type: str
  x509_size:
    description:
    - certificate size.
    type: int
    choices:
    - 2048
    - 4096
  x509_validity:
    description:
    - certificate validity in year.
    type: int
    default: 1

requirements:
  - python >= 3.6
  - PyOpenSSL
'''

EXAMPLES = r'''
- name: create x509 certificate into /tmp/certificates
  k8s_molecule_x509_cert:
    path: /tmp/certificates
'''


RETURN = r'''
cert:
  description:
  - The base64 encoded value of the certificate generated.
  returned: success
  type: str
key:
  description:
  - The base64 encoded value of the private key.
  returned: success
  type: str
'''

import traceback
import socket
import random
import os
import base64

from ansible.module_utils.basic import AnsibleModule

try:
    from OpenSSL import crypto

    HAS_OPENSSL_PY_LIBRARY = True
except ImportError as e:
    HAS_OPENSSL_PY_LIBRARY = False
    pyopenssl_import_exception = e
    IMPORT_OPENSSL_ERR = traceback.format_exc()


def generate_self_signed_cert(key_size, validity):
    pkey = crypto.PKey()
    pkey.generate_key(crypto.TYPE_RSA, key_size)

    x509 = crypto.X509()
    subject = x509.get_subject()
    subject.commonName = socket.gethostname()
    x509.set_issuer(subject)
    x509.gmtime_adj_notBefore(0)
    x509.gmtime_adj_notAfter(validity * 365 * 24 * 60 * 60)
    x509.set_pubkey(pkey)
    x509.set_serial_number(random.randrange(100000))
    x509.set_version(2)
    host_extension = "DNS:%s" % socket.gethostname()
    x509.add_extensions([
        crypto.X509Extension(b"subjectAltName", False, host_extension.encode()),
        crypto.X509Extension(b"basicConstraints", True, b"CA:false")]
    )

    x509.sign(pkey, 'SHA256')

    return (crypto.dump_certificate(crypto.FILETYPE_PEM, x509),
            crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))


def execute_module(module):
    if not HAS_OPENSSL_PY_LIBRARY:
        module.fail_json(
            msg="This module requires PyOpenSSL python library, install it using `pip install pyopenssl`"
        )

    params = dict(
        key_size=module.params.get("x509_size"),
        validity=module.params.get("x509_validity")
    )
    certificate, private_key = generate_self_signed_cert(**params)

    path = module.params.get("path")
    prefix = module.params.get("prefix")
    with open(os.path.join(path, "%scertificate.pem" % prefix), "wb") as f:
        f.write(certificate)

    with open(os.path.join(path, "%sprivate_key.pem" % prefix), "wb") as f:
        f.write(private_key)

    module.exit_json(
        changed=True,
        cert=base64.b64encode(certificate).decode(),
        key=base64.b64encode(private_key).decode(),
    )


def main():
    argument_spec = dict(
        path=dict(type='path', required=True),
        prefix=dict(type='str', default=''),
        x509_size=dict(type='int', choices=[2048, 4096]),
        x509_validity=dict(type='int', default=1),
    )
    module = AnsibleModule(argument_spec=argument_spec)

    execute_module(module)


if __name__ == '__main__':
    main()
