"""Widget for a single d20 reference table with a Roll button."""
from __future__ import annotations
from collections import deque

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox, QFrame,
)

from core.reference.models import RollTable, RollBracket
from app.reference._dice import roll_d20

_HISTORY_LEN = 5
_ROW_BASE_STYLE = (
    "padding: 4px 6px; border-left: 3px solid transparent;"
)
_ROW_HIGHLIGHT_STYLE = (
    "padding: 4px 6px; border-left: 3px solid #c8783c;"
    "background: #2a221c; color: #f0d8b8;"
)


def _bracket_label(b: RollBracket) -> str:
    return str(b.min_roll) if b.min_roll == b.max_roll else f"{b.min_roll}-{b.max_roll}"


class RollTableCard(QGroupBox):
    def __init__(self, table: RollTable, parent: QWidget | None = None) -> None:
        super().__init__(table.name, parent)
        self._table = table
        self._history: deque[int] = deque(maxlen=_HISTORY_LEN)
        self._row_frames: list[QFrame] = []

        root = QVBoxLayout(self)
        root.addLayout(self._build_header())

        for bracket in table.brackets:
            frame = self._build_row(bracket)
            self._row_frames.append(frame)
            root.addWidget(frame)

    def name(self) -> str:
        return self._table.name

    def matches(self, query: str) -> bool:
        if not query:
            return True
        q = query.lower()
        if q in self._table.name.lower() or q in self._table.group.lower():
            return True
        return any(q in b.headline.lower() or q in b.body.lower() for b in self._table.brackets)

    def _build_header(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self._last_label = QLabel("—")
        self._last_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #c8783c; min-width: 36px;")
        self._last_label.setAlignment(Qt.AlignCenter)
        roll_btn = QPushButton("🎲 Roll d20")
        roll_btn.setObjectName("generateButton")
        roll_btn.clicked.connect(self._on_roll)
        self._history_label = QLabel("")
        self._history_label.setStyleSheet("color: #a09890; font-size: 11px;")
        row.addWidget(self._last_label)
        row.addWidget(roll_btn)
        row.addWidget(self._history_label, 1)
        return row

    def _build_row(self, bracket: RollBracket) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(_ROW_BASE_STYLE)
        v = QVBoxLayout(frame)
        v.setContentsMargins(4, 2, 4, 2)
        title = QLabel(f"<b>{_bracket_label(bracket)}</b> · {bracket.headline}")
        title.setTextFormat(Qt.RichText)
        body = QLabel(bracket.body)
        body.setWordWrap(True)
        body.setStyleSheet("color: #c8c0b6;")
        v.addWidget(title)
        v.addWidget(body)
        return frame

    def _on_roll(self) -> None:
        result = roll_d20()
        self._history.appendleft(result)
        self._last_label.setText(str(result))
        self._history_label.setText("Recent: " + ", ".join(str(r) for r in list(self._history)[1:]))
        winning = self._table.lookup(result)
        for frame, bracket in zip(self._row_frames, self._table.brackets):
            frame.setStyleSheet(_ROW_HIGHLIGHT_STYLE if bracket is winning else _ROW_BASE_STYLE)
