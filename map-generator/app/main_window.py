"""Main application window."""
from __future__ import annotations
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QFileDialog, QMessageBox, QStatusBar, QInputDialog,
)

from renderers.pil_renderer import PilRenderer
from app.region_wizard.wizard_window import RegionWizard
from app.region_workspace import RegionWorkspace
from persistence import RegionRepository, RegionSummary
from core.region_data import RegionData


_DB_FILENAME = "regions.sqlite"


class MainWindow(QMainWindow):
    def __init__(self, db_path: Path | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Salvage Union Map Generator")
        self.resize(1400, 900)

        self._renderer = PilRenderer()
        self._repository = RegionRepository(db_path or Path.cwd() / _DB_FILENAME)
        self._workspace = RegionWorkspace(self._repository)
        self.setCentralWidget(self._workspace)

        self._status = QStatusBar()
        self.setStatusBar(self._status)

        self._build_menu()
        self._apply_stylesheet()
        self._status.showMessage("No region open.")

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction("&New Region Wizard…", self._on_region_wizard, "Ctrl+W")
        file_menu.addAction("&Open Region…", self._on_open_region, "Ctrl+O")
        file_menu.addAction("&Delete Region…", self._on_delete_region)
        file_menu.addSeparator()
        file_menu.addAction("&Export PNG…", self._on_export, "Ctrl+E")
        file_menu.addSeparator()
        file_menu.addAction("&Quit", self.close, "Ctrl+Q")

        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction("&About", self._on_about)

    def _on_region_wizard(self) -> None:
        wizard = RegionWizard(self)
        wizard.region_created.connect(self._on_region_data_ready)
        wizard.exec()

    def _on_region_data_ready(self, region_data: object) -> None:
        if not isinstance(region_data, RegionData):
            return
        try:
            self._repository.save_region(region_data)
            self._workspace.open_region(region_data)
        except Exception as exc:
            QMessageBox.critical(self, "Region Save Error", str(exc))
            return
        self._status.showMessage(f"Opened region: {region_data.name}", 4000)

    def _on_open_region(self) -> None:
        summaries = self._repository.list_regions()
        if not summaries:
            QMessageBox.information(self, "Open Region", "No saved regions yet.")
            return
        labels = [_summary_label(s) for s in summaries]
        choice, ok = QInputDialog.getItem(
            self, "Open Region", "Saved regions:", labels, 0, False,
        )
        if not ok:
            return
        target = summaries[labels.index(choice)]
        region = self._repository.load_region(target.id)
        if region is None:
            QMessageBox.warning(self, "Open Region", "Region could not be loaded.")
            return
        self._workspace.open_region(region)
        self._status.showMessage(f"Opened region: {region.name}", 4000)

    def _on_delete_region(self) -> None:
        summaries = self._repository.list_regions()
        if not summaries:
            QMessageBox.information(self, "Delete Region", "No saved regions.")
            return
        labels = [_summary_label(s) for s in summaries]
        choice, ok = QInputDialog.getItem(
            self, "Delete Region", "Region to delete:", labels, 0, False,
        )
        if not ok:
            return
        target = summaries[labels.index(choice)]
        confirm = QMessageBox.question(
            self, "Delete Region",
            f"Delete '{target.name}' permanently? This cannot be undone.",
        )
        if confirm != QMessageBox.Yes:
            return
        self._repository.delete_region(target.id)
        current = self._workspace.current_region()
        if current is not None and current.id == target.id:
            self._workspace.close_region()
        self._status.showMessage(f"Deleted region: {target.name}", 4000)

    def _on_export(self) -> None:
        graph = self._workspace.current_view_graph()
        if graph is None or not graph.nodes:
            QMessageBox.information(self, "Export", "Open a region first.")
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
            QComboBox, QSpinBox, QLineEdit, QTextEdit, QTextBrowser {
                background: #252220; border: 1px solid #3a3530; padding: 2px 4px; border-radius: 2px;
            }
            QSplitter::handle { background: #3a3530; }
            QTreeWidget, QListWidget { background: #141210; border: 1px solid #3a3530; }
        """)


def _summary_label(s: RegionSummary) -> str:
    return f"{s.name} — {s.terrain_type} · Tech {s.tech_level}"
