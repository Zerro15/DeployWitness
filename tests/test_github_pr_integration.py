from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts import github_pr_check

BASE = "a" * 40
HEAD = "b" * 40
CONTRACT = b"""services:
  api:
    image: example/api
    networks: [backend]
  db:
    image: postgres:16
    networks: [backend]
networks:
  backend: {}
x-deploywitness:
  required_network_links:
    - from: api
      to: db
"""
BROKEN = CONTRACT.replace(b"networks: [backend]", b"networks: [frontend]", 1).replace(
    b"  backend: {}", b"  backend: {}\n  frontend: {}"
)
SAFE = CONTRACT.replace(
    b"    image: example/api", b"    image: example/api\n    labels: [safe-change]"
)


def _run_analysis(
    monkeypatch: pytest.MonkeyPatch,
    paths: list[bytes],
    blobs: dict[tuple[str, str], bytes | None],
    tree_paths: dict[str, list[bytes]] | None = None,
) -> tuple[str, int]:
    def fake_git(*args: str) -> bytes:
        if args[0] == "diff":
            assert args[:3] == ("diff", "--no-renames", "--name-only")
            return b"\0".join(paths) + b"\0"
        assert args[0] == "ls-tree"
        commit = args[4]
        selected = (
            tree_paths[commit]
            if tree_paths is not None
            else [
                path.encode()
                for (blob_commit, path), data in blobs.items()
                if blob_commit == commit and data
            ]
        )
        return b"\0".join(selected) + b"\0"

    def fake_blob(commit: str, path: str) -> bytes | None:
        return blobs.get((commit, path))

    monkeypatch.setattr(github_pr_check, "_git", fake_git)
    monkeypatch.setattr(github_pr_check, "_blob", fake_blob)
    return github_pr_check.analyze(BASE, HEAD)


