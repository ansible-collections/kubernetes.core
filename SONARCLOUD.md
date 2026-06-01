# SonarCloud

Dashboard:

[SonarCloud project overview](https://sonarcloud.io/project/overview?id=ansible-collections_kubernetes.core)

## CI integration

Sonar analysis is implemented in **[.github/workflows/sonarcloud.yml](.github/workflows/sonarcloud.yml)**, triggered by **`workflow_run`** when the **`all_green`** workflow completes successfully (same pattern as [ansible-collections/amazon.aws](https://github.com/ansible-collections/amazon.aws)).

**[.github/workflows/all_green_check.yaml](.github/workflows/all_green_check.yaml)** runs **linters** (on pull requests), **sanity**, **units**, and an independent **coverage** job, then passes the aggregate **`all_green`** gate. The **coverage** job uploads a **`coverage`** artifact; **[sonarcloud.yml](.github/workflows/sonarcloud.yml)** downloads it from that run via **`dawidd6/action-download-artifact`** and passes **`sonar.python.coverage.reportPaths`** to the scanner.

The scan step uses **`SonarSource/sonarqube-scan-action`** (pinned SHA in the workflow file). PR parameters (**`sonar.pullrequest.*`**) are resolved with **`gh`** when the triggering event was a pull request.

Workflow files:

- [.github/workflows/all_green_check.yaml](.github/workflows/all_green_check.yaml) — **`all_green`** gate and **coverage** artifact upload (coverage runs independently of sanity/units so XML is produced even when the matrix is still running).
- [.github/workflows/sonarcloud.yml](.github/workflows/sonarcloud.yml) — **`finalize`** job on **`workflow_run`** (`all_green`): checkout **`head_sha`**, download **`coverage*`**, **`SONAR_ARGS`**, SonarCloud scan.

Scanner configuration lives in [sonar-project.properties](sonar-project.properties).

The **coverage** job uses **`ansible-test`** (`units --coverage`, then **`coverage combine`** / **`coverage xml`**), writes **`coverage.xml`** at the repo root, and rewrites paths (workspace prefix and **`ansible_collections/kubernetes/core/`**) so they match **`sonar.sources=.`**. **`pytest-cov`** is listed in **`tests/unit/requirements.txt`** for parity; **`ansible-test`** owns the XML used in CI.

**`sonarcloud.yml`** needs **`permissions: actions: read`** for artifact download and uses org secret **`ANSIBLE_COLLECTIONS_ORG_SONAR_TOKEN_CICD_BOT`**.

Fork PRs still run **`all_green`** for CI; Sonar is skipped when **`head_repository`** is not this repository (fork-head PRs). Same-repo PRs and upstream **`push`** events run Sonar after **`all_green`** succeeds.

## Branch protection (repository settings)

If **`SonarCloud scan`** or **`all_green`** should block merges, add them under **Settings** > **Branches** > **Required status checks** for the protected branch. That is not configured in YAML.
