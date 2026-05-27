"""Top-level Region Workspace: nav rail + stacked Region/Area views."""
from __future__ import annotations
import uuid

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QStackedWidget, QLabel

from core.region_data import RegionData, AreaDetails
from core.map_graph import MapGraph
from generators.region_wizard_gen import build_graph as build_region_graph
from generators.point_crawl import PointCrawlGenerator
from persistence import RegionRepository
from app.region_workspace.nav_rail import NavRail
from app.region_workspace.region_view import RegionView
from app.region_workspace.area_view import AreaView


class RegionWorkspace(QWidget):
    region_changed = Signal(object)  # emits RegionData

    def __init__(self, repository: RegionRepository, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._repo = repository
        self._region: RegionData | None = None
        self._region_graph: MapGraph | None = None

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._nav = NavRail()
        root.addWidget(self._nav)

        self._stack = QStackedWidget()
        self._placeholder = QLabel("No region open. Use File → New Region Wizard or Open Region…")
        self._placeholder.setStyleSheet("color: #6a6560; padding: 24px;")
        self._region_view = RegionView()
        self._area_view = AreaView()
        self._stack.addWidget(self._placeholder)
        self._stack.addWidget(self._region_view)
        self._stack.addWidget(self._area_view)
        root.addWidget(self._stack, 1)

        self._nav.region_selected.connect(self._show_region)
        self._nav.area_selected.connect(self._show_area)
        self._nav.new_area_requested.connect(self._on_new_area)
        self._nav.delete_area_requested.connect(self._on_delete_area)
        self._region_view.notes_changed.connect(self._on_region_notes)
        self._area_view.notes_changed.connect(self._on_area_notes)
        self._area_view.regenerate_requested.connect(self._on_area_regenerate)
        self._area_view.point_edited.connect(self._on_point_edited)
        self._area_view.graph_mutated.connect(self._on_area_graph_mutated)
        self._area_view.background_chosen.connect(self._on_background_chosen)
        self._area_view.background_cleared.connect(self._on_background_cleared)

    def open_region(self, region: RegionData) -> None:
        self._region = region
        self._region_graph = build_region_graph(region)
        self._nav.load_region(region)
        self._show_region()
        self.region_changed.emit(region)

    def current_region(self) -> RegionData | None:
        return self._region

    def current_view_graph(self) -> MapGraph | None:
        if self._stack.currentWidget() is self._area_view:
            return self._area_view.current_graph()
        return self._region_graph

    def close_region(self) -> None:
        self._region = None
        self._region_graph = None
        self._nav.clear()
        self._stack.setCurrentWidget(self._placeholder)

    def _show_region(self) -> None:
        if self._region is None:
            return
        self._region_view.load(self._region, self._region_graph)
        self._stack.setCurrentWidget(self._region_view)

    def _show_area(self, area_id: str) -> None:
        if self._region is None:
            return
        area = _find_area(self._region, area_id)
        if area is None:
            return
        graph = self._repo.load_area_point_crawl(area_id)
        if graph is None:
            graph = self._generate_area_graph(area)
            self._repo.save_area_point_crawl(area_id, graph)
        bg = self._repo.get_area_background(area_id)
        self._area_view.load(area, graph, bg.image_bytes if bg else None)
        self._stack.setCurrentWidget(self._area_view)

    def _on_new_area(self) -> None:
        if self._region is None:
            return
        new_area = AreaDetails(name=f"New Area {len(self._region.areas) + 1}")
        self._region.areas.append(new_area)
        self._repo.save_region(self._region)
        self._region_graph = build_region_graph(self._region)
        self._nav.load_region(self._region)

    def _on_delete_area(self, area_id: str) -> None:
        if self._region is None:
            return
        self._region.areas = [a for a in self._region.areas if a.id != area_id]
        self._repo.save_region(self._region)
        self._region_graph = build_region_graph(self._region)
        self._nav.load_region(self._region)
        self._show_region()

    def _on_region_notes(self, notes: str) -> None:
        if self._region is None:
            return
        self._region.gm_notes = notes
        self._repo.update_region_notes(self._region.id, notes)

    def _on_area_notes(self, area_id: str, notes: str) -> None:
        if self._region is None:
            return
        area = _find_area(self._region, area_id)
        if area is None:
            return
        area.notes = notes
        self._repo.update_area(area)

    def _on_area_regenerate(self, area_id: str) -> None:
        if self._region is None:
            return
        area = _find_area(self._region, area_id)
        if area is None:
            return
        graph = self._generate_area_graph(area)
        self._repo.save_area_point_crawl(area_id, graph)
        self._area_view.load(area, graph)

    def _on_point_edited(
        self, area_id: str, _node_id: str, _name: str, _type: str, _desc: str, _scrap: int,
    ) -> None:
        graph = self._area_view.current_graph()
        if graph is None:
            return
        self._repo.save_area_point_crawl(area_id, graph)

    def _on_area_graph_mutated(self, area_id: str) -> None:
        graph = self._area_view.current_graph()
        if graph is None:
            return
        self._repo.save_area_point_crawl(area_id, graph)

    def _on_background_chosen(self, area_id: str, file_path: str) -> None:
        try:
            data = open(file_path, "rb").read()
        except OSError:
            return
        from PySide6.QtGui import QPixmap
        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            return
        self._repo.set_area_background(area_id, data, pixmap.width(), pixmap.height())

    def _on_background_cleared(self, area_id: str) -> None:
        self._repo.clear_area_background(area_id)

    def _generate_area_graph(self, area: AreaDetails) -> MapGraph:
        if self._region is None:
            raise RuntimeError("No region open")
        params = {
            "seed": 0,
            "node_count": 10,
            "connectivity": "dungeon",
            "map_title": area.name or "Area",
            "tech_level": self._region.tech_level,
            "scrap_budget": area.scrap_budget,
            "terrain_type": self._region.terrain_type,
        }
        return PointCrawlGenerator().generate(params)


def _find_area(region: RegionData, area_id: str) -> AreaDetails | None:
    for area in region.areas:
        if area.id == area_id:
            return area
    return None
