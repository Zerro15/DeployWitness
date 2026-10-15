# DeployWitness

**Know what breaks before you deploy.**

DeployWitness compares two Docker Compose configurations and explains changed service contracts. An explicit contract can produce a deterministic **configuration break witness**. Without one, a changed connection or mount is reported as a risk, not a proven outage.

```text
PROVEN_CONFIG_BREAK COMPOSE_NETWORK_LINK api->db: Previously shared service network is absent
  Fix: Attach api and db to one shared network, or update the contract deliberately
```

In `examples/before/compose.yaml`, `api` and `db` share `backend`; the candidate moves `api` to `frontend`. The baseline declares `api -> db` as a required network link. The witness proves that this declared Compose invariant is broken. It does **not** claim that a live request failed.

## Quick start

Python 3.12+ is required. The package is not yet published on PyPI.

```bash
python -m pip install -e '.[dev]'
deploywitness check --base examples/before/compose.yaml --head examples/after/compose.yaml
deploywitness check --base examples/before/compose.yaml --head examples/after/compose.yaml --format json
deploywitness scan examples/before
deploywitness rules
deploywitness version
```

Exit codes: `0` means no proven break (risks may still exist), `2` means at least one proven configuration break, and `3` means invalid or unresolved input. `NO_FINDING` only describes the rules currently checked.

`scan` discovers standard Compose filenames in the selected directory. If several are present, use `--file`; it never guesses which configuration is deployed. Change analysis requires explicit `--base` and `--head` paths.

## Contracts and supported checks

The baseline may declare contracts in the Compose extension field `x-deploywitness`:

```yaml
x-deploywitness:
  required_network_links:
    - from: api
      to: db
  required_mounts:
    db: [/var/lib/postgresql/data]
  required_environment:
    api: [DATABASE_URL]
```

Current rules detect removed services, shared-network relationships, dependency edges, mounts, and environment keys. Explicit contracts can prove that a declared network link, mount target, or environment key is absent. `depends_on` alone is never proof of required network connectivity. A mount contract describes target presence only: a changed source is a risk, not proof of data loss. Significant environment value changes are risks; values and their digests are never included in reports. JSON and Markdown output are available with `--format`.

Unresolved interpolation, profiles, `include`, `extends`, `network_mode`, YAML merge keys, unsupported attachments such as `env_file`, configs, and secrets, host port publishing, and top-level named-volume options produce `UNKNOWN`; the tool will not label an incomplete analysis `NO_FINDING`. Multi-file overrides are not merged in this alpha version. Acyclic YAML anchors, network aliases, and declared external network names are understood, but external network existence is not checked. Pass already resolved, reviewed files for meaningful comparisons; do not resolve untrusted Compose files by executing them. Docker and a Docker socket are not required.

## Local checks and CI

```bash
python -m pytest
python -m ruff check .
python -m mypy src
python -m build
git diff --check
```

Examples for [GitHub Actions](.github/workflows/example-check.yml), [GitLab](docs/INTEGRATIONS.md), and [Forgejo](docs/INTEGRATIONS.md) run on the user's own runner. No account, service, telemetry, or network call is needed for analysis after installation.

## Roadmap and contribution

See [ROADMAP.md](ROADMAP.md), [architecture](docs/ARCHITECTURE.md), [security architecture](docs/SECURITY_ARCHITECTURE.md), [competitive analysis](docs/COMPETITIVE_ANALYSIS.md), and [release strategy](docs/RELEASING.md). Contributions are welcome under [CONTRIBUTING.md](CONTRIBUTING.md). This project follows SemVer; `0.1.0a1` is pre-release and the witness schema may change before `1.0.0`.
