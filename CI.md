# Continuous Integration (CI)

## Kubernetes Upstream Testing

GitHub Actions are used to run the CI for the kubernetes.core collection. The workflows used for the CI can be found [here](https://github.com/ansible-collections/kubernetes.core/tree/main/.github/workflows). These workflows include jobs to run the unit tests, sanity tests, linters, integration tests, and changelog checks.

The collection uses reusable workflows from [ansible-network/github_actions](https://github.com/ansible-network/github_actions) for standardized testing.

To learn more about the testing strategy, see [this proposal](https://github.com/ansible-collections/cloud-content-handbook/blob/main/Proposals/core_collection_dependency.md).

### PR Testing Workflows

The following tests run on every pull request:

| Job | Description | Python Versions | ansible-core Versions |
| --- | ----------- | --------------- | --------------------- |
| Changelog | Checks for the presence of changelog fragments | 3.12 | devel |
| Linters | Runs `black`, `flake8`, `isort`, `yamllint`, and `ansible-lint` on plugins and tests | 3.10 | devel |
| Sanity | Runs ansible sanity checks | See compatibility table below | Determined by reusable workflow |
| Unit tests | Executes unit test cases | See compatibility table below | Determined by reusable workflow |
| Integration tests | Executes integration test suites using KinD cluster (split across 8 jobs, tests with Turbo mode enabled/disabled) | 3.12 | milestone |

### Python Version Compatibility by ansible-core Version

These are determined by the reusable workflows from [ansible-network/github_actions](https://github.com/ansible-network/github_actions) and the collection's minimum requirements.

For the official Ansible core support matrix, see the [Ansible documentation](https://docs.ansible.com/ansible/latest/reference_appendices/release_and_maintenance.html#ansible-core-support-matrix).

The collection requires:
- **ansible-core**: >=2.16
- **Python**: 3.10+

| ansible-core Version | Sanity Tests | Unit Tests | Integration Tests |
| -------------------- | ------------ | ---------- | ----------------- |
| devel | 3.12, 3.13, 3.14 | 3.12, 3.13 | - |
| stable-2.20 | 3.12, 3.13, 3.14 | 3.12, 3.13, 3.14 | - |
| stable-2.19 | 3.11, 3.12, 3.13 | 3.11, 3.12, 3.13 | - |
| stable-2.18 | 3.11, 3.12, 3.13 | 3.11, 3.12, 3.13 | - |
| stable-2.17 | 3.10, 3.11, 3.12 | 3.10, 3.11, 3.12 | - |
| stable-2.16 | 3.10, 3.11 | 3.10, 3.11 | - |
| milestone | - | - | 3.12 |

**Note**:
- ansible-core 2.16 reached EOL in May 2025.
- ansible-core 2.17 reached EOL in November 2025.

### Integration Test Details

Integration tests have specific characteristics:
- Run on a KinD (Kubernetes in Docker) cluster using node image `kindest/node:v1.29.2`
- Split across 8 parallel jobs using `ansible_test_splitter`
- Execute twice for each test target: once with Turbo mode enabled, once with Turbo mode disabled
- Require additional collection dependencies: `cloud.common`, `ansible.posix`, `community.general`
- Use Python 3.12 with `milestone` ansible-core version

### Additional Dependencies

The collection depends on the following for integration testing:
- **Kubernetes cluster**: KinD v1.29.2 node image
- **Python packages**: kubernetes>=24.2.0, jsonpatch, kubernetes-validate, requests-oauthlib
- **Collections**: cloud.common, ansible.posix, community.general
- **External tools**: Helm v3.x (required for Helm module tests)

### Turbo Mode Testing

Integration tests are executed with both Turbo mode enabled and disabled via the `ENABLE_TURBO_MODE` environment variable. Turbo mode is a tech preview feature provided by the `cloud.common` collection that uses persistent connections for improved performance.
