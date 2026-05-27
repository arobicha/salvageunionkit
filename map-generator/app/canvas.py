"""Interactive map canvas: QGraphicsScene + QGraphicsView."""
from __future__ import annotations

from PySide6.QtCore import Qt, QPointF, Signal
from PySide6.QtGui import QColor, QWheelEvent
from PySide6.QtWidgets import (
    QGraphicsScene,
    QGraphicsView,
    QWidget,
)

from core.map_graph import MapGraph
from core.node import LocationNode
from app.node_item import NodeItem, NodeSignals
from app.edge_item import EdgeItem

_BG_COLOR = QColor(18, 16, 14)
_SCENE_SIZE = 800.0


class MapCanvas(QGraphicsView):
    node_selected = Signal(str)      # node_id
    graph_mutated = Signal()         # any structural change
    area_activated = Signal(str)     # node_id — double-click on an area node

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(0, 0, _SCENE_SIZE, _SCENE_SIZE)
        self._scene.setBackgroundBrush(_BG_COLOR)
        self.setScene(self._scene)
        from PySide6.QtGui import QPainter
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        self._graph: MapGraph | None = None
        self._node_items: dict[str, NodeItem] = {}
        self._edge_items: dict[str, EdgeItem] = {}
        self._signals = NodeSignals()
        self._wire_signals()

    def _wire_signals(self) -> None:
        self._signals.moved.connect(self._on_node_moved)
        self._signals.type_changed.connect(self._on_type_changed)
        self._signals.deleted.connect(self._on_node_deleted)
        self._signals.selected.connect(self.node_selected)

    def load_graph(self, graph: MapGraph) -> None:
        self._scene.clear()
        self._node_items.clear()
        self._edge_items.clear()
        self._graph = graph

        for edge in graph.edges:
            item = EdgeItem(edge)
            self._scene.addItem(item)
            self._edge_items[edge.id] = item

        for idx, node in enumerate(graph.nodes, start=1):
            item = NodeItem(node, idx, self._signals)
            item.setPos(node.x * _SCENE_SIZE, node.y * _SCENE_SIZE)
            self._scene.addItem(item)
            self._node_items[node.id] = item

        self._refresh_edges()

    def current_graph(self) -> MapGraph | None:
        return self._graph

    def _refresh_edges(self) -> None:
        for edge_item in self._edge_items.values():
            src_item = self._node_items.get(edge_item.source_node_id)
            dst_item = self._node_items.get(edge_item.target_node_id)
            if src_item and dst_item:
                edge_item.update_endpoints(src_item.scenePos(), dst_item.scenePos())

    def _on_node_moved(self, node_id: str, _sx: float, _sy: float) -> None:
        if self._graph is None:
            return
        item = self._node_items.get(node_id)
        if item is None:
            return
        pos = item.scenePos()
        sx = pos.x() / _SCENE_SIZE
        sy = pos.y() / _SCENE_SIZE
        for node in self._graph.nodes:
            if node.id == node_id:
                node.x = max(0.0, min(1.0, sx))
                node.y = max(0.0, min(1.0, sy))
                break
        self._refresh_edges()

    def _on_type_changed(self, node_id: str, new_type: str) -> None:
        if self._graph is None:
            return
        for node in self._graph.nodes:
            if node.id == node_id:
                node.type = new_type
                break
        item = self._node_items.get(node_id)
        if item:
            node = self._graph.node_by_id(node_id)
            item.update_node(node)
        self.graph_mutated.emit()

    def _on_node_deleted(self, node_id: str) -> None:
        if self._graph is None:
            return
        self._graph.nodes = [n for n in self._graph.nodes if n.id != node_id]
        edges_to_remove = [
            eid for eid, e in self._edge_items.items()
            if e.source_node_id == node_id or e.target_node_id == node_id
        ]
        for eid in edges_to_remove:
            self._scene.removeItem(self._edge_items.pop(eid))
        self._graph.edges = [
            e for e in self._graph.edges
            if e.source_id != node_id and e.target_id != node_id
        ]
        item = self._node_items.pop(node_id, None)
        if item:
            self._scene.removeItem(item)
        self.graph_mutated.emit()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.RubberBandDrag)
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        for item in self.items(event.pos()):
            if isinstance(item, NodeItem) and item._node.type == "area":
                self.area_activated.emit(item.node_id)
                return
        super().mouseDoubleClickEvent(event)
