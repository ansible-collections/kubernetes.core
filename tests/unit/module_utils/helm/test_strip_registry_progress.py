# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
import yaml
from ansible_collections.kubernetes.core.plugins.module_utils.helm import (
    strip_registry_progress,
)

# What helm's registry client prints, verbatim. Since helm 4.2.1 this goes to
# stdout ahead of the command's real output (helm/helm#32056).
PULLED = "Pulled: registry.example.com/charts/demochart:109.0.1_up1.0.2\n"
DIGEST = (
    "Digest: sha256:41e9b37f85fa7f5df5fc7f2b7b068eb56ae1592784eee28f535563b599850249\n"
)
PUSHED = "Pushed: registry.example.com/charts/demochart:109.0.1_up1.0.2\n"
UNDERSCORE_WARNING = (
    "registry.example.com/charts/demochart:109.0.1_up1.0.2 contains an underscore.\n"
    "\n"
    "OCI artifact references (e.g. tags) do not support the plus sign (+). To support\n"
    "storing semantic versions, Helm adopts the convention of changing plus (+) to\n"
    "an underscore (_) in chart version tags when pushing to a registry and back to\n"
    "a plus (+) when pulling from a registry.\n"
)

# 'helm show chart' output. Note that helm marshals Chart.yaml with sorted keys, so
# 'annotations' precedes 'apiVersion' and the metadata does not reliably start with
# a fixed key.
CHART_YAML = (
    "annotations:\n"
    "  category: Demo\n"
    "apiVersion: v2\n"
    "appVersion: 1.16.0\n"
    "description: A Helm chart for Kubernetes\n"
    "name: demochart\n"
    "type: application\n"
    "version: 109.0.1+up1.0.2\n"
)

# 'helm template' output.
MANIFESTS = (
    "---\n"
    "# Source: demochart/templates/serviceaccount.yaml\n"
    "apiVersion: v1\n"
    "kind: ServiceAccount\n"
    "metadata:\n"
    "  name: rel-demochart\n"
)

# 'helm template --output-dir' output.
WROTE = (
    "wrote outdir/demochart/templates/serviceaccount.yaml\n"
    "wrote outdir/demochart/templates/service.yaml\n"
)


@pytest.mark.parametrize(
    "payload",
    [CHART_YAML, MANIFESTS, WROTE, ""],
    ids=["show_chart", "template", "template_output_dir", "empty"],
)
@pytest.mark.parametrize(
    "progress",
    [
        "",
        PULLED + DIGEST,
        PULLED + DIGEST + UNDERSCORE_WARNING,
        PUSHED + DIGEST + UNDERSCORE_WARNING,
    ],
    ids=["none", "pulled_digest", "with_warning", "pushed_with_warning"],
)
def test_progress_is_stripped_and_payload_is_untouched(progress, payload):
    assert strip_registry_progress(progress + payload) == payload


def test_show_chart_output_is_parseable_once_stripped():
    # Unstripped, the free-text warning makes this invalid YAML.
    out = PULLED + DIGEST + UNDERSCORE_WARNING + CHART_YAML
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load(out)

    chart_info = yaml.safe_load(strip_registry_progress(out))
    assert chart_info["name"] == "demochart"
    assert chart_info["version"] == "109.0.1+up1.0.2"
    assert chart_info["annotations"] == {"category": "Demo"}


def test_pulled_and_digest_alone_parse_as_yaml_but_pollute_the_result():
    # Without the warning the output is still valid YAML, so the pollution is silent.
    assert yaml.safe_load(PULLED + DIGEST + CHART_YAML)["Pulled"]
    assert "Pulled" not in yaml.safe_load(
        strip_registry_progress(PULLED + DIGEST + CHART_YAML)
    )


def test_reworded_warning_is_left_alone():
    # A message helm no longer emits verbatim must not be partially consumed: better
    # to fail loudly than to silently drop a line of real output.
    reworded = UNDERSCORE_WARNING.replace("plus sign (+)", "plus character (+)")
    out = PULLED + DIGEST + reworded + CHART_YAML
    assert strip_registry_progress(out) == reworded + CHART_YAML


def test_progress_like_lines_inside_the_payload_are_kept():
    payload = "description: |\n  Digest: not a helm message\n" + CHART_YAML
    assert strip_registry_progress(PULLED + payload) == payload