def test_github_summary_marks_explicit_contract_violation_as_proven(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary, status = _run_analysis(
        monkeypatch,
        [b"compose.yaml"],
        {(BASE, "compose.yaml"): CONTRACT, (HEAD, "compose.yaml"): BROKEN},
    )
    assert status == 2
    assert "PROVEN_CONFIG_BREAK" in summary
    assert "shared network" in summary


def test_github_summary_reports_safe_change_without_claiming_safety(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary, status = _run_analysis(
        monkeypatch,
        [b"compose.yaml"],
        {(BASE, "compose.yaml"): CONTRACT, (HEAD, "compose.yaml"): SAFE},
    )
    assert status == 0
    assert "NO_FINDING" in summary
    assert "not a safety guarantee" in summary


def test_uncontracted_network_change_stays_a_risk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = CONTRACT.split(b"x-deploywitness:", 1)[0]
    head = base.replace(b"networks: [backend]", b"networks: [frontend]", 1).replace(
        b"  backend: {}", b"  backend: {}\n  frontend: {}"
    )
    summary, status = _run_analysis(
        monkeypatch,
        [b"compose.yaml"],
        {(BASE, "compose.yaml"): base, (HEAD, "compose.yaml"): head},
    )
    assert status == 0
    assert "POTENTIAL_RISK" in summary
    assert "PROVEN_CONFIG_BREAK" not in summary


def test_unsupported_profiles_are_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profiled = b"services:\n  api:\n    image: example/api\n    profiles: [prod]\n"
    summary, status = _run_analysis(
        monkeypatch,
        [b"compose.yaml"],
        {(BASE, "compose.yaml"): profiled, (HEAD, "compose.yaml"): profiled},
    )
    assert status == 3
    assert "UNKNOWN" in summary
    assert "profiles" in summary


def test_multiple_changed_compose_files_in_one_directory_are_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary, status = _run_analysis(
        monkeypatch,
        [b"compose.yaml", b"compose.override.yaml"],
        {},
    )
    assert status == 3
    assert summary.count("**UNKNOWN**") == 2
    assert "effective configuration is not resolved" in summary


def test_unchanged_compose_override_prevents_a_false_proof(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary, status = _run_analysis(
        monkeypatch,
        [b"compose.yaml"],
        {(BASE, "compose.yaml"): CONTRACT, (HEAD, "compose.yaml"): BROKEN},
        {
            BASE: [b"compose.yaml", b"compose.override.yaml"],
            HEAD: [b"compose.yaml", b"compose.override.yaml"],
        },
    )
    assert status == 3
    assert "UNKNOWN" in summary
    assert "effective configuration is not resolved" in summary


@pytest.mark.parametrize("base_blob,head_blob", [(None, CONTRACT), (CONTRACT, None)])
def test_added_or_deleted_compose_file_is_unknown(
    monkeypatch: pytest.MonkeyPatch, base_blob: bytes | None, head_blob: bytes | None
) -> None:
    summary, status = _run_analysis(
        monkeypatch,
        [b"compose.yaml"],
        {(BASE, "compose.yaml"): base_blob, (HEAD, "compose.yaml"): head_blob},
    )
    assert status == 3
    assert "added or removed" in summary


def test_secret_values_are_not_in_markdown_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = CONTRACT.replace(
        b"networks: [backend]\n  db:",
        b"networks: [backend]\n    environment: {PASSWORD: initial-secret}\n  db:",
        1,
    )
    head = base.replace(b"initial-secret", b"never-print-this-secret")
    summary, _ = _run_analysis(
        monkeypatch,
        [b"compose.yaml"],
        {(BASE, "compose.yaml"): base, (HEAD, "compose.yaml"): head},
    )
    assert "never-print-this-secret" not in summary
    assert "initial-secret" not in summary


def test_markdown_strings_cannot_inject_new_headings() -> None:
    rendered = github_pr_check._markdown_text("service\n## forged heading <script>")
    assert "\n## forged heading" not in rendered
    assert "\\#" in rendered
    assert "\\<script\\>" in rendered


def test_non_utf8_compose_path_is_unknown_instead_of_ignored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary, status = _run_analysis(monkeypatch, [b"odd-\xff-directory/compose.yaml"], {})
    assert status == 3
    assert "UNKNOWN" in summary
    assert "path that cannot be safely represented as UTF-8" in summary
    assert "NO_FINDING" not in summary


def test_excessive_changed_compose_files_are_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = [f"service-{index}/compose.yaml".encode("ascii") for index in range(51)]
    summary, status = _run_analysis(monkeypatch, paths, {})
    assert status == 3
    assert "more than 50 Compose files changed" in summary


@pytest.mark.parametrize(("fetched", "expected"), [(HEAD, True), (BASE, False)])
def test_post_analysis_head_check_detects_a_pr_update(
    monkeypatch: pytest.MonkeyPatch, fetched: str, expected: bool
) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_git(*args: str) -> bytes:
        calls.append(args)
        if args[0] == "fetch":
            return b""
        assert args == ("rev-parse", "FETCH_HEAD")
        return fetched.encode("ascii")

    monkeypatch.setattr(github_pr_check, "_git", fake_git)
    assert github_pr_check._head_is_current("42", HEAD) is expected
    assert calls[0] == ("fetch", "--depth=1", "--no-tags", "origin", "refs/pull/42/head")


def test_head_update_during_analysis_overrides_a_stale_proof(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(github_pr_check, "_git", lambda *_args: HEAD.encode("ascii"))
    monkeypatch.setattr(github_pr_check, "analyze", lambda *_args: ("PROVEN_CONFIG_BREAK\n", 2))
    monkeypatch.setattr(github_pr_check, "_head_is_current", lambda *_args: False)
    monkeypatch.setenv("DEPLOYWITNESS_BASE_SHA", BASE)
    monkeypatch.setenv("DEPLOYWITNESS_HEAD_SHA", HEAD)
    monkeypatch.setenv("DEPLOYWITNESS_PR_NUMBER", "42")
    summary_path = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_path))

    assert github_pr_check.main() == 3
    assert "UNKNOWN" in capsys.readouterr().out
    assert "PROVEN_CONFIG_BREAK" not in summary_path.read_text(encoding="utf-8")


def test_script_reads_real_base_and_head_git_objects(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo = tmp_path / "consumer"
    repo.mkdir()

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    git("init")
    git("config", "user.name", "DeployWitness tests")
    git("config", "user.email", "tests@example.invalid")
    (repo / "compose.yaml").write_bytes(CONTRACT)
    git("add", "compose.yaml")
    git("commit", "-m", "baseline")
    base = git("rev-parse", "HEAD")
    (repo / "compose.yaml").write_bytes(BROKEN)
    git("commit", "-am", "break contract")
    head = git("rev-parse", "HEAD")
    git("fetch", ".", head)

    summary_file = tmp_path / "summary.md"
    monkeypatch.chdir(repo)
    monkeypatch.setenv("DEPLOYWITNESS_BASE_SHA", base)
    monkeypatch.setenv("DEPLOYWITNESS_HEAD_SHA", head)
    monkeypatch.setenv("DEPLOYWITNESS_PR_NUMBER", "42")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))
    monkeypatch.setattr(
        github_pr_check, "_head_is_current", lambda _number, expected: expected == head
    )
    assert github_pr_check.main() == 2
    summary = summary_file.read_text(encoding="utf-8")
    assert "PROVEN_CONFIG_BREAK" in summary
    assert "base/compose" in summary
    assert "head/compose" in summary
