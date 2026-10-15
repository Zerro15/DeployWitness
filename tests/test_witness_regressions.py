"""Independent regression scenarios for confidence, Compose parsing, and witness integrity."""

from dataclasses import replace
from pathlib import Path

import pytest

from deploywitness.compose import InputError, load_compose
from deploywitness.engine import compare, verify_static
from deploywitness.model import SourceRef


def pair(tmp_path: Path, before: str, after: str) -> tuple[Path, Path]:
    base, head = tmp_path / "before.yaml", tmp_path / "after.yaml"
    base.write_text(before, encoding="utf-8")
    head.write_text(after, encoding="utf-8")
    return base, head


def statuses(tmp_path: Path, before: str, after: str) -> set[str]:
    base, head = pair(tmp_path, before, after)
    return {w.status for w in compare(base, head)}


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        # Scenario 1: removing an unreferenced service is a risk, not proof.
        ("services: {api: {}, worker: {}}", "services: {api: {}}", "POTENTIAL_RISK"),
        # Scenario 2: a dangling depends_on after service deletion is a config break.
        (
            "services: {api: {depends_on: [db]}, db: {}}",
            "services: {api: {depends_on: [db]}}",
            "PROVEN_CONFIG_BREAK",
        ),
        # Scenario 3: removing depends_on while keeping both services is only a risk.
        (
            "services: {api: {depends_on: [db]}, db: {}}",
            "services: {api: {}, db: {}}",
            "POTENTIAL_RISK",
        ),
        # Scenario 4: mount source replacement does not violate target-presence contract.
        (
            "services: {db: {volumes: [data:/db]}}\n"
            "x-deploywitness: {required_mounts: {db: [/db]}}",
            "services: {db: {volumes: [fresh:/db]}}",
            "POTENTIAL_RISK",
        ),
        # Scenario 5: removal of required mount target is proven.
        (
            "services: {db: {volumes: [data:/db]}}\n"
            "x-deploywitness: {required_mounts: {db: [/db]}}",
            "services: {db: {}}",
            "PROVEN_CONFIG_BREAK",
        ),
        # Scenario 6: removal of an undeclared mount is a risk.
        ("services: {db: {volumes: [data:/db]}}", "services: {db: {}}", "POTENTIAL_RISK"),
        # Scenario 7: baseline contract already false is unknown.
        (
            "services: {db: {}}\nx-deploywitness: {required_mounts: {db: [/db]}}",
            "services: {db: {}}",
            "UNKNOWN",
        ),
        # Scenario 8: removed required environment key is proven.
        (
            "services: {api: {environment: {URL: db}}}\n"
            "x-deploywitness: {required_environment: {api: [URL]}}",
            "services: {api: {environment: {}}}",
            "PROVEN_CONFIG_BREAK",
        ),
        # Scenario 9: removed uncontracted environment key is only a risk.
        (
            "services: {api: {environment: {URL: db}}}",
            "services: {api: {environment: {}}}",
            "POTENTIAL_RISK",
        ),
        # Scenario 10: significant value change does not claim a proven break.
        (
            "services: {api: {environment: {URL: db}}}\n"
            "x-deploywitness: {required_environment: {api: [URL]}}",
            "services: {api: {environment: {URL: other}}}",
            "POTENTIAL_RISK",
        ),
        # Scenario 11: unmarked environment value change is not reported.
        (
            "services: {api: {environment: {URL: db}}}",
            "services: {api: {environment: {URL: other}}}",
            "NO_FINDING",
        ),
        # Scenario 12: contract drift prevents a proof.
        (
            "services: {api: {networks: [n]}, db: {networks: [n]}}\n"
            "x-deploywitness: {required_network_links: [{from: api, to: db}]}",
            "services: {api: {networks: [other]}, db: {networks: [n]}}\n"
            "x-deploywitness: {required_network_links: []}",
            "UNKNOWN",
        ),
        # Scenario 13: unresolved interpolation is explicit.
        ("services: {api: {image: '${IMAGE}'}}", "services: {api: {}}", "UNKNOWN"),
        # Scenario 14: profiles are explicit unknown.
        ("services: {api: {profiles: [prod]}}", "services: {api: {}}", "UNKNOWN"),
        # Scenario 15: include is explicit unknown.
        ("include: [extra.yaml]\nservices: {api: {}}", "services: {api: {}}", "UNKNOWN"),
        # Scenario 16: extends is explicit unknown.
        ("services: {api: {extends: {service: base}}}", "services: {api: {}}", "UNKNOWN"),
        # Scenario 17: network_mode relationship is explicit unknown.
        (
            "services: {api: {network_mode: service:db}, db: {}}",
            "services: {api: {}, db: {}}",
            "UNKNOWN",
        ),
        # Scenario 18: ordinary network loss without a contract is a risk.
        (
            "services: {api: {networks: [n]}, db: {networks: [n]}}",
            "services: {api: {networks: [other]}, db: {networks: [n]}}",
            "POTENTIAL_RISK",
        ),
        # Scenario 19: aliases don't erase shared network membership.
        (
            "services: {api: {networks: {n: {aliases: [gateway]}}}, db: {networks: [n]}}",
            "services: {api: {networks: {n: {aliases: [api]}}}, db: {networks: [n]}}",
            "NO_FINDING",
        ),
        # Scenario 20: external networks are modeled by their declared key.
        (
            "services: {api: {networks: [n]}, db: {networks: [n]}}\n"
            "networks: {n: {external: true}}\n"
            "x-deploywitness: {required_network_links: [{from: api, to: db}]}",
            "services: {api: {networks: [other]}, db: {networks: [n]}}\n"
            "networks: {n: {external: true}}",
            "PROVEN_CONFIG_BREAK",
        ),
        # Scenario 21: network change with a missing baseline contract is unknown.
        (
            "services: {api: {networks: [x]}, db: {networks: [n]}}\n"
            "x-deploywitness: {required_network_links: [{from: api, to: db}]}",
            "services: {api: {networks: [y]}, db: {networks: [n]}}",
            "UNKNOWN",
        ),
        # Scenario 22: adding a service alone doesn't claim breakage.
        ("services: {api: {}}", "services: {api: {}, worker: {}}", "NO_FINDING"),
        # Scenario 23: service dependency target already absent in baseline is not a proof.
        ("services: {api: {}}", "services: {api: {depends_on: [new]}, new: {}}", "NO_FINDING"),
        # Scenario 24: config with a profile still reports UNKNOWN when no rule changed.
        ("services: {api: {profiles: [ops]}}", "services: {api: {profiles: [ops]}}", "UNKNOWN"),
        # Scenario 25: changing a network alias alone is safe for modeled connectivity.
        (
            "services: {api: {networks: {n: {aliases: [one]}}}}",
            "services: {api: {networks: {n: {aliases: [two]}}}}",
            "NO_FINDING",
        ),
        # Scenario 26: changing the mount type/source is a risk absent a narrower invariant.
        (
            "services: {db: {volumes: [data:/db]}}",
            "services: {db: {volumes: [./data:/db]}}",
            "POTENTIAL_RISK",
        ),
        # Scenario 27: removed service with no explicit consumers is not proof.
        ("services: {api: {}, cache: {}}", "services: {api: {}}", "POTENTIAL_RISK"),
        # Scenario 28: removed network contract target with intact baseline contract is proven.
        (
            "services: {api: {networks: [n]}, db: {networks: [n]}}\n"
            "x-deploywitness: {required_network_links: [{from: api, to: db}]}",
            "services: {api: {networks: [n]}}",
            "PROVEN_CONFIG_BREAK",
        ),
        # Scenario 29: contract-preserving safe network edit is no finding.
        (
            "services: {api: {networks: [n, x]}, db: {networks: [n]}}\n"
            "x-deploywitness: {required_network_links: [{from: api, to: db}]}",
            "services: {api: {networks: [n, y]}, db: {networks: [n]}}",
            "NO_FINDING",
        ),
        # Scenario 30: removing optional environment key is a risk.
        (
            "services: {api: {environment: {DEBUG: '1'}}}",
            "services: {api: {environment: {}}}",
            "POTENTIAL_RISK",
        ),
        # Scenario 31: removing dependency edge and target together is not proof.
        (
            "services: {api: {depends_on: [db]}, db: {}}",
            "services: {api: {}}",
            "POTENTIAL_RISK",
        ),
        # Scenario 32: env_file values are unresolved, so key removal cannot be proven.
        (
            "services: {api: {env_file: [.env], environment: {}}}",
            "services: {api: {environment: {}}}",
            "UNKNOWN",
        ),
        # Scenario 33: YAML merge keys are not partially interpreted.
        (
            "x-common: &common {networks: [n]}\nservices: {api: {<<: *common}}",
            "services: {api: {}}",
            "UNKNOWN",
        ),
        # Scenario 34: secrets attachments are unresolved.
        (
            "services: {api: {secrets: [db_password]}}",
            "services: {api: {}}",
            "UNKNOWN",
        ),
        # Scenario 35: read-only to read-write mount change is detected as risk.
        (
            "services: {db: {volumes: [data:/db:ro]}}",
            "services: {db: {volumes: [data:/db:rw]}}",
            "POTENTIAL_RISK",
        ),
        # Scenario 36: named volume resource options are not silently ignored.
        (
            "services: {db: {volumes: [data:/db]}}\nvolumes: {data: {name: old_data}}",
            "services: {db: {volumes: [data:/db]}}\nvolumes: {data: {name: new_data}}",
            "UNKNOWN",
        ),
        # Scenario 37: changing the required mount contract alongside removal is unknown.
        (
            "services: {db: {volumes: [data:/db]}}\n"
            "x-deploywitness: {required_mounts: {db: [/db]}}",
            "services: {db: {}}\nx-deploywitness: {required_mounts: {db: []}}",
            "UNKNOWN",
        ),
        # Scenario 38: changing the environment contract alongside key removal is unknown.
        (
            "services: {api: {environment: {URL: db}}}\n"
            "x-deploywitness: {required_environment: {api: [URL]}}",
            "services: {api: {environment: {}}}\n"
            "x-deploywitness: {required_environment: {api: []}}",
            "UNKNOWN",
        ),
        # Scenario 39: removing both service and its declared mount contract is unknown.
        (
            "services: {db: {volumes: [data:/db]}}\n"
            "x-deploywitness: {required_mounts: {db: [/db]}}",
            "services: {}\nx-deploywitness: {}",
            "UNKNOWN",
        ),
    ],
)
def test_independent_confidence_scenarios(
    tmp_path: Path, before: str, after: str, expected: str
) -> None:
    actual = statuses(tmp_path, before, after)
    if expected == "NO_FINDING":
        assert actual == set()
    else:
        assert expected in actual


