# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QComboBox, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt
from qt_db import list_groups, upsert_group, delete_group


class GroupsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('تعاریف گروه‌ها')
        self.resize(900, 600)
        self._build_ui()
        self._load()

    def _build_ui(self):
        root = QVBoxLayout(self)

        # سرچ
        search_box = QHBoxLayout()
        self.search = QLineEdit(); self.search.setPlaceholderText('جستجو نام گروه...')
        btn_search = QPushButton('جستجو'); btn_search.clicked.connect(self._load)
        search_box.addWidget(QLabel('جستجو:'))
        search_box.addWidget(self.search)
        search_box.addWidget(btn_search)
        root.addLayout(search_box)

        # جدول
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(['شناسه', 'نام گروه', 'گروه والد'])
        root.addWidget(self.table)

        # فرم پایین
        form = QGroupBox('افزودن/ویرایش')
        f = QHBoxLayout()
        self.name_edit = QLineEdit(); self.name_edit.setPlaceholderText('نام گروه')
        self.parent_combo = QComboBox(); self._reload_parents()
        self.btn_save = QPushButton('ذخیره'); self.btn_save.clicked.connect(self._save)
        self.btn_delete = QPushButton('حذف'); self.btn_delete.clicked.connect(self._delete)
        f.addWidget(QLabel('نام:'))
        f.addWidget(self.name_edit)
        f.addWidget(QLabel('والد:'))
        f.addWidget(self.parent_combo)
        f.addWidget(self.btn_save)
        f.addWidget(self.btn_delete)
        form.setLayout(f)
        root.addWidget(form)

        self.table.cellClicked.connect(self._select_row)

    def _reload_parents(self):
        self.parent_combo.clear()
        self.parent_combo.addItem('— (بدون والد)', None)
        for row in list_groups(None):
            self.parent_combo.addItem(row['name'], row['id'])

    def _load(self):
        q = self.search.text().strip()
        rows = list_groups(None) if not q else []
        if not rows and q:
            from qt_db import search_groups
            rows = search_groups(q)
        self.table.setRowCount(0)
        for r, row in enumerate(rows):
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(row['id'])))
            self.table.setItem(r, 1, QTableWidgetItem(row['name']))
            parent_name = ''
            if row['parent_id']:
                # یافتن والد سطح اول
                for p in list_groups(None):
                    if p['id'] == row['parent_id']:
                        parent_name = p['name']
                        break
            self.table.setItem(r, 2, QTableWidgetItem(parent_name))

    def _current_group_id(self):
        idx = self.table.currentRow()
        if idx < 0:
            return None
        return int(self.table.item(idx, 0).text())

    def _select_row(self):
        gid = self._current_group_id()
        if gid is None:
            return
        self.name_edit.setText(self.table.item(self.table.currentRow(), 1).text())
        parent_name = self.table.item(self.table.currentRow(), 2).text()
        i = self.parent_combo.findText(parent_name) if parent_name else 0
        self.parent_combo.setCurrentIndex(max(i, 0))

    def _save(self):
        name = self.name_edit.text().strip()
        parent_id = self.parent_combo.currentData()
        if not name:
            QMessageBox.warning(self, 'هشدار', 'نام گروه را وارد کنید')
            return
        upsert_group(name, parent_id, self._current_group_id())
        self._reload_parents(); self._load()
        self.name_edit.clear(); self.parent_combo.setCurrentIndex(0)

    def _delete(self):
        gid = self._current_group_id()
        if gid is None:
            QMessageBox.warning(self, 'هشدار', 'یک ردیف را انتخاب کنید')
            return
        delete_group(gid)
        self._reload_parents(); self._load()



