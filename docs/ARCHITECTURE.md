# Architecture

DeployWitness is a local CLI and Python library. `compose.py` accepts a bounded, safe YAML subset and builds service, network, mount, dependency, and environment-key facts. `engine.py` compares two immutable models and emits a `Witness`. `report.py` serializes the same model to terminal, JSON, or Markdown. No backend or Docker access exists.

The witness schema version is `1`. Each finding carries a rule ID, status, baseline facts, changed elements, invariant, source lines, suggested fix, and static test descriptor. `verify_static` recomputes a witness against files. The test descriptor is declarative, never executable code.

Confidence ladder: `PROVEN_CONFIG_BREAK` means a declared configuration invariant changed from satisfied to violated. `POTENTIAL_RISK` means a meaningful change lacks an explicit contract. `UNKNOWN` means effective configuration may differ due to unsupported Compose features. `REPRODUCED_FAILURE` is reserved for future isolated execution and is never emitted today. `NO_FINDING` means no supported rule matched.

The architecture permits future platform adapters that produce a common graph and facts. Terraform, Kubernetes, GitHub Actions, SARIF, and sandbox reproduction remain out of scope until the Compose model is reliable.

## Known limitations

- No Compose multi-file merge, interpolation resolution, or profile selection.
- Service removal and network aliases are not yet evaluated.
- The current network rule examines retained `depends_on` pairs, so an undeclared dependency can be missed.
- Source references identify service fields, not every YAML scalar.
- Mount comparison is syntactic; it does not inspect data or prove data loss.
- The project does not execute Compose validation. Docker's rendered model may differ.
