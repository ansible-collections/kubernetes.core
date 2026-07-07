.. _kubernetes.core.kubeconfig_module:


**************************
kubernetes.core.kubeconfig
**************************

**Generate, update, and optionally write Kubernetes kubeconfig files**


Version added: 6.5.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Build, update, and manage Kubernetes kubeconfig files using structured input.
- Supports loading an existing kubeconfig file and merging clusters, users, and contexts.
- Can optionally write the resulting kubeconfig to a destination path.
- Ensures idempotent behavior by only updating files when changes occur.



Requirements
------------
The below requirements are needed on the host that executes this module.

- PyYAML >= 5.1


Parameters
----------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="3">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
            <th width="100%">Comments</th>
        </tr>
            <tr>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>clusters</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">[]</div>
                </td>
                <td>
                        <div>List of cluster definitions to merge into the kubeconfig.</div>
                        <div>Each cluster is identified by its <code>name</code>.</div>
                        <div>When <code>name</code> matches an existing cluster, the default <code>behavior</code> is V(merge).</div>
                        <div>See the <code>behavior</code> suboption for V(replace), V(keep), and V(remove).</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>behavior</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>merge</b>&nbsp;&larr;</div></li>
                                    <li>replace</li>
                                    <li>keep</li>
                                    <li>remove</li>
                        </ul>
                </td>
                <td>
                        <div>How to handle merging if a cluster with this name already exists.</div>
                        <div><code>merge</code> - Update only the specified fields, preserve others (default).</div>
                        <div><code>replace</code> - Replace the entire cluster definition.</div>
                        <div><code>keep</code> - Keep existing cluster, skip this entry.</div>
                        <div><code>remove</code> - Remove the cluster entry entirely. Silently skipped if the entry does not exist.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>cluster</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Cluster configuration details.</div>
                        <div>Not required when <code>behavior</code> is V(remove).</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>certificate-authority</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Path to a CA certificate file for validating the API server certificate.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>certificate-authority-data</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Base64 encoded CA certificate data.</div>
                        <div>Use this instead of <code>certificate-authority</code> for embedded certificates.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>insecure-skip-tls-verify</b>
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
                        <div>If true, the server&#x27;s certificate will not be validated.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>proxy-url</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Optional proxy URL for cluster connections.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>server</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Kubernetes API server URL (e.g., <code>https://k8s.example.com:6443</code>).</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>tls-server-name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Server name to use for server certificate validation.</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Unique name identifier for the cluster.</div>
                </td>
            </tr>

            <tr>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>contexts</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">[]</div>
                </td>
                <td>
                        <div>List of context definitions linking users and clusters.</div>
                        <div>Each context is identified by its <code>name</code>.</div>
                        <div>When <code>name</code> matches an existing context, the default <code>behavior</code> is V(merge).</div>
                        <div>See the <code>behavior</code> suboption for V(replace), V(keep), and V(remove).</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>behavior</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>merge</b>&nbsp;&larr;</div></li>
                                    <li>replace</li>
                                    <li>keep</li>
                                    <li>remove</li>
                        </ul>
                </td>
                <td>
                        <div>How to handle merging if a context with this name already exists.</div>
                        <div><code>merge</code> - Update only the specified fields, preserve others (default).</div>
                        <div><code>replace</code> - Replace the entire context definition.</div>
                        <div><code>keep</code> - Keep existing context, skip this entry.</div>
                        <div><code>remove</code> - Remove the context entry entirely. Silently skipped if the entry does not exist.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>context</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Context configuration linking cluster and user.</div>
                        <div>Not required when <code>behavior</code> is V(remove).</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>cluster</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the cluster to use (must match a cluster name in O(clusters)).</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
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
                        <div>Default namespace to use for this context.</div>
                        <div>If not specified, defaults to <code>default</code>.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>user</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the user to authenticate as (must match a user name in O(users)).</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Unique name identifier for the context.</div>
                </td>
            </tr>

            <tr>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>current_context</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the context to set as current/active.</div>
                        <div>This context will be used by default when using kubectl.</div>
                        <div>Must match one of the context names defined in O(contexts).</div>
                </td>
            </tr>
            <tr>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dest</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Destination path where the final kubeconfig should be written.</div>
                        <div>If not specified, the kubeconfig will be saved to O(path).</div>
                        <div>Allows copying and modifying a kubeconfig to a new location.</div>
                </td>
            </tr>
            <tr>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>path</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Path to an existing kubeconfig file to load and merge from.</div>
                        <div>If the file does not exist, a new kubeconfig will be created.</div>
                        <div>This becomes the default destination if O(dest) is not specified.</div>
                </td>
            </tr>
            <tr>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>preferences</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">{}</div>
                </td>
                <td>
                        <div>Kubeconfig preferences.</div>
                        <div>Used for client-side settings like color output, default editor, etc.</div>
                </td>
            </tr>
            <tr>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>users</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">[]</div>
                </td>
                <td>
                        <div>List of user authentication configurations.</div>
                        <div>Each user is identified by its <code>name</code>.</div>
                        <div>When <code>name</code> matches an existing user, the default <code>behavior</code> is V(merge).</div>
                        <div>See the <code>behavior</code> suboption for V(replace), V(keep), and V(remove).</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>behavior</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>merge</b>&nbsp;&larr;</div></li>
                                    <li>replace</li>
                                    <li>keep</li>
                                    <li>remove</li>
                        </ul>
                </td>
                <td>
                        <div>How to handle merging if a user with this name already exists.</div>
                        <div><code>merge</code> - Update only the specified fields, preserve others (default).</div>
                        <div><code>replace</code> - Replace the entire user definition.</div>
                        <div><code>keep</code> - Keep existing user, skip this entry.</div>
                        <div><code>remove</code> - Remove the user entry entirely. Silently skipped if the entry does not exist.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Unique name identifier for the user.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>user</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>User authentication configuration.</div>
                        <div>Not required when <code>behavior</code> is V(remove).</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>auth-provider</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Authentication provider configuration (e.g., for GCP, Azure).</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>client-certificate</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Path to client certificate file.</div>
                        <div>Used for certificate-based authentication.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>client-certificate-data</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Base64 encoded client certificate.</div>
                        <div>Use instead of <code>client-certificate</code> for embedded certificates.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>client-key</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Path to client private key file.</div>
                        <div>Must be provided with <code>client-certificate</code>.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>client-key-data</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Base64 encoded client private key.</div>
                        <div>Use instead of <code>client-key</code> for embedded keys.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>exec</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Exec-based credential plugin configuration.</div>
                        <div>Used for external authentication providers.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
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
                        <div>Password for basic authentication.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>token</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Bearer token for authentication.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
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
                        <div>Username for basic authentication.</div>
                </td>
            </tr>


    </table>
    <br/>


