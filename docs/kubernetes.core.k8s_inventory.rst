.. _kubernetes.core.k8s_inventory:


*******************
kubernetes.core.k8s
*******************

**Kubernetes (K8s) inventory source**



.. contents::
   :local:
   :depth: 1

DEPRECATED
----------
:Removed in collection release after 
:Why: As discussed in https://github.com/ansible-collections/kubernetes.core/issues/31, we decided to
remove the k8s inventory plugin in release 5.0.0.

:Alternative: Use :ref:`kubernetes.core.k8s_info <kubernetes.core.k8s_info_module>` and :ref:`ansible.builtin.add_host <ansible.builtin.add_host_module>` instead.



Synopsis
--------
- Fetch containers and services for one or more clusters.
- Groups by cluster name, namespace, namespace_services, namespace_pods, and labels.
- Uses the kubectl connection plugin to access the Kubernetes cluster.
- Uses k8s.(yml|yaml) YAML configuration file to set parameter values.



Requirements
------------
The below requirements are needed on the local Ansible controller node that executes this inventory.

- python >= 3.9
- kubernetes >= 24.2.0
- PyYAML >= 3.11


Parameters
----------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="2">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
                <th>Configuration</th>
            <th width="100%">Comments</th>
        </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>connections</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                    <td>
                    </td>
                <td>
                        <div>Optional list of cluster connection settings. If no connections are provided, the default <em>~/.kube/config</em> and active context will be used, and objects will be returned for all namespaces the active user is authorized to access.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>api_key</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                    <td>
                    </td>
                <td>
                        <div>Token used to authenticate with the API. Can also be specified via K8S_AUTH_API_KEY environment variable.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ca_cert</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                    <td>
                    </td>
                <td>
                        <div>Path to a CA certificate used to authenticate with the API. Can also be specified via K8S_AUTH_SSL_CA_CERT environment variable.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: ssl_ca_cert</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>client_cert</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                    <td>
                    </td>
                <td>
                        <div>Path to a certificate used to authenticate with the API. Can also be specified via K8S_AUTH_CERT_FILE environment variable.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: cert_file</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>client_key</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                    <td>
                    </td>
                <td>
                        <div>Path to a key file used to authenticate with the API. Can also be specified via K8S_AUTH_KEY_FILE environment variable.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: key_file</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>context</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                    <td>
                    </td>
                <td>
                        <div>The name of a context found in the config file. Can also be specified via K8S_AUTH_CONTEXT environment variable.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>host</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                    <td>
                    </td>
                <td>
                        <div>Provide a URL for accessing the API. Can also be specified via K8S_AUTH_HOST environment variable.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>kubeconfig</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                    <td>
                    </td>
                <td>
                        <div>Path to an existing Kubernetes config file. If not provided, and no other connection options are provided, the Kubernetes client will attempt to load the default configuration file from <em>~/.kube/config</em>. Can also be specified via K8S_AUTH_KUBECONFIG environment variable.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                    <td>
                    </td>
                <td>
                        <div>Optional name to assign to the cluster. If not provided, a name is constructed from the server and port.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>namespaces</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                    <td>
                    </td>
                <td>
                        <div>List of namespaces. If not specified, will fetch all containers for all namespaces user is authorized to access.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>password</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                    <td>
                    </td>
                <td>
                        <div>Provide a password for authenticating with the API. Can also be specified via K8S_AUTH_PASSWORD environment variable.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>username</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                    <td>
                    </td>
                <td>
                        <div>Provide a username for authenticating with the API. Can also be specified via K8S_AUTH_USERNAME environment variable.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>validate_certs</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>no</li>
                                    <li>yes</li>
                        </ul>
                </td>
                    <td>
                    </td>
                <td>
                        <div>Whether or not to verify the API server&#x27;s SSL certificates. Can also be specified via K8S_AUTH_VERIFY_SSL environment variable.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: verify_ssl</div>
                </td>
            </tr>

            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>plugin</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>kubernetes.core.k8s</li>
                                    <li>k8s</li>
                                    <li>community.kubernetes.k8s</li>
                        </ul>
                </td>
                    <td>
                    </td>
                <td>
                        <div>token that ensures this is a source file for the &#x27;k8s&#x27; plugin.</div>
                </td>
            </tr>
    </table>
    <br/>




Examples
--------

.. code-block:: yaml

    # File must be named k8s.yaml or k8s.yml

    - name: Authenticate with token, and return all pods and services for all namespaces
      plugin: kubernetes.core.k8s
      connections:
        - host: https://192.168.64.4:8443
          api_key: xxxxxxxxxxxxxxxx
          validate_certs: false

    - name: Use default config (~/.kube/config) file and active context, and return objects for a specific namespace
      plugin: kubernetes.core.k8s
      connections:
        - namespaces:
            - testing

    - name: Use a custom config file, and a specific context.
      plugin: kubernetes.core.k8s
      connections:
        - kubeconfig: /path/to/config
          context: 'awx/192-168-64-4:8443/developer'




Status
------


- This inventory will be removed in version 5.0.0. *[deprecated]*
- For more information see `DEPRECATED`_.


Authors
~~~~~~~

- Chris Houseknecht (@chouseknecht)
- Fabian von Feilitzsch (@fabianvf)


.. hint::
    Configuration entries for each entry type have a low to high priority order. For example, a variable that is lower in the list will override a variable that is higher up.
