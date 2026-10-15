"""Small, serializable domain model. No configuration values enter reports."""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

Status = Literal[
    "PROVEN_CONFIG_BREAK", "REPRODUCED_FAILURE", "POTENTIAL_RISK", "UNKNOWN", "NO_FINDING"
]


@dataclass(frozen=True)
class SourceRef:
    file: str
    line: int


@dataclass(frozen=True)
class Mount:
    target: str
    kind: str
    source: str | None


@dataclass(frozen=True)
class Service:
    name: str
    networks: frozenset[str]
    mounts: tuple[Mount, ...]
    environment_keys: frozenset[str]
    depends_on: frozenset[str]
    profile: bool


@dataclass(frozen=True)
class ComposeModel:
    path: Path
    services: dict[str, Service]
    contracts: dict[str, Any]
    lines: dict[str, int]
    unresolved: bool


@dataclass(frozen=True)
class Witness:
    rule_id: str
    status: Status
    subject: str
    summary: str
    base_facts: dict[str, Any]
    changed_elements: dict[str, Any]
    invariant: str
    sources: tuple[SourceRef, ...]
    fix: str
    static_test: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
