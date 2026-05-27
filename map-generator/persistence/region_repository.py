"""Repository for region persistence — sole entry point to the DB."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select, delete
from sqlalchemy.orm import sessionmaker, Session

from core.region_data import RegionData, AreaDetails
from core.map_graph import MapGraph
from persistence.engine import build_engine, build_session_factory
from persistence.schema import RegionORM, AreaORM
from persistence import mappers


@dataclass(frozen=True)
class AreaBackground:
    image_bytes: bytes
    native_w: int
    native_h: int


@dataclass(frozen=True)
class RegionSummary:
    id: str
    name: str
    terrain_type: str
    tech_level: int


class RegionRepository:
    def __init__(self, db_path: Path) -> None:
        self._engine = build_engine(db_path)
        self._session_factory: sessionmaker[Session] = build_session_factory(self._engine)

    def list_regions(self) -> list[RegionSummary]:
        with self._session_factory() as session:
            rows = session.execute(
                select(RegionORM.id, RegionORM.name, RegionORM.terrain_type, RegionORM.tech_level)
                .order_by(RegionORM.created_at.desc())
            ).all()
            return [RegionSummary(id=r[0], name=r[1], terrain_type=r[2], tech_level=r[3]) for r in rows]

    def save_region(self, region: RegionData) -> None:
        with self._session_factory() as session:
            preserved = _capture_area_blobs(session, region.id)
            existing = session.get(RegionORM, region.id)
            if existing is not None:
                session.delete(existing)
                session.flush()
            session.add(mappers.region_to_orm(region))
            session.flush()
            _restore_area_blobs(session, region.id, preserved)
            session.commit()

    def load_region(self, region_id: str) -> RegionData | None:
        with self._session_factory() as session:
            orm = session.get(RegionORM, region_id)
            if orm is None:
                return None
            return mappers.region_from_orm(orm)

    def delete_region(self, region_id: str) -> None:
        with self._session_factory() as session:
            session.execute(delete(RegionORM).where(RegionORM.id == region_id))
            session.commit()

    def update_region_notes(self, region_id: str, notes: str) -> None:
        with self._session_factory() as session:
            orm = session.get(RegionORM, region_id)
            if orm is None:
                return
            orm.gm_notes = notes
            session.commit()

    def update_area(self, area: AreaDetails) -> None:
        with self._session_factory() as session:
            orm = session.get(AreaORM, area.id)
            if orm is None:
                return
            orm.name = area.name
            orm.description = area.description
            orm.is_salvage = area.is_salvage
            orm.is_starting = area.is_starting
            orm.linked_threat_id = area.linked_threat_id
            orm.scrap_budget = area.scrap_budget
            orm.notes = area.notes
            session.commit()

    def save_area_point_crawl(self, area_id: str, graph: MapGraph) -> None:
        with self._session_factory() as session:
            orm = session.get(AreaORM, area_id)
            if orm is None:
                return
            orm.point_crawl_json = mappers.graph_to_json(graph)
            session.commit()

    def load_area_point_crawl(self, area_id: str) -> MapGraph | None:
        with self._session_factory() as session:
            orm = session.get(AreaORM, area_id)
            if orm is None:
                return None
            return mappers.graph_from_json(orm.point_crawl_json)

    def set_area_background(
        self, area_id: str, image_bytes: bytes, native_w: int, native_h: int,
    ) -> None:
        with self._session_factory() as session:
            orm = session.get(AreaORM, area_id)
            if orm is None:
                return
            orm.background_image = image_bytes
            orm.background_native_w = native_w
            orm.background_native_h = native_h
            session.commit()

    def clear_area_background(self, area_id: str) -> None:
        with self._session_factory() as session:
            orm = session.get(AreaORM, area_id)
            if orm is None:
                return
            orm.background_image = None
            orm.background_native_w = 0
            orm.background_native_h = 0
            session.commit()

    def get_area_background(self, area_id: str) -> AreaBackground | None:
        with self._session_factory() as session:
            orm = session.get(AreaORM, area_id)
            if orm is None or not orm.background_image:
                return None
            return AreaBackground(
                image_bytes=bytes(orm.background_image),
                native_w=orm.background_native_w,
                native_h=orm.background_native_h,
            )


def _capture_area_blobs(session: Session, region_id: str) -> dict[str, dict]:
    rows = session.execute(
        select(AreaORM).where(AreaORM.region_id == region_id)
    ).scalars().all()
    return {
        r.id: {
            "point_crawl_json": r.point_crawl_json,
            "background_image": r.background_image,
            "background_native_w": r.background_native_w,
            "background_native_h": r.background_native_h,
        }
        for r in rows
    }


def _restore_area_blobs(
    session: Session, region_id: str, preserved: dict[str, dict],
) -> None:
    if not preserved:
        return
    rows = session.execute(
        select(AreaORM).where(AreaORM.region_id == region_id)
    ).scalars().all()
    for row in rows:
        saved = preserved.get(row.id)
        if not saved:
            continue
        row.point_crawl_json = saved["point_crawl_json"]
        row.background_image = saved["background_image"]
        row.background_native_w = saved["background_native_w"]
        row.background_native_h = saved["background_native_h"]
