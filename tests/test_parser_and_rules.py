from pathlib import Path

import pytest

from deploywitness.compose import InputError, load_compose
from deploywitness.engine import compare


def write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_uncontracted_network_change_is_risk(tmp_path: Path) -> None:
    before = write(tmp_path, "old.yaml", """services:
  api:
    depends_on: [db]
    networks: [one]
  db:
    networks: [one]
""")
    after = write(tmp_path, "new.yaml", """services:
  api:
    depends_on: [db]
    networks: [two]
  db:
    networks: [one]
""")
    assert compare(before, after)[0].status == "POTENTIAL_RISK"


def test_explicit_link_without_depends_on_is_proven(tmp_path: Path) -> None:
    before = write(tmp_path, "old.yaml", """services:
  api: {networks: [one]}
  db: {networks: [one]}
x-deploywitness:
  required_network_links: [{from: api, to: db}]
""")
    after = write(tmp_path, "new.yaml", """services:
  api: {networks: [two]}
  db: {networks: [one]}
""")
    assert compare(before, after)[0].status == "PROVEN_CONFIG_BREAK"


def test_environment_value_change_is_not_reported(tmp_path: Path) -> None:
    before = write(tmp_path, "old.yaml", "services:\n  api:\n    environment: {TOKEN: secret1}\n")
    after = write(tmp_path, "new.yaml", "services:\n  api:\n    environment: {TOKEN: secret2}\n")
    assert compare(before, after) == []


def test_required_environment_key_removed_without_leaking_value(tmp_path: Path) -> None:
    before = write(tmp_path, "old.yaml", """services:
  api:
    environment: {TOKEN: secret1}
x-deploywitness:
  required_environment: {api: [TOKEN]}
""")
    after = write(tmp_path, "new.yaml", "services:\n  api:\n    environment: {}\n")
    finding = compare(before, after)[0]
    assert finding.status == "PROVEN_CONFIG_BREAK"
    assert "secret1" not in str(finding.to_dict())


def test_changed_named_volume_contract(tmp_path: Path) -> None:
    before = write(tmp_path, "old.yaml", """services:
  db:
    volumes: [data:/db]
x-deploywitness:
  required_mounts: {db: [/db]}
""")
    after = write(tmp_path, "new.yaml", "services:\n  db:\n    volumes: [empty:/db]\n")
    finding = compare(before, after)[0]
    assert finding.rule_id == "COMPOSE_VOLUME_MOUNT"
    assert finding.status == "PROVEN_CONFIG_BREAK"


def test_interpolation_downgrades_proof(tmp_path: Path) -> None:
    before = write(tmp_path, "old.yaml", """services:
  api:
    depends_on: [db]
    networks: [one]
    image: ${IMAGE}
  db:
    networks: [one]
x-deploywitness:
  required_network_links: [{from: api, to: db}]
""")
    after = write(tmp_path, "new.yaml", """services:
  api:
    depends_on: [db]
    networks: [two]
  db:
    networks: [one]
""")
    assert compare(before, after)[0].status == "UNKNOWN"


def test_rejects_bad_or_oversized_yaml(tmp_path: Path) -> None:
    with pytest.raises(InputError):
        load_compose(write(tmp_path, "bad.yaml", "services: ["))
    with pytest.raises(InputError):
        load_compose(write(tmp_path, "huge.yaml", "x" * 1_000_001))


def test_rejects_alias_cycle(tmp_path: Path) -> None:
    with pytest.raises(InputError):
        load_compose(write(tmp_path, "cycle.yaml", "services: &a {api: *a}"))
