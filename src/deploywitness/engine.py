"""Conservative static comparison of Compose facts and declared invariants."""

from pathlib import Path
from typing import Any

from deploywitness.compose import InputError, load_compose
from deploywitness.graph import ContractGraph
from deploywitness.model import ComposeModel, SourceRef, Status, Witness


def _ref(model: ComposeModel, name: str, field: str) -> SourceRef:
    return SourceRef(str(model.path), model.lines.get(f"{name}.{field}", model.lines.get(name, 1)))


def _witness(
    rule: str,
    status: Status,
    subject: str,
    summary: str,
    base: dict[str, Any],
    change: dict[str, Any],
    invariant: str,
    refs: tuple[SourceRef, ...],
    fix: str,
    test: dict[str, Any],
) -> Witness:
    return Witness(rule, status, subject, summary, base, change, invariant, refs, fix, test)


def _contract_map(model: ComposeModel, name: str) -> dict[str, Any]:
    value = model.contracts.get(name, {})
    if not isinstance(value, dict):
        raise InputError(f"{name} contract must be a mapping")
    return value


def _required(model: ComposeModel, kind: str, service: str, item: str) -> bool:
    values = _contract_map(model, kind).get(service, [])
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise InputError(f"{kind}.{service} contract must be a list of strings")
    return item in values


def _network_contract(model: ComposeModel, source: str, target: str) -> bool:
    links = model.contracts.get("required_network_links", [])
    if not isinstance(links, list):
        raise InputError("required_network_links must be a list")
    for link in links:
        if (
            not isinstance(link, dict)
            or not isinstance(link.get("from"), str)
            or not isinstance(link.get("to"), str)
        ):
            raise InputError("required_network_links entries need string from/to values")
    return any(link["from"] == source and link["to"] == target for link in links)


def _all_links(model: ComposeModel) -> set[tuple[str, str]]:
    links = model.contracts.get("required_network_links", [])
    if not isinstance(links, list):
        raise InputError("required_network_links must be a list")
    result: set[tuple[str, str]] = set()
    for link in links:
        if (
            not isinstance(link, dict)
            or not isinstance(link.get("from"), str)
            or not isinstance(link.get("to"), str)
        ):
            raise InputError("required_network_links entries need string from/to values")
        result.add((link["from"], link["to"]))
    return result


def _validate_contracts(model: ComposeModel) -> None:
    _all_links(model)
    for kind in ("required_mounts", "required_environment"):
        values = _contract_map(model, kind)
        for service, items in values.items():
            if (
                not isinstance(service, str)
                or not isinstance(items, list)
                or not all(isinstance(item, str) for item in items)
            ):
                raise InputError(f"{kind} entries must map service names to string lists")


def _downgrade(status: Status, unresolved: bool) -> Status:
    return "UNKNOWN" if unresolved else status


def _unresolved_findings(base: ComposeModel, head: ComposeModel) -> list[Witness]:
    reasons = sorted(set(base.unresolved_reasons + head.unresolved_reasons))
    if not reasons:
        return []
    return [
        _witness(
            "COMPOSE_ANALYSIS_INCOMPLETE",
            "UNKNOWN",
            "compose-model",
            "Some Compose semantics could not be resolved; findings are not conclusive",
            {"base_unresolved": list(base.unresolved_reasons)},
            {"head_unresolved": list(head.unresolved_reasons)},
            "Both inputs must be represented by a resolved effective Compose model",
            (SourceRef(str(base.path), 1), SourceRef(str(head.path), 1)),
            "Provide resolved, reviewed Compose files without unsupported features",
            {"operator": "effective_model_resolved", "unresolved_reasons": reasons},
        )
    ]


