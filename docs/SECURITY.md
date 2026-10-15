# Security overview

[English](SECURITY.md) | [Русский](ru/SECURITY.md) · [Documentation index](README.md)

DeployWitness analyzes untrusted configuration locally. It has no analysis backend, telemetry, Docker socket access, or default code execution. After Python dependencies are installed, analysis makes no network calls.

The YAML parser uses a safe loader, rejects duplicate keys and unsafe tags, and bounds file size, node count, nesting depth, and service count. It never invokes Compose interpolation or reads `.env` files or production secrets. Environment values are used only in memory for comparison; values and hashes are omitted from reports. Bind mount paths and network names can still be sensitive.

Compose behavior the parser cannot model returns `UNKNOWN`; do not treat `NO_FINDING` as a deployment safety guarantee. Runtime reproduction is not implemented.

See the [detailed threat model](SECURITY_ARCHITECTURE.md) and the repository [security policy](../SECURITY.md) for vulnerability reporting.
