"""Composite Area View: point-crawl map + inspector + notes."""
from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QSplitter, QVBoxLayout, QLabel, QTabWidget, QPushButton, QHBoxLayout

from core.region_data import AreaDetails
from core.map_graph import MapGraph
from app.canvas import MapCanvas
from app.region_workspace.area_view.point_inspector import PointInspector
from app.region_workspace.region_view.notes_editor import NotesEditor


class AreaView(QWidget):
    notes_changed = Signal(str, str)               # area_id, notes
    regenerate_requested = Signal(str)             # area_id
    point_edited = Signal(str, str, str, str, str, int)  # area_id, node_id, name, type, desc, scrap

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._area_id: str | None = None
        self._graph: MapGraph | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        header_row = QHBoxLayout()
        self._header = QLabel("")
        self._header.setStyleSheet(
            "font-weight: bold; color: #c8783c; font-size: 14px; padding: 6px 8px;"
        )
        header_row.addWidget(self._header, 1)
        self._regen_btn = QPushButton("Regenerate Map")
        self._regen_btn.clicked.connect(self._on_regen)
        header_row.addWidget(self._regen_btn)
        root.addLayout(header_row)

        splitter = QSplitter(Qt.Horizontal)
        self._canvas = MapCanvas()
        self._canvas.node_selected.connect(self._on_node_selected)
        splitter.addWidget(self._canvas)

        right = QTabWidget()
        self._inspector = PointInspector()
        self._inspector.point_committed.connect(self._on_point_committed)
        self._notes = NotesEditor()
        self._notes.notes_changed.connect(self._on_notes)
        right.addTab(self._inspector, "Inspector")
        right.addTab(self._notes, "Notes")
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        root.addWidget(splitter, 1)

    def load(self, area: AreaDetails, graph: MapGraph | None) -> None:
        self._area_id = area.id
        self._graph = graph
        self._header.setText(
            f"Area: {area.name}  ·  {area.scrap_budget}sc"
            + ("  ·  salvage" if area.is_salvage else "")
            + ("  ·  starting" if area.is_starting else "")
        )
        self._inspector.clear()
        self._notes.set_notes(area.notes)
        if graph is not None:
            self._canvas.load_graph(graph)
        else:
            self._canvas.load_graph(_empty_graph(area.name))

    def current_graph(self) -> MapGraph | None:
        return self._canvas.current_graph()

    def _on_regen(self) -> None:
        if self._area_id is not None:
            self.regenerate_requested.emit(self._area_id)

    def _on_node_selected(self, node_id: str) -> None:
        graph = self._canvas.current_graph()
        if graph is None:
            return
        try:
            self._inspector.show_point(graph.node_by_id(node_id))
        except KeyError:
            pass

    def _on_notes(self, notes: str) -> None:
        if self._area_id is not None:
            self.notes_changed.emit(self._area_id, notes)

    def _on_point_committed(
        self, node_id: str, name: str, node_type: str, description: str, scrap: int,
    ) -> None:
        graph = self._canvas.current_graph()
        if graph is None or self._area_id is None:
            return
        try:
            node = graph.node_by_id(node_id)
        except KeyError:
            return
        node.name = name
        node.type = node_type
        node.description = description
        node.scrap_value = scrap
        item = self._canvas._node_items.get(node_id)
        if item:
            item.update_node(node)
        self.point_edited.emit(self._area_id, node_id, name, node_type, description, scrap)


def _empty_graph(name: str) -> MapGraph:
    return MapGraph(
        title=name or "Area",
        subtitle="",
        terrain_type="",
        nodes=[],
        edges=[],
        generator_id="",
        generator_params={},
    )
