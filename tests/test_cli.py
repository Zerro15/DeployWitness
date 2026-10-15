from pathlib import Path

import pytest

from deploywitness.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_check_exit_code_and_json(capsys: object) -> None:
    result = main(
        [
            "check",
            "--base",
            str(ROOT / "examples/before/compose.yaml"),
            "--head",
            str(ROOT / "examples/after/compose.yaml"),
            "--format",
            "json",
        ]
    )
    assert result == 2


def test_scan_ambiguous(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "compose.yaml").write_text("services: {api: {}}")
    (tmp_path / "docker-compose.yml").write_text("services: {api: {}}")
    assert main(["scan", str(tmp_path)]) == 3
    assert "UNKNOWN" in capsys.readouterr().out


def test_check_unknown_returns_incomplete_exit_code(tmp_path: Path) -> None:
    base, head = tmp_path / "base.yaml", tmp_path / "head.yaml"
    base.write_text("services: {api: {profiles: [prod]}}", encoding="utf-8")
    head.write_text("services: {api: {}}", encoding="utf-8")
    assert main(["check", "--base", str(base), "--head", str(head)]) == 3
