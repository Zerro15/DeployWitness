"""Validate bilingual documentation links and warn about stale translations."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"(!?)\[[^\]]*\]\((<[^>]+>|[^)]+)\)")
HTML_LINK = re.compile(r"\b(src|srcset|href)=[\"']([^\"']+)[\"']", re.IGNORECASE)
PAIRS = {
    "README.md": "README.ru.md",
    "docs/README.md": "docs/ru/README.md",
    "docs/GETTING_STARTED.md": "docs/ru/GETTING_STARTED.md",
    "docs/CLI_REFERENCE.md": "docs/ru/CLI_REFERENCE.md",
    "docs/FAILURE_WITNESS.md": "docs/ru/FAILURE_WITNESS.md",
    "docs/ARCHITECTURE.md": "docs/ru/ARCHITECTURE.md",
    "docs/SUPPORTED_COMPOSE_FEATURES.md": "docs/ru/SUPPORTED_COMPOSE_FEATURES.md",
    "docs/INTEGRATIONS.md": "docs/ru/CI_INTEGRATIONS.md",
    "docs/SECURITY.md": "docs/ru/SECURITY.md",
    "docs/SECURITY_ARCHITECTURE.md": "docs/ru/SECURITY_ARCHITECTURE.md",
    "docs/FAQ.md": "docs/ru/FAQ.md",
}
REQUIRED = [
    *PAIRS,
    *PAIRS.values(),
    "docs/i18n/TRANSLATION_GUIDE.md",
    "docs/i18n/GLOSSARY.md",
    "docs/i18n/WEBSITE_LOCALIZATION.md",
]


def relative_target(source: Path, raw_target: str) -> Path | None:
    target = raw_target.strip().strip("<>").split()[0]
    parsed = urlsplit(target)
    if parsed.scheme or target.startswith("//"):
        return None
    target_path = unquote(parsed.path)
    if not target_path:
        return None
    if target_path.startswith("/"):
        return ROOT / target_path.lstrip("/")
    return source.parent / target_path


def changed_paths(base: str, head: str) -> set[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return set(result.stdout.splitlines())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="")
    parser.add_argument("--head", default="")
    args = parser.parse_args()
    errors: list[str] = []

    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append(f"Required localization file is missing: {relative}")

    for english, russian in PAIRS.items():
        en_path, ru_path = ROOT / english, ROOT / russian
        if not en_path.is_file() or not ru_path.is_file():
            continue
        en_text, ru_text = en_path.read_text(encoding="utf-8"), ru_path.read_text(encoding="utf-8")
        en_link = Path(os.path.relpath(russian, Path(english).parent)).as_posix()
        ru_link = Path(os.path.relpath(english, Path(russian).parent)).as_posix()
        if en_link not in en_text:
            errors.append(f"Missing English → Russian switch in {english}")
        if ru_link not in ru_text:
            errors.append(f"Missing Russian → English switch in {russian}")

    markdown_files = [
        path
        for path in ROOT.rglob("*.md")
        if not any(part in {".git", ".venv", "build", "dist"} for part in path.parts)
    ]
    for source in markdown_files:
        content = source.read_text(encoding="utf-8")
        targets = [
            (match.group(1) == "!", match.group(2))
            for match in MARKDOWN_LINK.finditer(content)
        ]
        for match in HTML_LINK.finditer(content):
            attribute, value = match.group(1).lower(), match.group(2)
            candidates = value.split(",") if attribute == "srcset" else [value]
            targets.extend((attribute in {"src", "srcset"}, item) for item in candidates)
        for is_image, raw_target in targets:
            target = relative_target(source, raw_target)
            if target is None:
                continue
            if not target.exists():
                kind = "image" if is_image else "link"
                errors.append(f"Broken local {kind} in {source.relative_to(ROOT)}: {raw_target}")

    if args.base and args.head and not args.base.startswith("0000000"):
        changed = changed_paths(args.base, args.head)
        for english, russian in PAIRS.items():
            if english in changed and russian not in changed:
                print(
                    f"::warning file={english}::English source changed without an update to "
                    f"{russian}; review translation freshness."
                )

    if errors:
        print("Localization checks failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        f"Localization checks passed ({len(PAIRS)} language pairs, "
        f"{len(markdown_files)} Markdown files)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