def test_reused_yaml_anchor_is_supported(tmp_path: Path) -> None:
    path = tmp_path / "anchors.yaml"
    path.write_text(
        """services:
  api: &svc {networks: [backend]}
  worker: *svc
""",
        encoding="utf-8",
    )
    model = load_compose(path)
    assert model.services["api"].networks == model.services["worker"].networks


def test_alias_cycle_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "cycle.yaml"
    path.write_text("services: &root {api: *root}", encoding="utf-8")
    with pytest.raises(InputError):
        load_compose(path)


def test_override_filename_is_unknown(tmp_path: Path) -> None:
    base = tmp_path / "compose.yaml"
    override = tmp_path / "compose.override.yaml"
    base.write_text("services: {api: {}}", encoding="utf-8")
    override.write_text("services: {api: {}}", encoding="utf-8")
    assert "UNKNOWN" in {w.status for w in compare(base, override)}


def test_invalid_alias_shape_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad-alias.yaml"
    path.write_text("services: {api: {networks: {n: {aliases: nope}}}}", encoding="utf-8")
    with pytest.raises(InputError):
        load_compose(path)


def test_excessive_yaml_depth_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "deep.yaml"
    path.write_text(
        "services:\n  api:\n" + "    nested:\n" * 50 + "      value: true\n",
        encoding="utf-8",
    )
    with pytest.raises(InputError):
        load_compose(path)


def test_witness_source_refs_are_recomputed_and_bounded(tmp_path: Path) -> None:
    before, after = pair(
        tmp_path,
        "services:\n  api:\n    networks: [n]\n  db:\n    networks: [n]\n"
        "x-deploywitness:\n  required_network_links: [{from: api, to: db}]\n",
        "services:\n  api:\n    networks: [other]\n  db:\n    networks: [n]\n",
    )
    witness = compare(before, after)[0]
    assert all(ref.line > 0 and Path(ref.file).is_file() for ref in witness.sources)
    contract_ref = next(ref for ref in witness.sources if ref.file == str(before) and ref.line > 5)
    assert (
        "required_network_links"
        in before.read_text(encoding="utf-8").splitlines()[contract_ref.line - 1]
    )
    assert not verify_static(
        replace(witness, sources=(SourceRef(str(before), 10_000),)), before, after
    )
