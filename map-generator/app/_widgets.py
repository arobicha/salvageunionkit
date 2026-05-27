"""Reusable Qt widget factory helpers shared across the UI."""
from __future__ import annotations
from typing import Any

from PySide6.QtWidgets import (
    QWidget, QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit,
    QCheckBox, QFrame,
)


def widget_for_spec(spec: dict[str, Any]) -> QWidget:
    """Build a param-editing widget from a generator schema spec entry."""
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
        idx = w.findText(str(spec.get("default", "")))
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


def hline() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    return line
