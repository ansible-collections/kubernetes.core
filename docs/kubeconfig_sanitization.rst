.. _kubeconfig_sanitization:


**************************************
Kubeconfig Sanitization Implementation
**************************************

Overview
--------

This document describes the fine-grained `kubeconfig`_ sanitization feature implemented in kubernetes.core collection to selectively hide sensitive information from Ansible logs while preserving non-sensitive debugging information.

Problem Statement
-----------------

Previously, kubeconfig parameters had to use a blanket ``no_log=True`` restriction to prevent sensitive data from appearing in logs. This approach had several drawbacks:

1. **Complete blackout**: Even file paths were hidden, making debugging difficult
2. **All-or-nothing**: No way to show non-sensitive kubeconfig fields for debugging
3. **Poor UX**: Users couldn't see the kubeconfig file path being used

Solution
--------

This implementation provides a fine-grained sanitization policy that:

1. **Preserves file paths**: When kubeconfig is a string (file path), it's logged normally
2. **Selective hiding**: When kubeconfig is a dictionary, only sensitive fields are hidden
3. **Maintains structure**: The overall kubeconfig structure is preserved for debugging
4. **Automatic integration**: Works transparently with all kubernetes.core modules

Implementation Details
----------------------

Sensitive Fields Identified
~~~~~~~~~~~~~~~~~~~~~~~~~~~

User-level sensitive fields:
  - ``token``
  - ``password``
  - ``client-certificate-data``
  - ``client-key-data``
  - ``refresh-token``
  - ``id-token``
  - ``access-token``

Cluster-level sensitive fields:
  - ``certificate-authority-data``

Architecture
~~~~~~~~~~~~

The sanitization is implemented through three main components:

1. **sanitize.py module**: Core sanitization logic
2. **AnsibleK8SModule integration**: Automatic sanitization on ``exit_json`` and ``fail_json``
3. **Argument specification**: ``kubeconfig`` parameter remains ``type='raw'`` without ``no_log=True``

Code Flow
~~~~~~~~~

::

  1. Module execution starts
  2. kubeconfig parameter is processed normally (no blanket no_log)
  3. Module completes and calls exit_json() or fail_json()
  4. AnsibleK8SModule.exit_json() intercepts the call
  5. sanitize_module_return_value() processes the result
  6. Sensitive kubeconfig fields are replaced with "**HIDDEN**"
  7. Sanitized result is passed to the underlying AnsibleModule

Examples
--------

String kubeconfig (file path) - Preserved
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   - name: Apply manifest
     kubernetes.core.k8s:
       kubeconfig: "/home/user/.kube/config"
       # ... other parameters

**Log output**: Shows the actual file path for debugging

::

   "kubeconfig": "/home/user/.kube/config"

Dictionary kubeconfig - Selectively sanitized
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   - name: Apply with inline kubeconfig
     kubernetes.core.k8s:
       kubeconfig:
         users:
           - name: admin
             user:
               token: "eyJhbGciOiJSUzI1NiIs..."
               username: "admin"
         clusters:
           - name: default
             cluster:
               server: "https://kubernetes.example.com"
               certificate-authority-data: "LS0tLS1CRUdJTi..."
       # ... other parameters

**Log output**: Sensitive fields hidden, non-sensitive preserved

.. code-block:: json

   {
     "kubeconfig": {
       "users": [{
         "name": "admin",
         "user": {
           "token": "**HIDDEN**",
           "username": "admin"
         }
       }],
       "clusters": [{
         "name": "default", 
         "cluster": {
           "server": "https://kubernetes.example.com",
           "certificate-authority-data": "**HIDDEN**"
         }
       }]
     }
   }

Testing
-------

The implementation includes comprehensive tests:

1. **Unit tests** (``test_sanitize.py``): Test sanitization functions directly
2. **Integration verification**: End-to-end testing of the sanitization flow

Tests confirm:

- ✅ String kubeconfig paths are preserved
- ✅ Dictionary kubeconfig sensitive fields are hidden
- ✅ Dictionary kubeconfig non-sensitive fields are preserved
- ✅ Integration with AnsibleK8SModule works correctly
- ✅ Both ``exit_json`` and ``fail_json`` sanitize appropriately

Backward Compatibility
----------------------

This implementation maintains full backward compatibility:

- Existing playbooks using file paths continue to work unchanged
- Existing playbooks using dictionary kubeconfig continue to work
- The ``kubeconfig`` parameter specification is unchanged (``type='raw'``)
- No breaking changes to module interfaces

Security Benefits
-----------------

1. **Improved debugging**: File paths and non-sensitive config visible in logs
2. **Maintained security**: Certificates, tokens, and keys remain hidden
3. **Fine-grained control**: Only truly sensitive data is redacted
4. **Consistent application**: Works across all kubernetes.core modules automatically

.. _kubeconfig: https://kubernetes.io/docs/reference/config-api/kubeconfig.v1/
