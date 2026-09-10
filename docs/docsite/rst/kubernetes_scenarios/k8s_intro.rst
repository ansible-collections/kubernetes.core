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

- Ansible 2.16.0 or latest installed
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

Sharing options across tasks with action groups
===============================================

Repeating the same authentication options on every task gets verbose quickly. The collection
defines two `action groups <https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_module_defaults.html#module-defaults-groups>`_
so you can set them once with ``module_defaults``:

``kubernetes.core.k8s``
    Modules that talk to the Kubernetes API and accept the standard authentication options
    (``kubeconfig``, ``context``, ``host``, ``api_key``, ``validate_certs``, and so on):
    ``k8s``, ``k8s_cluster_info``, ``k8s_cp``, ``k8s_drain``, ``k8s_exec``, ``k8s_info``,
    ``k8s_json_patch``, ``k8s_log``, ``k8s_rollback``, ``k8s_scale``, ``k8s_service``, and
    ``k8s_taint``.

``kubernetes.core.helm``
    Modules that shell out to the ``helm`` binary and accept its shared authentication
    options (``binary_path``, ``kubeconfig``, ``context``, ``host``, ``api_key``,
    ``ca_cert``, ``validate_certs``): ``helm``, ``helm_info``, ``helm_plugin``,
    ``helm_plugin_info``, and ``helm_repository``.

Prefix the group name with ``group/`` to use it:

.. code-block:: yaml

    - hosts: localhost
      module_defaults:
        group/kubernetes.core.k8s:
          kubeconfig: /path/to/kubeconfig
          context: staging
        group/kubernetes.core.helm:
          binary_path: /path/to/helm
          kubeconfig: /path/to/kubeconfig
          context: staging
      tasks:
        - name: Create a namespace
          kubernetes.core.k8s:
            definition:
              apiVersion: v1
              kind: Namespace
              metadata:
                name: monitoring

        - name: Read it back
          kubernetes.core.k8s_info:
            kind: Namespace
            name: monitoring

        - name: Add the prometheus chart repository
          kubernetes.core.helm_repository:
            name: prometheus-community
            repo_url: https://prometheus-community.github.io/helm-charts

        - name: Deploy the kube-prometheus-stack chart
          kubernetes.core.helm:
            name: kube-prometheus-stack
            chart_ref: prometheus-community/kube-prometheus-stack
            release_namespace: monitoring

        - name: Collect the releases in that namespace
          kubernetes.core.helm_info:
            name: kube-prometheus-stack
            release_namespace: monitoring

Every task picks up ``kubeconfig`` and ``context`` from its group without repeating them, the
``helm`` modules additionally pick up ``binary_path``, and an option set on an individual task
still wins over the group default.

.. note::

   Always write the group name fully qualified as ``group/kubernetes.core.k8s``. A bare
   ``group/k8s`` refers to the legacy ``k8s`` group that ansible-core defined back when the
   Kubernetes modules shipped in core itself. The two are not the same group, and the legacy
   one does not cover the modules in this collection.

Some modules are deliberately **not** in these groups because they do not accept the shared
authentication options, and including them would make ``module_defaults`` fail for everyone
using the group:

- ``helm_pull`` and ``helm_template`` accept only ``binary_path``.
- ``helm_registry_auth`` accepts ``binary_path`` and its own ``host``, which is an OCI
  registry URL rather than a Kubernetes API server.
- ``kubeconfig`` writes a kubeconfig file locally and takes no cluster connection options.

Pass options to those modules directly, or give them their own per-module ``module_defaults``
entry.

Reporting an issue
==================

- If you find a bug or have a suggestion regarding modules or plugins, please file issues at `Ansible Kubernetes collection <https://github.com/ansible-collections/kubernetes.core/issues>`_.
- If you find a bug regarding Kubernetes Python client, please file issues at `Kubernetes Client issues <https://github.com/kubernetes-client/python/issues>`_.
- If you find a bug regarding Kubectl binary, please file issues at `Kubectl issue tracker <https://github.com/kubernetes/kubectl/issues>`_
- If you find a bug regarding Helm binary, please file issues at `Helm issue tracker <https://github.com/helm/helm/issues>`_.
