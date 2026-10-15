from dataclasses import replace
from pathlib import Path

from deploywitness.engine import compare, verify_static

ROOT = Path(__file__).resolve().parents[1]


def test_network_contract_before_after_fixed() -> None:
    before = ROOT / "examples/before/compose.yaml"
    after = ROOT / "examples/after/compose.yaml"
    fixed = ROOT / "examples/fixed/compose.yaml"
    assert compare(before, before) == []
    findings = compare(before, after)
    assert len(findings) == 1
    witness = findings[0]
    assert witness.status == "PROVEN_CONFIG_BREAK"
    assert witness.rule_id == "COMPOSE_NETWORK_LINK"
    assert verify_static(witness, before, after)
    assert not verify_static(witness, before, fixed)
    assert not verify_static(replace(witness, invariant="fake invariant"), before, after)
    assert not verify_static(replace(witness, summary="fabricated"), before, after)
    assert not verify_static(replace(witness, fix="unsafe fix"), before, after)
    assert not verify_static(replace(witness, status="POTENTIAL_RISK"), before, after)
    assert not verify_static(replace(witness, rule_id="FAKE_RULE"), before, after)
    assert not verify_static(replace(witness, subject="other->service"), before, after)
    assert not verify_static(replace(witness, invariant="different invariant"), before, after)
    assert not verify_static(
        replace(witness, base_facts={"shared_networks": ["fake"]}), before, after
    )
    assert not verify_static(
        replace(witness, changed_elements={"head_shared_networks": ["fake"]}), before, after
    )
    assert not verify_static(
        replace(witness, static_test={"operator": "always_true"}), before, after
    )
    assert not verify_static(replace(witness, sources=()), before, after)
    assert compare(before, fixed) == []
    assert "redacted" not in str(witness.to_dict())
