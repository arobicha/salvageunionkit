"""Procedural name and sub-type generation for Salvage Union locations."""
from __future__ import annotations
import json
import random
from pathlib import Path

_DATA_PATH = Path(__file__).parent.parent / "data" / "name_parts.json"
_parts: dict | None = None


def _load() -> dict:
    global _parts
    if _parts is None:
        _parts = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    return _parts


# ── Area map names ────────────────────────────────────────────────────────────

def generate_name(node_type: str, rng: random.Random) -> str:
    parts = _load()
    bucket = parts.get(node_type, next(iter(parts.values())))
    prefixes: list[str] = bucket.get("prefixes", [])
    middles: list[str] = bucket.get("middles", [])

    if node_type in ("entry", "encounter", "environmental"):
        return rng.choice(prefixes) + rng.choice(middles)
    return rng.choice(prefixes) + " " + rng.choice(middles)


def generate_subtype(node_type: str, rng: random.Random) -> str:
    """Return a specific threat/loot sub-type description for an area-map node."""
    parts = _load()
    bucket = parts.get(node_type, {})
    subtypes: list[str] = bucket.get("subtypes", [])
    if not subtypes:
        return ""
    return rng.choice(subtypes)


# ── Region map names ──────────────────────────────────────────────────────────

def generate_settlement_name(rng: random.Random) -> str:
    parts = _load()
    bucket = parts["settlement"]
    return rng.choice(bucket["prefixes"]) + rng.choice(bucket["middles"])


def generate_area_name(rng: random.Random) -> str:
    parts = _load()
    bucket = parts["area"]
    return rng.choice(bucket["prefixes"]) + " " + rng.choice(bucket["middles"])


def generate_threat_name(subtype: str, rng: random.Random) -> str:
    """Generate a threat name appropriate to its Salvage Union sub-type."""
    parts = _load()
    key = f"threat_{subtype.lower()}"
    bucket = parts.get(key, {})

    if subtype == "Tyrant":
        templates: list[str] = bucket.get("templates", ["{name}"])
        names: list[str] = bucket.get("names", ["Unknown"])
        return rng.choice(templates).format(name=rng.choice(names))

    # Torment, Environmental, Brute, Aberration all use "The <name>" pattern
    names = bucket.get("names", ["Unknown"])
    return "The " + rng.choice(names)
