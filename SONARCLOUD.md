# SonarCloud

Dashboard:

[SonarCloud project overview](https://sonarcloud.io/project/overview?id=ansible-collections_kubernetes.core)

## CI integration

Sonar analysis is implemented in **[.github/workflows/sonarcloud.yml](.github/workflows/sonarcloud.yml)** as a **reusable workflow** (`on: workflow_call` only). It is **not** triggered by `workflow_run`.

**[.github/workflows/all_green_check.yaml](.github/workflows/all_green_check.yaml)** runs **linters** (on pull requests), **sanity**, **units**, and **coverage**, passes the aggregate **`all_green`** gate, then calls **`sonarcloud.yml`** via a **`sonarcloud`** job when the conditions below are met. The **coverage** job uploads a **`coverage`** artifact; the Sonar job downloads it in the **same** workflow run.

The caller runs on **`pull_request`** or **`push`**, so the reusable workflow inherits that **`github.event`**. **`actions/checkout`** uses **`github.event.pull_request.head.sha`** on pull requests and **`github.sha`** on push (Sonar-friendly checkout). PR parameters (**`sonar.pullrequest.*`**) are taken from **`github.event.pull_request`** (no `gh` API calls in **`sonarcloud.yml`**).

The scan step uses **`SonarSource/sonarqube-scan-action`** (pinned SHA in the workflow file) with **`sonar.python.coverage.reportPaths`** set from any **`coverage*.xml`** files found under the workspace after the artifact download. The overall flow (coverage in CI, then Sonar with XML) follows the same idea as [ansible-collections/amazon.aws#2871](https://github.com/ansible-collections/amazon.aws/pull/2871), using **`workflow_call`** from **`all_green`** instead of a separate **`workflow_run`** finalize workflow.

Workflow files:

- [.github/workflows/all_green_check.yaml](.github/workflows/all_green_check.yaml) -- **`all_green`** gate, **coverage** artifact upload, and **`sonarcloud`** job (**`uses: ./.github/workflows/sonarcloud.yml`**, passing only **`ANSIBLE_COLLECTIONS_ORG_SONAR_TOKEN_CICD_BOT`**) after **`all_green`** and **`coverage`** succeed, gated for **`push`** and same-repo **`pull_request`** when that secret is set.
- [.github/workflows/sonarcloud.yml](.github/workflows/sonarcloud.yml) -- **`scan`** job: checkout, download **`coverage`**, **`SONAR_ARGS`**, SonarCloud scan.

Scanner configuration lives in [sonar-project.properties](sonar-project.properties).

The **coverage** job (in **`all_green`**) uses **`ansible-test`** (`units --coverage`, then **`coverage combine`** / **`coverage xml`**), then writes **`coverage.xml`** with workspace paths normalized for Sonar. **`pytest-cov`** is listed in **`tests/unit/requirements.txt`** for parity and any direct pytest runs; **`ansible-test`** still owns the coverage data used in CI.

**`sonarcloud.yml`** declares a required secret **`ANSIBLE_COLLECTIONS_ORG_SONAR_TOKEN_CICD_BOT`** and **`permissions: contents: read`**, **`pull-requests: read`**.

Org secrets and fork PR behavior follow GitHub's [secrets in Actions](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions) documentation. The **`sonarcloud`** job is **`if:`**-gated so the org token is not used for fork-head checkouts; fork PRs still run **`all_green`** for CI without running Sonar.

## Branch protection (repository settings)

If **`SonarCloud scan`** or **`all_green`** should block merges, add them under **Settings** > **Branches** > **Required status checks** for the protected branch. That is not configured in YAML.
