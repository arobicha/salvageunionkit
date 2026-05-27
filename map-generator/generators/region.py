"""Region-level point crawl generator for Salvage Union."""
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
    spine_branch_positions,
    build_organic_edges,
    build_dungeon_edges,
    ensure_connected,
)
from generators._naming import (
    generate_settlement_name,
    generate_area_name,
    generate_threat_name,
)
from generators._scrap import apportion_area_budgets, region_total_budget

THREAT_SUBTYPES = ("Tyrant", "Torment", "Environmental", "Brute", "Aberration")

_CONNECTIVITY_MODES = ("organic", "spine_branch", "dungeon")

PARAMS_SCHEMA: dict[str, Any] = {
    "settlement_count": {
        "type": "int",
        "label": "Settlements",
        "default": 2,
        "min": 1,
        "max": 4,
    },
    "threat_count": {
        "type": "int",
        "label": "Threats",
        "default": 3,
        "min": 1,
        "max": 5,
    },
    "area_count": {
        "type": "int",
        "label": "Areas",
        "default": 5,
        "min": 2,
        "max": 10,
    },
    "connectivity": {
        "type": "enum",
        "label": "Layout Style",
        "default": "organic",
        "options": list(_CONNECTIVITY_MODES),
    },
    "tech_level": {
        "type": "int",
        "label": "Tech Level",
        "default": 2,
        "min": 1,
        "max": 5,
    },
    "map_title": {
        "type": "str",
        "label": "Map Title",
        "default": "The Region",
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


def _pick_threat_subtypes(count: int, rng: random.Random) -> list[str]:
    """Pick `count` threat sub-types; unique until pool is exhausted."""
    pool = list(THREAT_SUBTYPES)
    rng.shuffle(pool)
    result: list[str] = []
    while len(result) < count:
        result.extend(pool[: count - len(result)])
    return result[:count]


def _build_nodes(
    settlement_count: int,
    threat_count: int,
    area_count: int,
    positions: list[tuple[float, float]],
    area_budgets: list[int],
    rng: random.Random,
) -> list[LocationNode]:
    threat_subtypes = _pick_threat_subtypes(threat_count, rng)
    nodes: list[LocationNode] = []
    idx = 0

    for _ in range(settlement_count):
        nodes.append(LocationNode(
            id=str(uuid.uuid4()),
            name=generate_settlement_name(rng),
            type="settlement",
            x=positions[idx][0],
            y=positions[idx][1],
        ))
        idx += 1

    for subtype in threat_subtypes:
        nodes.append(LocationNode(
            id=str(uuid.uuid4()),
            name=generate_threat_name(subtype, rng),
            type="threat",
            x=positions[idx][0],
            y=positions[idx][1],
            description=subtype,
        ))
        idx += 1

    for area_idx in range(area_count):
        nodes.append(LocationNode(
            id=str(uuid.uuid4()),
            name=generate_area_name(rng),
            type="area",
            x=positions[idx][0],
            y=positions[idx][1],
            scrap_value=area_budgets[area_idx],
        ))
        idx += 1

    return nodes


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


def _build_edges(
    mode: str,
    count: int,
    positions: list[tuple[float, float]],
    nodes: list[LocationNode],
    rng: random.Random,
) -> list[MapEdge]:
    if mode == "spine_branch":
        raw = _spine_branch_edges(count, positions)
    elif mode == "dungeon":
        raw = build_dungeon_edges(positions, rng, extra_ratio=0.30)
    else:
        raw = ensure_connected(count, build_organic_edges(positions), positions)

    return [
        MapEdge(
            id=str(uuid.uuid4()),
            source_id=nodes[a].id,
            target_id=nodes[b].id,
        )
        for a, b in raw
    ]


class RegionGenerator(AbstractMapGenerator):
    id = "region"
    label = "Region"
    params_schema = PARAMS_SCHEMA

    def generate(self, params: dict[str, Any]) -> MapGraph:
        settlement_count = max(1, int(params.get("settlement_count", 2)))
        threat_count = min(5, max(1, int(params.get("threat_count", 3))))
        area_count = max(2, int(params.get("area_count", 5)))
        tech_level = max(1, min(5, int(params.get("tech_level", 2))))
        mode = str(params.get("connectivity", "organic"))
        title = str(params.get("map_title", "The Region"))
        terrain = str(params.get("terrain_type", "Ashfall Plains"))
        seed = int(params.get("seed", 0))

        if mode not in _CONNECTIVITY_MODES:
            raise ValueError(f"Unknown connectivity mode '{mode}'")

        total = settlement_count + threat_count + area_count
        rng = random.Random(seed or None)
        positions = poisson_disk_sample(total, rng)

        area_budgets = apportion_area_budgets(area_count, tech_level, rng)
        total_budget = region_total_budget(tech_level, area_count)

        nodes = _build_nodes(
            settlement_count, threat_count, area_count,
            positions, area_budgets, rng,
        )
        edges = _build_edges(mode, total, positions, nodes, rng)

        return MapGraph(
            title=title,
            subtitle=f"A {terrain} Region · Tech {tech_level}",
            terrain_type=terrain,
            nodes=nodes,
            edges=edges,
            generator_id=self.id,
            generator_params=dict(params),
            tech_level=tech_level,
            scrap_budget=total_budget,
        )


GeneratorRegistry.register(RegionGenerator())
