from __future__ import annotations
from dataclasses import dataclass
from typing import Final

EdgeType = str  # "road" | "path" | "hidden"

VALID_EDGE_TYPES: Final[frozenset[str]] = frozenset({"road", "path", "hidden"})


@dataclass
class MapEdge:
    id: str
    source_id: str
    target_id: str
    type: EdgeType = "road"
    difficulty: int = 1

    def __post_init__(self) -> None:
        if self.type not in VALID_EDGE_TYPES:
            raise ValueError(f"Unknown edge type '{self.type}'. Must be one of {VALID_EDGE_TYPES}")
        if not (1 <= self.difficulty <= 5):
            raise ValueError(f"Difficulty must be 1–5; got {self.difficulty}")
