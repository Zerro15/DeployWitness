"""Deterministic, static comparison of Compose service contracts."""

from pathlib import Path
from typing import Any, cast

from deploywitness.compose import InputError, load_compose
from deploywitness.model import ComposeModel, SourceRef, Status, Witness


def _ref(model: ComposeModel, name: str, field: str) -> SourceRef:
    return SourceRef(str(model.path), model.lines.get(f"{name}.{field}", model.lines.get(name, 1)))


def _witness(rule: str, status: Status, subject: str, summary: str,
             base: dict[str, Any], change: dict[str, Any], invariant: str,
             refs: tuple[SourceRef, ...], fix: str, test: dict[str, Any]) -> Witness:
    return Witness(rule, status, subject, summary, base, change, invariant, refs, fix, test)


def _network_contract(model: ComposeModel, source: str, target: str) -> bool:
    links = model.contracts.get("required_network_links", [])
    if not isinstance(links, list):
        raise InputError("required_network_links must be a list")
    return any(isinstance(link, dict) and link.get("from") == source
               and link.get("to") == target for link in links)


def _required(model: ComposeModel, kind: str, service: str, item: str) -> bool:
    group = model.contracts.get(kind, {})
    if not isinstance(group, dict):
        raise InputError(f"{kind} contract must be a mapping")
    values = group.get(service, [])
    if not isinstance(values, list):
        raise InputError(f"{kind}.{service} contract must be a list")
    return item in values


def compare(base_path: Path, head_path: Path) -> list[Witness]:
    base = load_compose(base_path)
    head = load_compose(head_path)
    findings: list[Witness] = []
    unresolved = base.unresolved or head.unresolved
    links = base.contracts.get("required_network_links", [])
    if not isinstance(links, list):
        raise InputError("required_network_links must be a list")
    declared_pairs: set[tuple[str, str]] = {(cast(str, link.get("from")),
                                             cast(str, link.get("to"))) for link in links
                      if isinstance(link, dict) and isinstance(link.get("from"), str)
                      and isinstance(link.get("to"), str)}
    for name in sorted(base.services.keys() & head.services.keys()):
        old, new = base.services[name], head.services[name]
        targets = old.depends_on | {target for source, target in declared_pairs if source == name}
        for target in sorted(targets & base.services.keys() & head.services.keys()):
            old_shared = old.networks & base.services[target].networks
            new_shared = new.networks & head.services[target].networks
            if old_shared and not new_shared:
                contract = _network_contract(base, name, target)
                status: Status = "UNKNOWN" if unresolved else (
                    "PROVEN_CONFIG_BREAK" if contract else "POTENTIAL_RISK")
                findings.append(_witness(
                    "COMPOSE_NETWORK_LINK", status, f"{name}->{target}",
                    "Previously shared service network is absent",
                    {"shared_networks": sorted(old_shared),
                     "depends_on_declared": target in old.depends_on,
                     "explicit_contract": contract},
                    {"head_shared_networks": sorted(new_shared)},
                    f"{name} and {target} share a network" if contract else
                    "No explicit connectivity invariant declared",
                    (_ref(base, name, "networks"), _ref(head, name, "networks"),
                     _ref(head, target, "networks")),
                    f"Attach {name} and {target} to one shared network, "
                    "or update the contract deliberately",
                    {"operator": "shared_network", "services": [name, target],
                     "base_expected": True, "head_expected": False},
                ))
        old_mounts = {mount.target: mount for mount in old.mounts}
        new_mounts = {mount.target: mount for mount in new.mounts}
        for target, old_mount in sorted(old_mounts.items()):
            new_mount = new_mounts.get(target)
            if new_mount == old_mount:
                continue
            contract = _required(base, "required_mounts", name, target)
            status = "UNKNOWN" if unresolved else (
                "PROVEN_CONFIG_BREAK" if contract else "POTENTIAL_RISK")
            findings.append(_witness(
                "COMPOSE_VOLUME_MOUNT", status, f"{name}:{target}",
                "Persistent mount removed or changed",
                {"target": target, "kind": old_mount.kind, "source": old_mount.source},
                {"head_mount": None if new_mount is None else
                 {"kind": new_mount.kind, "source": new_mount.source}},
                f"{name} retains its declared mount at {target}" if contract else
                "No explicit mount invariant declared",
                (_ref(base, name, "volumes"), _ref(head, name, "volumes")),
                f"Restore the intended mount at {target}; "
                "check existing data before changing sources",
                {"operator": "mount_equals", "service": name, "target": target,
                 "base_expected": {"kind": old_mount.kind, "source": old_mount.source}},
            ))
        for key in sorted(old.environment_keys - new.environment_keys):
            contract = _required(base, "required_environment", name, key)
            status = "UNKNOWN" if unresolved else (
                "PROVEN_CONFIG_BREAK" if contract else "POTENTIAL_RISK")
            findings.append(_witness(
                "COMPOSE_ENV_KEY", status, f"{name}:{key}", "Environment key removed",
                {"key_present": key}, {"key_removed": key},
                f"{name} declares environment key {key}" if contract else
                "No explicit environment invariant declared",
                (_ref(base, name, "environment"), _ref(head, name, "environment")),
                f"Restore {key} or update the contract deliberately",
                {"operator": "environment_key_present", "service": name, "key": key,
                 "base_expected": True, "head_expected": False},
            ))
    return findings


def verify_static(witness: Witness, base_path: Path, head_path: Path) -> bool:
    """Recompute the named invariant from files, independent of stored claim values."""
    return any(candidate.rule_id == witness.rule_id and
               candidate.subject == witness.subject and
               candidate.status == witness.status for candidate in compare(base_path, head_path))
