#!/usr/bin/env bash

set -eux
id=$*

if [[ "$id" == "all" ]] || [[ "$id" == "" ]]; then
    molecule test
else
    tags=$(tr '\n' ',' < "molecule/default/tags_${id}.txt")
    molecule test -- -v --tags "$tags"
fi