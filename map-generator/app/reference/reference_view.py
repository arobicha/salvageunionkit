"""Composite reference view: search bar + grouped scrollable cards."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QScrollArea,
    QFrame,
)

from core.reference import load_reference_sheet
from core.reference.models import ReferenceSheet
from app.reference.roll_table_card import RollTableCard
from app.reference.section_card import SectionCard


class ReferenceView(QWidget):
    def __init__(
        self,
        sheet: ReferenceSheet | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._sheet = sheet or load_reference_sheet()
        self._cards: list[RollTableCard | SectionCard] = []
        self._group_frames: dict[str, QFrame] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addLayout(self._build_header())
        root.addWidget(self._build_scroll(), 1)

    def _build_header(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(8, 8, 8, 4)
        title = QLabel("GM Reference")
        title.setStyleSheet(
            "font-weight: bold; color: #c8783c; font-size: 14px;"
        )
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search tables and rules…")
        self._search.textChanged.connect(self._apply_filter)
        row.addWidget(title)
        row.addStretch()
        row.addWidget(self._search, 2)
        return row

    def _build_scroll(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        body = QWidget()
        v = QVBoxLayout(body)
        v.setAlignment(Qt.AlignTop)
        v.setContentsMargins(8, 4, 8, 8)

        for group in self._sheet.groups():
            frame = self._build_group(group)
            self._group_frames[group] = frame
            v.addWidget(frame)
        v.addStretch(1)

        scroll.setWidget(body)
        return scroll

    def _build_group(self, group: str) -> QFrame:
        frame = QFrame()
        inner = QVBoxLayout(frame)
        inner.setContentsMargins(0, 6, 0, 6)

        header = QLabel(group)
        header.setStyleSheet(
            "font-weight: bold; color: #c8783c; font-size: 13px;"
            "border-bottom: 1px solid #3a3530; padding: 4px 2px;"
        )
        inner.addWidget(header)

        for table in self._sheet.tables:
            if table.group != group:
                continue
            card = RollTableCard(table)
            self._cards.append(card)
            inner.addWidget(card)

        for section in self._sheet.sections:
            if section.group != group:
                continue
            card = SectionCard(section)
            self._cards.append(card)
            inner.addWidget(card)

        return frame

    def _apply_filter(self, query: str) -> None:
        for card in self._cards:
            card.setVisible(card.matches(query))
        for group, frame in self._group_frames.items():
            visible = any(c.isVisible() for c in self._cards_for_group(group))
            frame.setVisible(visible)

    def _cards_for_group(self, group: str) -> list[RollTableCard | SectionCard]:
        ids = {t.name for t in self._sheet.tables if t.group == group}
        ids |= {s.name for s in self._sheet.sections if s.group == group}
        return [c for c in self._cards if c.name() in ids]
