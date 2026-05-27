"""Point crawl area-map generator for Salvage Union."""
from __future__ import annotations
import random
import uuid
from typing import Any

from core.map_graph import MapGraph
from core.node import LocationNode
from core.edge import MapEdge
from generators.base import AbstractMapGenerator, GeneratorRegistry
from generators._spatial import (
    poisson_disk_sample,
    hub_spoke_positions,
    spine_branch_positions,
    build_organic_edges,
    build_dungeon_edges,
    ensure_connected,
)
from generators._naming import generate_name, generate_subtype
from generators._scrap import distribute_scrap

# Weights must sum to 1.0
_TYPE_WEIGHTS: dict[str, float] = {
    "entry":         0.10,
    "encounter":     0.25,
    "environmental": 0.20,
    "scrap_guarded": 0.20,
    "scrap_open":    0.15,
    "special":       0.10,
}

_CONNECTIVITY_MODES = ("dungeon", "organic", "hub_spoke", "spine_branch")

PARAMS_SCHEMA: dict[str, Any] = {
    "node_count": {
        "type": "int",
        "label": "Node Count",
        "default": 10,
        "min": 4,
        "max": 20,
    },
    "connectivity": {
        "type": "enum",
        "label": "Layout Style",
        "default": "dungeon",
        "options": list(_CONNECTIVITY_MODES),
    },
    "map_title": {
        "type": "str",
        "label": "Map Title",
        "default": "The Rusting Reach",
    },
    "tech_level": {
        "type": "int",
        "label": "Tech Level",
        "default": 2,
        "min": 1,
        "max": 5,
    },
    "scrap_budget": {
        "type": "int",
        "label": "Scrap Budget",
        "default": 0,
        "min": 0,
        "max": 500,
    },
    "terrain_type": {
        "type": "str",
        "label": "Terrain Type",
        "default": "Ashfall Plains",
    },
    "seed": {
        "type": "int",
        "label": "Seed",
        "default": 0,
        "min": 0,
        "max": 999999,
    },
}


def _assign_types(count: int, rng: random.Random) -> list[str]:
    types = list(_TYPE_WEIGHTS.keys())
    weights = [_TYPE_WEIGHTS[t] for t in types]
    assigned = rng.choices(types, weights=weights, k=count)
    # Guarantee at least one entry point
    if "entry" not in assigned:
        assigned[rng.randrange(count)] = "entry"
    return assigned


def _positions_for_mode(
    mode: str,
    count: int,
    rng: random.Random,
) -> list[tuple[float, float]]:
    if mode == "hub_spoke":
        return hub_spoke_positions(count, rng)
    if mode == "spine_branch":
        return spine_branch_positions(count, rng)
    return poisson_disk_sample(count, rng)


def _edges_for_mode(
    mode: str,
    count: int,
    positions: list[tuple[float, float]],
    rng: random.Random,
) -> list[tuple[int, int]]:
    if mode == "dungeon":
        # MST + short loops; NOT forced to be fully connected
        return build_dungeon_edges(positions, rng, extra_ratio=0.25)
    if mode == "hub_spoke":
        return _hub_spoke_edges(count, rng)
    if mode == "spine_branch":
        return _spine_branch_edges(count, positions)
    # organic: dense Delaunay graph, forced connected
    return ensure_connected(count, build_organic_edges(positions), positions)


def _hub_spoke_edges(count: int, rng: random.Random) -> list[tuple[int, int]]:
    edges = [(0, i) for i in range(1, count)]
    candidates = [(i, j) for i in range(1, count) for j in range(i + 1, count)]
    extra = rng.sample(candidates, min(max(1, int(len(candidates) * 0.30)), len(candidates)))
    return edges + extra


def _spine_branch_edges(
    count: int,
    positions: list[tuple[float, float]],
) -> list[tuple[int, int]]:
    spine_count = max(2, int(count * 0.4))
    edges: list[tuple[int, int]] = [(i, i + 1) for i in range(spine_count - 1)]
    for branch_idx in range(spine_count, count):
        bx, by = positions[branch_idx]
        closest = min(
            range(spine_count),
            key=lambda s: (positions[s][0] - bx) ** 2 + (positions[s][1] - by) ** 2,
        )
        edges.append((closest, branch_idx))
    return edges


class PointCrawlGenerator(AbstractMapGenerator):
    id = "point_crawl"
    label = "Point Crawl"
    params_schema = PARAMS_SCHEMA

    def generate(self, params: dict[str, Any]) -> MapGraph:
        seed: int = int(params.get("seed", 0))
        count: int = int(params.get("node_count", 10))
        mode: str = str(params.get("connectivity", "dungeon"))
        title: str = str(params.get("map_title", "The Rusting Reach"))
        terrain: str = str(params.get("terrain_type", "Ashfall Plains"))
        tech_level: int = max(1, min(5, int(params.get("tech_level", 2))))
        scrap_budget: int = max(0, int(params.get("scrap_budget", 0)))

        if mode not in _CONNECTIVITY_MODES:
            raise ValueError(f"Unknown connectivity mode '{mode}'")

        rng = random.Random(seed or None)
        positions = _positions_for_mode(mode, count, rng)
        node_types = _assign_types(count, rng)

        nodes = [
            LocationNode(
                id=str(uuid.uuid4()),
                name=generate_name(node_types[i], rng),
                type=node_types[i],
                x=positions[i][0],
                y=positions[i][1],
                description=generate_subtype(node_types[i], rng),
            )
            for i in range(count)
        ]

        if scrap_budget > 0:
            distribute_scrap(nodes, scrap_budget, rng)

        raw_edges = _edges_for_mode(mode, count, positions, rng)

        edges = [
            MapEdge(
                id=str(uuid.uuid4()),
                source_id=nodes[a].id,
                target_id=nodes[b].id,
            )
            for a, b in raw_edges
        ]

        return MapGraph(
            title=title,
            subtitle=f"A {terrain} Area",
            terrain_type=terrain,
            nodes=nodes,
            edges=edges,
            generator_id=self.id,
            generator_params=dict(params),
            tech_level=tech_level,
            scrap_budget=scrap_budget,
        )


GeneratorRegistry.register(PointCrawlGenerator())
