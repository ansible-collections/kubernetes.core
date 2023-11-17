.. _kubernetes.core.k8s_scale_module:


*************************
kubernetes.core.k8s_scale
*************************

**Set a new size for a Deployment, ReplicaSet, Replication Controller, or Job.**



.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Similar to the kubectl scale command. Use to set the number of replicas for a Deployment, ReplicaSet, or Replication Controller, or the parallelism attribute of a Job. Supports check mode.
- ``wait`` parameter is not supported for Jobs.



Requirements
------------
The below requirements are needed on the host that executes this module.

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
            <th width="100%">Comments</th>
        </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>api_key</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Token used to authenticate with the API. Can also be specified via K8S_AUTH_API_KEY environment variable.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>api_version</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"v1"</div>
                </td>
                <td>
                        <div>Use to specify the API version.</div>
                        <div>Use to create, delete, or discover an object without providing a full resource definition.</div>
                        <div>Use in conjunction with <em>kind</em>, <em>name</em>, and <em>namespace</em> to identify a specific object.</div>
                        <div>If <em>resource definition</em> is provided, the <em>apiVersion</em> value from the <em>resource_definition</em> will override this option.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: api, version</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ca_cert</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">path</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Path to a CA certificate used to authenticate with the API. The full certificate chain must be provided to avoid certificate validation errors. Can also be specified via K8S_AUTH_SSL_CA_CERT environment variable.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: ssl_ca_cert</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>client_cert</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">path</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Path to a certificate used to authenticate with the API. Can also be specified via K8S_AUTH_CERT_FILE environment variable.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: cert_file</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>client_key</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">path</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Path to a key file used to authenticate with the API. Can also be specified via K8S_AUTH_KEY_FILE environment variable.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: key_file</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>context</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The name of a context found in the config file. Can also be specified via K8S_AUTH_CONTEXT environment variable.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>continue_on_error</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 2.0.0</div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>no</b>&nbsp;&larr;</div></li>
                                    <li>yes</li>
                        </ul>
                </td>
                <td>
                        <div>Whether to continue on errors when multiple resources are defined.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>current_replicas</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>For Deployment, ReplicaSet, Replication Controller, only scale, if the number of existing replicas matches. In the case of a Job, update parallelism only if the current parallelism value matches.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>host</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Provide a URL for accessing the API. Can also be specified via K8S_AUTH_HOST environment variable.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>impersonate_groups</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 2.3.0</div>
                </td>
                <td>
                </td>
                <td>
                        <div>Group(s) to impersonate for the operation.</div>
                        <div>Can also be specified via K8S_AUTH_IMPERSONATE_GROUPS environment. Example: Group1,Group2</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>impersonate_user</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 2.3.0</div>
                </td>
                <td>
                </td>
                <td>
                        <div>Username to impersonate for the operation.</div>
                        <div>Can also be specified via K8S_AUTH_IMPERSONATE_USER environment.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>kind</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Use to specify an object model.</div>
                        <div>Use to create, delete, or discover an object without providing a full resource definition.</div>
                        <div>Use in conjunction with <em>api_version</em>, <em>name</em>, and <em>namespace</em> to identify a specific object.</div>
                        <div>If <em>resource definition</em> is provided, the <em>kind</em> value from the <em>resource_definition</em> will override this option.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>kubeconfig</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">raw</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Path to an existing Kubernetes config file. If not provided, and no other connection options are provided, the Kubernetes client will attempt to load the default configuration file from <em>~/.kube/config</em>. Can also be specified via K8S_AUTH_KUBECONFIG environment variable.</div>
                        <div>Multiple Kubernetes config file can be provided using separator &#x27;;&#x27; for Windows platform or &#x27;:&#x27; for others platforms.</div>
                        <div>The kubernetes configuration can be provided as dictionary. This feature requires a python kubernetes client version &gt;= 17.17.0. Added in version 2.2.0.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>label_selectors</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 2.0.0</div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">[]</div>
                </td>
                <td>
                        <div>List of label selectors to use to filter results.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Use to specify an object name.</div>
                        <div>Use to create, delete, or discover an object without providing a full resource definition.</div>
                        <div>Use in conjunction with <em>api_version</em>, <em>kind</em> and <em>namespace</em> to identify a specific object.</div>
                        <div>If <em>resource definition</em> is provided, the <em>metadata.name</em> value from the <em>resource_definition</em> will override this option.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>namespace</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Use to specify an object namespace.</div>
                        <div>Useful when creating, deleting, or discovering an object without providing a full resource definition.</div>
                        <div>Use in conjunction with <em>api_version</em>, <em>kind</em>, and <em>name</em> to identify a specific object.</div>
                        <div>If <em>resource definition</em> is provided, the <em>metadata.namespace</em> value from the <em>resource_definition</em> will override this option.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>no_proxy</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 2.3.0</div>
                </td>
                <td>
                </td>
                <td>
                        <div>The comma separated list of hosts/domains/IP/CIDR that shouldn&#x27;t go through proxy. Can also be specified via K8S_AUTH_NO_PROXY environment variable.</div>
                        <div>Please note that this module does not pick up typical proxy settings from the environment (e.g. NO_PROXY).</div>
                        <div>This feature requires kubernetes&gt;=19.15.0. When kubernetes library is less than 19.15.0, it fails even no_proxy set in correct.</div>
                        <div>example value is &quot;localhost,.local,.example.com,127.0.0.1,127.0.0.0/8,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16&quot;</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>password</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Provide a password for authenticating with the API. Can also be specified via K8S_AUTH_PASSWORD environment variable.</div>
                        <div>Please read the description of the <code>username</code> option for a discussion of when this option is applicable.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>persist_config</b>
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
                        <div>Whether or not to save the kube config refresh tokens. Can also be specified via K8S_AUTH_PERSIST_CONFIG environment variable.</div>
                        <div>When the k8s context is using a user credentials with refresh tokens (like oidc or gke/gcloud auth), the token is refreshed by the k8s python client library but not saved by default. So the old refresh token can expire and the next auth might fail. Setting this flag to true will tell the k8s python client to save the new refresh token to the kube config file.</div>
                        <div>Default to false.</div>
                        <div>Please note that the current version of the k8s python client library does not support setting this flag to True yet.</div>
                        <div>The fix for this k8s python library is here: https://github.com/kubernetes-client/python-base/pull/169</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>proxy</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The URL of an HTTP proxy to use for the connection. Can also be specified via K8S_AUTH_PROXY environment variable.</div>
                        <div>Please note that this module does not pick up typical proxy settings from the environment (e.g. HTTP_PROXY).</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>proxy_headers</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 2.0.0</div>
                </td>
                <td>
                </td>
                <td>
                        <div>The Header used for the HTTP proxy.</div>
                        <div>Documentation can be found here <a href='https://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html?highlight=proxy_headers#urllib3.util.make_headers'>https://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html?highlight=proxy_headers#urllib3.util.make_headers</a>.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>basic_auth</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Colon-separated username:password for basic authentication header.</div>
                        <div>Can also be specified via K8S_AUTH_PROXY_HEADERS_BASIC_AUTH environment.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>proxy_basic_auth</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Colon-separated username:password for proxy basic authentication header.</div>
                        <div>Can also be specified via K8S_AUTH_PROXY_HEADERS_PROXY_BASIC_AUTH environment.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>user_agent</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>String representing the user-agent you want, such as foo/1.0.</div>
                        <div>Can also be specified via K8S_AUTH_PROXY_HEADERS_USER_AGENT environment.</div>
                </td>
            </tr>

            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>replicas</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The desired number of replicas.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>resource_definition</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Provide a valid YAML definition (either as a string, list, or dict) for an object when creating or updating.</div>
                        <div>NOTE: <em>kind</em>, <em>api_version</em>, <em>name</em>, and <em>namespace</em> will be overwritten by corresponding values found in the provided <em>resource_definition</em>.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: definition, inline</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>resource_version</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Only attempt to scale, if the current object version matches.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>src</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">path</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Provide a path to a file containing a valid YAML definition of an object or objects to be created or updated. Mutually exclusive with <em>resource_definition</em>. NOTE: <em>kind</em>, <em>api_version</em>, <em>name</em>, and <em>namespace</em> will be overwritten by corresponding values found in the configuration read in from the <em>src</em> file.</div>
                        <div>Reads from the local file system. To read from the Ansible controller&#x27;s file system, including vaulted files, use the file lookup plugin or template lookup plugin, combined with the from_yaml filter, and pass the result to <em>resource_definition</em>. See Examples below.</div>
                        <div>The URL to manifest files that can be used to create the resource. Added in version 2.4.0.</div>
                        <div>Mutually exclusive with <em>template</em> in case of <span class='module'>kubernetes.core.k8s</span> module.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>username</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Provide a username for authenticating with the API. Can also be specified via K8S_AUTH_USERNAME environment variable.</div>
                        <div>Please note that this only works with clusters configured to use HTTP Basic Auth. If your cluster has a different form of authentication (e.g. OAuth2 in OpenShift), this option will not work as expected and you should look into the <span class='module'>community.okd.k8s_auth</span> module, as that might do what you need.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
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
                        <div>Whether or not to verify the API server&#x27;s SSL certificates. Can also be specified via K8S_AUTH_VERIFY_SSL environment variable.</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: verify_ssl</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>wait</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>no</li>
                                    <li><div style="color: blue"><b>yes</b>&nbsp;&larr;</div></li>
                        </ul>
                </td>
                <td>
                        <div>For Deployment, ReplicaSet, Replication Controller, wait for the status value of <em>ready_replicas</em> to change to the number of <em>replicas</em>. In the case of a Job, this option is ignored.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>wait_sleep</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 2.0.0</div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">5</div>
                </td>
                <td>
                        <div>Number of seconds to sleep between checks.</div>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>wait_timeout</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">20</div>
                </td>
                <td>
                        <div>When <code>wait</code> is <em>True</em>, the number of seconds to wait for the <em>ready_replicas</em> status to equal  <em>replicas</em>. If the status is not reached within the allotted time, an error will result. In the case of a Job, this option is ignored.</div>
                </td>
            </tr>
    </table>
    <br/>


