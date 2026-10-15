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
    assert compare(before, fixed) == []
    assert "redacted" not in str(witness.to_dict())
