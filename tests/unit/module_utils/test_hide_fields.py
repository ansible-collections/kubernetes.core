from ansible_collections.kubernetes.core.plugins.module_utils.k8s.service import (
    hide_fields,
)


def test_hiding_missing_field_does_nothing():
    output = dict(
        kind="ConfigMap", metadata=dict(name="foo"), data=dict(one="1", two="2")
    )
    hidden_fields = ["doesnotexist"]
    assert hide_fields(output, hidden_fields) == output


def test_hiding_simple_field():
    output = dict(
        kind="ConfigMap", metadata=dict(name="foo"), data=dict(one="1", two="2")
    )
    hidden_fields = ["metadata"]
    expected = dict(kind="ConfigMap", data=dict(one="1", two="2"))
    assert hide_fields(output, hidden_fields) == expected


def test_hiding_only_key_in_dict_removes_dict():
    output = dict(kind="ConfigMap", metadata=dict(name="foo"), data=dict(one="1"))
    hidden_fields = ["data.one"]
    expected = dict(kind="ConfigMap", metadata=dict(name="foo"))
    assert hide_fields(output, hidden_fields) == expected


def test_hiding_all_keys_in_dict_removes_dict():
    output = dict(
        kind="ConfigMap", metadata=dict(name="foo"), data=dict(one="1", two="2")
    )
    hidden_fields = ["data.one", "data.two"]
    expected = dict(kind="ConfigMap", metadata=dict(name="foo"))
    assert hide_fields(output, hidden_fields) == expected


def test_hiding_multiple_fields():
    output = dict(
        kind="ConfigMap", metadata=dict(name="foo"), data=dict(one="1", two="2")
    )
    hidden_fields = ["metadata", "data.one"]
    expected = dict(kind="ConfigMap", data=dict(two="2"))
    assert hide_fields(output, hidden_fields) == expected


def test_hiding_dict_key():
    output = dict(
        kind="ConfigMap",
        metadata=dict(
            name="foo",
            annotations={
                "kubectl.kubernetes.io/last-applied-configuration": '{"testvalue"}'
            },
        ),
        data=dict(one="1", two="2"),
    )
    hidden_fields = [
        "metadata.annotations[kubectl.kubernetes.io/last-applied-configuration]",
    ]
    expected = dict(
        kind="ConfigMap", metadata=dict(name="foo"), data=dict(one="1", two="2")
    )
    assert hide_fields(output, hidden_fields) == expected


def test_hiding_list_value_key():
    output = dict(
        kind="Pod",
        metadata=dict(name="foo"),
        spec=dict(
            containers=[
                dict(
                    name="containers",
                    image="busybox",
                    env=[
                        dict(name="ENV1", value="env1"),
                        dict(name="ENV2", value="env2"),
                        dict(name="ENV3", value="env3"),
                    ],
                )
            ]
        ),
    )
    hidden_fields = ["spec.containers[0].env[1].value"]
    expected = dict(
        kind="Pod",
        metadata=dict(name="foo"),
        spec=dict(
            containers=[
                dict(
                    name="containers",
                    image="busybox",
                    env=[
                        dict(name="ENV1", value="env1"),
                        dict(name="ENV2"),
                        dict(name="ENV3", value="env3"),
                    ],
                )
            ]
        ),
    )
    assert hide_fields(output, hidden_fields) == expected


def test_hiding_last_list_item():
    output = dict(
        kind="Pod",
        metadata=dict(name="foo"),
        spec=dict(
            containers=[
                dict(
                    name="containers",
                    image="busybox",
                    env=[
                        dict(name="ENV1", value="env1"),
                    ],
                )
            ]
        ),
    )
    hidden_fields = ["spec.containers[0].env[0]"]
    expected = dict(
        kind="Pod",
        metadata=dict(name="foo"),
        spec=dict(
            containers=[
                dict(
                    name="containers",
                    image="busybox",
                )
            ]
        ),
    )
    assert hide_fields(output, hidden_fields) == expected


def test_hiding_nested_dicts_using_brackets():
    output = dict(
        kind="Pod",
        metadata=dict(name="foo"),
        spec=dict(
            containers=[
                dict(
                    name="containers",
                    image="busybox",
                    securityContext=dict(runAsUser=101),
                )
            ]
        ),
    )
    hidden_fields = ["spec.containers[0][securityContext][runAsUser]"]
    expected = dict(
        kind="Pod",
        metadata=dict(name="foo"),
        spec=dict(
            containers=[
                dict(
                    name="containers",
                    image="busybox",
                )
            ]
        ),
    )
    if hide_fields(output, hidden_fields) != expected:
        print(output)
        print(expected)
    assert hide_fields(output, hidden_fields) == expected
