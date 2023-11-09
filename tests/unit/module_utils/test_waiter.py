import os
import time
from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.waiter import (
    DummyWaiter,
    Waiter,
    clock,
    custom_condition,
    deployment_ready,
    exists,
    get_waiter,
    pod_ready,
    resource_absent,
)
from kubernetes.dynamic.exceptions import NotFoundError
from kubernetes.dynamic.resource import ResourceInstance


def resources(filepath):
    current = Path(os.path.dirname(os.path.abspath(__file__)))
    with open(current / filepath) as fp:
        return [ResourceInstance(None, d) for d in yaml.safe_load_all(fp)]


RESOURCES = resources("fixtures/definitions.yml")
PODS = resources("fixtures/pods.yml")
DEPLOYMENTS = resources("fixtures/deployments.yml")


def test_clock_times_out():
    start = time.monotonic()
    for x in clock(5, 1):
        pass
    elapsed = int(time.monotonic() - start)
    assert x == 5
    assert 5 <= elapsed <= 6


@pytest.mark.parametrize(
    "resource,expected",
    zip(RESOURCES + [None, {}], [True, True, True, False, False, False]),
)
def test_exists_and_absent_checks_for_existence(resource, expected):
    assert exists(resource) is expected
    assert resource_absent(resource) is not expected


@pytest.mark.parametrize("pod,expected", zip(PODS, [True, False, True, True]))
def test_pod_ready_checks_readiness(pod, expected):
    assert pod_ready(pod) is expected


@pytest.mark.parametrize("pod,expected", zip(PODS, [True, False, False, False]))
def test_custom_condition_checks_readiness(pod, expected):
    condition = {"type": "www.example.com/gate", "status": "True"}
    assert custom_condition(condition, pod) is expected


@pytest.mark.parametrize("deployment,expected", zip(DEPLOYMENTS, [True, False]))
def test_deployment_ready_checks_readiness(deployment, expected):
    assert deployment_ready(deployment) is expected


def test_dummywaiter_returns_resource_immediately():
    resource = {
        "kind": "Pod",
        "apiVersion": "v1",
        "metadata": {"name": "foopod", "namespace": "foobar"},
    }
    result, instance, elapsed = DummyWaiter().wait(resource, 10, 100)
    assert result is True
    assert instance == resource
    assert elapsed == 0


def test_waiter_waits_for_missing_resource():
    spec = {"get.side_effect": NotFoundError(Mock())}
    client = Mock(**spec)
    resource = Mock()
    result, instance, elapsed = Waiter(client, resource, exists).wait(
        timeout=3,
        sleep=1,
        name=RESOURCES[0]["metadata"].get("name"),
        namespace=RESOURCES[0]["metadata"].get("namespace"),
    )
    assert result is False
    assert instance == {}
    assert abs(elapsed - 3) <= 1


@pytest.mark.parametrize("resource,expected", zip(RESOURCES, [True, True, True, False]))
def test_waiter_waits_for_resource_to_exist(resource, expected):
    result = resource.to_dict()
    spec = {"get.side_effect": [NotFoundError(Mock()), resource, resource, resource]}
    client = Mock(**spec)
    success, instance, elapsed = Waiter(client, Mock(), exists).wait(
        timeout=3,
        sleep=1,
        name=result["metadata"].get("name"),
        namespace=result["metadata"].get("namespace"),
    )
    assert success is expected
    assert instance == result
    assert abs(elapsed - 2) <= 1


def test_get_waiter_returns_correct_waiter():
    assert get_waiter(Mock(), PODS[0]).predicate == pod_ready
    waiter = get_waiter(Mock(), PODS[0], check_mode=True)
    assert isinstance(waiter, DummyWaiter)
    assert get_waiter(Mock(), PODS[0], state="absent").predicate == resource_absent
    assert (
        get_waiter(
            Mock(), PODS[0], condition={"type": "Ready", "status": "True"}
        ).predicate.func
        == custom_condition
    )