Notes
-----

.. note::
   - Input data is merged by resource name (cluster, user, context).
   - Updates under O(clusters), O(users), and O(contexts) are matched by ``name`` against the kubeconfig loaded from O(path).
   - For an existing ``name``, each entry's ``behavior`` suboption controls the update.
   - The default is V(merge), which merges nested ``cluster``, ``user``, and ``context`` data so unspecified keys are preserved.
   - With V(replace), the previous entry for that name is dropped and only the new definition is used.
   - With V(keep), the existing entry is left unchanged.
   - With V(remove), the existing entry is deleted from the kubeconfig entirely. If no entry with that name exists, the operation is silently skipped.
   - This can be used to move kubeconfig files to a different location with different content.
   - This module does not validate cluster connectivity or authentication.
   - The module supports ``check_mode`` and will not write files when enabled.
   - The structure follows standard Kubernetes kubeconfig format as defined in the Kubernetes documentation.
   - Tokens and sensitive data should be protected using ansible-vault or environment variables.


See Also
--------

.. seealso::

   `Kubernetes kubeconfig documentation <https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/>`_
       Official Kubernetes documentation for kubeconfig files
   `kubectl config documentation <https://kubernetes.io/docs/reference/kubectl/generated/kubectl_config/>`_
       kubectl commands for working with kubeconfig files


Examples
--------

.. code-block:: yaml

    # Create a new kubeconfig file with a single cluster
    - name: Create basic kubeconfig
      kubernetes.core.kubeconfig:
        path: /home/user/.kube/config
        clusters:
          - name: production-cluster
            cluster:
              server: https://prod.k8s.example.com:6443
              certificate-authority-data: LS0tLS1CRUdJTi...
        users:
          - name: admin-user
            user:
              token: eyJhbGciOiJSUzI1NiIsImtpZCI6IiJ9...
        contexts:
          - name: prod-admin
            context:
              cluster: production-cluster
              user: admin-user
              namespace: production
        current_context: prod-admin

    - name: Add a second cluster to an existing kubeconfig without touching other entries
      kubernetes.core.kubeconfig:
        path: /home/user/.kube/config
        clusters:
          - name: staging-cluster
            cluster:
              server: https://staging.k8s.example.com:6443
              insecure-skip-tls-verify: true
        users:
          - name: staging-user
            user:
              client-certificate: /path/to/staging.crt
              client-key: /path/to/staging.key
        contexts:
          - name: staging-admin
            context:
              cluster: staging-cluster
              user: staging-user
              namespace: staging

    - name: Update only the token for an existing user, preserving all other user fields
      kubernetes.core.kubeconfig:
        path: /home/user/.kube/config
        users:
          - name: admin-user
            behavior: merge
            user:
              token: "{{ new_admin_token }}"

    - name: Replace a cluster definition entirely.
      kubernetes.core.kubeconfig:
        path: /home/user/.kube/config
        clusters:
          - name: production-cluster
            behavior: replace
            cluster:
              server: https://new-prod.k8s.example.com:6443
              certificate-authority-data: LS0tLS1CRUdJTi...

    - name: Remove a decommissioned cluster, user, and context
      kubernetes.core.kubeconfig:
        path: /home/user/.kube/config
        clusters:
          - name: old-cluster
            behavior: remove
        users:
          - name: old-user
            behavior: remove
        contexts:
          - name: old-context
            behavior: remove

    - name: Switch the active context
      kubernetes.core.kubeconfig:
        path: /home/user/.kube/config
        current_context: staging-admin

    - name: Copy a kubeconfig to a new location with an additional cluster merged in
      kubernetes.core.kubeconfig:
        path: /home/user/.kube/config
        dest: /home/user/.kube/config-ci
        clusters:
          - name: ci-cluster
            cluster:
              server: https://ci.k8s.example.com:6443
              insecure-skip-tls-verify: true



Return Values
-------------
Common return values are documented `here <https://docs.ansible.com/projects/ansible/latest/reference_appendices/common_return_values.html#common-return-values>`_, the following are the fields unique to this module:

.. raw:: html

    <table border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="1">Key</th>
            <th>Returned</th>
            <th width="100%">Description</th>
        </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>dest</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>The path where the kubeconfig was written.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">/home/user/.kube/config</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>kubeconfig</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>The complete kubeconfig data structure.</div>
                    <br/>
                </td>
            </tr>
    </table>
    <br/><br/>


Status
------


Authors
~~~~~~~

- Youssef Khalid Ali (@YoussefKhalidAli)
