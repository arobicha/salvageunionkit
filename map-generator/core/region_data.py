"""Rich region data model populated by the region creation wizard."""
from __future__ import annotations
from dataclasses import dataclass, field
import uuid


def _new_id() -> str:
    return str(uuid.uuid4())


@dataclass
class ThreatDetails:
    subtype: str = "Tyrant"   # Tyrant | Torment | Environmental | Brute | Aberration
    name: str = ""
    description: str = ""
    id: str = field(default_factory=_new_id)


@dataclass
class SettlementDetails:
    name: str = ""
    feature: str = ""          # e.g. "Built around a massive Mech Reactor"
    linked_threat_id: str = ""
    id: str = field(default_factory=_new_id)


@dataclass
class AreaDetails:
    name: str = ""
    description: str = ""
    is_salvage: bool = False    # has scrap to collect
    is_starting: bool = False   # safe Mech deploy point
    linked_threat_id: str = ""
    scrap_budget: int = 0
    id: str = field(default_factory=_new_id)


@dataclass
class EncounterEntry:
    roll: int = 1
    description: str = ""
    threat_id: str = ""


@dataclass
class RegionData:
    name: str = "The Region"
    core_feature: str = ""
    terrain_type: str = "Ashfall Plains"
    tech_level: int = 2
    threats: list[ThreatDetails] = field(default_factory=list)
    settlements: list[SettlementDetails] = field(default_factory=list)
    areas: list[AreaDetails] = field(default_factory=list)
    encounter_table: list[EncounterEntry] = field(default_factory=list)
    id: str = field(default_factory=_new_id)
