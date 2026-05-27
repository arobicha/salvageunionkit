"""Widget for a static rules reference section."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox

from core.reference.models import ReferenceSection


class SectionCard(QGroupBox):
    def __init__(self, section: ReferenceSection, parent: QWidget | None = None) -> None:
        title = section.name if not section.page_ref else f"{section.name}  ·  {section.page_ref}"
        super().__init__(title, parent)
        self._section = section

        v = QVBoxLayout(self)
        body = QLabel(section.body)
        body.setWordWrap(True)
        body.setAlignment(Qt.AlignTop)
        body.setStyleSheet("color: #c8c0b6; padding: 2px 4px;")
        v.addWidget(body)

    def name(self) -> str:
        return self._section.name

    def matches(self, query: str) -> bool:
        if not query:
            return True
        q = query.lower()
        return (
            q in self._section.name.lower()
            or q in self._section.group.lower()
            or q in self._section.body.lower()
        )
