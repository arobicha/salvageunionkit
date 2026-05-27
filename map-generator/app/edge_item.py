"""Qt canvas item representing a connection edge between two nodes."""
from __future__ import annotations

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt, Signal, QObject
from PySide6.QtGui import QColor, QPen, QPainter
from PySide6.QtWidgets import (
    QGraphicsPathItem,
    QGraphicsItem,
    QGraphicsSceneContextMenuEvent,
    QMenu,
    QStyleOptionGraphicsItem,
    QWidget,
)

from core.edge import MapEdge

_UNDERLAY_COLOR = QColor(255, 240, 210, 110)
_OVERLAY_COLOR = QColor(60, 40, 25, 230)
_SELECTED_COLOR = QColor(200, 120, 60, 255)
_DASH_PX = 14.0
_GAP_PX = 10.0
_OVERLAY_W = 5
_UNDERLAY_W = 11
_HIT_TOLERANCE = 10


class EdgeSignals(QObject):
    deleted = Signal(str)   # edge_id
    selected = Signal(str)  # edge_id


class EdgeItem(QGraphicsPathItem):
    def __init__(self, edge: MapEdge, signals: EdgeSignals | None = None) -> None:
        super().__init__()
        self._edge = edge
        self._signals = signals
        self._src: QPointF = QPointF(0, 0)
        self._dst: QPointF = QPointF(0, 0)
        self.setZValue(-1)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)

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
        from PySide6.QtGui import QPainterPath, QPainterPathStroker
        self.prepareGeometryChange()
        self._src = src
        self._dst = dst
        path = QPainterPath()
        path.moveTo(src)
        path.lineTo(dst)
        self.setPath(path)
        stroker = QPainterPathStroker()
        stroker.setWidth(_HIT_TOLERANCE * 2)
        self._hit_shape = stroker.createStroke(path)

    def shape(self):
        return getattr(self, "_hit_shape", super().shape())

    def boundingRect(self) -> QRectF:
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

        underlay = QPen(_UNDERLAY_COLOR, _UNDERLAY_W)
        underlay.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(underlay)
        painter.drawLine(line)

        overlay_color = _SELECTED_COLOR if self.isSelected() else _OVERLAY_COLOR
        overlay = QPen(overlay_color, _OVERLAY_W)
        overlay.setCapStyle(Qt.PenCapStyle.FlatCap)
        overlay.setDashPattern([_DASH_PX / _OVERLAY_W, _GAP_PX / _OVERLAY_W])
        painter.setPen(overlay)
        painter.drawLine(line)

        painter.restore()

    def mousePressEvent(self, event) -> None:
        if self._signals is not None:
            self._signals.selected.emit(self._edge.id)
        super().mousePressEvent(event)

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent) -> None:
        menu = QMenu()
        delete_action = menu.addAction("Delete Connection")
        chosen = menu.exec(event.screenPos())
        if chosen is delete_action and self._signals is not None:
            self._signals.deleted.emit(self._edge.id)
