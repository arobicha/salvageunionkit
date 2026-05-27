"""Composite Region View: lists + notes + region map preview."""
from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QSplitter, QVBoxLayout, QLabel, QTabWidget

from core.region_data import RegionData
from core.map_graph import MapGraph
from app.region_workspace.region_view.entity_lists import EntityLists
from app.region_workspace.region_view.notes_editor import NotesEditor
from app.region_workspace.region_view.region_map_preview import RegionMapPreview


class RegionView(QWidget):
    notes_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._header = QLabel("")
        self._header.setStyleSheet(
            "font-weight: bold; color: #c8783c; font-size: 14px; padding: 6px 8px;"
        )
        root.addWidget(self._header)

        splitter = QSplitter(Qt.Horizontal)
        self._lists = EntityLists()
        splitter.addWidget(self._lists)

        self._tabs = QTabWidget()
        self._notes = NotesEditor()
        self._map = RegionMapPreview()
        self._tabs.addTab(self._map, "Region Map")
        self._tabs.addTab(self._notes, "GM Notes")
        splitter.addWidget(self._tabs)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        root.addWidget(splitter, 1)

        self._notes.notes_changed.connect(self.notes_changed)

    def load(self, region: RegionData, region_graph: MapGraph | None) -> None:
        self._header.setText(
            f"{region.name}  ·  {region.terrain_type}  ·  Tech {region.tech_level}  "
            f"·  Max Scrap {region.max_scrap_budget}sc"
        )
        self._lists.populate(region)
        self._notes.set_notes(region.gm_notes)
        self._map.set_graph(region_graph)
