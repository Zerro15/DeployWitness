from pathlib import Path

from deploywitness.compose import load_compose
from deploywitness.graph import ContractGraph, Edge

ROOT = Path(__file__).resolve().parents[1]


def test_graph_contains_service_relationships() -> None:
    model = load_compose(ROOT / "examples/before/compose.yaml")
    graph = ContractGraph.from_compose(model)
    assert Edge("api", "db", "depends_on") in graph.edges
    assert Edge("api", "backend", "network") in graph.edges
    assert Edge("db", "/var/lib/postgresql/data", "mount") in graph.edges
    assert graph.shared_networks("api", "db") == frozenset({"backend"})
