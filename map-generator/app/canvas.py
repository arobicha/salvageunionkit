"""Interactive map canvas: QGraphicsScene + QGraphicsView."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QImage, QPixmap, QWheelEvent, QKeyEvent
from PySide6.QtWidgets import (
    QGraphicsScene,
    QGraphicsView,
    QWidget,
)

from core.map_graph import MapGraph
from app.node_item import NodeItem, NodeSignals
from app.edge_item import EdgeItem, EdgeSignals
from app._canvas_background import CanvasBackground

_BG_COLOR = QColor(18, 16, 14)
_DEFAULT_SCENE_SIZE = 800.0


class MapCanvas(QGraphicsView):
    node_selected = Signal(str)      # node_id
    edge_selected = Signal(str)      # edge_id
    graph_mutated = Signal()         # any structural change
    area_activated = Signal(str)     # node_id — double-click on an area node

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(0, 0, _DEFAULT_SCENE_SIZE, _DEFAULT_SCENE_SIZE)
        self._scene.setBackgroundBrush(_BG_COLOR)
        self.setScene(self._scene)
        from PySide6.QtGui import QPainter
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setFocusPolicy(Qt.StrongFocus)

        self._graph: MapGraph | None = None
        self._node_items: dict[str, NodeItem] = {}
        self._edge_items: dict[str, EdgeItem] = {}
        self._node_signals = NodeSignals()
        self._edge_signals = EdgeSignals()
        self._background = CanvasBackground(self._scene)
        self._wire_signals()

    def _wire_signals(self) -> None:
        self._node_signals.moved.connect(self._on_node_moved)
        self._node_signals.type_changed.connect(self._on_type_changed)
        self._node_signals.deleted.connect(self._on_node_deleted)
        self._node_signals.selected.connect(self.node_selected)
        self._edge_signals.selected.connect(self.edge_selected)
        self._edge_signals.deleted.connect(self._on_edge_deleted)

    def load_graph(self, graph: MapGraph) -> None:
        self._scene.clear()
        self._node_items.clear()
        self._edge_items.clear()
        self._graph = graph
        self._background = CanvasBackground(self._scene)
        self._scene.setSceneRect(0, 0, _DEFAULT_SCENE_SIZE, _DEFAULT_SCENE_SIZE)

        sw, sh = self._scene.width(), self._scene.height()
        for edge in graph.edges:
            item = EdgeItem(edge, self._edge_signals)
            self._scene.addItem(item)
            self._edge_items[edge.id] = item

        for idx, node in enumerate(graph.nodes, start=1):
            item = NodeItem(node, idx, self._node_signals)
            item.setPos(node.x * sw, node.y * sh)
            self._scene.addItem(item)
            self._node_items[node.id] = item

        self._refresh_edges()

    def current_graph(self) -> MapGraph | None:
        return self._graph

    def set_background_image(self, pixmap: QPixmap) -> tuple[int, int]:
        dims = self._background.set_pixmap(pixmap)
        self._reposition_nodes()
        self._refresh_edges()
        return dims.native_w, dims.native_h

    def clear_background_image(self) -> None:
        self._background.clear()
        self._reposition_nodes()
        self._refresh_edges()

    def export_to_image(self) -> QImage:
        return self._background.export_image()

    def _reposition_nodes(self) -> None:
        sw, sh = self._scene.width(), self._scene.height()
        for node_id, item in self._node_items.items():
            if self._graph is None:
                continue
            try:
                node = self._graph.node_by_id(node_id)
            except KeyError:
                continue
            item.setPos(node.x * sw, node.y * sh)

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
        rect = self._scene.sceneRect()
        pos = item.scenePos()
        sx = (pos.x() - rect.x()) / rect.width()
        sy = (pos.y() - rect.y()) / rect.height()
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

    def _on_edge_deleted(self, edge_id: str) -> None:
        if self._graph is None:
            return
        item = self._edge_items.pop(edge_id, None)
        if item is None:
            return
        self._scene.removeItem(item)
        self._graph.edges = [e for e in self._graph.edges if e.id != edge_id]
        self.graph_mutated.emit()

    def delete_selected(self) -> None:
        for item in list(self._scene.selectedItems()):
            if isinstance(item, NodeItem):
                self._on_node_deleted(item.node_id)
            elif isinstance(item, EdgeItem):
                self._on_edge_deleted(item.edge_id)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.delete_selected()
            return
        super().keyPressEvent(event)

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
