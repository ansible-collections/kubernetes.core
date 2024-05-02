.. _kubernetes.core.kubectl_connection:


***********************
kubernetes.core.kubectl
***********************

**Execute tasks in pods running on Kubernetes.**



.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Use the kubectl exec command to run tasks in, or put/fetch files to, pods running on the Kubernetes container platform.



Requirements
------------
The below requirements are needed on the local Ansible controller node that executes this connection.

- kubectl (go binary)


Parameters
----------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="1">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
                <th>Configuration</th>
            <th width="100%">Comments</th>
        </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ca_cert</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                    <td>
                                <div>env:K8S_AUTH_SSL_CA_CERT</div>
                                <div>var: ansible_kubectl_ssl_ca_cert</div>
                                <div>var: ansible_kubectl_ca_cert</div>
                    </td>
                <td>
                        <div>Path to a CA certificate used to authenticate with the API.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: kubectl_ssl_ca_cert</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>client_cert</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                    <td>
                                <div>env:K8S_AUTH_CERT_FILE</div>
                                <div>var: ansible_kubectl_cert_file</div>
                                <div>var: ansible_kubectl_client_cert</div>
                    </td>
                <td>
                        <div>Path to a certificate used to authenticate with the API.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: kubectl_cert_file</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>client_key</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                    <td>
                                <div>env:K8S_AUTH_KEY_FILE</div>
                                <div>var: ansible_kubectl_key_file</div>
                                <div>var: ansible_kubectl_client_key</div>
                    </td>
                <td>
                        <div>Path to a key file used to authenticate with the API.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: kubectl_key_file</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>kubectl_container</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                    <td>
                                <div>env:K8S_AUTH_CONTAINER</div>
                                <div>var: ansible_kubectl_container</div>
                    </td>
                <td>
                        <div>Container name.</div>
                        <div>Required when a pod contains more than one container.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>kubectl_context</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                    <td>
                                <div>env:K8S_AUTH_CONTEXT</div>
                                <div>var: ansible_kubectl_context</div>
                    </td>
                <td>
                        <div>The name of a context found in the K8s config file.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>kubectl_extra_args</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                    <td>
                                <div>env:K8S_AUTH_EXTRA_ARGS</div>
                                <div>var: ansible_kubectl_extra_args</div>
                    </td>
                <td>
                        <div>Extra arguments to pass to the kubectl command line.</div>
                        <div>Please be aware that this passes information directly on the command line and it could expose sensitive data.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>kubectl_host</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                    <td>
                                <div>env:K8S_AUTH_HOST</div>
                                <div>env:K8S_AUTH_SERVER</div>
                                <div>var: ansible_kubectl_host</div>
                                <div>var: ansible_kubectl_server</div>
                    </td>
                <td>
                        <div>URL for accessing the API.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>kubectl_kubeconfig</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                    <td>
                                <div>env:K8S_AUTH_KUBECONFIG</div>
                                <div>var: ansible_kubectl_kubeconfig</div>
                                <div>var: ansible_kubectl_config</div>
                    </td>
                <td>
                        <div>Path to a kubectl config file. Defaults to <em>~/.kube/config</em></div>
                        <div>The configuration can be provided as dictionary. Added in version 2.4.0.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>kubectl_local_env_vars</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 3.1.0</div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">{}</div>
                </td>
                    <td>
                                <div>var: ansible_kubectl_local_env_vars</div>
                    </td>
                <td>
                        <div>Local enviromantal variable to be passed locally to the kubectl command line.</div>
                        <div>Please be aware that this passes information directly on the command line and it could expose sensitive data.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>kubectl_namespace</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                    <td>
                                <div>env:K8S_AUTH_NAMESPACE</div>
                                <div>var: ansible_kubectl_namespace</div>
                    </td>
                <td>
                        <div>The namespace of the pod</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>kubectl_password</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                    <td>
                                <div>env:K8S_AUTH_PASSWORD</div>
                                <div>var: ansible_kubectl_password</div>
                    </td>
                <td>
                        <div>Provide a password for authenticating with the API.</div>
                        <div>Please be aware that this passes information directly on the command line and it could expose sensitive data. We recommend using the file based authentication options instead.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>kubectl_pod</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                    <td>
                                <div>env:K8S_AUTH_POD</div>
                                <div>var: ansible_kubectl_pod</div>
                    </td>
                <td>
                        <div>Pod name.</div>
                        <div>Required when the host name does not match pod name.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>kubectl_token</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                    <td>
                                <div>env:K8S_AUTH_TOKEN</div>
                                <div>env:K8S_AUTH_API_KEY</div>
                                <div>var: ansible_kubectl_token</div>
                                <div>var: ansible_kubectl_api_key</div>
                    </td>
                <td>
                        <div>API authentication bearer token.</div>
                        <div>Please be aware that this passes information directly on the command line and it could expose sensitive data. We recommend using the file based authentication options instead.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>kubectl_username</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                    <td>
                                <div>env:K8S_AUTH_USERNAME</div>
                                <div>var: ansible_kubectl_username</div>
                                <div>var: ansible_kubectl_user</div>
                    </td>
                <td>
                        <div>Provide a username for authenticating with the API.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>validate_certs</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                    <td>
                                <div>env:K8S_AUTH_VERIFY_SSL</div>
                                <div>var: ansible_kubectl_verify_ssl</div>
                                <div>var: ansible_kubectl_validate_certs</div>
                    </td>
                <td>
                        <div>Whether or not to verify the API server&#x27;s SSL certificate. Defaults to <em>true</em>.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: kubectl_verify_ssl</div>
                </td>
            </tr>
    </table>
    <br/>








Status
------


Authors
~~~~~~~

- xuxinkun (@xuxinkun)


.. hint::
    Configuration entries for each entry type have a low to high priority order. For example, a variable that is lower in the list will override a variable that is higher up.
