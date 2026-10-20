# Running Helm Integration Tests Locally

This guide explains how to run the `helm*` integration test targets locally using `ansible-test`.

## Prerequisites

- `ansible-test` available in your environment (installed with `ansible-core`)
- A Kubernetes cluster accessible via `kubectl` (for targets that interact with a cluster)

## Configuration

Create an `integration_config.yml` file under `tests/integration/` with the following variables:

```yaml
setup_helm_version: vx.x.x # e.g v4.2.1
helm_install_path: /path/to/helm/directory
```

### Variables

| Variable | Description |
|---|---|
| `setup_helm_version` | The Helm version to install (e.g. `v4.2.1`). The `v` prefix is optional and will be added automatically if omitted. |
| `helm_install_path` | Path to a directory that either already contains a `helm` executable matching the version set in `setup_helm_version`, or an empty/non-existent directory where Helm will be downloaded and installed. |

If a `helm` binary already exists at `<helm_install_path>/helm`, the setup will skip the download and use the existing binary directly.

## Running Tests

Run a specific Helm test target with:

```bash
ansible-test integration --python <version> -v --no-temp-workdir <target>
```

For example, to run the `helm` target with Python 3.12:

```bash
ansible-test integration --python 3.12 -v --no-temp-workdir helm
```

You can run multiple targets in a single command:

```bash
ansible-test integration --python 3.12 -v --no-temp-workdir helm helm_diff helm_plugin
```
