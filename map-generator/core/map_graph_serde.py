"""JSON-serializable (de)serialization for MapGraph values."""
from __future__ import annotations
from typing import Any

from core.map_graph import MapGraph
from core.node import LocationNode
from core.edge import MapEdge


def to_dict(graph: MapGraph) -> dict[str, Any]:
    return {
        "title": graph.title,
        "subtitle": graph.subtitle,
        "terrain_type": graph.terrain_type,
        "generator_id": graph.generator_id,
        "generator_params": dict(graph.generator_params),
        "tech_level": graph.tech_level,
        "scrap_budget": graph.scrap_budget,
        "nodes": [_node_to_dict(n) for n in graph.nodes],
        "edges": [_edge_to_dict(e) for e in graph.edges],
    }


def from_dict(data: dict[str, Any]) -> MapGraph:
    return MapGraph(
        title=data["title"],
        subtitle=data.get("subtitle", ""),
        terrain_type=data.get("terrain_type", ""),
        nodes=[_node_from_dict(n) for n in data.get("nodes", [])],
        edges=[_edge_from_dict(e) for e in data.get("edges", [])],
        generator_id=data.get("generator_id", ""),
        generator_params=dict(data.get("generator_params", {})),
        tech_level=int(data.get("tech_level", 1)),
        scrap_budget=int(data.get("scrap_budget", 0)),
    )


def _node_to_dict(node: LocationNode) -> dict[str, Any]:
    return {
        "id": node.id,
        "name": node.name,
        "type": node.type,
        "x": node.x,
        "y": node.y,
        "description": node.description,
        "scrap_value": node.scrap_value,
        "tags": list(node.tags),
    }


def _node_from_dict(d: dict[str, Any]) -> LocationNode:
    return LocationNode(
        id=d["id"],
        name=d["name"],
        type=d["type"],
        x=float(d["x"]),
        y=float(d["y"]),
        description=d.get("description", ""),
        scrap_value=int(d.get("scrap_value", 0)),
        tags=list(d.get("tags", [])),
    )


def _edge_to_dict(edge: MapEdge) -> dict[str, Any]:
    return {
        "id": edge.id,
        "source_id": edge.source_id,
        "target_id": edge.target_id,
        "type": edge.type,
        "difficulty": edge.difficulty,
    }


def _edge_from_dict(d: dict[str, Any]) -> MapEdge:
    return MapEdge(
        id=d["id"],
        source_id=d["source_id"],
        target_id=d["target_id"],
        type=d.get("type", "road"),
        difficulty=int(d.get("difficulty", 1)),
    )