Notes
-----

.. note::
   - To avoid SSL certificate validation errors when ``validate_certs`` is *True*, the full certificate chain for the API server must be provided via ``ca_cert`` or in the kubeconfig file.



Examples
--------

.. code-block:: yaml

    - name: Scale deployment up, and extend timeout
      kubernetes.core.k8s_scale:
        api_version: v1
        kind: Deployment
        name: elastic
        namespace: myproject
        replicas: 3
        wait_timeout: 60

    - name: Scale deployment down when current replicas match
      kubernetes.core.k8s_scale:
        api_version: v1
        kind: Deployment
        name: elastic
        namespace: myproject
        current_replicas: 3
        replicas: 2

    - name: Increase job parallelism
      kubernetes.core.k8s_scale:
        api_version: batch/v1
        kind: job
        name: pi-with-timeout
        namespace: testing
        replicas: 2

    # Match object using local file or inline definition

    - name: Scale deployment based on a file from the local filesystem
      kubernetes.core.k8s_scale:
        src: /myproject/elastic_deployment.yml
        replicas: 3
        wait: no

    - name: Scale deployment based on a template output
      kubernetes.core.k8s_scale:
        resource_definition: "{{ lookup('template', '/myproject/elastic_deployment.yml') | from_yaml }}"
        replicas: 3
        wait: no

    - name: Scale deployment based on a file from the Ansible controller filesystem
      kubernetes.core.k8s_scale:
        resource_definition: "{{ lookup('file', '/myproject/elastic_deployment.yml') | from_yaml }}"
        replicas: 3
        wait: no

    - name: Scale deployment using label selectors (continue operation in case error occured on one resource)
      kubernetes.core.k8s_scale:
        replicas: 3
        kind: Deployment
        namespace: test
        label_selectors:
          - app=test
        continue_on_error: true



