from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from core.node import LocationNode
from core.edge import MapEdge


@dataclass
class MapGraph:
    title: str
    subtitle: str
    terrain_type: str
    nodes: list[LocationNode]
    edges: list[MapEdge]
    generator_id: str
    generator_params: dict[str, Any]
    tech_level: int = 1
    scrap_budget: int = 0
    renderer_hints: dict[str, Any] = field(default_factory=dict)

    def node_by_id(self, node_id: str) -> LocationNode:
        for node in self.nodes:
            if node.id == node_id:
                return node
        raise KeyError(f"No node with id '{node_id}'")

    def edges_for_node(self, node_id: str) -> list[MapEdge]:
        return [e for e in self.edges if e.source_id == node_id or e.target_id == node_id]

    def present_types(self) -> list[str]:
        seen: list[str] = []
        for node in self.nodes:
            if node.type not in seen:
                seen.append(node.type)
        return seen
