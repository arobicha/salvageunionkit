"""Inspector form for editing the currently-selected point on an area map."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QTextEdit, QSpinBox, QPushButton, QGroupBox,
)

from core.node import LocationNode, VALID_TYPES

_AREA_TYPE_LABELS = {
    "entry": "Entry Point",
    "encounter": "Encounter",
    "environmental": "Environmental Hazard",
    "scrap_guarded": "Scrap (Guarded)",
    "scrap_open": "Scrap (Open)",
    "special": "Special",
}


class PointInspector(QWidget):
    point_committed = Signal(str, str, str, str, int)  # id, name, type, description, scrap_value

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_id: str | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)

        box = QGroupBox("Selected Point")
        self._box = box
        box.setEnabled(False)
        vbox = QVBoxLayout(box)

        vbox.addWidget(QLabel("Name"))
        self._name = QLineEdit()
        vbox.addWidget(self._name)

        vbox.addWidget(QLabel("Type"))
        self._type = QComboBox()
        for t, label in _AREA_TYPE_LABELS.items():
            self._type.addItem(label, t)
        vbox.addWidget(self._type)

        vbox.addWidget(QLabel("Description"))
        self._desc = QTextEdit()
        self._desc.setMaximumHeight(120)
        vbox.addWidget(self._desc)

        scrap_row = QHBoxLayout()
        scrap_row.addWidget(QLabel("Scrap"))
        self._scrap = QSpinBox()
        self._scrap.setRange(0, 999)
        self._scrap.setSuffix("sc")
        scrap_row.addWidget(self._scrap)
        vbox.addLayout(scrap_row)

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self._commit)
        vbox.addWidget(apply_btn)

        root.addWidget(box)
        root.addStretch(1)

    def show_point(self, node: LocationNode) -> None:
        self._current_id = node.id
        self._name.setText(node.name)
        idx = self._type.findData(node.type)
        if idx >= 0:
            self._type.setCurrentIndex(idx)
        self._desc.setPlainText(node.description)
        self._scrap.setValue(node.scrap_value)
        self._box.setEnabled(True)

    def clear(self) -> None:
        self._current_id = None
        self._box.setEnabled(False)

    def _commit(self) -> None:
        if self._current_id is None:
            return
        node_type = self._type.currentData()
        if node_type not in VALID_TYPES:
            return
        self.point_committed.emit(
            self._current_id,
            self._name.text(),
            node_type,
            self._desc.toPlainText(),
            self._scrap.value(),
        )
