"""Converts RegionData from the creation wizard into a renderable MapGraph."""
from __future__ import annotations
import random
import uuid

from core.map_graph import MapGraph
from core.node import LocationNode
from core.edge import MapEdge
from core.region_data import RegionData
from generators._spatial import poisson_disk_sample, build_organic_edges, ensure_connected
from generators._scrap import apportion_area_budgets


def build_graph(region: RegionData, seed: int = 0) -> MapGraph:
    """Convert filled-in RegionData into a MapGraph for display and export."""
    total = len(region.settlements) + len(region.threats) + len(region.areas)
    if total == 0:
        return _empty_graph(region)

    rng = random.Random(seed or None)
    positions = poisson_disk_sample(total, rng)

    # Fill per-area scrap budgets that the user left at 0
    area_budgets = apportion_area_budgets(len(region.areas), region.tech_level, rng)
    for area, budget in zip(region.areas, area_budgets):
        if area.scrap_budget == 0:
            area.scrap_budget = budget

    nodes = _build_nodes(region, positions)
    raw_edges = ensure_connected(total, build_organic_edges(positions), positions)
    edges = [
        MapEdge(
            id=str(uuid.uuid4()),
            source_id=nodes[a].id,
            target_id=nodes[b].id,
        )
        for a, b in raw_edges
    ]

    return MapGraph(
        title=region.name,
        subtitle=f"A {region.terrain_type} Region · Tech {region.tech_level}",
        terrain_type=region.terrain_type,
        nodes=nodes,
        edges=edges,
        generator_id="region_wizard",
        generator_params={},
        tech_level=region.tech_level,
        scrap_budget=sum(a.scrap_budget for a in region.areas),
        renderer_hints={"region_data": region},
    )


def _build_nodes(
    region: RegionData,
    positions: list[tuple[float, float]],
) -> list[LocationNode]:
    nodes: list[LocationNode] = []
    idx = 0

    for s in region.settlements:
        nodes.append(LocationNode(
            id=s.id,
            name=s.name or "Settlement",
            type="settlement",
            x=positions[idx][0],
            y=positions[idx][1],
            description=s.feature,
        ))
        idx += 1

    for t in region.threats:
        nodes.append(LocationNode(
            id=t.id,
            name=t.name or "Unknown Threat",
            type="threat",
            x=positions[idx][0],
            y=positions[idx][1],
            description=t.subtype,
        ))
        idx += 1

    for a in region.areas:
        tags: list[str] = []
        if a.is_salvage:
            tags.append("salvage")
        if a.is_starting:
            tags.append("starting")
        nodes.append(LocationNode(
            id=a.id,
            name=a.name or "Area",
            type="area",
            x=positions[idx][0],
            y=positions[idx][1],
            description=a.description,
            scrap_value=a.scrap_budget,
            tags=tags,
        ))
        idx += 1

    return nodes


def _empty_graph(region: RegionData) -> MapGraph:
    return MapGraph(
        title=region.name,
        subtitle=f"A {region.terrain_type} Region",
        terrain_type=region.terrain_type,
        nodes=[],
        edges=[],
        generator_id="region_wizard",
        generator_params={},
        tech_level=region.tech_level,
        renderer_hints={"region_data": region},
    )
