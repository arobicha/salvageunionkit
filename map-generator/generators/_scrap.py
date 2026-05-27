"""Scrap budget calculation and distribution for Salvage Union maps."""
from __future__ import annotations
import random

from core.node import LocationNode

# Base scrap budget available per area, indexed by tech level (1–5).
_AREA_BUDGET_BY_TECH: dict[int, int] = {
    1: 20,
    2: 35,
    3: 55,
    4: 80,
    5: 120,
}

# Weight controls how much of the budget each scrap node type receives.
_NODE_SCRAP_WEIGHT: dict[str, float] = {
    "scrap_guarded": 2.0,  # higher risk, higher reward
    "scrap_open":    1.0,
    "area":          1.0,  # region area nodes carry their expected area budget
}

_SCRAP_NODE_TYPES: frozenset[str] = frozenset({"scrap_guarded", "scrap_open"})
_REGION_AREA_TYPES: frozenset[str] = frozenset({"area"})


def area_budget(tech_level: int) -> int:
    """Base scrap budget for one area at the given tech level."""
    return _AREA_BUDGET_BY_TECH[max(1, min(5, tech_level))]


def region_total_budget(tech_level: int, area_count: int) -> int:
    """Approximate total scrap for a region — sum of all area budgets."""
    return area_budget(tech_level) * area_count


def apportion_area_budgets(
    area_count: int,
    tech_level: int,
    rng: random.Random,
) -> list[int]:
    """Return per-area budgets with ±30% jitter, rounded to nearest 5."""
    base = area_budget(tech_level)
    result: list[int] = []
    for _ in range(area_count):
        jittered = base * rng.uniform(0.70, 1.30)
        result.append(max(5, round(jittered / 5) * 5))
    return result


def distribute_scrap(
    nodes: list[LocationNode],
    budget: int,
    rng: random.Random,
) -> None:
    """Distribute budget among scrap nodes in-place.

    Guarded scrap receives double the weight of open scrap.
    Each node's allocation is jittered ±20% then rounded to the nearest 5.
    """
    targets = [(i, n) for i, n in enumerate(nodes) if n.type in _SCRAP_NODE_TYPES]
    if not targets or budget <= 0:
        return

    total_weight = sum(_NODE_SCRAP_WEIGHT[n.type] for _, n in targets)
    for _, node in targets:
        weight = _NODE_SCRAP_WEIGHT[node.type]
        base = budget * weight / total_weight
        jittered = base * rng.uniform(0.80, 1.20)
        node.scrap_value = max(5, round(jittered / 5) * 5)
