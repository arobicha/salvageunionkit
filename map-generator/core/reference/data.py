"""Loader: parse the bundled reference_data.json into typed domain objects."""
from __future__ import annotations
import json
from pathlib import Path

from core.reference.models import (
    RollBracket, RollTable, ReferenceSection, ReferenceSheet,
)

_DATA_FILENAME = "reference_data.json"


def load_reference_sheet(path: Path | None = None) -> ReferenceSheet:
    json_path = path or (Path(__file__).parent / _DATA_FILENAME)
    raw = json.loads(json_path.read_text(encoding="utf-8"))
    tables = tuple(_parse_table(t) for t in raw["tables"])
    sections = tuple(_parse_section(s) for s in raw["sections"])
    return ReferenceSheet(tables=tables, sections=sections)


def _parse_table(raw: dict) -> RollTable:
    brackets = tuple(
        RollBracket(
            min_roll=int(b["min"]),
            max_roll=int(b["max"]),
            headline=str(b["headline"]),
            body=str(b["body"]),
        )
        for b in raw["brackets"]
    )
    return RollTable(
        id=str(raw["id"]),
        name=str(raw["name"]),
        group=str(raw["group"]),
        page_ref=str(raw.get("page_ref", "")),
        brackets=brackets,
    )


def _parse_section(raw: dict) -> ReferenceSection:
    return ReferenceSection(
        id=str(raw["id"]),
        name=str(raw["name"]),
        group=str(raw["group"]),
        page_ref=str(raw.get("page_ref", "")),
        body=str(raw["body"]),
    )
