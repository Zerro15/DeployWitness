# Failure Witness

[English](FAILURE_WITNESS.md) | [Русский](ru/FAILURE_WITNESS.md) · [Documentation index](README.md)

A **Failure Witness** is a structured, reproducible explanation of a configuration change. In the current alpha it is static evidence computed from the two reviewed Compose files and any explicit `x-deploywitness` contracts. It does not execute the application or prove that a runtime incident occurred.

## Confidence statuses

| Status | Meaning |
| --- | --- |
| `PROVEN_CONFIG_BREAK` | A statically checkable configuration invariant held in the baseline and is false in the candidate, or the candidate contains a structurally invalid dependency. This proves a configuration break, not runtime failure. |
| `POTENTIAL_RISK` | A relevant change is detected, but there is no sufficient explicit contract to prove it breaks the intended configuration. |
| `UNKNOWN` | The input or relevant Compose semantics are incomplete or unsupported, so the engine cannot make a reliable determination. |
| `NO_FINDING` | No implemented rule found a change to report. It is not a safety guarantee and is not a finding status for a specific witness. |
| `REPRODUCED_FAILURE` | Reserved for a future opt-in runtime reproduction. The current alpha never emits it. |

## What a witness contains

Schema version `1` records a rule ID, status, subject, summary, baseline facts, changed elements, invariant, source references, proposed fix, and a declarative static test. Environment values and their hashes are not serialized. `verify_static` reparses the inputs, independently recomputes the expected witness, and accepts only an exact match across substantive fields. The static test descriptor is data; it is never executed.

## Example contract

Declare that `api` and `db` must share a network in the baseline and candidate:

```yaml
x-deploywitness:
  required_network_links:
    - from: api
      to: db
```

If the baseline satisfies this invariant and the candidate does not, the engine can emit a `PROVEN_CONFIG_BREAK` witness. `depends_on` alone does not establish the network contract. Without an explicit contract, a removed relationship is a risk, not proof of an outage.

Mount contracts assert that a service still has a mount at the required target. A source change may point to a different or empty store, but does not prove data loss. See [supported Compose features](SUPPORTED_COMPOSE_FEATURES.md) for other rule families and limits.
