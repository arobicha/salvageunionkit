from __future__ import annotations
from dataclasses import dataclass, field
from typing import Final

NodeType = str

VALID_TYPES: Final[frozenset[str]] = frozenset({
    # ── Area map types ───────────────────────────────────────────────────
    "entry", "encounter", "environmental", "scrap_guarded", "scrap_open", "special",
    # ── Region map types ─────────────────────────────────────────────────
    "settlement", "threat", "area",
})


@dataclass
class LocationNode:
    id: str
    name: str
    type: NodeType
    x: float  # normalized 0.0–1.0
    y: float  # normalized 0.0–1.0
    description: str = ""
    scrap_value: int = 0
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.type not in VALID_TYPES:
            raise ValueError(f"Unknown node type '{self.type}'. Must be one of {VALID_TYPES}")
        if not (0.0 <= self.x <= 1.0 and 0.0 <= self.y <= 1.0):
            raise ValueError(f"Coordinates must be in [0,1]; got ({self.x}, {self.y})")
