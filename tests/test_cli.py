from pathlib import Path

from deploywitness.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_check_exit_code_and_json(capsys: object) -> None:
    result = main(["check", "--base", str(ROOT / "examples/before/compose.yaml"),
                   "--head", str(ROOT / "examples/after/compose.yaml"), "--format", "json"])
    assert result == 2


def test_scan_ambiguous(tmp_path: Path) -> None:
    (tmp_path / "compose.yaml").write_text("services: {api: {}}")
    (tmp_path / "docker-compose.yml").write_text("services: {api: {}}")
    assert main(["scan", str(tmp_path)]) == 3
