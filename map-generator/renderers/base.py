from __future__ import annotations
from abc import ABC, abstractmethod

from core.map_graph import MapGraph


class AbstractRenderer(ABC):
    @abstractmethod
    def render(self, graph: MapGraph, width: int, height: int) -> object:
        """Render `graph` into an image object at the given pixel dimensions."""
