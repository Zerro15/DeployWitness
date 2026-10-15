"""Conservative Compose subset parser. Unsupported resolution never yields proof."""

import hashlib
import re
from pathlib import Path
from typing import Any

import yaml
from yaml.nodes import MappingNode, Node, ScalarNode

from deploywitness.model import ComposeModel, Mount, Service

MAX_BYTES = 1_000_000
MAX_NODES = 20_000
MAX_DEPTH = 40
VARIABLE = re.compile(r"\$\{[^}]+\}")


class InputError(ValueError):
    """Invalid or unsupported input."""


class BoundedLoader(yaml.SafeLoader):
    """Reject expensive input before object construction completes."""

    def __init__(self, stream: str) -> None:
        super().__init__(stream)
        self.node_count = 0
        self.node_depth = 0

    def compose_node(self, parent: Node | None, index: Any) -> Node | None:
        self.node_count += 1
        self.node_depth += 1
        if self.node_count > MAX_NODES or self.node_depth > MAX_DEPTH:
            raise InputError("YAML complexity exceeds limit")
        try:
            return super().compose_node(parent, index)
        finally:
            self.node_depth -= 1

    def construct_mapping(self, node: MappingNode, deep: bool = False) -> dict[Any, Any]:
        result: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                duplicate = key in result
            except TypeError as exc:
                raise InputError("Invalid YAML mapping key") from exc
            if duplicate:
                raise InputError("Duplicate YAML mapping key")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def _construct_merge_key(loader: BoundedLoader, node: Node) -> str:
    if not isinstance(node, ScalarNode):
        raise InputError("Invalid YAML merge key")
    return loader.construct_scalar(node)


BoundedLoader.add_constructor("tag:yaml.org,2002:merge", _construct_merge_key)


def _check_tree(
    value: Any, ancestors: set[int] | None = None, depth: int = 0, checked: set[int] | None = None
) -> None:
    if ancestors is None:
        ancestors = set()
    if checked is None:
        checked = set()
    if depth > MAX_DEPTH:
        raise InputError("YAML nesting exceeds limit")
    if isinstance(value, (dict, list)):
        identity = id(value)
        if identity in ancestors:
            raise InputError("YAML alias cycle is unsupported")
        if identity in checked:
            return
        checked.add(identity)
        ancestors.add(identity)
        items = value.items() if isinstance(value, dict) else enumerate(value)
        for key, child in items:
            _check_tree(key, ancestors, depth + 1, checked)
            _check_tree(child, ancestors, depth + 1, checked)
        ancestors.remove(identity)


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
        if key.value == "x-deploywitness" and isinstance(value, MappingNode):
            for contract_key, contract_value in value.value:
                lines[f"__contract__.{contract_key.value}"] = contract_value.start_mark.line + 1
    return lines


def _mount(entry: Any) -> Mount:
    if isinstance(entry, str):
        parts = entry.split(":")
        if len(parts) == 1:
            return Mount(parts[0], "anonymous", None)
        source, target = parts[:2]
        kind = "bind" if source.startswith(("/", "./", "../", "~")) else "volume"
        mode = ":".join(part for part in parts[2:] if part != "rw") or None
        return Mount(target, kind, source, mode)
    if isinstance(entry, dict):
        mount_target = entry.get("target")
        mount_source = entry.get("source")
        mount_kind = entry.get("type", "volume")
        if not isinstance(mount_target, str) or not isinstance(mount_kind, str):
            raise InputError("Invalid long-form volume mount")
        return Mount(
            mount_target,
            mount_kind,
            mount_source if isinstance(mount_source, str) else None,
            "ro" if entry.get("read_only") is True else None,
        )
    raise InputError("Invalid volume mount")


def _names(value: Any, label: str) -> frozenset[str]:
    if isinstance(value, dict):
        return frozenset(str(key) for key in value)
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return frozenset(value)
    raise InputError(f"Invalid {label}")


def _network_names(value: Any) -> frozenset[str]:
    if isinstance(value, dict):
        for config in value.values():
            if config is None:
                continue
            if not isinstance(config, dict):
                raise InputError("Invalid service network configuration")
            aliases = config.get("aliases", [])
            if not isinstance(aliases, list) or not all(isinstance(a, str) for a in aliases):
                raise InputError("Invalid network aliases")
        return frozenset(str(key) for key in value)
    return _names(value, "networks")


