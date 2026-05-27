"""Background-pixmap helper for MapCanvas: scene sizing + export rendering."""
from __future__ import annotations
from dataclasses import dataclass

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPixmap, QImage, QPainter
from PySide6.QtWidgets import QGraphicsScene, QGraphicsPixmapItem

_BG_Z = -1000.0
_MAX_LOGICAL_SIDE = 800.0


@dataclass(frozen=True)
class BackgroundDims:
    logical_w: float
    logical_h: float
    native_w: int
    native_h: int


class CanvasBackground:
    def __init__(self, scene: QGraphicsScene) -> None:
        self._scene = scene
        self._item: QGraphicsPixmapItem | None = None
        self._dims: BackgroundDims | None = None

    def dims(self) -> BackgroundDims | None:
        return self._dims

    def set_pixmap(self, pixmap: QPixmap) -> BackgroundDims:
        self.clear()
        nw, nh = pixmap.width(), pixmap.height()
        if nw <= 0 or nh <= 0:
            raise ValueError("Background pixmap has zero dimensions")
        lw, lh = _fit_logical(nw, nh)
        scaled = pixmap.scaled(
            int(lw), int(lh),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        item = QGraphicsPixmapItem(scaled)
        item.setZValue(_BG_Z)
        item.setPos(0, 0)
        self._scene.addItem(item)
        self._scene.setSceneRect(0, 0, lw, lh)
        self._item = item
        self._dims = BackgroundDims(lw, lh, nw, nh)
        return self._dims

    def clear(self) -> None:
        if self._item is not None:
            self._scene.removeItem(self._item)
            self._item = None
        self._dims = None
        self._scene.setSceneRect(0, 0, _MAX_LOGICAL_SIDE, _MAX_LOGICAL_SIDE)

    def export_image(self) -> QImage:
        rect = self._scene.sceneRect()
        if self._dims is not None:
            out_w, out_h = self._dims.native_w, self._dims.native_h
        else:
            out_w = max(1, int(rect.width()))
            out_h = max(1, int(rect.height()))
        image = QImage(out_w, out_h, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self._scene.render(painter, QRectF(0, 0, out_w, out_h), rect)
        painter.end()
        return image


def _fit_logical(native_w: int, native_h: int) -> tuple[float, float]:
    if native_w >= native_h:
        return _MAX_LOGICAL_SIDE, _MAX_LOGICAL_SIDE * native_h / native_w
    return _MAX_LOGICAL_SIDE * native_w / native_h, _MAX_LOGICAL_SIDE
