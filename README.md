# Kubernetes Collection for Ansible

This repo will be the future home of all `kubernetes.core` development. This Ansible Content Collection began as `community.kubernetes` and, as of the release of 1.1.0, is in the process of being transitioned to this new name. See [kubernetes.community issue #221](https://github.com/ansible-collections/community.kubernetes/issues/221) for more. 

```yaml
---
collections:
  - name: kubernetes.core
    version: 1.1.1
```

It's preferable to use content in this collection using their Fully Qualified Collection Namespace (FQCN), for example `kubernetes.core.k8s_info`:

```yaml
---
- hosts: localhost
  gather_facts: false
  connection: local

  tasks:
    - name: Ensure the myapp Namespace exists.
      kubernetes.core.k8s:
        api_version: v1
        kind: Namespace
        name: myapp
        state: present

    - name: Ensure the myapp Service exists in the myapp Namespace.
      kubernetes.core.k8s:
        state: present
        definition:
          apiVersion: v1
          kind: Service
          metadata:
            name: myapp
            namespace: myapp
          spec:
            type: LoadBalancer
            ports:
            - port: 8080
              targetPort: 8080
            selector:
              app: myapp

    - name: Get a list of all Services in the myapp namespace.
      kubernetes.core.k8s_info:
        kind: Service
        namespace: myapp
      register: myapp_services

    - name: Display number of Services in the myapp namespace.
      debug:
        var: myapp_services.resources | count
```

If upgrading older playbooks which were built prior to Ansible 2.10 and this collection's existence, you can also define `collections` in your play and refer to this collection's modules as you did in Ansible 2.9 and below, as in this example:

```yaml
---
- hosts: localhost
  gather_facts: false
  connection: local

  collections:
    - kubernetes.core

  tasks:
    - name: Ensure the myapp Namespace exists.
      k8s:
        api_version: v1
        kind: Namespace
        name: myapp
        state: present
```

For documentation on how to use individual modules and other content included in this collection, please see the links in the 'Included content' section earlier in this README.

## More Information

For more information about Ansible's Kubernetes integration, join the `#ansible-kubernetes` channel on Freenode IRC, and browse the resources in the [Kubernetes Working Group](https://github.com/ansible/community/wiki/Kubernetes) Community wiki page.

## License

GNU General Public License v3.0 or later

See LICENCE to see the full text.
