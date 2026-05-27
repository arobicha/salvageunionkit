"""Read-only list panels for a region's threats, settlements, and areas."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QGroupBox,
)

from core.region_data import RegionData


class EntityLists(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)

        self._threats = self._make_list("Threats")
        self._settlements = self._make_list("Settlements")
        self._areas = self._make_list("Areas")
        for box in (self._threats[0], self._settlements[0], self._areas[0]):
            root.addWidget(box)

    @staticmethod
    def _make_list(title: str) -> tuple[QGroupBox, QListWidget]:
        box = QGroupBox(title)
        layout = QVBoxLayout(box)
        widget = QListWidget()
        layout.addWidget(widget)
        return box, widget

    def populate(self, region: RegionData) -> None:
        self._threats[1].clear()
        for t in region.threats:
            self._threats[1].addItem(QListWidgetItem(f"[{t.subtype}] {t.name or '(unnamed)'}"))
        self._settlements[1].clear()
        for s in region.settlements:
            self._settlements[1].addItem(QListWidgetItem(s.name or "(unnamed)"))
        self._areas[1].clear()
        for a in region.areas:
            flags = []
            if a.is_salvage:
                flags.append("salvage")
            if a.is_starting:
                flags.append("start")
            tag = f" ({', '.join(flags)})" if flags else ""
            self._areas[1].addItem(
                QListWidgetItem(f"{a.name or '(unnamed)'}{tag} — {a.scrap_budget}sc")
            )