def _contains_merge_key(value: Any, checked: set[int] | None = None) -> bool:
    if checked is None:
        checked = set()
    if isinstance(value, dict):
        identity = id(value)
        if identity in checked:
            return False
        checked.add(identity)
        return "<<" in value or any(_contains_merge_key(child, checked) for child in value.values())
    if isinstance(value, list):
        identity = id(value)
        if identity in checked:
            return False
        checked.add(identity)
        return any(_contains_merge_key(child, checked) for child in value)
    return False


def load_compose(path: Path) -> ComposeModel:
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise InputError(f"Missing or oversized Compose file: {path}")
    raw = path.read_bytes()
    if len(raw) > MAX_BYTES:
        raise InputError("Compose file exceeds size limit")
    try:
        content = raw.decode("utf-8")
        doc = yaml.load(content, Loader=BoundedLoader)
        node = yaml.compose(content, Loader=BoundedLoader)
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
        networks = _network_names(data.get("networks", ["default"]))
        depends = _names(data.get("depends_on", []), "depends_on")
        env = data.get("environment", {})
        if isinstance(env, list):
            if not all(isinstance(item, str) for item in env):
                raise InputError("Invalid environment")
            env_values = {item.split("=", 1)[0]: item.partition("=")[2] for item in env}
        elif isinstance(env, dict):
            env_values = {str(key): str(value) for key, value in env.items()}
        else:
            raise InputError("Invalid environment")
        env_keys = frozenset(env_values)
        env_digests = {
            key: hashlib.sha256(value.encode("utf-8")).hexdigest()
            for key, value in env_values.items()
        }
        volumes = data.get("volumes", [])
        if not isinstance(volumes, list):
            raise InputError("Invalid volumes")
        services[name] = Service(
            name,
            networks,
            tuple(_mount(v) for v in volumes),
            env_keys,
            env_digests,
            depends,
            bool(data.get("profiles")),
        )
    contracts = doc.get("x-deploywitness", {})
    if not isinstance(contracts, dict):
        raise InputError("x-deploywitness must be a mapping")
    # These features alter the effective model and are deliberately not guessed.
    reasons: list[str] = []
    if VARIABLE.search(content):
        reasons.append("variable interpolation is not resolved")
    if "include" in doc:
        reasons.append("Compose include is not resolved")
    if any("extends" in data for data in doc["services"].values() if isinstance(data, dict)):
        reasons.append("service extends is not resolved")
    if any(service.profile for service in services.values()):
        reasons.append("service profiles require an explicit profile selection")
    if any("network_mode" in data for data in doc["services"].values() if isinstance(data, dict)):
        reasons.append("network_mode relationships are not modeled")
    if _contains_merge_key(doc):
        reasons.append("YAML merge-key expansion is not supported")
    volume_definitions = doc.get("volumes", {})
    if not isinstance(volume_definitions, dict):
        raise InputError("Top-level volumes must be a mapping")
    if any(config not in ({}, None) for config in volume_definitions.values()):
        reasons.append("top-level volume driver/name options are not modeled")
    for service_name, data in doc["services"].items():
        if not isinstance(data, dict):
            continue
        for field in ("env_file", "configs", "secrets", "links", "volumes_from"):
            if field in data:
                reasons.append(f"service {service_name} uses unsupported {field}")
        mount_entries = data.get("volumes", [])
        if isinstance(mount_entries, list) and any(
            isinstance(mount, dict)
            and any(option in mount for option in ("bind", "volume", "tmpfs"))
            for mount in mount_entries
        ):
            reasons.append(f"service {service_name} uses advanced mount options")
        dependencies = data.get("depends_on")
        if isinstance(dependencies, dict) and any(
            isinstance(value, dict) for value in dependencies.values()
        ):
            reasons.append(f"service {service_name} uses depends_on conditions")
    if path.name in {
        "compose.override.yaml",
        "compose.override.yml",
        "docker-compose.override.yaml",
        "docker-compose.override.yml",
    }:
        reasons.append("override file cannot be analyzed without its ordered base files")
    return ComposeModel(
        path,
        services,
        contracts,
        _lines(node),
        bool(reasons),
        tuple(reasons),
        "x-deploywitness" in doc,
    )
