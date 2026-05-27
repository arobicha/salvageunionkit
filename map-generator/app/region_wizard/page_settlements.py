"""Wizard page 3: define 1-2 settlements."""
from __future__ import annotations
import random

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QGroupBox, QComboBox, QPushButton, QSpinBox,
)

from core.region_data import ThreatDetails, SettlementDetails
from generators._naming import generate_settlement_name

_FEATURE_HINTS = [
    "Built around a massive Mech Reactor",
    "Constructed entirely underground",
    "Sprawling tent city on the edge of an irradiated crater",
    "Fortified trading post, neutral ground",
    "Former corporate facility repurposed by survivors",
    "Built into the hull of a crashed Union Crawler",
]


class SettlementRow(QGroupBox):
    def __init__(self, number: int) -> None:
        super().__init__(f"Settlement {number}")
        self._rng = random.Random()
        vbox = QVBoxLayout(self)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Name:"))
        self._name = QLineEdit()
        name_row.addWidget(self._name, 1)
        suggest = QPushButton("🎲")
        suggest.setFixedWidth(32)
        suggest.setToolTip("Suggest name")
        suggest.clicked.connect(self._suggest_name)
        name_row.addWidget(suggest)
        vbox.addLayout(name_row)

        feat_row = QHBoxLayout()
        feat_row.addWidget(QLabel("Key Feature:"))
        self._feature = QLineEdit()
        self._feature.setPlaceholderText("What makes this settlement stand out?")
        feat_row.addWidget(self._feature, 1)
        suggest_feat = QPushButton("🎲")
        suggest_feat.setFixedWidth(32)
        suggest_feat.clicked.connect(self._suggest_feature)
        feat_row.addWidget(suggest_feat)
        vbox.addLayout(feat_row)

        threat_row = QHBoxLayout()
        threat_row.addWidget(QLabel("Linked Threat:"))
        self._threat_combo = QComboBox()
        self._threat_combo.addItem("None", "")
        threat_row.addWidget(self._threat_combo, 1)
        vbox.addLayout(threat_row)

        self._suggest_name()

    def _suggest_name(self) -> None:
        self._name.setText(generate_settlement_name(self._rng))

    def _suggest_feature(self) -> None:
        self._feature.setText(self._rng.choice(_FEATURE_HINTS))

    def update_threats(self, threats: list[ThreatDetails]) -> None:
        current = self._threat_combo.currentData()
        self._threat_combo.clear()
        self._threat_combo.addItem("None", "")
        for t in threats:
            self._threat_combo.addItem(f"{t.subtype}: {t.name}", t.id)
        idx = self._threat_combo.findData(current)
        if idx >= 0:
            self._threat_combo.setCurrentIndex(idx)

    def get_settlement(self) -> SettlementDetails:
        return SettlementDetails(
            name=self._name.text().strip() or "Settlement",
            feature=self._feature.text().strip(),
            linked_threat_id=self._threat_combo.currentData() or "",
        )


class PageSettlements(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        hint = QLabel(
            "Settlements are where people live. Link them to a threat to tie the region together.\n"
            "Consider: who leads this settlement, and how do they survive?"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #a09890; font-style: italic;")
        layout.addWidget(hint)

        count_row = QHBoxLayout()
        count_row.addWidget(QLabel("Number of Settlements:"))
        self._count = QSpinBox()
        self._count.setRange(1, 2)
        self._count.setValue(2)
        self._count.valueChanged.connect(self._on_count_changed)
        count_row.addWidget(self._count)
        count_row.addStretch()
        layout.addLayout(count_row)

        self._rows = [SettlementRow(i + 1) for i in range(2)]
        for row in self._rows:
            layout.addWidget(row)

        self._on_count_changed(2)

    def _on_count_changed(self, count: int) -> None:
        self._rows[1].setEnabled(count >= 2)
        self._rows[1].setVisible(count >= 2)

    def update_threats(self, threats: list[ThreatDetails]) -> None:
        for row in self._rows:
            row.update_threats(threats)

    def get_settlements(self) -> list[SettlementDetails]:
        count = self._count.value()
        return [self._rows[i].get_settlement() for i in range(count)]
