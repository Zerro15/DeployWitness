# CI integrations

[English](INTEGRATIONS.md) | [Русский](ru/CI_INTEGRATIONS.md) · [Documentation index](README.md)

Install dependencies in the repository owner's runner. Pin a release or commit once one exists. Until then, install from a reviewed checkout.

## GitHub Actions

The repository's [example workflow](../.github/workflows/example-check.yml) is manually dispatched (`workflow_dispatch`), uses `contents: read`, and compares the checked-in `examples/before/compose.yaml` and `examples/fixed/compose.yaml`. It demonstrates the CLI only. It does not discover pull request base/head, post a comment or summary, or use a published GitHub Action.

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
