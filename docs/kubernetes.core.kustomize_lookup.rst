.. _kubernetes.core.kustomize_lookup:


*************************
kubernetes.core.kustomize
*************************

**Build a set of kubernetes resources using a 'kustomization.yaml' file.**


Version added: 2.2.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Uses the kustomize or the kubectl tool.
- Return the result of ``kustomize build`` or ``kubectl kustomize``.



Requirements
------------
The below requirements are needed on the local Ansible controller node that executes this lookup.

- python >= 3.6


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
                    <b>binary_path</b>
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
                        <div>The path of a kustomize or kubectl binary to use.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dir</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"."</div>
                </td>
                    <td>
                    </td>
                <td>
                        <div>The directory path containing &#x27;kustomization.yaml&#x27;, or a git repository URL with a path suffix specifying same with respect to the repository root.</div>
                        <div>If omitted, &#x27;.&#x27; is assumed.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>enable_helm</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"False"</div>
                </td>
                    <td>
                    </td>
                <td>
                        <div>Enable the helm chart inflation generator</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>opt_dirs</b>
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
                        <div>An optional list of directories to search for the executable in addition to PATH.</div>
                </td>
            </tr>
    </table>
    <br/>


Notes
-----

.. note::
   - If both kustomize and kubectl are part of the PATH, kustomize will be used by the plugin.



Examples
--------

.. code-block:: yaml

    - name: Run lookup using kustomize
      ansible.builtin.set_fact:
        resources: "{{ lookup('kubernetes.core.kustomize', binary_path='/path/to/kustomize') }}"

    - name: Run lookup using kubectl kustomize
      ansible.builtin.set_fact:
        resources: "{{ lookup('kubernetes.core.kustomize', binary_path='/path/to/kubectl') }}"

    - name: Create kubernetes resources for lookup output
      kubernetes.core.k8s:
        definition: "{{ lookup('kubernetes.core.kustomize', dir='/path/to/kustomization') }}"

    - name: Create kubernetes resources for lookup output with `--enable-helm` set
      kubernetes.core.k8s:
        definition: "{{ lookup('kubernetes.core.kustomize', dir='/path/to/kustomization', enable_helm=True) }}"



Return Values
-------------
Common return values are documented `here <https://docs.ansible.com/ansible/latest/reference_appendices/common_return_values.html#common-return-values>`_, the following are the fields unique to this lookup:

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
                    <b>_list</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                    </div>
                </td>
                <td></td>
                <td>
                            <div>YAML string for the object definitions returned from the tool execution.</div>
                    <br/>
                        <div style="font-size: smaller"><b>Sample:</b></div>
                        <div style="font-size: smaller; color: blue; word-wrap: break-word; word-break: break-all;">{&#x27;kind&#x27;: &#x27;ConfigMap&#x27;, &#x27;apiVersion&#x27;: &#x27;v1&#x27;, &#x27;metadata&#x27;: {&#x27;name&#x27;: &#x27;my-config-map&#x27;, &#x27;namespace&#x27;: &#x27;default&#x27;}, &#x27;data&#x27;: {&#x27;key1&#x27;: &#x27;val1&#x27;}}</div>
                </td>
            </tr>
    </table>
    <br/><br/>


Status
------


Authors
~~~~~~~

- Aubin Bikouo (@abikouo)


.. hint::
    Configuration entries for each entry type have a low to high priority order. For example, a variable that is lower in the list will override a variable that is higher up.
