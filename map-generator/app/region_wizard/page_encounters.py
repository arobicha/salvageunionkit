"""Wizard page 5: random encounter table (d6)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QFrame,
)

from core.region_data import ThreatDetails, EncounterEntry

_TABLE_SIZE = 6

_GENERIC_ENTRIES = [
    "Wandering salvagers — may trade or turn hostile",
    "Abandoned wreck, partially stripped — signs of recent activity",
    "Signs of a recent battle — shell casings, oil slicks, drag marks",
    "Strange signal on the comms — source unclear",
    "Environmental hazard flare-up",
    "Empty ruins — useful for shelter or ambush",
    "A desperate scavenger begging for help",
    "Patrol from an unknown faction",
]

_THREAT_ENTRY_TEMPLATES = {
    "Tyrant":        "{name} patrol — {count} enforcement units scanning the area",
    "Torment":       "Evidence of the torment: {name} spreading further",
    "Environmental": "Sudden {name} event — take cover or risk damage",
    "Brute":         "{name} spotted moving through the area",
    "Aberration":    "Strange signs of {name} — unsettling but no immediate danger",
}


class EncounterRow(QWidget):
    def __init__(self, roll: int) -> None:
        super().__init__()
        self._roll = roll
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 2, 0, 2)

        lbl = QLabel(f"{roll}.")
        lbl.setFixedWidth(18)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row.addWidget(lbl)

        self._desc = QLineEdit()
        row.addWidget(self._desc, 1)

        self._threat_combo = QComboBox()
        self._threat_combo.setFixedWidth(180)
        self._threat_combo.addItem("None", "")
        row.addWidget(self._threat_combo)

    def update_threats(self, threats: list[ThreatDetails]) -> None:
        current = self._threat_combo.currentData()
        self._threat_combo.clear()
        self._threat_combo.addItem("None", "")
        for t in threats:
            self._threat_combo.addItem(f"{t.subtype}: {t.name}", t.id)
        idx = self._threat_combo.findData(current)
        if idx >= 0:
            self._threat_combo.setCurrentIndex(idx)

    def set_description(self, text: str) -> None:
        self._desc.setText(text)

    def get_entry(self) -> EncounterEntry:
        return EncounterEntry(
            roll=self._roll,
            description=self._desc.text().strip(),
            threat_id=self._threat_combo.currentData() or "",
        )


class PageEncounters(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        hint = QLabel(
            "A d6 encounter table rolled when Pilots travel between points.\n"
            "Auto-populated from your threats — edit freely."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #a09890; font-style: italic;")
        layout.addWidget(hint)

        header = QHBoxLayout()
        header.addWidget(QLabel(""), 0)       # roll #
        header.addWidget(QLabel("Description"), 1)
        header.addWidget(QLabel("Linked Threat"))
        layout.addLayout(header)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #3a3530;")
        layout.addWidget(line)

        self._rows = [EncounterRow(i + 1) for i in range(_TABLE_SIZE)]
        for row in self._rows:
            layout.addWidget(row)

        repop = QPushButton("🎲 Re-populate from Threats")
        repop.clicked.connect(lambda: self.setup(self._last_threats))
        layout.addWidget(repop)

        self._last_threats: list[ThreatDetails] = []

    def setup(self, threats: list[ThreatDetails]) -> None:
        self._last_threats = threats
        for row in self._rows:
            row.update_threats(threats)
        self._auto_populate(threats)

    def _auto_populate(self, threats: list[ThreatDetails]) -> None:
        import random
        rng = random.Random()
        entries: list[str] = []

        for t in threats[:3]:
            template = _THREAT_ENTRY_TEMPLATES.get(t.subtype, "{name} nearby")
            entries.append(template.format(name=t.name, count=rng.randint(2, 5)))

        generics = list(_GENERIC_ENTRIES)
        rng.shuffle(generics)
        while len(entries) < _TABLE_SIZE:
            entries.append(generics.pop(0) if generics else "Empty area")

        threat_ids = [""] * _TABLE_SIZE
        for i, t in enumerate(threats[:3]):
            threat_ids[i] = t.id

        for i, row in enumerate(self._rows):
            row.set_description(entries[i] if i < len(entries) else "")
            # Re-select threat if known
            combo = row._threat_combo
            idx = combo.findData(threat_ids[i])
            if idx >= 0:
                combo.setCurrentIndex(idx)

    def get_entries(self) -> list[EncounterEntry]:
        return [r.get_entry() for r in self._rows if r.get_entry().description]
