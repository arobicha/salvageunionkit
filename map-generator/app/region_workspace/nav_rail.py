"""Left navigation rail: Region root + per-area children."""
from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QHBoxLayout, QLabel,
)

from core.region_data import RegionData

_AREA_ID_ROLE = Qt.UserRole + 1
_KIND_ROLE = Qt.UserRole + 2
_KIND_REGION = "region"
_KIND_AREA = "area"


class NavRail(QWidget):
    region_selected = Signal()
    area_selected = Signal(str)        # area_id
    new_area_requested = Signal()
    delete_area_requested = Signal(str)  # area_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMaximumWidth(240)
        self.setMinimumWidth(180)

        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)

        header = QLabel("Workspace")
        header.setStyleSheet("font-weight: bold; color: #c8783c; padding: 2px 4px;")
        root.addWidget(header)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.itemSelectionChanged.connect(self._on_selection)
        root.addWidget(self._tree, 1)

        btn_row = QHBoxLayout()
        self._new_btn = QPushButton("+ Area")
        self._del_btn = QPushButton("− Area")
        self._new_btn.clicked.connect(self.new_area_requested)
        self._del_btn.clicked.connect(self._on_delete_clicked)
        btn_row.addWidget(self._new_btn)
        btn_row.addWidget(self._del_btn)
        root.addLayout(btn_row)

        self._region_item: QTreeWidgetItem | None = None

    def load_region(self, region: RegionData) -> None:
        self._tree.clear()
        root_item = QTreeWidgetItem([region.name or "Region"])
        root_item.setData(0, _KIND_ROLE, _KIND_REGION)
        self._tree.addTopLevelItem(root_item)
        for area in region.areas:
            child = QTreeWidgetItem([area.name or "Area"])
            child.setData(0, _KIND_ROLE, _KIND_AREA)
            child.setData(0, _AREA_ID_ROLE, area.id)
            root_item.addChild(child)
        root_item.setExpanded(True)
        self._region_item = root_item
        self._tree.setCurrentItem(root_item)

    def clear(self) -> None:
        self._tree.clear()
        self._region_item = None

    def _on_selection(self) -> None:
        item = self._tree.currentItem()
        if item is None:
            return
        kind = item.data(0, _KIND_ROLE)
        if kind == _KIND_REGION:
            self.region_selected.emit()
        elif kind == _KIND_AREA:
            self.area_selected.emit(item.data(0, _AREA_ID_ROLE))

    def _on_delete_clicked(self) -> None:
        item = self._tree.currentItem()
        if item is None or item.data(0, _KIND_ROLE) != _KIND_AREA:
            return
        self.delete_area_requested.emit(item.data(0, _AREA_ID_ROLE))
