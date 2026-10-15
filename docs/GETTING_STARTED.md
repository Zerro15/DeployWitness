# Getting started

[English](GETTING_STARTED.md) | [Русский](ru/GETTING_STARTED.md) · [Documentation index](README.md)

## Requirements

- Python 3.12 or newer.
- A reviewed Docker Compose YAML file. Docker Engine and the Docker CLI are not needed for static analysis.
- Network access is needed to install Python dependencies unless they are already available. After installation, analysis itself makes no network calls.

## Install the reviewed main commit before release

Until the first release is published, install the reviewed `main` commit `f40f05da1a374a79979d8958e8bacef7c360848b`:

```bash
git clone https://github.com/Zerro15/DeployWitness.git
cd DeployWitness
git checkout --detach f40f05da1a374a79979d8958e8bacef7c360848b
python -m pip install .
deploywitness check --base examples/before/compose.yaml --head examples/after/compose.yaml
```

The sample produces `PROVEN_CONFIG_BREAK` because the baseline explicitly requires a shared network and the candidate removes that relationship. This proves a static configuration contract violation, not a runtime outage.

## Install from a GitHub Release

After `v0.1.0a1` is published, the recommended installation is the wheel from the [GitHub Release](https://github.com/Zerro15/DeployWitness/releases). Download `deploywitness-0.1.0a1-py3-none-any.whl` and `SHA256SUMS.txt` into the same directory. Verify the wheel with this Python standard-library command; it checks only the named wheel, so the sdist does not need to be downloaded:

```text
python -c "import hashlib,pathlib,sys; f='deploywitness-0.1.0a1-py3-none-any.whl'; sums={name:digest for digest,name in (line.split(maxsplit=1) for line in pathlib.Path('SHA256SUMS.txt').read_text(encoding='ascii').splitlines())}; actual=hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest(); print('SHA256 OK:', f) if sums.get(f)==actual else sys.exit('SHA256 verification failed')"
```

The exact same command works in Linux, macOS, and Windows PowerShell. Then install and verify:

```text
python -m pip install ./deploywitness-0.1.0a1-py3-none-any.whl
deploywitness version
```

The `.tar.gz` source distribution is also attached for environments that need it; verify it by replacing the filename in the command with `deploywitness-0.1.0a1.tar.gz`. Installing dependencies may require access to your configured Python package index. Analysis itself makes no network requests. These assets become available only after a maintainer publishes the GitHub pre-release. A real fork-originated GitHub PR run has not yet been verified; see [integration limits](INTEGRATIONS.md).

## Scan one configuration

```bash
deploywitness scan .
```

`scan` discovers one standard Compose filename and summarizes the parsed services. It does **not** compare changes or establish safety. If several standard filenames exist, specify a reviewed file with `--file`. For change analysis, provide both versions with `check`.

## Compare changes

```bash
deploywitness check --base ./before/compose.yaml --head ./after/compose.yaml
deploywitness check --base ./before/compose.yaml --head ./after/compose.yaml --format markdown
deploywitness check --base ./before/compose.yaml --head ./after/compose.yaml --format json
```

Only one effective file is parsed for each side. Compose overrides are not merged. Provide reviewed effective files; do not run Compose interpolation or commands from an untrusted repository to prepare inputs.

## Develop locally

```bash
python -m pip install -e '.[dev]'
python -m pytest
python -m ruff check .
python -m mypy src
python -m build
```

See the [CLI reference](CLI_REFERENCE.md), [supported features](SUPPORTED_COMPOSE_FEATURES.md), and [security notes](SECURITY.md).
