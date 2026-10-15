# Security architecture and threat model

Input is an untrusted repository. Threats include oversized YAML, deeply nested objects, aliases/cycles, malicious YAML tags, secret leakage, hostile interpolation, and CI credential exposure.

The parser uses PyYAML `SafeLoader`, a 1 MB file limit, a 20,000-container node limit, depth limit 40, and 500-service limit. It rejects aliases/cycles after parsing. Future work should bound alias expansion during construction and use fuzzing to validate parser resource limits. Never run `docker compose`, shell, plugins, or arbitrary commands on analyzed input in the default path.

Environment values are discarded at parsing and never enter witnesses. Only key names are retained. Bind mount source paths and network names may still be sensitive and appear in output; review reports before sharing. The tool reads only paths explicitly passed or standard filenames in the selected directory. It never reads `.env` or production secrets and makes no network calls during analysis.

GitHub workflow examples use `contents: read`, no privileged token, and no `pull_request_target`. Users should avoid passing secrets into the analysis runner. Executable reproduction is postponed until a local sandbox with explicit consent, limits, and teardown exists.
