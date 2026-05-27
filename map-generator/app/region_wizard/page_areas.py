"""Wizard page 4: define 5 explorable areas."""
from __future__ import annotations
import random

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QGroupBox, QComboBox, QPushButton, QCheckBox, QScrollArea, QSpinBox,
)

from core.region_data import ThreatDetails, AreaDetails
from generators._naming import generate_area_name
from generators._scrap import area_budget


class AreaRow(QGroupBox):
    def __init__(self, number: int) -> None:
        super().__init__(f"Area {number}")
        self._rng = random.Random()
        vbox = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("Name:"))
        self._name = QLineEdit()
        top.addWidget(self._name, 1)
        suggest = QPushButton("🎲")
        suggest.setFixedWidth(32)
        suggest.setToolTip("Suggest name")
        suggest.clicked.connect(self._suggest_name)
        top.addWidget(suggest)
        top.addWidget(QLabel("Description:"))
        self._desc = QLineEdit()
        self._desc.setPlaceholderText("Short description")
        top.addWidget(self._desc, 2)
        vbox.addLayout(top)

        bottom = QHBoxLayout()
        self._salvage = QCheckBox("Salvage Point")
        self._salvage.setToolTip("Area contains scrap to collect (~15sc per point)")
        self._starting = QCheckBox("Starting Point")
        self._starting.setToolTip("Safe zone for Mech deployment")
        bottom.addWidget(self._salvage)
        bottom.addWidget(self._starting)

        bottom.addWidget(QLabel("Linked Threat:"))
        self._threat_combo = QComboBox()
        self._threat_combo.addItem("None", "")
        bottom.addWidget(self._threat_combo, 1)

        bottom.addWidget(QLabel("Scrap Override:"))
        self._scrap = QSpinBox()
        self._scrap.setRange(0, 500)
        self._scrap.setValue(0)
        self._scrap.setSpecialValueText("Auto")
        self._scrap.setToolTip("0 = auto from tech level")
        bottom.addWidget(self._scrap)
        vbox.addLayout(bottom)

        self._suggest_name()

    def _suggest_name(self) -> None:
        self._name.setText(generate_area_name(self._rng))

    def update_threats(self, threats: list[ThreatDetails]) -> None:
        current = self._threat_combo.currentData()
        self._threat_combo.clear()
        self._threat_combo.addItem("None", "")
        for t in threats:
            self._threat_combo.addItem(f"{t.subtype}: {t.name}", t.id)
        idx = self._threat_combo.findData(current)
        if idx >= 0:
            self._threat_combo.setCurrentIndex(idx)

    def get_area(self) -> AreaDetails:
        return AreaDetails(
            name=self._name.text().strip() or "Area",
            description=self._desc.text().strip(),
            is_salvage=self._salvage.isChecked(),
            is_starting=self._starting.isChecked(),
            linked_threat_id=self._threat_combo.currentData() or "",
            scrap_budget=self._scrap.value(),
        )


class PageAreas(QWidget):
    _DEFAULT_AREA_COUNT = 5

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        hint = QLabel(
            "Areas flesh out the region map. Link areas to threats (lair, territory, evidence).\n"
            "Mark salvage points where scrap can be found, and safe starting zones for Mech deployment."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #a09890; font-style: italic;")
        layout.addWidget(hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setAlignment(Qt.AlignTop)

        self._rows = [AreaRow(i + 1) for i in range(self._DEFAULT_AREA_COUNT)]
        for row in self._rows:
            content_layout.addWidget(row)

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def update_threats(self, threats: list[ThreatDetails]) -> None:
        for row in self._rows:
            row.update_threats(threats)

    def get_areas(self) -> list[AreaDetails]:
        return [r.get_area() for r in self._rows]
