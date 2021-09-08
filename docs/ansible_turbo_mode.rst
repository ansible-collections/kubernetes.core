.. _ansible_turbo_mode:


******************
Ansible Turbo mode
******************

Following document provides overview of Ansible Turbo mode in ``kubernetes.core`` collection.

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- A brief introduction about Ansible Turbo mode in ``kuberentes.core`` collection.
- Ansible Turbo mode is an optional performance optimization. It can be enabled by installing the cloud.common collection and setting the ``ENABLE_TURBO_MODE`` environment variable.

Requirements
------------

The following requirement is needed on the host that executes this module.

- The ``cloud.common`` collection (https://github.com/ansible-collections/cloud.common)

You will also need to set the environment variable ``ENABLE_TURBO_MODE=1`` on the managed host. This can be done in the same ways you would usually do so, for example::

  ---
  - hosts: remote
    environment:
      ENABLE_TURBO_MODE: 1
    tasks:
      ...


Installation
------------

You can install ``cloud.common`` collection using following command::

    # ansible-galaxy collection install cloud.common


Current situation without Ansible Turbo mode
============================================

The traditional execution flow of an Ansible module includes the following steps:

- Upload of a ZIP archive with the module and its dependencies
- Execution of the module
- Ansible collects the results once the script is finished

These steps happen for each task of a playbook, and on every host.

Most of the time, the execution of a module is fast enough for
the user. However, sometime the module requires significant amount of time,
just to initialize itself. This is a common situation with the API based modules.

A classic initialization involves the following steps:

- Load a Python library to access the remote resource (via SDK)
- Open a client
    - Load a bunch of Python modules.
    - Request a new TCP connection.
    - Create a session.
    - Authenticate the client.

All these steps are time consuming and the same operations will be running again and again.

For instance, here:

- ``import openstack``: takes 0.569s
- ``client = openstack.connect()``: takes 0.065s
- ``client.authorize()``: takes 1.360s,

These numbers are from test running against VexxHost public cloud.

In this case, it's a 2s-ish overhead per task. If the playbook
comes with 10 tasks, the execution time cannot go below 20s.

How Ansible Turbo Module improve the situation
==============================================

``AnsibleTurboModule`` is actually a class that inherites from
the standard ``AnsibleModule`` class that your modules probably
already use.
The big difference is that when a module starts, it also spawns
a little Python daemon. If a daemon already exists, it will just
reuse it.
All the module logic is run inside this Python daemon. This means:

- Python modules are actually loaded one time
- Ansible module can reuse an existing authenticated session.

The background service
======================

The daemon kills itself after 15s, and communication are done
through an Unix socket.
It runs in one single process and uses ``asyncio`` internally.
Consequently you can use the ``async`` keyword in your Ansible module.
This will be handy if you interact with a lot of remote systems
at the same time.

Security impact
===============

``ansible_module.turbo`` open an Unix socket to interact with the background service.
We use this service to open the connection toward the different target systems.

This is similar to what SSH does with the sockets.

Keep in mind that:

- All the modules can access the same cache. Soon an isolation will be done at the collection level (https://github.com/ansible-collections/cloud.common/pull/17)
- A task can load a different version of a library and impact the next tasks.
- If the same user runs two ``ansible-playbook`` at the same time, they will have access to the same cache.

When a module stores a session in a cache, it's a good idea to use a hash of the authentication information to identify the session.

Error management
================

``ansible_module.turbo`` uses exceptions to communicate a result back to the module.

- ``EmbeddedModuleFailure`` is raised when ``json_fail()`` is called.
- ``EmbeddedModuleSuccess`` is raised in case of success and returns the result to the origin module process.

These exceptions are defined in ``ansible_collections.cloud.common.plugins.module_utils.turbo.exceptions``.
You can raise ``EmbeddedModuleFailure`` exception yourself, for instance from a module in ``module_utils``.

.. note:: Be careful with the ``except Exception:`` blocks.
    Not only they are bad practice, but also may interface with this
    mechanism.


Troubleshooting
===============

You may want to manually start the server. This can be done with the following command:

.. code-block:: shell

  PYTHONPATH=$HOME/.ansible/collections python -m ansible_collections.cloud.common.plugins.module_utils.turbo.server --socket-path $HOME/.ansible/tmp/turbo_mode.kubernetes.core.socket

You can use the ``--help`` argument to get a list of the optional parameters.
