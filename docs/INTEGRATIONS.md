# CI integrations

Install dependencies in the repository owner's runner. Pin a release or commit once one exists. Until then, install from a reviewed checkout.

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
