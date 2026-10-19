# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt
from qt_db import list_admissions
from date_utils import format_date_jalali


class AdmissionSearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('جستجو پذیرش')
        self.resize(700, 420)
        self.selected_id = None
        v = QVBoxLayout(self)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(['شناسه', 'کد', 'نام', 'تاریخ', 'ساعت'])
        v.addWidget(self.table)
        btns = QHBoxLayout()
        ok = QPushButton('انتخاب')
        ok.clicked.connect(self._choose)
        cancel = QPushButton('انصراف')
        cancel.clicked.connect(self.reject)
        btns.addStretch(1); btns.addWidget(ok); btns.addWidget(cancel)
        v.addLayout(btns)
        self._load()

    def _load(self):
        rows = list_admissions()
        for r, row in enumerate(rows):
            self.table.insertRow(r)
            name = f"{row['first_name'] or ''} {row['last_name'] or ''}".strip()
            date_jalali = format_date_jalali(row['admission_date'] or '')  # تبدیل به شمسی
            vals = [row['id'], row['code'], name, date_jalali, row['admission_time']]
            for c, val in enumerate(vals):
                self.table.setItem(r, c, QTableWidgetItem(str(val)))

    def _choose(self):
        r = self.table.currentRow()
        if r < 0:
            self.reject(); return
        self.selected_id = int(self.table.item(r, 0).text())
        self.accept()


