# Supported Compose features

[English](SUPPORTED_COMPOSE_FEATURES.md) | [Русский](ru/SUPPORTED_COMPOSE_FEATURES.md) · [Documentation index](README.md)

DeployWitness currently parses **one effective Compose YAML file per side**. It does not implement the full Compose Specification or render files with Docker Compose. Unsupported or unresolved behavior must be treated as `UNKNOWN`, not as a clean result.

## Modeled inputs and rules

| Feature | Current behavior |
| --- | --- |
| Services | Detects added and removed service identities. A removal without a matching explicit invariant is a potential risk. |
| `depends_on` | Models structural dependency edges. Removal is a risk; a dangling target in the candidate is a proven invalid dependency. It does not imply network connectivity. |
| Networks | Compares modeled shared-network relationships and explicit `required_network_links`. A verified violation of the explicit contract can be proven. |
| Network aliases | Accepted as service network configuration; aliases do not change modeled network membership or prove reachability. |
| External networks | The declared external network name is modeled as membership. The tool cannot verify the network exists or is reachable at runtime. |
| YAML anchors and aliases | Acyclic anchors and aliases are supported. Cycles are rejected. YAML merge keys are unresolved and return `UNKNOWN`. |
| Volumes | Detects mount additions, removals, and changes. `required_mounts` asserts mount presence at a target only. Source changes are risks; data loss is not proven. |
| Environment | Detects key additions/removals and changes to significant values as risk. Values and their hashes are omitted from reports. Explicit `required_environment` can assert key presence. |

## Unresolved or unsupported

These conditions return `UNKNOWN` or make the effective model unavailable:

- Multi-file override merging and conventional override files.
- Variable interpolation and `.env` resolution.
- Profile selection, `include`, and `extends`.
- `network_mode` and any semantics that depend on the runtime network namespace.
- YAML merge keys.
- `env_file`, configs, secrets, legacy `links`, and `volumes_from`.
- Host port publishing (`ports`/`expose`), conditional `depends_on`, advanced long-form mount options, and top-level named-volume driver/name options.
- Inputs larger than 1 MB per file or changes involving more than 50 recognized Compose files.
- In GitHub PR checks, a changed `.env` or other YAML file alongside a standard Compose file returns `UNKNOWN`; auxiliary inputs are not merged or rendered.

The analyzer never executes Compose commands, shell, application code, or plugins. Provide reviewed files representing the effective base and candidate configurations. Bind paths and network names may appear in reports, so review them before sharing.

`NO_FINDING` means only that implemented rules found no change. It does not mean the whole Compose project was validated or the deployment is safe.
