# Architecture

DeployWitness is a local CLI and Python library. `compose.py` parses a bounded, safe YAML subset into service, network, mount, dependency, and environment-key facts. `graph.py` builds typed service relationships. `engine.py` compares those facts and emits deterministic witnesses. `report.py` renders terminal, JSON, and Markdown. There is no backend or Docker access.

The witness schema version is `1`. Findings carry a rule ID, status, baseline facts, changed elements, invariant, source references, proposed fix, and declarative static test. `verify_static` reparses both inputs and recomputes the complete expected witness; it accepts only exact agreement across every field. Static test descriptors are never executed.

`PROVEN_CONFIG_BREAK` is reserved for an explicit configuration invariant that held in the baseline and is false in the candidate, or a structurally invalid candidate dependency. `POTENTIAL_RISK` means a relevant change has no sufficient contract. `UNKNOWN` means the effective configuration or baseline contract cannot be established. `REPRODUCED_FAILURE` is reserved for future isolated reproduction and is never emitted today. `NO_FINDING` means only that no implemented rule found a change.

## Supported semantics and limits

- The parser recognizes one effective Compose file. It does not merge files, resolve interpolation, select profiles, or resolve `include`, `extends`, or `network_mode`; those cases produce `UNKNOWN`.
- A conventional override filename also produces `UNKNOWN` unless users first provide a reviewed effective file. The tool never executes Compose interpolation or commands from the analyzed repository.
- Acyclic YAML anchors and aliases are supported. Cycles are rejected. YAML merge keys produce `UNKNOWN` rather than being partially interpreted.
- Network aliases do not change modeled network membership. External network declarations are treated as named memberships; the tool cannot verify that the external network exists at runtime.
- `depends_on` is a structural dependency, not evidence of network connectivity. Removing an edge is a risk; a dangling target in the candidate is a proven invalid configuration.
- Removed services, shared-network relationships, mounts, and declared environment keys are detected. Without an explicit invariant, their removal is a risk. `required_mounts` asserts that a service has a mount at a target; changing its source is a risk, not proof of data loss.
- `env_file`, configs, secrets, legacy `links`, `volumes_from`, host port publishing (`ports`/`expose`), conditional `depends_on`, advanced long-form mount options, and top-level named-volume driver/name options produce `UNKNOWN` because their effective behavior is not modeled.
- Mount comparison is syntactic. It does not inspect data or prove data loss. Source references point to parsed service fields and contract declarations, not every YAML scalar.
- Docker Compose validation is not run; its rendered model may differ. `NO_FINDING` applies only to implemented rules.

Future Terraform, Kubernetes, GitHub Actions, SARIF, and sandbox support are out of scope until the Compose model is reliable.
