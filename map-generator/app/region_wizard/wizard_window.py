"""Region creation wizard: multi-step dialog that produces a RegionData."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QProgressBar, QFrame,
)

from core.region_data import RegionData
from app.region_wizard.page_overview import PageOverview
from app.region_wizard.page_threats import PageThreats
from app.region_wizard.page_settlements import PageSettlements
from app.region_wizard.page_areas import PageAreas
from app.region_wizard.page_encounters import PageEncounters
from app.region_wizard.page_review import PageReview

_STEP_TITLES = [
    "1 · Region Identity",
    "2 · Threats",
    "3 · Settlements",
    "4 · Areas",
    "5 · Encounter Table",
    "6 · Review & Generate",
]


class RegionWizard(QDialog):
    region_created = Signal(object)  # emits RegionData

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("New Region — Creation Wizard")
        self.resize(740, 620)
        self.setModal(True)

        self._page_overview = PageOverview()
        self._page_threats = PageThreats()
        self._page_settlements = PageSettlements()
        self._page_areas = PageAreas()
        self._page_encounters = PageEncounters()
        self._page_review = PageReview()

        self._pages = [
            self._page_overview,
            self._page_threats,
            self._page_settlements,
            self._page_areas,
            self._page_encounters,
            self._page_review,
        ]

        root = QVBoxLayout(self)

        # Header
        self._step_label = QLabel()
        self._step_label.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: #c8783c; padding: 4px 0;"
        )
        root.addWidget(self._step_label)

        self._progress = QProgressBar()
        self._progress.setRange(0, len(self._pages) - 1)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(6)
        root.addWidget(self._progress)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #3a3530;")
        root.addWidget(line)

        # Page stack
        self._stack = QStackedWidget()
        for p in self._pages:
            self._stack.addWidget(p)
        root.addWidget(self._stack, 1)

        # Footer buttons
        btn_row = QHBoxLayout()
        self._back_btn = QPushButton("← Back")
        self._next_btn = QPushButton("Next →")
        self._next_btn.setObjectName("generateButton")
        self._finish_btn = QPushButton("⚙ Generate Map")
        self._finish_btn.setObjectName("generateButton")
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        self._back_btn.clicked.connect(self._go_back)
        self._next_btn.clicked.connect(self._go_next)
        self._finish_btn.clicked.connect(self._finish)
        btn_row.addWidget(cancel)
        btn_row.addStretch()
        btn_row.addWidget(self._back_btn)
        btn_row.addWidget(self._next_btn)
        btn_row.addWidget(self._finish_btn)
        root.addLayout(btn_row)

        self._current = 0
        self._refresh()

    def _refresh(self) -> None:
        self._stack.setCurrentIndex(self._current)
        self._step_label.setText(_STEP_TITLES[self._current])
        self._progress.setValue(self._current)
        self._back_btn.setEnabled(self._current > 0)
        is_last = self._current == len(self._pages) - 1
        self._next_btn.setVisible(not is_last)
        self._finish_btn.setVisible(is_last)

    def _go_next(self) -> None:
        threats = self._page_threats.get_threats()
        # Push threat data into pages that need it before they're shown
        if self._current == 1:
            self._page_settlements.update_threats(threats)
        elif self._current == 2:
            self._page_areas.update_threats(threats)
        elif self._current == 3:
            self._page_encounters.setup(threats)
        elif self._current == len(self._pages) - 2:
            self._page_review.populate(self._collect())
        self._current += 1
        self._refresh()

    def _go_back(self) -> None:
        self._current -= 1
        self._refresh()

    def _finish(self) -> None:
        self._page_review.populate(self._collect())
        data = self._collect()
        self.region_created.emit(data)
        self.accept()

    def _collect(self) -> RegionData:
        ov = self._page_overview.get_data()
        return RegionData(
            name=ov["name"],
            core_feature=ov["core_feature"],
            terrain_type=ov["terrain_type"],
            tech_level=ov["tech_level"],
            threats=self._page_threats.get_threats(),
            settlements=self._page_settlements.get_settlements(),
            areas=self._page_areas.get_areas(),
            encounter_table=self._page_encounters.get_entries(),
        )
