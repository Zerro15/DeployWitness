# FAQ

[English](FAQ.md) | [Русский](ru/FAQ.md) · [Documentation index](README.md)

### Is DeployWitness a linter?

It compares two Compose configurations and checks modeled changes against explicit configuration contracts. It also reports risks where a change matters but there is not enough evidence to call it a proven break.

### Does it predict outages or prove a runtime failure?

No. `PROVEN_CONFIG_BREAK` means a statically checkable configuration invariant is violated. It does not mean a request or process was observed to fail. `REPRODUCED_FAILURE` is reserved and is not emitted today.

### Do I need to write contracts before trying it?

No contract is needed to parse or compare files. Without a contract, relevant removals may be reported as `POTENTIAL_RISK`; explicit `x-deploywitness` declarations enable stronger proof for supported invariants.

### What does `scan` do?

It discovers one standard Compose file and summarizes its services. It does not compare changes. Use `check --base ... --head ...` for a diff.

### Does it run Docker Compose, containers, or project code?

No. The static analyzer parses a bounded YAML subset and runs no commands from analyzed repositories. Docker is not required.

### Does it support Compose overrides, profiles, or `.env` files?

Not in this alpha. Those cases cannot be resolved reliably by the current parser and produce `UNKNOWN` or an incomplete result. See [supported features](SUPPORTED_COMPOSE_FEATURES.md).

### Are my configuration files sent anywhere?

No. Analysis is local and makes no network calls. Python package installation may require network access to fetch dependencies.

### Is there a ready-made PR checker or published package?

Not yet. The package is currently in [Draft PR #1](https://github.com/Zerro15/DeployWitness/pull/1) and is not published to PyPI. The GitHub workflow is a manually dispatched example using fixed repository files; it does not fetch PR base/head automatically.

### What does `NO_FINDING` mean?

Only that the currently implemented rules found no finding in the analyzed inputs. It is not a guarantee that the configuration is correct or safe.
