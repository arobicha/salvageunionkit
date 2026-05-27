"""Rendered region-map preview using PilRenderer."""
from __future__ import annotations
from io import BytesIO

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea

from core.map_graph import MapGraph
from renderers.pil_renderer import PilRenderer

_PREVIEW_W = 1024
_PREVIEW_H = 1024


class RegionMapPreview(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._renderer = PilRenderer()
        self._graph: MapGraph | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)

        self._refresh_btn = QPushButton("Refresh Map")
        self._refresh_btn.clicked.connect(self._render)
        root.addWidget(self._refresh_btn)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._image_label = QLabel("No region map.")
        self._image_label.setAlignment(Qt.AlignCenter)
        self._scroll.setWidget(self._image_label)
        root.addWidget(self._scroll, 1)

    def set_graph(self, graph: MapGraph | None) -> None:
        self._graph = graph
        self._render()

    def _render(self) -> None:
        if self._graph is None or not self._graph.nodes:
            self._image_label.setText("No region map.")
            self._image_label.setPixmap(QPixmap())
            return
        image = self._renderer.render(self._graph, _PREVIEW_W, _PREVIEW_H)
        buf = BytesIO()
        image.save(buf, format="PNG")
        qimg = QImage.fromData(buf.getvalue(), "PNG")
        self._image_label.setPixmap(QPixmap.fromImage(qimg))
        self._image_label.setText("")
