#!/usr/bin/env bash

set -eux

export ANSIBLE_ROLES_PATH="../"
USER_CREDENTIALS_DIR=$(pwd)

ansible-playbook playbooks/delete_resources.yml -e "user_credentials_dir=${USER_CREDENTIALS_DIR}" "$@"

{
export ANSIBLE_CALLBACKS_ENABLED=profile_tasks
export ANSIBLE_INVENTORY_ENABLED=kubernetes.core.k8s,yaml
export ANSIBLE_PYTHON_INTERPRETER=auto_silent

ansible-playbook playbooks/play.yml -i playbooks/test.inventory_k8s.yml "$@" &&

ansible-playbook playbooks/create_resources.yml -e "user_credentials_dir=${USER_CREDENTIALS_DIR}" "$@" &&

ansible-inventory -i playbooks/test_inventory_aliases_with_ssl_k8s.yml --list "$@" &&

ansible-inventory -i playbooks/test_inventory_aliases_no_ssl_k8s.yml --list "$@" &&

unset ANSIBLE_INVENTORY_ENABLED &&

ansible-playbook playbooks/delete_resources.yml -e "user_credentials_dir=${USER_CREDENTIALS_DIR}" "$@"

} || {
    ansible-playbook playbooks/delete_resources.yml -e "user_credentials_dir=${USER_CREDENTIALS_DIR}" "$@"
    exit 1
}