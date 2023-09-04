from ansible_collections.kubernetes.core.plugins.module_utils.k8s.service import (
    hide_fields,
)

tests = [
    dict(
        output=dict(
            kind="ConfigMap", metadata=dict(name="foo"), data=dict(one="1", two="2")
        ),
        hide_fields=["metadata"],
        expected=dict(kind="ConfigMap", data=dict(one="1", two="2")),
    ),
    dict(
        output=dict(
            kind="ConfigMap",
            metadata=dict(
                name="foo",
                annotations={
                    "kubectl.kubernetes.io/last-applied-configuration": '{"testvalue"}'
                },
            ),
            data=dict(one="1", two="2"),
        ),
        hide_fields=[
            "metadata.annotations[kubectl.kubernetes.io/last-applied-configuration]",
            "data.one",
        ],
        expected=dict(kind="ConfigMap", metadata=dict(name="foo"), data=dict(two="2")),
    ),
    dict(
        output=dict(
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
        ),
        hide_fields=["spec.containers[0].env[1].value"],
        expected=dict(
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
        ),
    ),
]


def test_hide_fields():
    for test in tests:
        if hide_fields(test["output"], test["hide_fields"]) != test["expected"]:
            print(test["output"])
            print(hide_fields(test["output"], test["hide_fields"]))
            print(test["expected"])
        assert hide_fields(test["output"], test["hide_fields"]) == test["expected"]
