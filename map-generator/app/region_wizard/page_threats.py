"""Wizard page 2: define 3 regional threats."""
from __future__ import annotations
import random

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QGroupBox, QComboBox, QPushButton, QScrollArea,
)

from core.region_data import ThreatDetails
from generators._naming import generate_threat_name

SUBTYPES = ("Tyrant", "Torment", "Environmental", "Brute", "Aberration")

_DESC_HINTS = {
    "Tyrant":        "Commands forces, holds territory, controls resources.",
    "Torment":       "Disease, deprivation, or suffering afflicting the people.",
    "Environmental": "Radiation storms, acid rain, extreme heat, flooding…",
    "Brute":         "A single powerful foe — mech, Bio-Titan, or mercenary band.",
    "Aberration":    "Weird, grotesque elements — cult, mutated wastelanders, rogue AI.",
}


class ThreatRow(QGroupBox):
    def __init__(self, number: int) -> None:
        super().__init__(f"Threat {number}")
        self._rng = random.Random()
        vbox = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("Type:"))
        self._subtype = QComboBox()
        for s in SUBTYPES:
            self._subtype.addItem(s)
        default = SUBTYPES[(number - 1) % len(SUBTYPES)]
        self._subtype.setCurrentText(default)
        top.addWidget(self._subtype)

        top.addWidget(QLabel("Name:"))
        self._name = QLineEdit()
        top.addWidget(self._name, 1)
        suggest = QPushButton("🎲")
        suggest.setFixedWidth(32)
        suggest.setToolTip("Suggest name")
        suggest.clicked.connect(self._suggest)
        top.addWidget(suggest)
        vbox.addLayout(top)

        desc_row = QHBoxLayout()
        desc_row.addWidget(QLabel("Description:"))
        self._desc = QLineEdit()
        self._desc.setPlaceholderText(_DESC_HINTS.get(default, ""))
        desc_row.addWidget(self._desc, 1)
        vbox.addLayout(desc_row)

        self._subtype.currentTextChanged.connect(self._on_subtype_changed)
        self._suggest()

    def _suggest(self) -> None:
        subtype = self._subtype.currentText()
        self._name.setText(generate_threat_name(subtype, self._rng))

    def _on_subtype_changed(self, subtype: str) -> None:
        self._desc.setPlaceholderText(_DESC_HINTS.get(subtype, ""))
        self._suggest()

    def get_threat(self) -> ThreatDetails:
        return ThreatDetails(
            subtype=self._subtype.currentText(),
            name=self._name.text().strip() or "Unknown Threat",
            description=self._desc.text().strip(),
        )


class PageThreats(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        hint = QLabel(
            "Create 3 threats that define the danger in this region.\n"
            "Each threat links to encounters, areas, and the encounter table."
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

        self._rows = [ThreatRow(i + 1) for i in range(3)]
        for row in self._rows:
            content_layout.addWidget(row)

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def get_threats(self) -> list[ThreatDetails]:
        return [r.get_threat() for r in self._rows]
