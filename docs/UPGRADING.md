# Upgrade guide

[English](UPGRADING.md) | [Русский](ru/UPGRADING.md) · [Documentation index](README.md)

DeployWitness is pre-1.0. Treat upgrades as potentially breaking and review the release notes before changing the pinned commit or package version.

## GitHub Actions users

Update the reusable workflow ref and its `deploywitness_ref` input together to the same reviewed full 40-character commit SHA. Read the release notes and rerun a known safe and known contract-breaking fixture in a test pull request. The result appears in the workflow run summary; the workflow does not post PR comments.

## Python package users

Create a fresh environment when changing alpha versions, install the chosen wheel or source checkout, and run `deploywitness version`. Do not assume the witness JSON schema is stable before 1.0. No migration step is currently required; keep prior reports if they are needed for audit history.
