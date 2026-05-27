"""Main application window."""
from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QSplitter, QFileDialog, QMessageBox, QStatusBar,
    QWidget, QToolBar,
)
from PySide6.QtGui import QAction

from generators.base import GeneratorRegistry
from generators.region_wizard_gen import build_graph as build_region_graph
from renderers.pil_renderer import PilRenderer
from app.canvas import MapCanvas
from app.sidebar import SidebarWidget
from app.region_wizard.wizard_window import RegionWizard
from core.map_graph import MapGraph


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Salvage Union Map Generator")
        self.resize(1200, 800)

        self._canvas = MapCanvas()
        self._sidebar = SidebarWidget()
        self._renderer = PilRenderer()
        self._region_graph: MapGraph | None = None  # saved when drilling into an area

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._canvas)
        splitter.addWidget(self._sidebar)
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)
        self.setCentralWidget(splitter)

        self._status = QStatusBar()
        self.setStatusBar(self._status)

        self._build_back_toolbar()
        self._wire_signals()
        self._build_menu()
        self._apply_stylesheet()

    def _build_back_toolbar(self) -> None:
        self._toolbar = QToolBar("Navigation")
        self._toolbar.setMovable(False)
        self._back_action = QAction("← Back to Region", self)
        self._back_action.triggered.connect(self._on_back_to_region)
        self._toolbar.addAction(self._back_action)
        self.addToolBar(self._toolbar)
        self._toolbar.setVisible(False)

    def _wire_signals(self) -> None:
        self._sidebar.generate_requested.connect(self._on_generate)
        self._sidebar.node_edit_committed.connect(self._on_node_edit)
        self._canvas.node_selected.connect(self._on_node_selected)
        self._canvas.graph_mutated.connect(self._refresh_status)
        self._canvas.area_activated.connect(self._on_area_activated)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction("&New Region Wizard…", self._on_region_wizard, "Ctrl+W")
        file_menu.addAction("&New Empty Map", self._on_new, "Ctrl+N")
        file_menu.addAction("&Export PNG…", self._on_export, "Ctrl+E")
        file_menu.addSeparator()
        file_menu.addAction("&Quit", self.close, "Ctrl+Q")

        edit_menu = self.menuBar().addMenu("&Edit")
        edit_menu.addAction("&Regenerate", self._sidebar._emit_generate, "Ctrl+R")

        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction("&About", self._on_about)

    def _on_region_wizard(self) -> None:
        wizard = RegionWizard(self)
        wizard.region_created.connect(self._on_region_data_ready)
        wizard.exec()

    def _on_region_data_ready(self, region_data: object) -> None:
        try:
            graph = build_region_graph(region_data)
        except Exception as exc:
            QMessageBox.critical(self, "Region Generation Error", str(exc))
            return
        self._region_graph = None
        self._toolbar.setVisible(False)
        self._sidebar.clear_region_context()
        self._canvas.load_graph(graph)
        self._sidebar.clear_node()
        self._refresh_status()

    def _on_area_activated(self, node_id: str) -> None:
        graph = self._canvas.current_graph()
        if graph is None:
            return
        try:
            node = graph.node_by_id(node_id)
        except KeyError:
            return
        region_data = graph.renderer_hints.get("region_data")
        self._region_graph = graph
        self._toolbar.setVisible(True)
        self._sidebar.set_params("point_crawl", {
            "scrap_budget": node.scrap_value,
            "tech_level": graph.tech_level,
            "map_title": node.name,
        })
        self._sidebar.set_region_context(region_data)
        self._sidebar.clear_node()
        self._status.showMessage(
            f"Area: {node.name} — set params and click Generate  |  "
            "← Back to Region to return", 8000
        )

    def _on_back_to_region(self) -> None:
        if self._region_graph is None:
            return
        self._canvas.load_graph(self._region_graph)
        self._region_graph = None
        self._toolbar.setVisible(False)
        self._sidebar.clear_region_context()
        self._sidebar.clear_node()
        self._refresh_status()

    def _on_new(self) -> None:
        self._canvas.load_graph(
            MapGraph(
                title="New Map",
                subtitle="",
                terrain_type="",
                nodes=[],
                edges=[],
                generator_id="",
                generator_params={},
            )
        )
        self._sidebar.clear_node()
        self._refresh_status()

    def _on_generate(self, gen_id: str, params: dict) -> None:
        try:
            gen = GeneratorRegistry.get(gen_id)
            graph = gen.generate(params)
        except Exception as exc:
            QMessageBox.critical(self, "Generation Error", str(exc))
            return
        self._canvas.load_graph(graph)
        self._sidebar.clear_node()
        self._refresh_status()

    def _on_export(self) -> None:
        graph = self._canvas.current_graph()
        if graph is None or not graph.nodes:
            QMessageBox.information(self, "Export", "Generate a map first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PNG", str(Path.home()), "PNG Images (*.png)"
        )
        if not path:
            return
        try:
            image = self._renderer.render(graph, 2048, 2048)
            image.save(path)
            self._status.showMessage(f"Exported to {path}", 4000)
        except Exception as exc:
            QMessageBox.critical(self, "Export Error", str(exc))

    def _on_node_selected(self, node_id: str) -> None:
        graph = self._canvas.current_graph()
        if graph is None:
            return
        try:
            node = graph.node_by_id(node_id)
            self._sidebar.show_node(node)
        except KeyError:
            pass

    def _on_node_edit(
        self,
        node_id: str,
        name: str,
        node_type: str,
        description: str,
        scrap_value: int,
    ) -> None:
        graph = self._canvas.current_graph()
        if graph is None:
            return
        try:
            node = graph.node_by_id(node_id)
        except KeyError:
            return
        node.name = name
        node.type = node_type
        node.description = description
        node.scrap_value = scrap_value
        item = self._canvas._node_items.get(node_id)
        if item:
            item.update_node(node)
        self._refresh_status()

    def _refresh_status(self) -> None:
        graph = self._canvas.current_graph()
        if graph is None:
            self._status.showMessage("No map loaded")
            return
        self._status.showMessage(
            f"{len(graph.nodes)} nodes · {len(graph.edges)} edges · {graph.title}"
        )

    def _on_about(self) -> None:
        QMessageBox.about(
            self,
            "Salvage Union Map Generator",
            "Procedural point crawl generator for Salvage Union campaigns.\n\n"
            "Part of the salvageunionkit project.",
        )

    def _apply_stylesheet(self) -> None:
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #1a1816; color: #d4cfc8; }
            QGroupBox { border: 1px solid #3a3530; border-radius: 4px; margin-top: 6px; }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
            QPushButton { background: #2e2a26; border: 1px solid #4a4540; padding: 4px 10px; border-radius: 3px; }
            QPushButton:hover { background: #3e3a36; }
            QPushButton#generateButton { background: #5a3a1a; border-color: #c8783c; font-weight: bold; }
            QPushButton#generateButton:hover { background: #7a4a20; }
            QComboBox, QSpinBox, QLineEdit, QTextEdit {
                background: #252220; border: 1px solid #3a3530; padding: 2px 4px; border-radius: 2px;
            }
            QSplitter::handle { background: #3a3530; }
        """)
