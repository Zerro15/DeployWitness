# Getting started

[English](GETTING_STARTED.md) | [Русский](ru/GETTING_STARTED.md) · [Documentation index](README.md)

## Requirements

- Python 3.12 or newer.
- A reviewed Docker Compose YAML file. Docker Engine and the Docker CLI are not needed for static analysis.
- Network access is needed to install Python dependencies unless they are already available. After installation, analysis itself makes no network calls.

## Try the current alpha

DeployWitness is not published on PyPI yet. To try the current Compose alpha, install its source branch:

```bash
git clone --branch feat/compose-witness-mvp https://github.com/Zerro15/DeployWitness.git
cd DeployWitness
python -m pip install .
deploywitness check --base examples/before/compose.yaml --head examples/after/compose.yaml
```

The sample produces `PROVEN_CONFIG_BREAK` because the baseline explicitly requires a shared network and the candidate removes that relationship. This proves a static configuration contract violation, not a runtime outage.

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
