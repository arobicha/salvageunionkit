"""Side-by-side markdown editor and rendered preview."""
from __future__ import annotations

from PySide6.QtCore import Signal, QTimer
from PySide6.QtWidgets import QWidget, QTextEdit, QTextBrowser, QSplitter, QVBoxLayout

_AUTOSAVE_MS = 600


class NotesEditor(QWidget):
    notes_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._splitter = QSplitter()
        self._source = QTextEdit()
        self._source.setPlaceholderText("# GM Notes\n\nMarkdown supported…")
        self._preview = QTextBrowser()
        self._splitter.addWidget(self._source)
        self._splitter.addWidget(self._preview)
        root.addWidget(self._splitter)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(_AUTOSAVE_MS)
        self._timer.timeout.connect(self._flush)

        self._source.textChanged.connect(self._on_changed)
        self._suppress = False

    def set_notes(self, markdown: str) -> None:
        self._suppress = True
        self._source.setPlainText(markdown)
        self._preview.setMarkdown(markdown)
        self._suppress = False

    def _on_changed(self) -> None:
        if self._suppress:
            return
        self._preview.setMarkdown(self._source.toPlainText())
        self._timer.start()

    def _flush(self) -> None:
        self.notes_changed.emit(self._source.toPlainText())
