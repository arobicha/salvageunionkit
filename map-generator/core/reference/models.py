"""Immutable domain types for the GM reference sheet."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class RollBracket:
    min_roll: int
    max_roll: int
    headline: str
    body: str

    def contains(self, roll: int) -> bool:
        return self.min_roll <= roll <= self.max_roll


@dataclass(frozen=True)
class RollTable:
    id: str
    name: str
    group: str
    page_ref: str
    brackets: tuple[RollBracket, ...]

    def lookup(self, roll: int) -> RollBracket:
        for bracket in self.brackets:
            if bracket.contains(roll):
                return bracket
        raise ValueError(f"No bracket in {self.id} covers roll {roll}")


@dataclass(frozen=True)
class ReferenceSection:
    id: str
    name: str
    group: str
    page_ref: str
    body: str


@dataclass(frozen=True)
class ReferenceSheet:
    tables: tuple[RollTable, ...]
    sections: tuple[ReferenceSection, ...]

    def groups(self) -> tuple[str, ...]:
        seen: list[str] = []
        for item in (*self.tables, *self.sections):
            if item.group not in seen:
                seen.append(item.group)
        return tuple(seen)
