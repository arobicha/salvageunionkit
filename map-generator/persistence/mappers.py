"""Pure conversion between core dataclasses and ORM rows."""
from __future__ import annotations
import json

from core.region_data import (
    RegionData, ThreatDetails, SettlementDetails, AreaDetails, EncounterEntry,
)
from core.map_graph import MapGraph
from core import map_graph_serde
from persistence.schema import (
    RegionORM, AreaORM, ThreatORM, SettlementORM, EncounterEntryORM,
)


def region_to_orm(region: RegionData) -> RegionORM:
    return RegionORM(
        id=region.id,
        name=region.name,
        core_feature=region.core_feature,
        terrain_type=region.terrain_type,
        tech_level=region.tech_level,
        max_scrap_budget=region.max_scrap_budget,
        gm_notes=region.gm_notes,
        areas=[area_to_orm(a, region.id) for a in region.areas],
        threats=[threat_to_orm(t, region.id) for t in region.threats],
        settlements=[settlement_to_orm(s, region.id) for s in region.settlements],
        encounter_entries=[encounter_to_orm(e, region.id) for e in region.encounter_table],
    )


def area_to_orm(area: AreaDetails, region_id: str) -> AreaORM:
    return AreaORM(
        id=area.id,
        region_id=region_id,
        name=area.name,
        description=area.description,
        is_salvage=area.is_salvage,
        is_starting=area.is_starting,
        linked_threat_id=area.linked_threat_id,
        scrap_budget=area.scrap_budget,
        notes=area.notes,
        point_crawl_json="",
    )


def threat_to_orm(threat: ThreatDetails, region_id: str) -> ThreatORM:
    return ThreatORM(
        id=threat.id,
        region_id=region_id,
        subtype=threat.subtype,
        name=threat.name,
        description=threat.description,
    )


def settlement_to_orm(s: SettlementDetails, region_id: str) -> SettlementORM:
    return SettlementORM(
        id=s.id,
        region_id=region_id,
        name=s.name,
        feature=s.feature,
        linked_threat_id=s.linked_threat_id,
    )


def encounter_to_orm(e: EncounterEntry, region_id: str) -> EncounterEntryORM:
    return EncounterEntryORM(
        region_id=region_id,
        roll=e.roll,
        description=e.description,
        threat_id=e.threat_id,
    )


def region_from_orm(orm: RegionORM) -> RegionData:
    return RegionData(
        id=orm.id,
        name=orm.name,
        core_feature=orm.core_feature,
        terrain_type=orm.terrain_type,
        tech_level=orm.tech_level,
        max_scrap_budget=orm.max_scrap_budget,
        gm_notes=orm.gm_notes,
        threats=[
            ThreatDetails(
                id=t.id, subtype=t.subtype, name=t.name, description=t.description,
            ) for t in orm.threats
        ],
        settlements=[
            SettlementDetails(
                id=s.id, name=s.name, feature=s.feature,
                linked_threat_id=s.linked_threat_id,
            ) for s in orm.settlements
        ],
        areas=[area_from_orm(a) for a in orm.areas],
        encounter_table=[
            EncounterEntry(roll=e.roll, description=e.description, threat_id=e.threat_id)
            for e in orm.encounter_entries
        ],
    )


def area_from_orm(orm: AreaORM) -> AreaDetails:
    return AreaDetails(
        id=orm.id,
        name=orm.name,
        description=orm.description,
        is_salvage=orm.is_salvage,
        is_starting=orm.is_starting,
        linked_threat_id=orm.linked_threat_id,
        scrap_budget=orm.scrap_budget,
        notes=orm.notes,
    )


def graph_to_json(graph: MapGraph) -> str:
    return json.dumps(map_graph_serde.to_dict(graph))


def graph_from_json(blob: str) -> MapGraph | None:
    if not blob:
        return None
    return map_graph_serde.from_dict(json.loads(blob))
