"""Sidebar panel: generator controls and node editor."""
from __future__ import annotations
from typing import Any

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSpinBox, QLineEdit, QTextEdit, QPushButton, QGroupBox,
    QFrame, QCheckBox,
)

from generators.base import GeneratorRegistry
from core.node import LocationNode, VALID_TYPES


class SidebarWidget(QWidget):
    generate_requested = Signal(str, dict)   # generator_id, params
    node_edit_committed = Signal(str, str, str, str, int)  # id, name, type, description, scrap_value

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._param_widgets: dict[str, QWidget] = {}
        self._current_node_id: str | None = None

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)

        self._build_generator_section(root)
        root.addWidget(_hline())
        self._build_node_section(root)

    # ── Generator section ────────────────────────────────────────────────────

    def _build_generator_section(self, layout: QVBoxLayout) -> None:
        box = QGroupBox("Generator")
        vbox = QVBoxLayout(box)

        self._gen_combo = QComboBox()
        for gen in GeneratorRegistry.all():
            self._gen_combo.addItem(gen.label, gen.id)
        self._gen_combo.currentIndexChanged.connect(self._on_generator_changed)
        vbox.addWidget(self._gen_combo)

        self._params_area = QWidget()
        self._params_layout = QVBoxLayout(self._params_area)
        self._params_layout.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(self._params_area)

        seed_row = QHBoxLayout()
        seed_row.addWidget(QLabel("Seed"))
        self._seed_spin = QSpinBox()
        self._seed_spin.setRange(0, 999999)
        self._seed_spin.setValue(0)
        self._seed_locked = QCheckBox("Lock")
        self._reroll_btn = QPushButton("Re-roll")
        self._reroll_btn.clicked.connect(self._reroll_seed)
        seed_row.addWidget(self._seed_spin)
        seed_row.addWidget(self._seed_locked)
        seed_row.addWidget(self._reroll_btn)
        vbox.addLayout(seed_row)

        self._gen_btn = QPushButton("Generate")
        self._gen_btn.setObjectName("generateButton")
        self._gen_btn.clicked.connect(self._emit_generate)
        vbox.addWidget(self._gen_btn)

        layout.addWidget(box)
        self._on_generator_changed(0)

    def _on_generator_changed(self, _index: int) -> None:
        gen_id: str = self._gen_combo.currentData()
        gen = GeneratorRegistry.get(gen_id)
        self._rebuild_params(gen.params_schema)

    def _rebuild_params(self, schema: dict[str, Any]) -> None:
        while self._params_layout.count():
            item = self._params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._param_widgets.clear()

        for key, spec in schema.items():
            if key == "seed":
                continue
            label = QLabel(spec.get("label", key))
            widget = _widget_for_spec(spec)
            self._param_widgets[key] = widget
            row = QHBoxLayout()
            row.addWidget(label)
            row.addWidget(widget)
            container = QWidget()
            container.setLayout(row)
            self._params_layout.addWidget(container)

    def _reroll_seed(self) -> None:
        if not self._seed_locked.isChecked():
            import random
            self._seed_spin.setValue(random.randint(0, 999999))

    def _emit_generate(self) -> None:
        gen_id: str = self._gen_combo.currentData()
        params = self._collect_params()
        params["seed"] = self._seed_spin.value()
        self.generate_requested.emit(gen_id, params)

    def _collect_params(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, widget in self._param_widgets.items():
            if isinstance(widget, QSpinBox):
                result[key] = widget.value()
            elif isinstance(widget, QComboBox):
                result[key] = widget.currentText()
            elif isinstance(widget, QLineEdit):
                result[key] = widget.text()
            elif isinstance(widget, QCheckBox):
                result[key] = widget.isChecked()
        return result

    # ── Node editor section ───────────────────────────────────────────────────

    def _build_node_section(self, layout: QVBoxLayout) -> None:
        self._node_box = QGroupBox("Selected Node")
        self._node_box.setEnabled(False)
        vbox = QVBoxLayout(self._node_box)

        vbox.addWidget(QLabel("Name"))
        self._name_edit = QLineEdit()
        vbox.addWidget(self._name_edit)

        vbox.addWidget(QLabel("Type"))
        self._type_combo = QComboBox()
        _TYPE_LABELS = {
            # Area map
            "entry": "Entry Point",
            "encounter": "Encounter",
            "environmental": "Environmental Hazard",
            "scrap_guarded": "Scrap (Guarded)",
            "scrap_open": "Scrap (Open)",
            "special": "Special",
            # Region map
            "settlement": "Settlement",
            "threat": "Threat",
            "area": "Area",
        }
        for t, label in _TYPE_LABELS.items():
            self._type_combo.addItem(label, t)
        vbox.addWidget(self._type_combo)

        vbox.addWidget(QLabel("Description"))
        self._desc_edit = QTextEdit()
        self._desc_edit.setMaximumHeight(80)
        vbox.addWidget(self._desc_edit)

        scrap_row = QHBoxLayout()
        scrap_row.addWidget(QLabel("Scrap Value"))
        self._scrap_spin = QSpinBox()
        self._scrap_spin.setRange(0, 999)
        self._scrap_spin.setSuffix("sc")
        scrap_row.addWidget(self._scrap_spin)
        vbox.addLayout(scrap_row)

        self._apply_btn = QPushButton("Apply Changes")
        self._apply_btn.clicked.connect(self._commit_node_edit)
        vbox.addWidget(self._apply_btn)

        layout.addWidget(self._node_box)

    def show_node(self, node: LocationNode) -> None:
        self._current_node_id = node.id
        self._name_edit.setText(node.name)
        idx = self._type_combo.findData(node.type)
        if idx >= 0:
            self._type_combo.setCurrentIndex(idx)
        self._desc_edit.setPlainText(node.description)
        self._scrap_spin.setValue(node.scrap_value)
        self._node_box.setEnabled(True)

    def clear_node(self) -> None:
        self._current_node_id = None
        self._node_box.setEnabled(False)

    def _commit_node_edit(self) -> None:
        if self._current_node_id is None:
            return
        self.node_edit_committed.emit(
            self._current_node_id,
            self._name_edit.text(),
            self._type_combo.currentData(),
            self._desc_edit.toPlainText(),
            self._scrap_spin.value(),
        )


def _widget_for_spec(spec: dict[str, Any]) -> QWidget:
    kind = spec.get("type", "str")
    if kind == "int":
        w = QSpinBox()
        w.setRange(spec.get("min", 0), spec.get("max", 9999))
        w.setValue(spec.get("default", 0))
        return w
    if kind == "enum":
        w = QComboBox()
        for opt in spec.get("options", []):
            w.addItem(str(opt))
        default = spec.get("default", "")
        idx = w.findText(str(default))
        if idx >= 0:
            w.setCurrentIndex(idx)
        return w
    if kind == "bool":
        w = QCheckBox()
        w.setChecked(bool(spec.get("default", False)))
        return w
    w = QLineEdit()
    w.setText(str(spec.get("default", "")))
    return w


def _hline() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    return line
