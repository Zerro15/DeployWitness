# CLI reference

[English](CLI_REFERENCE.md) | [Русский](ru/CLI_REFERENCE.md) · [Documentation index](README.md)

The executable is `deploywitness`. These commands describe the current alpha CLI.

## `check`

Compare two explicit Compose files:

```text
deploywitness check --base BASE --head HEAD [--format text|json|markdown]
```

- `--base`: baseline YAML file.
- `--head`: candidate YAML file.
- `--format`: optional output format; default is `text`.

The tool does not infer Git revisions, merge Compose overrides, or select profiles. If the effective configuration is unresolved, findings may be `UNKNOWN` and the command exits `3`.

## `scan`

Discover and parse a Compose file without a baseline:

```text
deploywitness scan [PATH] [--file FILE]
```

`PATH` defaults to the current directory. Without `--file`, `scan` checks these standard names in that directory: `compose.yaml`, `compose.yml`, `docker-compose.yaml`, and `docker-compose.yml`. If more than one is present, it returns `UNKNOWN` and asks you to choose one explicitly. `--file` selects a reviewed file.

`scan` reports the number of parsed services and unresolved parser conditions. It is not a change detector and a clean scan is not a safety result.

## Other commands

- `deploywitness rules`: list implemented rule identifiers.
- `deploywitness version`: print the package version.
- `deploywitness --help` and `deploywitness check --help`: show CLI help.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | No proven break. Risks may exist; `NO_FINDING` is limited to implemented rules. |
| `2` | At least one `PROVEN_CONFIG_BREAK`. |
| `3` | Invalid input, unresolved analysis, or `UNKNOWN`. |

When both a proven break and an unknown finding exist, the current CLI prioritizes exit code `2`; inspect the complete report for both results.

## Formats

`text` is the default terminal report. `markdown` is suitable for a job summary or artifact. `json` includes `schema_version` and structured finding fields. The witness schema is currently version `1` and may change before `1.0.0`.

See [Failure Witness](FAILURE_WITNESS.md) for status semantics and [CI integrations](INTEGRATIONS.md) for current runner examples.
