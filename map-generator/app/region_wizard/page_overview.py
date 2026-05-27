"""Wizard page 1: region name, core feature, terrain, tech level."""
from __future__ import annotations
import random

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QSpinBox, QPushButton,
)

from generators._naming import generate_settlement_name

_TERRAIN_SUGGESTIONS = [
    "Ashfall Plains", "Irradiated Badlands", "Frozen Wastes",
    "Smog-Choked Industrial Zone", "Flooded Lowlands", "Sand-Scoured Desert",
    "Overgrown Ruins", "Toxic Swamp", "Rocky Highland",
]

_FEATURE_SUGGESTIONS = [
    "A blasted wasteland scoured by radiation storms and roving raiders.",
    "A heavily industrialised zone littered with the carcasses of dead factories.",
    "A frozen expanse where ancient ice hides buried machinery and forgotten dead.",
    "Nomadic scavenger tribes fight over the bones of a collapsed megacity.",
    "Corporate drones enforce order over a resource-rich poisoned landscape.",
]


class PageOverview(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._rng = random.Random()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        layout.addWidget(_section("Region Identity"))

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Region Name:"))
        self._name = QLineEdit()
        self._name.setPlaceholderText("e.g. The Badlands")
        name_row.addWidget(self._name, 1)
        suggest_name = QPushButton("🎲")
        suggest_name.setFixedWidth(32)
        suggest_name.setToolTip("Suggest a name")
        suggest_name.clicked.connect(self._suggest_name)
        name_row.addWidget(suggest_name)
        layout.addLayout(name_row)

        layout.addWidget(QLabel("Core Feature (describe the region's defining character):"))
        self._feature = QTextEdit()
        self._feature.setPlaceholderText("e.g. A hot, sand-filled wasteland full of nomadic scavengers…")
        self._feature.setMaximumHeight(90)
        suggest_feat = QPushButton("🎲 Suggest Feature")
        suggest_feat.clicked.connect(self._suggest_feature)
        layout.addWidget(self._feature)
        layout.addWidget(suggest_feat)

        terrain_row = QHBoxLayout()
        terrain_row.addWidget(QLabel("Terrain Type:"))
        self._terrain = QLineEdit()
        self._terrain.setPlaceholderText("e.g. Ashfall Plains")
        terrain_row.addWidget(self._terrain, 1)
        suggest_terrain = QPushButton("🎲")
        suggest_terrain.setFixedWidth(32)
        suggest_terrain.clicked.connect(self._suggest_terrain)
        terrain_row.addWidget(suggest_terrain)
        layout.addLayout(terrain_row)

        tech_row = QHBoxLayout()
        tech_row.addWidget(QLabel("Tech Level (1 = primitive salvage, 5 = apex technology):"))
        self._tech = QSpinBox()
        self._tech.setRange(1, 5)
        self._tech.setValue(2)
        tech_row.addWidget(self._tech)
        tech_row.addStretch()
        layout.addLayout(tech_row)

        self._suggest_name()
        self._suggest_terrain()

    def _suggest_name(self) -> None:
        self._name.setText(generate_settlement_name(self._rng))

    def _suggest_feature(self) -> None:
        self._feature.setPlainText(self._rng.choice(_FEATURE_SUGGESTIONS))

    def _suggest_terrain(self) -> None:
        self._terrain.setText(self._rng.choice(_TERRAIN_SUGGESTIONS))

    def get_data(self) -> dict:
        return {
            "name": self._name.text().strip() or "The Region",
            "core_feature": self._feature.toPlainText().strip(),
            "terrain_type": self._terrain.text().strip() or "Ashfall Plains",
            "tech_level": self._tech.value(),
        }


def _section(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("font-weight: bold; color: #c8783c; font-size: 13px;")
    return lbl
