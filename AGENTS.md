# Agent guidance

This repository is local-first and offline at runtime. Never add telemetry, mandatory backend, Docker socket access, or code execution in static analysis. Keep `PROVEN_CONFIG_BREAK` reserved for explicit violated invariants, `REPRODUCED_FAILURE` for actual isolated reproduction, and `NO_FINDING` scoped to implemented rules. Run local quality checks before reporting success. Do not publish to PyPI without maintainer authorization.
