# Copyright [2017] [Red Hat, Inc.]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.kubernetes.core.plugins.module_utils.apply import (
    apply_patch,
    merge,
)

tests = [
    dict(
        last_applied=dict(
            kind="ConfigMap", metadata=dict(name="foo"), data=dict(one="1", two="2")
        ),
        desired=dict(
            kind="ConfigMap", metadata=dict(name="foo"), data=dict(one="1", two="2")
        ),
        expected={},
    ),
    dict(
        last_applied=dict(
            kind="ConfigMap", metadata=dict(name="foo"), data=dict(one="1", two="2")
        ),
        desired=dict(
            kind="ConfigMap",
            metadata=dict(name="foo"),
            data=dict(one="1", two="2", three="3"),
        ),
        expected=dict(data=dict(three="3")),
    ),
    dict(
        last_applied=dict(
            kind="ConfigMap", metadata=dict(name="foo"), data=dict(one="1", two="2")
        ),
        desired=dict(
            kind="ConfigMap", metadata=dict(name="foo"), data=dict(one="1", three="3")
        ),
        expected=dict(data=dict(two=None, three="3")),
    ),
    dict(
        last_applied=dict(
            kind="ConfigMap",
            metadata=dict(name="foo", annotations=dict(this="one", hello="world")),
            data=dict(one="1", two="2"),
        ),
        desired=dict(
            kind="ConfigMap", metadata=dict(name="foo"), data=dict(one="1", three="3")
        ),
        expected=dict(metadata=dict(annotations=None), data=dict(two=None, three="3")),
    ),
    dict(
        last_applied=dict(
            kind="Service",
            metadata=dict(name="foo"),
            spec=dict(ports=[dict(port=8080, name="http")]),
        ),
        actual=dict(
            kind="Service",
            metadata=dict(name="foo"),
            spec=dict(ports=[dict(port=8080, protocol="TCP", name="http")]),
        ),
        desired=dict(
            kind="Service",
            metadata=dict(name="foo"),
            spec=dict(ports=[dict(port=8080, name="http")]),
        ),
        expected=dict(spec=dict(ports=[dict(port=8080, protocol="TCP", name="http")])),
    ),
    dict(
        last_applied=dict(
            kind="Service",
            metadata=dict(name="foo"),
            spec=dict(ports=[dict(port=8080, name="http")]),
        ),
        actual=dict(
            kind="Service",
            metadata=dict(name="foo"),
            spec=dict(ports=[dict(port=8080, protocol="TCP", name="http")]),
        ),
        desired=dict(
            kind="Service",
            metadata=dict(name="foo"),
            spec=dict(ports=[dict(port=8081, name="http")]),
        ),
        expected=dict(spec=dict(ports=[dict(port=8081, name="http")])),
    ),
    dict(
        last_applied=dict(
            kind="Service",
            metadata=dict(name="foo"),
            spec=dict(ports=[dict(port=8080, name="http")]),
        ),
        actual=dict(
            kind="Service",
            metadata=dict(name="foo"),
            spec=dict(ports=[dict(port=8080, protocol="TCP", name="http")]),
        ),
        desired=dict(
            kind="Service",
            metadata=dict(name="foo"),
            spec=dict(
                ports=[dict(port=8443, name="https"), dict(port=8080, name="http")]
            ),
        ),
        expected=dict(
            spec=dict(
                ports=[
                    dict(port=8443, name="https"),
                    dict(port=8080, name="http", protocol="TCP"),
                ]
            )
        ),
    ),
    dict(
        last_applied=dict(
            kind="Service",
            metadata=dict(name="foo"),
            spec=dict(
                ports=[dict(port=8443, name="https"), dict(port=8080, name="http")]
            ),
        ),
        actual=dict(
            kind="Service",
            metadata=dict(name="foo"),
            spec=dict(
                ports=[
                    dict(port=8443, protocol="TCP", name="https"),
                    dict(port=8080, protocol="TCP", name="http"),
                ]
            ),
        ),
        desired=dict(
            kind="Service",
            metadata=dict(name="foo"),
            spec=dict(ports=[dict(port=8080, name="http")]),
        ),
        expected=dict(spec=dict(ports=[dict(port=8080, name="http", protocol="TCP")])),
    ),
    dict(
        last_applied=dict(
            kind="Service",
            metadata=dict(name="foo"),
            spec=dict(
                ports=[
                    dict(port=8443, name="https", madeup="xyz"),
                    dict(port=8080, name="http"),
                ]
            ),
        ),
        actual=dict(
            kind="Service",
            metadata=dict(name="foo"),
            spec=dict(
                ports=[
                    dict(port=8443, protocol="TCP", name="https", madeup="xyz"),
                    dict(port=8080, protocol="TCP", name="http"),
                ]
            ),
        ),
        desired=dict(
            kind="Service",
            metadata=dict(name="foo"),
            spec=dict(ports=[dict(port=8443, name="https")]),
        ),
        expected=dict(
            spec=dict(
                ports=[dict(madeup=None, port=8443, name="https", protocol="TCP")]
            )
        ),
    ),
    dict(
        last_applied=dict(
            kind="Pod",
            metadata=dict(name="foo"),
            spec=dict(
                containers=[
                    dict(
                        name="busybox",
                        image="busybox",
                        resources=dict(
                            requests=dict(cpu="100m", memory="100Mi"),
                            limits=dict(cpu="100m", memory="100Mi"),
                        ),
                    )
                ]
            ),
        ),
        actual=dict(
            kind="Pod",
            metadata=dict(name="foo"),
            spec=dict(
                containers=[
                    dict(
                        name="busybox",
                        image="busybox",
                        resources=dict(
                            requests=dict(cpu="100m", memory="100Mi"),
                            limits=dict(cpu="100m", memory="100Mi"),
                        ),
                    )
                ]
            ),
        ),
        desired=dict(
            kind="Pod",
            metadata=dict(name="foo"),
            spec=dict(
                containers=[
                    dict(
                        name="busybox",
                        image="busybox",
                        resources=dict(
                            requests=dict(cpu="50m", memory="50Mi"),
                            limits=dict(memory="50Mi"),
                        ),
                    )
                ]
            ),
        ),
        expected=dict(
            spec=dict(
                containers=[
                    dict(
                        name="busybox",
                        image="busybox",
                        resources=dict(
                            requests=dict(cpu="50m", memory="50Mi"),
                            limits=dict(cpu=None, memory="50Mi"),
                        ),
                    )
                ]
            )
        ),
    ),
    dict(
        desired=dict(
            kind="Pod",
            spec=dict(
                containers=[
                    dict(
                        name="hello",
                        volumeMounts=[dict(name="test", mountPath="/test")],
                    )
                ],
                volumes=[dict(name="test", configMap=dict(name="test"))],
            ),
        ),
        last_applied=dict(
            kind="Pod",
            spec=dict(
                containers=[
                    dict(
                        name="hello",
                        volumeMounts=[dict(name="test", mountPath="/test")],
                    )
                ],
                volumes=[dict(name="test", configMap=dict(name="test"))],
            ),
        ),
        actual=dict(
            kind="Pod",
            spec=dict(
                containers=[
                    dict(
                        name="hello",
                        volumeMounts=[
                            dict(name="test", mountPath="/test"),
                            dict(
                                mountPath="/var/run/secrets/kubernetes.io/serviceaccount",
                                name="default-token-xyz",
                            ),
                        ],
                    )
                ],
                volumes=[
                    dict(name="test", configMap=dict(name="test")),
                    dict(
                        name="default-token-xyz",
                        secret=dict(secretName="default-token-xyz"),
                    ),
                ],
            ),
        ),
        expected=dict(
            spec=dict(
                containers=[
                    dict(
                        name="hello",
                        volumeMounts=[
                            dict(name="test", mountPath="/test"),
                            dict(
                                mountPath="/var/run/secrets/kubernetes.io/serviceaccount",
                                name="default-token-xyz",
                            ),
                        ],
                    )
                ],
                volumes=[
                    dict(name="test", configMap=dict(name="test")),
                    dict(
                        name="default-token-xyz",
                        secret=dict(secretName="default-token-xyz"),
                    ),
                ],
            )
        ),
    ),
    # This next one is based on a real world case where definition was mostly
    # str type and everything else was mostly unicode type (don't ask me how)
    dict(
        last_applied={
            "kind": "ConfigMap",
            "data": {"one": "1", "three": "3", "two": "2"},
            "apiVersion": "v1",
            "metadata": {"namespace": "apply", "name": "apply-configmap"},
        },
        actual={
            "kind": "ConfigMap",
            "data": {"one": "1", "three": "3", "two": "2"},
            "apiVersion": "v1",
            "metadata": {
                "namespace": "apply",
                "name": "apply-configmap",
                "resourceVersion": "1714994",
                "creationTimestamp": "2019-08-17T05:08:05Z",
                "annotations": {},
                "selfLink": "/api/v1/namespaces/apply/configmaps/apply-configmap",
                "uid": "fed45fb0-c0ac-11e9-9d95-025000000001",
            },
        },
        desired={
            "kind": "ConfigMap",
            "data": {"one": "1", "three": "3", "two": "2"},
            "apiVersion": "v1",
            "metadata": {"namespace": "apply", "name": "apply-configmap"},
        },
        expected=dict(),
    ),
    # apply a Deployment, then scale the Deployment (which doesn't affect last-applied)
    # then apply the Deployment again. Should un-scale the Deployment
    dict(
        last_applied={
            "kind": "Deployment",
            "spec": {
                "replicas": 1,
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "name": "this_must_exist",
                                "envFrom": [
                                    {"configMapRef": {"name": "config-xyz"}},
                                    {"secretRef": {"name": "config-wxy"}},
                                ],
                            }
                        ]
                    }
                },
            },
            "metadata": {"namespace": "apply", "name": "apply-deployment"},
        },
        actual={
            "kind": "Deployment",
            "spec": {
                "replicas": 0,
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "name": "this_must_exist",
                                "envFrom": [
                                    {"configMapRef": {"name": "config-xyz"}},
                                    {"secretRef": {"name": "config-wxy"}},
                                ],
                            }
                        ]
                    }
                },
            },
            "metadata": {"namespace": "apply", "name": "apply-deployment"},
        },
        desired={
            "kind": "Deployment",
            "spec": {
                "replicas": 1,
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "name": "this_must_exist",
                                "envFrom": [{"configMapRef": {"name": "config-abc"}}],
                            }
                        ]
                    }
                },
            },
            "metadata": {"namespace": "apply", "name": "apply-deployment"},
        },
        expected={
            "spec": {
                "replicas": 1,
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "name": "this_must_exist",
                                "envFrom": [{"configMapRef": {"name": "config-abc"}}],
                            }
                        ]
                    }
                },
            }
        },
    ),
    dict(
        last_applied={"kind": "MadeUp", "toplevel": {"original": "entry"}},
        actual={
            "kind": "MadeUp",
            "toplevel": {
                "original": "entry",
                "another": {"nested": {"entry": "value"}},
            },
        },
        desired={
            "kind": "MadeUp",
            "toplevel": {
                "original": "entry",
                "another": {"nested": {"entry": "value"}},
            },
        },
        expected={},
    ),
]


def test_merges():
    for test in tests:
        assert (
            merge(
                test["last_applied"],
                test["desired"],
                test.get("actual", test["last_applied"]),
            )
            == test["expected"]
        )


def test_apply_patch():
    actual = dict(
        kind="ConfigMap",
        metadata=dict(
            name="foo",
            annotations={
                "kubectl.kubernetes.io/last-applied-configuration": '{"data":{"one":"1","two":"2"},"kind":"ConfigMap",'
                '"metadata":{"annotations":{"hello":"world","this":"one"},"name":"foo"}}',
                "this": "one",
                "hello": "world",
            },
        ),
        data=dict(one="1", two="2"),
    )
    desired = dict(
        kind="ConfigMap", metadata=dict(name="foo"), data=dict(one="1", three="3")
    )
    expected = dict(
        metadata=dict(
            annotations={
                "kubectl.kubernetes.io/last-applied-configuration": '{"data":{"one":"1","three":"3"},"kind":"ConfigMap","metadata":{"name":"foo"}}',
                "this": None,
                "hello": None,
            }
        ),
        data=dict(two=None, three="3"),
    )
    assert apply_patch(actual, desired) == (actual, expected)
