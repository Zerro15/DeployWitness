"""Dependency-light CLI; argparse avoids an extra runtime framework."""

import argparse
import sys
from pathlib import Path

from deploywitness import __version__
from deploywitness.compose import InputError, load_compose
from deploywitness.engine import compare
from deploywitness.report import render

NAMES = ("compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="deploywitness")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="Compare explicit base and head Compose files")
    check.add_argument("--base", type=Path, required=True)
    check.add_argument("--head", type=Path, required=True)
    check.add_argument("--format", choices=("text", "json", "markdown"), default="text")
    scan = commands.add_parser("scan", help="Discover Compose files in a directory")
    scan.add_argument("path", nargs="?", type=Path, default=Path("."))
    scan.add_argument("--file", type=Path, help="Choose a specific Compose file")
    commands.add_parser("rules", help="List implemented rules")
    commands.add_parser("version", help="Show version")
    args = parser.parse_args(argv)
    if args.command == "version":
        print(__version__)
        return 0
    if args.command == "rules":
        print("COMPOSE_NETWORK_LINK\nCOMPOSE_VOLUME_MOUNT\nCOMPOSE_ENV_KEY\nCOMPOSE_ENV_VALUE")
        return 0
    try:
        if args.command == "scan":
            candidates = (
                [args.file]
                if args.file
                else [args.path / name for name in NAMES if (args.path / name).is_file()]
            )
            if len(candidates) > 1:
                print(
                    "UNKNOWN - multiple Compose files found; select one reviewed effective file "
                    "with --file"
                )
                return 3
            if len(candidates) != 1:
                raise InputError(f"Found {len(candidates)} Compose files; choose one with --file")
            model = load_compose(candidates[0])
            print(f"Discovered {model.path}: {len(model.services)} services")
            if model.unresolved:
                print(f"UNKNOWN - analysis incomplete: {'; '.join(model.unresolved_reasons)}")
                return 3
            print("NO_FINDING - scan has no base state; use check for change analysis")
            return 0
        findings = compare(args.base, args.head)
        print(render(findings, args.format))
        if any(w.status == "PROVEN_CONFIG_BREAK" for w in findings):
            return 2
        return 3 if any(w.status == "UNKNOWN" for w in findings) else 0
    except (InputError, OSError) as exc:
        print(f"deploywitness: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
