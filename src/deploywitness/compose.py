"""Conservative Compose subset parser. Unsupported resolution never yields proof."""

import re
from pathlib import Path
from typing import Any

import yaml
from yaml.nodes import MappingNode, Node

from deploywitness.model import ComposeModel, Mount, Service

MAX_BYTES = 1_000_000
MAX_NODES = 20_000
MAX_DEPTH = 40
VARIABLE = re.compile(r"\$\{[^}]+\}")


class InputError(ValueError):
    """Invalid or unsupported input."""


def _check_tree(value: Any, seen: set[int], depth: int = 0) -> None:
    if depth > MAX_DEPTH:
        raise InputError("YAML nesting exceeds limit")
    if isinstance(value, (dict, list)):
        if id(value) in seen:
            raise InputError("YAML aliases or cycles are unsupported")
        seen.add(id(value))
        if len(seen) > MAX_NODES:
            raise InputError("YAML complexity exceeds limit")
        items = value.items() if isinstance(value, dict) else enumerate(value)
        for key, child in items:
            _check_tree(key, seen, depth + 1)
            _check_tree(child, seen, depth + 1)


def _lines(node: Node) -> dict[str, int]:
    lines: dict[str, int] = {}
    if not isinstance(node, MappingNode):
        return lines
    for key, value in node.value:
        if key.value == "services" and isinstance(value, MappingNode):
            for service_key, service_node in value.value:
                name = str(service_key.value)
                lines[name] = service_key.start_mark.line + 1
                if isinstance(service_node, MappingNode):
                    for field_key, field_node in service_node.value:
                        lines[f"{name}.{field_key.value}"] = field_node.start_mark.line + 1
    return lines


def _mount(entry: Any) -> Mount:
    if isinstance(entry, str):
        parts = entry.split(":")
        if len(parts) == 1:
            return Mount(parts[0], "anonymous", None)
        source, target = parts[:2]
        kind = "bind" if source.startswith(("/", "./", "../", "~")) else "volume"
        return Mount(target, kind, source)
    if isinstance(entry, dict):
        mount_target = entry.get("target")
        mount_source = entry.get("source")
        mount_kind = entry.get("type", "volume")
        if not isinstance(mount_target, str) or not isinstance(mount_kind, str):
            raise InputError("Invalid long-form volume mount")
        return Mount(mount_target, mount_kind,
                     mount_source if isinstance(mount_source, str) else None)
    raise InputError("Invalid volume mount")


def _names(value: Any, label: str) -> frozenset[str]:
    if isinstance(value, dict):
        return frozenset(str(key) for key in value)
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return frozenset(value)
    raise InputError(f"Invalid {label}")


def load_compose(path: Path) -> ComposeModel:
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise InputError(f"Missing or oversized Compose file: {path}")
    raw = path.read_bytes()
    if len(raw) > MAX_BYTES:
        raise InputError("Compose file exceeds size limit")
    try:
        content = raw.decode("utf-8")
        doc = yaml.safe_load(content)
        node = yaml.compose(content, Loader=yaml.SafeLoader)
    except (UnicodeError, yaml.YAMLError, RecursionError) as exc:
        raise InputError("Invalid or overly complex YAML") from exc
    if not isinstance(doc, dict) or not isinstance(doc.get("services"), dict) or node is None:
        raise InputError("Compose document needs a services mapping")
    _check_tree(doc, set())
    if len(doc["services"]) > 500:
        raise InputError("Too many services")
    services: dict[str, Service] = {}
    for name, data in doc["services"].items():
        if not isinstance(name, str) or not isinstance(data, dict):
            raise InputError("Invalid service definition")
        networks = _names(data.get("networks", ["default"]), "networks")
        depends = _names(data.get("depends_on", []), "depends_on")
        env = data.get("environment", {})
        if isinstance(env, list):
            env_keys = frozenset(item.split("=", 1)[0] for item in env if isinstance(item, str))
        elif isinstance(env, dict):
            env_keys = frozenset(str(key) for key in env)
        else:
            raise InputError("Invalid environment")
        volumes = data.get("volumes", [])
        if not isinstance(volumes, list):
            raise InputError("Invalid volumes")
        services[name] = Service(name, networks, tuple(_mount(v) for v in volumes), env_keys,
                                 depends, bool(data.get("profiles")))
    contracts = doc.get("x-deploywitness", {})
    if not isinstance(contracts, dict):
        raise InputError("x-deploywitness must be a mapping")
    # Interpolation, extends/includes and profiles can change the effective model.
    unresolved = bool(VARIABLE.search(content)) or "include" in doc or any(
        "extends" in data for data in doc["services"].values() if isinstance(data, dict)
    ) or any(service.profile for service in services.values()) or any(
        "network_mode" in data for data in doc["services"].values() if isinstance(data, dict)
    )
    return ComposeModel(path, services, contracts, _lines(node), unresolved)
