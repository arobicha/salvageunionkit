"""Composite Area View: point-crawl map + inspector + notes."""
from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QSplitter, QVBoxLayout, QLabel, QTabWidget, QPushButton,
    QHBoxLayout, QFileDialog, QMessageBox,
)

from core.region_data import AreaDetails
from core.map_graph import MapGraph
from app.canvas import MapCanvas
from app.region_workspace.area_view.point_inspector import PointInspector
from app.region_workspace.region_view.notes_editor import NotesEditor

_IMAGE_FILTER = "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
_PNG_FILTER = "PNG Images (*.png)"


class AreaView(QWidget):
    notes_changed = Signal(str, str)
    regenerate_requested = Signal(str)
    point_edited = Signal(str, str, str, str, str, int)
    graph_mutated = Signal(str)                       # area_id
    background_chosen = Signal(str, str)              # area_id, file_path
    background_cleared = Signal(str)                  # area_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._area_id: str | None = None
        self._graph: MapGraph | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addLayout(self._build_header())
        root.addWidget(self._build_splitter(), 1)
        self._wire_canvas()

    def _build_header(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self._header = QLabel("")
        self._header.setStyleSheet(
            "font-weight: bold; color: #c8783c; font-size: 14px; padding: 6px 8px;"
        )
        row.addWidget(self._header, 1)
        self._regen_btn = QPushButton("Regenerate Map")
        self._set_bg_btn = QPushButton("Set Background…")
        self._clear_bg_btn = QPushButton("Clear Background")
        self._export_btn = QPushButton("Export PNG…")
        self._regen_btn.clicked.connect(self._on_regen)
        self._set_bg_btn.clicked.connect(self._on_set_background)
        self._clear_bg_btn.clicked.connect(self._on_clear_background)
        self._export_btn.clicked.connect(self._on_export)
        for b in (self._regen_btn, self._set_bg_btn, self._clear_bg_btn, self._export_btn):
            row.addWidget(b)
        return row

    def _build_splitter(self) -> QSplitter:
        splitter = QSplitter(Qt.Horizontal)
        self._canvas = MapCanvas()
        splitter.addWidget(self._canvas)
        right = QTabWidget()
        self._inspector = PointInspector()
        self._notes = NotesEditor()
        right.addTab(self._inspector, "Inspector")
        right.addTab(self._notes, "Notes")
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        return splitter

    def _wire_canvas(self) -> None:
        self._canvas.node_selected.connect(self._on_node_selected)
        self._canvas.graph_mutated.connect(self._on_graph_mutated)
        self._inspector.point_committed.connect(self._on_point_committed)
        self._notes.notes_changed.connect(self._on_notes)

    def load(
        self,
        area: AreaDetails,
        graph: MapGraph | None,
        background_bytes: bytes | None = None,
    ) -> None:
        self._area_id = area.id
        self._graph = graph
        self._header.setText(
            f"Area: {area.name}  ·  {area.scrap_budget}sc"
            + ("  ·  salvage" if area.is_salvage else "")
            + ("  ·  starting" if area.is_starting else "")
        )
        self._inspector.clear()
        self._notes.set_notes(area.notes)
        self._canvas.load_graph(graph if graph is not None else _empty_graph(area.name))
        if background_bytes:
            pixmap = QPixmap()
            if pixmap.loadFromData(background_bytes):
                self._canvas.set_background_image(pixmap)

    def current_graph(self) -> MapGraph | None:
        return self._canvas.current_graph()

    def _on_regen(self) -> None:
        if self._area_id is not None:
            self.regenerate_requested.emit(self._area_id)

    def _on_set_background(self) -> None:
        if self._area_id is None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose Background Image", str(Path.home()), _IMAGE_FILTER,
        )
        if not path:
            return
        pixmap = QPixmap(path)
        if pixmap.isNull():
            QMessageBox.warning(self, "Background", f"Could not load image: {path}")
            return
        self._canvas.set_background_image(pixmap)
        self.background_chosen.emit(self._area_id, path)

    def _on_clear_background(self) -> None:
        if self._area_id is None:
            return
        self._canvas.clear_background_image()
        self.background_cleared.emit(self._area_id)

    def _on_export(self) -> None:
        if self._area_id is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Map PNG", str(Path.home()), _PNG_FILTER,
        )
        if not path:
            return
        image = self._canvas.export_to_image()
        if not image.save(path, "PNG"):
            QMessageBox.warning(self, "Export", f"Could not save image: {path}")

    def _on_node_selected(self, node_id: str) -> None:
        graph = self._canvas.current_graph()
        if graph is None:
            return
        try:
            self._inspector.show_point(graph.node_by_id(node_id))
        except KeyError:
            pass

    def _on_graph_mutated(self) -> None:
        if self._area_id is not None:
            self.graph_mutated.emit(self._area_id)

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