Return Values
-------------
Common return values are documented `here <https://docs.ansible.com/ansible/latest/reference_appendices/common_return_values.html#common-return-values>`_, the following are the fields unique to this module:

.. raw:: html

    <table border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="2">Key</th>
            <th>Returned</th>
            <th width="100%">Description</th>
        </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>result</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">complex</span>
                    </div>
                </td>
                <td>success</td>
                <td>
                            <div>If a change was made, will return the patched object, otherwise returns the existing object.</div>
                    <br/>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>api_version</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td>success</td>
                <td>
                            <div>The versioned schema of this representation of an object.</div>
                    <br/>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>duration</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>when <code>wait</code> is true</td>
                <td>
                            <div>elapsed time of task in seconds</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">48</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>kind</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td>success</td>
                <td>
                            <div>Represents the REST resource this object represents.</div>
                    <br/>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>metadata</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">complex</span>
                    </div>
                </td>
                <td>success</td>
                <td>
                            <div>Standard object metadata. Includes name, namespace, annotations, labels, etc.</div>
                    <br/>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>spec</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">complex</span>
                    </div>
                </td>
                <td>success</td>
                <td>
                            <div>Specific attributes of the object. Will vary based on the <em>api_version</em> and <em>kind</em>.</div>
                    <br/>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder">&nbsp;</td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>status</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">complex</span>
                    </div>
                </td>
                <td>success</td>
                <td>
                            <div>Current status details for the object.</div>
                    <br/>
                </td>
            </tr>

    </table>
    <br/><br/>


Status
------


Authors
~~~~~~~

- Chris Houseknecht (@chouseknecht)
- Fabian von Feilitzsch (@fabianvf)
