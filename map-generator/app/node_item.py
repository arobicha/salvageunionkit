"""Qt canvas item representing a single location node."""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal, QObject
from PySide6.QtGui import QBrush, QColor, QPen, QPainter, QFont
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsSceneMouseEvent,
    QMenu,
    QGraphicsSceneContextMenuEvent,
    QStyleOptionGraphicsItem,
    QWidget,
)

from core.node import LocationNode

_TYPE_COLORS: dict[str, QColor] = {
    # Area map
    "entry":         QColor(100, 130, 155),
    "encounter":     QColor(185,  45,  35),
    "environmental": QColor(155, 175,  45),
    "scrap_guarded": QColor(200, 145,  35),
    "scrap_open":    QColor(165, 155, 110),
    "special":       QColor(120,  75, 175),
    # Region map
    "settlement":    QColor(210, 175,  55),
    "threat":        QColor(190,  50,  50),
    "area":          QColor(180, 180, 185),
}

_RADIUS = 18


def _tooltip(node: "LocationNode") -> str:
    parts = [f"<b>{node.name}</b>", node.type]
    if node.description:
        parts.append(node.description)
    if node.scrap_value > 0:
        parts.append(f"Scrap: {node.scrap_value}sc")
    return "<br>".join(parts)


class NodeSignals(QObject):
    moved = Signal(str, float, float)     # node_id, scene_x, scene_y
    type_changed = Signal(str, str)       # node_id, new_type
    deleted = Signal(str)                 # node_id
    selected = Signal(str)               # node_id


class NodeItem(QGraphicsEllipseItem):
    def __init__(self, node: LocationNode, index: int, signals: NodeSignals) -> None:
        super().__init__(-_RADIUS, -_RADIUS, _RADIUS * 2, _RADIUS * 2)
        self._node = node
        self._index = index
        self._signals = signals

        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.setToolTip(_tooltip(node))
        self._apply_color()

    @property
    def node_id(self) -> str:
        return self._node.id

    def update_node(self, node: LocationNode) -> None:
        self._node = node
        self._apply_color()
        self.setToolTip(_tooltip(node))
        self.update()

    def _apply_color(self) -> None:
        color = _TYPE_COLORS.get(self._node.type, _TYPE_COLORS["scrap_open"])
        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor(20, 20, 20), 2))

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        super().paint(painter, option, widget)
        painter.setFont(QFont("DejaVu Sans", 9, QFont.Bold))
        painter.setPen(QPen(QColor(15, 15, 15)))
        painter.drawText(self.boundingRect(), Qt.AlignCenter, str(self._index))

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: object) -> object:
        if change == QGraphicsItem.ItemPositionHasChanged:
            scene = self.scene()
            if scene:
                rect = scene.sceneRect()
                sx = (self.x() - rect.x()) / rect.width()
                sy = (self.y() - rect.y()) / rect.height()
                self._signals.moved.emit(self._node.id, sx, sy)
        return super().itemChange(change, value)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self._signals.selected.emit(self._node.id)
        super().mousePressEvent(event)

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent) -> None:
        _TYPE_LABELS = {
            # Area map
            "entry": "Entry Point",
            "encounter": "Encounter",
            "environmental": "Environmental Hazard",
            "scrap_guarded": "Scrap (Guarded)",
            "scrap_open": "Scrap (Open)",
            "special": "Special",
            # Region map
            "settlement": "Settlement",
            "threat": "Threat",
            "area": "Area",
        }
        menu = QMenu()
        type_menu = menu.addMenu("Change Type")
        for node_type, label in _TYPE_LABELS.items():
            action = type_menu.addAction(label)
            action.setData(node_type)
        menu.addSeparator()
        delete_action = menu.addAction("Delete Node")

        chosen = menu.exec(event.screenPos())
        if chosen is None:
            return
        if chosen == delete_action:
            self._signals.deleted.emit(self._node.id)
        elif chosen.data():
            self._signals.type_changed.emit(self._node.id, chosen.data())
