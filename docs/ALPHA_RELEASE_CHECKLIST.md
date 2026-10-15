# Alpha release checklist

[English](ALPHA_RELEASE_CHECKLIST.md) | [Русский](ru/ALPHA_RELEASE_CHECKLIST.md) · [Documentation index](README.md)

This checklist prepares `0.1.0a1`; it does not publish a release or package.

## Before tagging

- [ ] Merge only reviewed PRs; confirm `main` contains the intended source and documentation.
- [ ] Select the exact version and commit. Keep `pyproject.toml`, `CHANGELOG.md`, and release notes aligned.
- [ ] Run `python -m pytest`, `python -m ruff check .`, `python -m mypy src`, `python scripts/check_i18n.py`, and `git diff --check`.
- [ ] Build with `python -m build`; inspect wheel and sdist contents.
- [ ] Generate `SHA256SUMS.txt` from the exact wheel and sdist, verify both entries, and attach the file with the artifacts.
- [ ] Create a clean Python 3.12 virtual environment, install the wheel, run `deploywitness --help`, `deploywitness version`, and a checked-in example.
- [ ] Confirm workflow action dependencies and reusable workflow are pinned to reviewed commits; verify green CI for the exact commit.
- [ ] Review the [supported feature matrix](SUPPORTED_COMPOSE_FEATURES.md), known limitations, English/Russian instructions, and upgrade notes.
- [ ] State clearly that a real fork-originated PR run has not yet been verified, if still true at release time.

## GitHub Release plan

1. After maintainer approval, create an annotated `v0.1.0a1` tag on the reviewed commit.
2. Create a GitHub pre-release from that tag using [`releases/0.1.0a1.md`](releases/0.1.0a1.md); include wheel and sdist only if their checksums and contents were verified.
3. Attach `SHA256SUMS.txt` and link the [installation](GETTING_STARTED.md), limitations, and upgrade docs. Do not call the alpha production-ready.

## First public announcement

1. Publish the GitHub pre-release only after the checklist above is complete and the remaining fork-test limitation is stated.
2. Announce it first in the repository's GitHub Discussions or README release section, linking directly to the release, installation guide, feature matrix, and security policy.
3. Keep the announcement scoped: early Compose alpha, supported static checks, user-owned runners, no backend or telemetry, and known limitations. Do not claim full Compose compatibility, runtime outage prediction, or production readiness.

## PyPI plan (separate approval)

PyPI publication is not part of GitHub Release creation. If separately approved and trusted publishing is configured for the project, use that flow (or another maintainer-controlled method), upload only the verified artifacts for the tagged commit, then test installation in a fresh environment. Do not add long-lived PyPI credentials to repository secrets for this alpha.

## Supported capabilities at alpha

| Area | Supported now | Conservative result when incomplete |
| --- | --- | --- |
| CLI | `scan`, file-to-file `check`, text/Markdown/JSON reports | Explicit errors for invalid input |
| Compose | One effective YAML file per side; modeled services, `depends_on`, networks, mounts, selected environment keys | `UNKNOWN` for unsupported or unresolved semantics |
| Witnesses | Static proof for explicit supported contracts; risks for uncontracted changes | Never claims runtime reproduction |
| GitHub PR | Reusable workflow, base/head blob comparison, Markdown job summary | `UNKNOWN` for added/deleted or ambiguous layouts |
| Execution | Local process or user's CI runner; no analysis backend | Install dependencies before offline analysis |

See [draft release notes](releases/0.1.0a1.md) for the user-facing summary and [known limitations](SUPPORTED_COMPOSE_FEATURES.md).