def compare(base_path: Path, head_path: Path) -> list[Witness]:
    """Compare modeled state; only explicit, unchanged invariants can establish proof."""
    base = load_compose(base_path)
    head = load_compose(head_path)
    _validate_contracts(base)
    _validate_contracts(head)
    base_graph = ContractGraph.from_compose(base)
    head_graph = ContractGraph.from_compose(head)
    unresolved = base.unresolved or head.unresolved
    contract_drift = head.contracts_present and head.contracts != base.contracts
    findings: list[Witness] = []
    base_links = _all_links(base)
    if contract_drift:
        changed_sections = sorted(
            key
            for key in base.contracts.keys() | head.contracts.keys()
            if base.contracts.get(key) != head.contracts.get(key)
        )
        contract_sources = tuple(
            SourceRef(str(model.path), model.lines.get("__contracts__", 1))
            for model in (base, head)
            if model.contracts_present
        )
        findings.append(
            _witness(
                "COMPOSE_CONTRACT_CHANGED",
                "UNKNOWN",
                "x-deploywitness",
                "Contract declarations differ between baseline and candidate",
                {"present": base.contracts_present, "changed_sections": changed_sections},
                {"present": head.contracts_present},
                "Contract changes require review before they can justify or suppress proof",
                contract_sources,
                "Review the contract edit and rerun the comparison against the intended invariant",
                {"operator": "contract_declarations_equal", "expected": False},
            )
        )

    for model, label in ((base, "baseline"), (head, "candidate")):
        for service in model.services.values():
            for target in sorted(service.depends_on - model.services.keys()):
                dependency_status: Status = (
                    "UNKNOWN" if label == "baseline" else "PROVEN_CONFIG_BREAK"
                )
                findings.append(
                    _witness(
                        "COMPOSE_DEPENDENCY_TARGET_MISSING",
                        _downgrade(dependency_status, unresolved),
                        f"{service.name}->{target}",
                        f"{label.capitalize()} depends_on references an undefined service",
                        {"source_present": True, "target_present": False},
                        {"depends_on_declared": True},
                        "Every depends_on target identifies a service in the same effective model",
                        (_ref(model, service.name, "depends_on"),),
                        "Define the target service or correct the dependency name",
                        {
                            "operator": "service_present",
                            "service": target,
                            "expected": True,
                            "model": label,
                        },
                    )
                )

    # A baseline contract that is already false cannot prove a regression. Keep it
    # visible as UNKNOWN so the caller knows the contract is not a valid oracle.
    for source, target in sorted(base_links):
        if (
            source not in base.services
            or target not in base.services
            or not base_graph.shared_networks(source, target)
        ):
            findings.append(
                _witness(
                    "COMPOSE_BASELINE_CONTRACT_INVALID",
                    "UNKNOWN",
                    f"{source}->{target}",
                    "Baseline required network link is not satisfied",
                    {
                        "source_present": source in base.services,
                        "target_present": target in base.services,
                        "shared_networks": sorted(base_graph.shared_networks(source, target)),
                    },
                    {"contract": "required_network_links"},
                    "The declared baseline network invariant must hold before comparison",
                    (_ref(base, "__contract__", "required_network_links"),),
                    "Correct the baseline or revise the contract after review",
                    {
                        "operator": "shared_network",
                        "services": [source, target],
                        "base_expected": True,
                    },
                )
            )
    for kind, contracts in (
        ("required_mounts", base.contracts.get("required_mounts", {})),
        ("required_environment", base.contracts.get("required_environment", {})),
    ):
        if not isinstance(contracts, dict):
            raise InputError(f"{kind} contract must be a mapping")
        for service_name, required_items in sorted(contracts.items()):
            if (
                not isinstance(service_name, str)
                or not isinstance(required_items, list)
                or not all(isinstance(item, str) for item in required_items)
            ):
                raise InputError(f"{kind} entries must map service names to string lists")
            baseline_service = base.services.get(service_name)
            for item in required_items:
                present = bool(
                    baseline_service
                    and (
                        any(mount.target == item for mount in baseline_service.mounts)
                        if kind == "required_mounts"
                        else item in baseline_service.environment_keys
                    )
                )
                if not present:
                    findings.append(
                        _witness(
                            "COMPOSE_BASELINE_CONTRACT_INVALID",
                            "UNKNOWN",
                            f"{service_name}:{item}",
                            f"Baseline {kind} contract is not satisfied",
                            {
                                "service_present": baseline_service is not None,
                                "item_present": False,
                            },
                            {"contract": kind},
                            "The declared baseline invariant must hold before comparison",
                            (_ref(base, "__contract__", kind),),
                            "Correct the baseline or revise the contract after review",
                            {
                                "operator": "contract_valid_in_baseline",
                                "kind": kind,
                                "service": service_name,
                                "item": item,
                            },
                        )
                    )

    # A removed service is a configuration change with consequences that depend on
    # its consumers. It is proven only when a declared network contract or a
    # depends_on target is made structurally impossible.
    for name in sorted(base.services.keys() - head.services.keys()):
        contract_users = sorted(
            source
            for source, target in base_links
            if target == name and base_graph.shared_networks(source, target)
        )
        dependents = sorted(
            service.name for service in head.services.values() if name in service.depends_on
        )
        baseline_service = base.services[name]
        required_mount_targets = sorted(
            mount.target
            for mount in baseline_service.mounts
            if mount.target in _contract_map(base, "required_mounts").get(name, [])
        )
        required_environment_keys = sorted(
            key
            for key in baseline_service.environment_keys
            if key in _contract_map(base, "required_environment").get(name, [])
        )
        required_mount = bool(required_mount_targets)
        required_environment = bool(required_environment_keys)
        status: Status = (
            "PROVEN_CONFIG_BREAK"
            if dependents
            or required_mount
            or required_environment
            or (contract_users and head.contracts == base.contracts)
            else "POTENTIAL_RISK"
        )
        if contract_drift and (contract_users or required_mount or required_environment):
            status = "UNKNOWN"
        findings.append(
            _witness(
                "COMPOSE_SERVICE_REMOVED",
                _downgrade(status, unresolved),
                name,
                "Service present in the baseline is absent from the candidate",
                {
                    "present": True,
                    "required_link_users": contract_users,
                    "depends_on_users": dependents,
                    "required_mount_targets": required_mount_targets,
                    "required_environment_keys": required_environment_keys,
                },
                {"present": False},
                "A service required by a contract or still referenced by depends_on remains defined"
                if contract_users or dependents or required_mount or required_environment
                else "No explicit service-presence contract declared",
                (_ref(base, name, "__service__"),),
                "Restore the service or update its consumers and contracts deliberately",
                {
                    "operator": "service_present",
                    "service": name,
                    "base_expected": True,
                    "head_expected": False,
                    "required_mount_targets": required_mount_targets,
                    "required_environment_keys": required_environment_keys,
                },
            )
        )

    # Compose depends_on is itself a structural reference, but not evidence of a
    # network requirement. Removing the target invalidates that reference; removing
    # only the edge is a risk because runtime necessity is unknown.
    for name in sorted(base.services.keys() & head.services.keys()):
        old, new = base.services[name], head.services[name]
        for target in sorted(old.depends_on - new.depends_on):
            # Removing both a service and its dependency edge is not proof that the
            # runtime contract is broken; only a still-dangling edge is structural proof.
            dependency_status = "POTENTIAL_RISK"
            findings.append(
                _witness(
                    "COMPOSE_DEPENDENCY_REMOVED",
                    _downgrade(dependency_status, unresolved),
                    f"{name}->{target}",
                    "Compose depends_on relationship was removed",
                    {"declared": True, "target_present_in_head": target in head.services},
                    {"declared": False},
                    "The declared dependency edge remains present"
                    if target not in head.services
                    else "No explicit dependency invariant declared",
                    (_ref(base, name, "depends_on"), _ref(head, name, "depends_on")),
                    "Restore the dependency if startup ordering or lifecycle coupling is required",
                    {
                        "operator": "depends_on_present",
                        "service": name,
                        "target": target,
                        "base_expected": True,
                        "head_expected": False,
                    },
                )
            )

    # Consider every pair that was connected in the baseline, not only declared
    # depends_on pairs. Connectivity is an observed configuration fact; without an
    # explicit contract its loss is a risk, not proof of an outage.
    old_pairs: set[tuple[str, str]] = set()
    names = sorted(base.services)
    for index, left in enumerate(names):
        for right in names[index + 1 :]:
            shared = base_graph.shared_networks(left, right)
            if shared:
                old_pairs.add((left, right))
    old_pairs.update(base_links)
    for source, target in sorted(old_pairs):
        old_shared = base_graph.shared_networks(source, target)
        new_shared = (
            head_graph.shared_networks(source, target)
            if (source in head.services and target in head.services)
            else frozenset()
        )
        if old_shared and new_shared:
            continue
        if not old_shared and (source, target) not in base_links:
            continue
        contract = _network_contract(base, source, target)
        network_status: Status = (
            "UNKNOWN"
            if contract and not old_shared
            else "PROVEN_CONFIG_BREAK"
            if contract
            else "POTENTIAL_RISK"
        )
        if contract and contract_drift:
            network_status = "UNKNOWN"
        findings.append(
            _witness(
                "COMPOSE_NETWORK_LINK",
                _downgrade(network_status, unresolved),
                f"{source}->{target}",
                "Required or previously shared service network is absent",
                {
                    "shared_networks": sorted(old_shared),
                    "depends_on_declared": source in base.services
                    and target in base.services[source].depends_on,
                    "explicit_contract": contract,
                },
                {
                    "head_shared_networks": sorted(new_shared),
                    "source_present": source in head.services,
                    "target_present": target in head.services,
                },
                f"{source} and {target} share a network"
                if contract
                else "No explicit connectivity invariant declared",
                tuple(
                    [
                        _ref(base, source, "networks"),
                        *([_ref(head, source, "networks")] if source in head.services else []),
                        *([_ref(head, target, "networks")] if target in head.services else []),
                        *(
                            [_ref(base, "__contract__", "required_network_links")]
                            if contract
                            else []
                        ),
                    ]
                ),
                f"Attach {source} and {target} to one shared network, "
                "or update the contract deliberately",
                {
                    "operator": "shared_network",
                    "services": [source, target],
                    "base_expected": True,
                    "head_expected": False,
                },
            )
        )

    for name in sorted(base.services.keys() & head.services.keys()):
        old, new = base.services[name], head.services[name]
        old_mounts = {mount.target: mount for mount in old.mounts}
        new_mounts = {mount.target: mount for mount in new.mounts}
        for target, old_mount in sorted(old_mounts.items()):
            new_mount = new_mounts.get(target)
            if new_mount == old_mount:
                continue
            required = _required(base, "required_mounts", name, target)
            removed = new_mount is None
            # required_mounts means target presence only. A source change may point
            # to an empty/new volume, but does not establish loss or invariant break.
            mount_status: Status = (
                "PROVEN_CONFIG_BREAK" if required and removed else "POTENTIAL_RISK"
            )
            if required and contract_drift:
                mount_status = "UNKNOWN"
            findings.append(
                _witness(
                    "COMPOSE_VOLUME_MOUNT",
                    _downgrade(mount_status, unresolved),
                    f"{name}:{target}",
                    "Persistent mount was removed or its source/type changed",
                    {
                        "target": target,
                        "kind": old_mount.kind,
                        "source": old_mount.source,
                        "mode": old_mount.mode,
                        "required_target": required,
                    },
                    {
                        "head_mount": None
                        if new_mount is None
                        else {
                            "kind": new_mount.kind,
                            "source": new_mount.source,
                            "mode": new_mount.mode,
                        }
                    },
                    f"{name} retains a mount at {target}"
                    if required
                    else "No explicit mount invariant declared",
                    (
                        _ref(base, name, "volumes"),
                        _ref(head, name, "volumes"),
                        *([_ref(base, "__contract__", "required_mounts")] if required else []),
                    ),
                    f"Restore the intended mount at {target}; "
                    "check existing data before changing sources",
                    {
                        "operator": "mount_target_present",
                        "service": name,
                        "target": target,
                        "base_expected": True,
                        "head_expected": not removed,
                    },
                )
            )
        for key in sorted(old.environment_keys - new.environment_keys):
            required = _required(base, "required_environment", name, key)
            environment_status: Status = "PROVEN_CONFIG_BREAK" if required else "POTENTIAL_RISK"
            if required and contract_drift:
                environment_status = "UNKNOWN"
            findings.append(
                _witness(
                    "COMPOSE_ENV_KEY",
                    _downgrade(environment_status, unresolved),
                    f"{name}:{key}",
                    "Environment key removed",
                    {"key_present": True, "required": required},
                    {"key_present": False},
                    f"{name} declares environment key {key}"
                    if required
                    else "No explicit environment invariant declared",
                    (
                        _ref(base, name, "environment"),
                        _ref(head, name, "environment"),
                        *([_ref(base, "__contract__", "required_environment")] if required else []),
                    ),
                    f"Restore {key} or update the contract deliberately",
                    {
                        "operator": "environment_key_present",
                        "service": name,
                        "key": key,
                        "base_expected": True,
                        "head_expected": False,
                    },
                )
            )
        for key in sorted(old.environment_keys & new.environment_keys):
            if old.environment_digests[key] != new.environment_digests[key] and _required(
                base, "required_environment", name, key
            ):
                findings.append(
                    _witness(
                        "COMPOSE_ENV_VALUE",
                        _downgrade("POTENTIAL_RISK", unresolved),
                        f"{name}:{key}",
                        "Significant environment value changed",
                        {"key_present": True},
                        {"value_changed": True},
                        "Key presence is required; no exact value contract declared",
                        (
                            _ref(base, name, "environment"),
                            _ref(head, name, "environment"),
                            _ref(base, "__contract__", "required_environment"),
                        ),
                        f"Review the intended value of {key} without sharing secrets in reports",
                        {"operator": "environment_value_changed", "service": name, "key": key},
                    )
                )

    findings.extend(_unresolved_findings(base, head))
    return findings


def verify_static(witness: Witness, base_path: Path, head_path: Path) -> bool:
    """Reparse both inputs and require exact agreement with an independently recomputed witness."""
    if witness.status not in {"PROVEN_CONFIG_BREAK", "POTENTIAL_RISK", "UNKNOWN"}:
        return False
    try:
        return witness in compare(base_path, head_path)
    except (InputError, OSError, ValueError):
        return False
