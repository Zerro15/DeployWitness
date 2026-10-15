"""Typed graph of statically visible Compose relationships."""

from dataclasses import dataclass
from typing import Literal

from deploywitness.model import ComposeModel

EdgeKind = Literal["network", "mount", "depends_on"]


@dataclass(frozen=True, order=True)
class Edge:
    source: str
    target: str
    kind: EdgeKind


@dataclass(frozen=True)
class ContractGraph:
    edges: frozenset[Edge]

    @classmethod
    def from_compose(cls, model: ComposeModel) -> "ContractGraph":
        edges: set[Edge] = set()
        for service in model.services.values():
            edges.update(Edge(service.name, network, "network")
                         for network in service.networks)
            edges.update(Edge(service.name, mount.target, "mount")
                         for mount in service.mounts)
            edges.update(Edge(service.name, target, "depends_on")
                         for target in service.depends_on)
        return cls(frozenset(edges))

    def shared_networks(self, left: str, right: str) -> frozenset[str]:
        left_networks = {edge.target for edge in self.edges
                         if edge.source == left and edge.kind == "network"}
        right_networks = {edge.target for edge in self.edges
                          if edge.source == right and edge.kind == "network"}
        return frozenset(left_networks & right_networks)
