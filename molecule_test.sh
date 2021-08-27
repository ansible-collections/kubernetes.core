#!/usr/bin/env bash

set -eux
id=$*

if [[ "$id" == "all" ]] || [[ "$id" == "" ]]; then
    molecule test
else
    tags=$(cat molecule/default/tags_${id}.txt | tr '\n' ',')
    molecule test -- -v --tags $tags
fi