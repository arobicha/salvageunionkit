"""Wizard page 6: summary review before generating the map."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit

from core.region_data import RegionData


class PageReview(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        title = QLabel("Review Your Region")
        title.setStyleSheet("font-weight: bold; color: #c8783c; font-size: 14px;")
        layout.addWidget(title)

        hint = QLabel("Review everything below, then click Generate Map.")
        hint.setStyleSheet("color: #a09890; font-style: italic;")
        layout.addWidget(hint)

        self._summary = QTextEdit()
        self._summary.setReadOnly(True)
        self._summary.setStyleSheet("background: #141210; border: 1px solid #3a3530;")
        layout.addWidget(self._summary)

    def populate(self, region: RegionData) -> None:
        lines: list[str] = [
            f"REGION: {region.name}",
            f"Terrain: {region.terrain_type}   Tech Level: {region.tech_level}",
        ]
        if region.core_feature:
            lines += ["", region.core_feature]

        if region.threats:
            lines += ["", "── THREATS ──────────────────────────"]
            for t in region.threats:
                desc = f" — {t.description}" if t.description else ""
                lines.append(f"  [{t.subtype}] {t.name}{desc}")

        if region.settlements:
            lines += ["", "── SETTLEMENTS ──────────────────────"]
            for s in region.settlements:
                feat = f" ({s.feature})" if s.feature else ""
                lines.append(f"  {s.name}{feat}")

        if region.areas:
            lines += ["", "── AREAS ────────────────────────────"]
            for a in region.areas:
                flags = []
                if a.is_salvage:
                    flags.append("Salvage")
                if a.is_starting:
                    flags.append("Start")
                scrap = f" [{a.scrap_budget}sc]" if a.scrap_budget else ""
                tag = f" ({', '.join(flags)})" if flags else ""
                desc = f" — {a.description}" if a.description else ""
                lines.append(f"  {a.name}{scrap}{tag}{desc}")

        if region.encounter_table:
            lines += ["", "── ENCOUNTER TABLE (d6) ─────────────"]
            for e in region.encounter_table:
                lines.append(f"  {e.roll}. {e.description}")

        self._summary.setPlainText("\n".join(lines))
