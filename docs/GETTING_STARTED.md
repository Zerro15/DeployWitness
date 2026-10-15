# Getting started

[English](GETTING_STARTED.md) | [Русский](ru/GETTING_STARTED.md) · [Documentation index](README.md)

## Requirements

- Python 3.12 or newer.
- A reviewed Docker Compose YAML file. Docker Engine and the Docker CLI are not needed for static analysis.
- Network access is needed to install Python dependencies unless they are already available. After installation, analysis itself makes no network calls.

## Install the alpha from GitHub Release

The recommended install is the verified wheel attached to the [v0.1.0a1 GitHub Release](https://github.com/Zerro15/DeployWitness/releases/tag/v0.1.0a1). Download the [wheel](https://github.com/Zerro15/DeployWitness/releases/download/v0.1.0a1/deploywitness-0.1.0a1-py3-none-any.whl) and [SHA256SUMS.txt](https://github.com/Zerro15/DeployWitness/releases/download/v0.1.0a1/SHA256SUMS.txt) into the same folder. In a terminal opened in that folder, verify the wheel:

```text
python -c "import hashlib,pathlib,sys; f='deploywitness-0.1.0a1-py3-none-any.whl'; sums={name:digest for digest,name in (line.split(maxsplit=1) for line in pathlib.Path('SHA256SUMS.txt').read_text(encoding='ascii').splitlines())}; actual=hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest(); print('SHA256 OK:', f) if sums.get(f)==actual else sys.exit('SHA256 verification failed')"
```

The same command works in Linux, macOS, and Windows PowerShell. It checks the wheel using only the wheel and checksum file; you do not need to download the sdist. Then install and verify:

```text
python -m pip install ./deploywitness-0.1.0a1-py3-none-any.whl
deploywitness version
```

For an alternative source install, clone the release tag and install from its checkout:

```bash
git clone --branch v0.1.0a1 --depth 1 https://github.com/Zerro15/DeployWitness.git
cd DeployWitness
python -m pip install .
deploywitness check --base examples/before/compose.yaml --head examples/after/compose.yaml
```

The sample produces `PROVEN_CONFIG_BREAK` because the baseline explicitly requires a shared network and the candidate removes that relationship. This proves a static configuration contract violation, not a runtime outage. Installing dependencies may require access to your configured Python package index; analysis itself makes no network requests. A real fork-originated GitHub PR run has not yet been verified; see [integration limits](INTEGRATIONS.md).

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
