"""Sidebar panel that shows regional threats when editing an area map."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QScrollArea, QFrame,
)

from core.region_data import RegionData, ThreatDetails

_SUBTYPE_COLORS = {
    "Tyrant":        "#d4a030",
    "Torment":       "#a060c0",
    "Environmental": "#70a050",
    "Brute":         "#d05030",
    "Aberration":    "#4090c0",
}


class ThreatChip(QWidget):
    def __init__(self, threat: ThreatDetails) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)

        color = _SUBTYPE_COLORS.get(threat.subtype, "#888")
        header = QLabel(f"<b style='color:{color}'>[{threat.subtype}]</b> {threat.name}")
        header.setTextFormat(Qt.RichText)
        layout.addWidget(header)

        if threat.description:
            desc = QLabel(threat.description)
            desc.setWordWrap(True)
            desc.setStyleSheet("color: #a09890; font-size: 11px;")
            layout.addWidget(desc)

        frame = QFrame(self)
        frame.setStyleSheet(f"border-left: 3px solid {color};")


class RegionContextPanel(QGroupBox):
    """Shows the parent region's threats as GM reference while editing an area."""

    def __init__(self) -> None:
        super().__init__("Region Threats")
        self._layout = QVBoxLayout(self)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.NoFrame)
        self._scroll.setMaximumHeight(240)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setAlignment(Qt.AlignTop)
        self._scroll.setWidget(self._content)
        self._layout.addWidget(self._scroll)

        self._empty_label = QLabel("No region context loaded.")
        self._empty_label.setStyleSheet("color: #6a6560; font-style: italic;")
        self._content_layout.addWidget(self._empty_label)

    def set_region(self, region: RegionData | None) -> None:
        # Clear existing chips
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if region is None or not region.threats:
            self._empty_label = QLabel("No region context loaded.")
            self._empty_label.setStyleSheet("color: #6a6560; font-style: italic;")
            self._content_layout.addWidget(self._empty_label)
            return

        for threat in region.threats:
            chip = ThreatChip(threat)
            chip.setStyleSheet(
                "background: #1e1c1a; border: 1px solid #3a3530; border-radius: 3px;"
            )
            self._content_layout.addWidget(chip)

        budget_lbl = QLabel(
            f"Budget: {sum(a.scrap_budget for a in region.areas)}sc total "
            f"· Tech {region.tech_level}"
        )
        budget_lbl.setStyleSheet("color: #c8783c; font-size: 11px; padding-top: 4px;")
        self._content_layout.addWidget(budget_lbl)
