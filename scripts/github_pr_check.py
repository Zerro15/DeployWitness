"""Analyze changed Compose blobs from a pull request without checking out PR code."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import replace
from pathlib import Path, PurePosixPath

from deploywitness.compose import MAX_BYTES, InputError
from deploywitness.engine import compare
from deploywitness.model import Witness

COMPOSE_NAMES = {
    "compose.yaml",
    "compose.yml",
    "docker-compose.yaml",
    "docker-compose.yml",
    "compose.override.yaml",
    "compose.override.yml",
    "docker-compose.override.yaml",
    "docker-compose.override.yml",
}
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


class IntegrationError(Exception):
    """A PR ref or repository input could not be analyzed safely."""


def _git(*args: str) -> bytes:
    result = subprocess.run(["git", *args], check=False, capture_output=True)
    if result.returncode:
        raise IntegrationError("Could not read the pull request Git data")
    return result.stdout


def _compose_path(raw_path: bytes) -> str | None:
    try:
        path = raw_path.decode("utf-8")
    except UnicodeDecodeError:
        return None
    pure = PurePosixPath(path)
    if (
        "\\" in path
        or pure.is_absolute()
        or any(part in {"", ".", ".."} for part in path.split("/"))
        or pure.name not in COMPOSE_NAMES
    ):
        return None
    return path


def _compose_files(commit: str, parent: str) -> set[str]:
    args = ["ls-tree", "-r", "--name-only", "-z", commit]
    args.extend(["--", "." if parent == "." else f":(literal){parent}"])
    output = _git(*args)
    return {
        path
        for raw in output.split(b"\0")
        if raw and (path := _compose_path(raw)) is not None
        and str(PurePosixPath(path).parent) == parent
    }


def _blob(commit: str, path: str) -> bytes | None:
    size = subprocess.run(
        ["git", "cat-file", "-s", f"{commit}:{path}"],
        check=False,
        capture_output=True,
    )
    if size.returncode:
        return None
    try:
        if int(size.stdout) > MAX_BYTES:
            raise InputError("Compose blob exceeds the supported size limit")
    except ValueError as exc:
        raise InputError("Could not validate Compose blob size") from exc
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        check=False,
        capture_output=True,
    )
    if result.returncode:
        return None
    if len(result.stdout) > MAX_BYTES:
        raise InputError("Compose blob exceeds the supported size limit")
    return result.stdout


def _markdown_text(value: str) -> str:
    """Escape untrusted configuration strings before placing them in a GitHub summary."""
    escaped = value.replace("\\", "\\\\")
    for character in "`*_{}[]()#+-.!|><":
        escaped = escaped.replace(character, f"\\{character}")
    return escaped.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")


def _render_findings(findings: list[Witness]) -> str:
    if not findings:
        return (
            "**NO_FINDING** — no issue found among checked rules; "
            "this is not a safety guarantee."
        )
    rows: list[str] = []
    for finding in findings:
        # Keep the typed witness model as the source of report data. Dynamic strings
        # originate in untrusted Compose files and must not create Markdown structure.
        rows.extend(
            [
                f"### **{finding.status}** — {_markdown_text(finding.subject)}",
                "",
                _markdown_text(finding.summary),
                "",
                f"Rule: {_markdown_text(finding.rule_id)}  ",
                f"Invariant: {_markdown_text(finding.invariant)}  ",
                f"Suggested fix: {_markdown_text(finding.fix)}",
            ]
        )
        if finding.sources:
            rows.extend(
                [
                    "",
                    "Sources: "
                    + ", ".join(
                        f"{_markdown_text(source.file)}:{source.line}"
                        for source in finding.sources
                    ),
                ]
            )
        details = [
            str(reason)
            for facts in (finding.base_facts, finding.changed_elements)
            for key in ("base_unresolved", "head_unresolved", "changed_sections")
            for reason in facts.get(key, [])
        ]
        if details:
            detail_text = "; ".join(_markdown_text(item) for item in details)
            rows.extend(["", f"Analysis details: {detail_text}"])
        rows.append("")
    return "\n".join(rows).rstrip()


def analyze(base: str, head: str) -> tuple[str, int]:
    """Return a Markdown report and a conservative process status."""
    if not SHA_PATTERN.fullmatch(base) or not SHA_PATTERN.fullmatch(head):
        raise IntegrationError("Base and head must be full commit SHAs")

    raw_names = _git("diff", "--no-renames", "--name-only", "-z", base, head, "--")
    paths = sorted(
        candidate
        for raw in raw_names.split(b"\0")
        if raw and (candidate := _compose_path(raw)) is not None
    )
    if not paths:
        return (
            "# DeployWitness pull request report\n\n"
            "No supported Compose files changed. No infrastructure conclusion was made.\n",
            0,
        )

    directory_counts = Counter(str(PurePosixPath(path).parent) for path in paths)
    sections: list[str] = [
        "# DeployWitness pull request report",
        "",
        f"Base: `{base[:12]}` · Head: `{head[:12]}`",
        "",
        "This check reads Compose blobs as data. It does not run pull request code.",
        "",
    ]
    saw_proven = False
    saw_unknown = False

    with tempfile.TemporaryDirectory(prefix="deploywitness-pr-") as temporary:
        root = Path(temporary)
        for path in paths:
            sections.extend([f"## {_markdown_text(path)}", ""])
            parent = str(PurePosixPath(path).parent)
            try:
                base_compose_files = _compose_files(base, parent)
                head_compose_files = _compose_files(head, parent)
            except IntegrationError:
                sections.extend(
                    ["**UNKNOWN** — Compose files in this directory could not be enumerated.", ""]
                )
                saw_unknown = True
                continue
            if (
                directory_counts[parent] > 1
                or len(base_compose_files) > 1
                or len(head_compose_files) > 1
            ):
                sections.extend(
                    [
                        "**UNKNOWN** — multiple Compose files changed in the same directory; "
                        "their effective configuration is not resolved.",
                        "",
                    ]
                )
                saw_unknown = True
                continue

            try:
                base_data = _blob(base, path)
                head_data = _blob(head, path)
            except InputError:
                sections.extend(
                    ["**UNKNOWN** — this Compose file exceeds the supported input limits.", ""]
                )
                saw_unknown = True
                continue
            if base_data is None or head_data is None:
                sections.extend(
                    [
                        "**UNKNOWN** — this Compose file was added or removed; the current "
                        "analyzer cannot compare a missing configuration state.",
                        "",
                    ]
                )
                saw_unknown = True
                continue

            base_file = root / "base" / path
            head_file = root / "head" / path
            base_file.parent.mkdir(parents=True, exist_ok=True)
            head_file.parent.mkdir(parents=True, exist_ok=True)
            base_file.write_bytes(base_data)
            head_file.write_bytes(head_data)
            try:
                findings = compare(base_file, head_file)
            except (InputError, OSError, ValueError):
                sections.extend(
                    [
                        "**UNKNOWN** — the changed configuration could not be parsed safely.",
                        "",
                    ]
                )
                saw_unknown = True
                continue

            normalized = []
            for finding in findings:
                sources = []
                for source in finding.sources:
                    source_path = Path(source.file)
                    try:
                        display_path = source_path.relative_to(root).as_posix()
                    except ValueError:
                        display_path = path
                    sources.append(replace(source, file=display_path))
                normalized.append(replace(finding, sources=tuple(sources)))
            findings = normalized
            sections.extend([_render_findings(findings), ""])
            saw_proven |= any(item.status == "PROVEN_CONFIG_BREAK" for item in findings)
            saw_unknown |= any(item.status == "UNKNOWN" for item in findings)

    summary = "\n".join(sections).rstrip() + "\n"
    return summary, 2 if saw_proven else 3 if saw_unknown else 0


def main() -> int:
    base = os.environ.get("DEPLOYWITNESS_BASE_SHA", "")
    head = os.environ.get("DEPLOYWITNESS_HEAD_SHA", "")
    try:
        actual_head = _git("rev-parse", "FETCH_HEAD").decode("ascii").strip()
        if actual_head != head:
            raise IntegrationError("Pull request head changed during this run; rerun the check")
        report, status = analyze(base, head)
    except IntegrationError as exc:
        report = (
            "# DeployWitness pull request report\n\n"
            f"**UNKNOWN** — {exc}. No safety conclusion was made.\n"
        )
        status = 3

    print(report, end="")
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as summary_file:
            summary_file.write(report)
    return status


if __name__ == "__main__":
    sys.exit(main())
