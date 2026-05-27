"""Qt canvas item representing a connection edge between two nodes."""
from __future__ import annotations

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPen, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QGraphicsPathItem,
    QStyleOptionGraphicsItem,
    QWidget,
)

from core.edge import MapEdge

_UNDERLAY_COLOR = QColor(255, 240, 210, 110)
_OVERLAY_COLOR = QColor(60, 40, 25, 230)
# Dash pattern in device pixels (Qt CustomDashLine units = pen width,
# so divide by pen width to get the right visual length at 5px pen).
_DASH_PX = 14.0   # visual px per dash segment
_GAP_PX = 10.0    # visual px per gap
_OVERLAY_W = 5
_UNDERLAY_W = 11


class EdgeItem(QGraphicsPathItem):
    def __init__(self, edge: MapEdge) -> None:
        super().__init__()
        self._edge = edge
        self._src: QPointF = QPointF(0, 0)
        self._dst: QPointF = QPointF(0, 0)
        self.setZValue(-1)
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, False)

    @property
    def edge_id(self) -> str:
        return self._edge.id

    @property
    def source_node_id(self) -> str:
        return self._edge.source_id

    @property
    def target_node_id(self) -> str:
        return self._edge.target_id

    def update_endpoints(self, src: QPointF, dst: QPointF) -> None:
        self.prepareGeometryChange()
        self._src = src
        self._dst = dst
        path = QPainterPath()
        path.moveTo(src)
        path.lineTo(dst)
        self.setPath(path)

    def boundingRect(self) -> QRectF:
        # Expand by pen width so Qt doesn't clip the stroke
        return self.path().boundingRect().adjusted(
            -_UNDERLAY_W, -_UNDERLAY_W, _UNDERLAY_W, _UNDERLAY_W
        )

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        line = QLineF(self._src, self._dst)
        if line.length() < 1:
            return

        painter.save()

        # Pass 1 — cream underlay
        underlay = QPen(_UNDERLAY_COLOR, _UNDERLAY_W)
        underlay.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(underlay)
        painter.drawLine(line)

        # Pass 2 — dark dashed overlay
        # setDashPattern units = multiples of pen width, so divide px by width
        overlay = QPen(_OVERLAY_COLOR, _OVERLAY_W)
        overlay.setCapStyle(Qt.PenCapStyle.FlatCap)
        overlay.setDashPattern([_DASH_PX / _OVERLAY_W, _GAP_PX / _OVERLAY_W])
        painter.setPen(overlay)
        painter.drawLine(line)

        painter.restore()
