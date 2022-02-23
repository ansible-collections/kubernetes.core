#!/usr/bin/env bash

set -eux

export ANSIBLE_INVENTORY_ENABLED=kubernetes.core.k8s,yaml
export ANSIBLE_PYTHON_INTERPRETER=auto_silent

ansible-playbook playbooks/play.yml -i playbooks/test.inventory_k8s.yml "$@"
