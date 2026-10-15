# CI integrations

[English](INTEGRATIONS.md) | [Русский](ru/CI_INTEGRATIONS.md) · [Documentation index](README.md)

The analysis runs on the repository owner's GitHub-hosted runner. The workflow itself and the analyzer source must both be pinned to the same reviewed, full 40-character DeployWitness commit SHA; branch names such as `main` are rejected for the analyzer input.

## GitHub Actions

DeployWitness provides a reusable workflow that compares the pull request base and head on the repository owner's GitHub-hosted runner. Add a caller workflow such as:

```yaml
name: DeployWitness
on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read

jobs:
  compose-analysis:
    uses: Zerro15/DeployWitness/.github/workflows/deploywitness-pr.yml@REPLACE_WITH_REVIEWED_40_CHARACTER_SHA
    with:
      deploywitness_ref: REPLACE_WITH_THE_SAME_SHA
```

Replace both placeholders with the same reviewed full SHA before committing the workflow. To obtain it, inspect the DeployWitness commit you reviewed (or a published release commit); use that SHA in both places. The reusable workflow checks out the target repository's base commit and DeployWitness source separately, fetches the PR head as Git data, and writes the report to the GitHub Actions job summary. It does not check out or execute PR code, create comments, or send configuration to a DeployWitness service. The included Actions dependencies are also pinned to full commit SHAs.

The caller needs only `contents: read`. It listens to `pull_request` events, so fork PRs use GitHub's read-only token/no-secret model; a real fork-originated run has not yet been exercised for this alpha. Repositories may need to approve a first-time contributor's workflow run.

To try it, add the workflow under `.github/workflows/deploywitness.yml`, open a PR that changes a supported Compose filename (`compose.yaml`, `compose.yml`, `docker-compose.yaml`, or `docker-compose.yml`), then inspect its Actions run. A safe edit should report `NO_FINDING`; removing a relationship only warns unless an explicit contract proves it; unsupported or incomplete input reports `UNKNOWN` and fails visibly. The complete supported-input matrix is in [Supported Compose features](SUPPORTED_COMPOSE_FEATURES.md).

### View the report

Open the repository's **Actions** tab, select the **DeployWitness** run for your pull request, and read the **workflow run summary**. The Markdown report is shown there under the job summary. Open the job itself only when you need step logs; DeployWitness does not post a pull request comment.

`PROVEN_CONFIG_BREAK` fails the check. `POTENTIAL_RISK` is advisory. `UNKNOWN` fails visibly as inconclusive. A clean result means only that implemented checks found no issue. Added/deleted Compose files, multiple Compose files in the same directory, changed `.env` or other adjacent YAML inputs, unsupported features, or oversized inputs are reported as `UNKNOWN`.

The [manual example workflow](../.github/workflows/example-check.yml) remains available for trying the CLI against the repository's fixed examples.

## GitLab

```yaml
deploywitness:
  image: python:3.12
  script:
    - pip install .
    - deploywitness check --base examples/before/compose.yaml --head examples/after/compose.yaml
```

## Forgejo Actions

```yaml
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install .
      - run: deploywitness check --base examples/before/compose.yaml --head examples/after/compose.yaml
```

The examples compare checked-in files. To inspect a PR, your CI must provide trusted base and head files explicitly. Do not execute untrusted PR code with privileged credentials.
