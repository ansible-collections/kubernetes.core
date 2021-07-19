.. _ansible_collections.kubernetes.core.docsite.k8s_ansible_intro:

**************************************
Introduction to Ansible for Kubernetes
**************************************

.. contents::
  :local:

Introduction
============

The `kubernetes.core collection <https://galaxy.ansible.com/kubernetes/core>`_ offers several modules and plugins for orchestrating Kubernetes.

Requirements
============

To use the modules, you'll need the following:

- Ansible 2.9.17 or latest installed
- `Kubernetes Python client <https://pypi.org/project/kubernetes/>`_  installed on the host that will execute the modules.


Installation
============

The Kubernetes modules are part of the Ansible Kubernetes collection.

To install the collection, run the following:

.. code-block:: bash

    $ ansible-galaxy collection install kubernetes.core


Authenticating with the API
===========================

By default the Kubernetes Rest Client will look for ``~/.kube/config``, and if found, connect using the active context. You can override the location of the file using the ``kubeconfig`` parameter, and the context, using the ``context`` parameter.

Basic authentication is also supported using the ``username`` and ``password`` options. You can override the URL using the ``host`` parameter. Certificate authentication works through the ``ssl_ca_cert``, ``cert_file``, and ``key_file`` parameters, and for token authentication, use the ``api_key`` parameter.

To disable SSL certificate verification, set ``verify_ssl`` to false.

Reporting an issue
==================

- If you find a bug or have a suggestion regarding modules or plugins, please file issues at `Ansible Kubernetes collection <https://github.com/ansible-collections/kubernetes.core/issues>`_.
- If you find a bug regarding Kubernetes Python client, please file issues at `Kubernetes Client issues <https://github.com/kubernetes-client/python/issues>`_.
- If you find a bug regarding Kubectl binary, please file issues at `Kubectl issue tracker <https://github.com/kubernetes/kubectl/issues>`_
- If you find a bug regarding Helm binary, please file issues at `Helm issue tracker <https://github.com/helm/helm/issues>`_.
