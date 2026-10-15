# Security architecture and threat model

[English](SECURITY_ARCHITECTURE.md) | [Русский](ru/SECURITY_ARCHITECTURE.md) · [Documentation index](README.md)

Input is an untrusted repository. Threats include oversized YAML, deeply nested objects, aliases/cycles, malicious YAML tags, secret leakage, hostile interpolation, and CI credential exposure.

The parser extends PyYAML `SafeLoader` with a 1 MB per-file limit, a 50 changed-Compose-file limit in PR analysis, a 20,000-node composition limit, depth limit 40, duplicate-key rejection, and 500-service limit. Acyclic YAML anchors and aliases are allowed; cycles are rejected. YAML merge keys and Compose features the parser does not model return `UNKNOWN`. The current regression corpus exercises malformed YAML, duplicate keys, unsafe tags, cycles, reused anchors, oversize input, and excessive nesting. Dedicated fuzzing remains open work. Never run `docker compose`, shell, plugins, or arbitrary commands on analyzed input in the default path.

Environment values are hashed in memory for change detection and never enter witnesses; the digests are never serialized either. Bind mount source paths and network names may still be sensitive and appear in output; review reports before sharing. The tool reads only paths explicitly passed or standard filenames in the selected directory. It never reads `.env` or production secrets and makes no network calls during analysis.

GitHub workflow examples use `contents: read`, no privileged token, and no `pull_request_target`. Users should avoid passing secrets into the analysis runner. Executable reproduction is postponed until a local sandbox with explicit consent, limits, and teardown exists.
