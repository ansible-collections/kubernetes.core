#!/usr/bin/env bash
# Run `molecule test` on multiple scenario
# Scenario list provided as input

set -eux
scenario_list=$*

if [[ -z "$scenario_list" ]]; then
    molecule test --all
else
    for scenario in $scenario_list; do
        molecule test -s ${scenario}
    done
fi