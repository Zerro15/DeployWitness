"""Terminal, JSON and Markdown reporters."""

import json

from deploywitness.model import Witness


def render(findings: list[Witness], fmt: str) -> str:
    if fmt == "json":
        return json.dumps({"schema_version": "1", "result": "NO_FINDING" if not findings else
                           "FINDINGS", "findings": [w.to_dict() for w in findings]}, indent=2)
    if not findings:
        return "NO_FINDING — no issue found among checked rules; this is not a safety guarantee."
    if fmt == "markdown":
        rows = ["# DeployWitness report", "", "Static Compose change analysis.", ""]
        for w in findings:
            rows.extend([f"## {w.status}: {w.subject}", "", w.summary, "",
                         f"Rule: `{w.rule_id}`", "", f"Invariant: {w.invariant}", "",
                         f"Suggested fix: {w.fix}", ""])
        return "\n".join(rows)
    return "\n".join(f"{w.status} {w.rule_id} {w.subject}: {w.summary}\n"
                     f"  Fix: {w.fix}" for w in findings)
