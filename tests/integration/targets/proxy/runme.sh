#!/usr/bin/env bash

set -eux

docker rm -f squid

docker run --name squid -d -p 3128:3128 -v $(pwd)/files/squid.passwd:/etc/squid/passwd -v $(pwd)/files/squid.conf:/etc/squid/squid.conf sameersbn/squid:3.5.27-2

until [ "`docker inspect -f {{.State.Running}} squid`"=="true" ]; do
    sleep 1
done

python $(pwd)/ping_proxy.py

ansible-playbook playbook.yaml -v

docker rm -f squid