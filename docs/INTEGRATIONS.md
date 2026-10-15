# CI integrations

[English](INTEGRATIONS.md) | [Русский](ru/CI_INTEGRATIONS.md) · [Documentation index](README.md)

Install dependencies in the repository owner's runner. Pin a release or commit once one exists. Until then, install from a reviewed checkout.

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
    uses: Zerro15/DeployWitness/.github/workflows/deploywitness-pr.yml@main
    with:
      deploywitness_ref: main
```

For production use, replace both `@main` and `deploywitness_ref: main` with the same reviewed DeployWitness commit SHA. The workflow checks out the target repository's base commit and DeployWitness source separately, fetches the PR head as Git data, and writes the report to the GitHub Actions job summary. It does not check out or execute PR code, create comments, or send configuration to a DeployWitness service.

### View the report

Open the repository's **Actions** tab, select the **DeployWitness** run for your pull request, and read the **workflow run summary**. The Markdown report is shown there under the job summary. Open the job itself only when you need step logs; DeployWitness does not post a pull request comment.

PROVEN_CONFIG_BREAK fails the check. POTENTIAL_RISK is advisory. UNKNOWN fails visibly as inconclusive. A clean result means only that implemented checks found no issue. Added/deleted Compose files, multiple Compose files in the same directory, unsupported features, or oversized inputs are reported as UNKNOWN.

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
