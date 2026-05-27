from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

from core.map_graph import MapGraph


class AbstractMapGenerator(ABC):
    id: str
    label: str
    params_schema: dict[str, Any]  # JSON Schema describing sidebar controls

    @abstractmethod
    def generate(self, params: dict[str, Any]) -> MapGraph:
        """Produce a MapGraph from the given parameter dict."""


class GeneratorRegistry:
    _generators: dict[str, AbstractMapGenerator] = {}

    @classmethod
    def register(cls, generator: AbstractMapGenerator) -> AbstractMapGenerator:
        cls._generators[generator.id] = generator
        return generator

    @classmethod
    def get(cls, generator_id: str) -> AbstractMapGenerator:
        if generator_id not in cls._generators:
            raise KeyError(f"No generator registered with id '{generator_id}'")
        return cls._generators[generator_id]

    @classmethod
    def all(cls) -> list[AbstractMapGenerator]:
        return list(cls._generators.values())
