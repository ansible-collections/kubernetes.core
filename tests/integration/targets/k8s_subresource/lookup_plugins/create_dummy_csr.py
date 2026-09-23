# python 3 headers, required if submitting to Ansible
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
  name: create_dummy_csr
  author: Yorick Gruijthuijzen (@yorick1989) <yorick-1989@hotmail.com>
  version_added: "1.0"
  short_description: Returns test csr content
  description:
      - Returns test csr content
  options:
    _term:
      description: The Common Name
      required: True
      type: string
"""

from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

display = Display()

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


class LookupModule(LookupBase):
    """Main module implementation"""

    def run(self, terms, variables=None, **kwargs):
        common_name = terms[0]

        display.debug("Generating CSR with the Common Name: %s" % common_name)

        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=int(kwargs.get("key_size", 2048)),
        )

        return [
            x509.CertificateSigningRequestBuilder()
            .subject_name(
                x509.Name(
                    [
                        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
                    ]
                )
            )
            .sign(key, hashes.SHA256())
            .public_bytes(serialization.Encoding.PEM)
        ]
