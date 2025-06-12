#!/usr/bin/env bash
set -eux
export ANSIBLE_ROLES_PATH=../
ansible-playbook playbooks/play.yaml -i inventory.ini "$@"