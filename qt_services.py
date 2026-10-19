# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QComboBox, QSpinBox, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from qt_db import list_services, search_services, upsert_service, delete_service, list_groups


class ServicesWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('تعریف خدمات')
        self.resize(1000, 600)

        self.persian_font = QFont('Tahoma', 9)
        self.persian_font.setStyleHint(QFont.SansSerif)
        self.setFont(self.persian_font)

        self._build_ui()
        self._load()

    def _build_ui(self):
        root = QVBoxLayout(self)

        top = QHBoxLayout()
        self.q = QLineEdit()
        self.q.setPlaceholderText('نام/کد خدمت...')
        self.q.setFont(self.persian_font)

        btn_search = QPushButton('جستجو')
        btn_search.clicked.connect(self._load)
        
        top.addWidget(QLabel('جستجو:'))
        top.addWidget(self.q)
        top.addWidget(btn_search)
        root.addLayout(top)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            'کد خدمت', 'نام خدمت', 'قیمت خصوصی', 'قیمت دولتی',
            'جزء فنی', 'جزء حرفه‌ای', 'سهم بیمه', 'سهم بیمار'
        ])
        self.table.setFont(self.persian_font)
        header = self.table.horizontalHeader()
        header.setFont(self.persian_font)
        self.table.cellClicked.connect(self._pick)
        root.addWidget(self.table)

        form = QGroupBox('افزودن / ویرایش')
        f = QHBoxLayout()

        self.code = QLineEdit(); self.code.setPlaceholderText('کد'); self.code.setFont(self.persian_font)
        self.name = QLineEdit(); self.name.setPlaceholderText('نام خدمت'); self.name.setFont(self.persian_font)
        self.group = QComboBox(); self.group.setFont(self.persian_font)
        self._reload_groups()

        self.price = QSpinBox()
        self.price.setRange(0, 1_000_000_000)
        self.price.setSingleStep(1000)

        btn_save = QPushButton('ذخیره')
        btn_del = QPushButton('حذف')
        btn_save.clicked.connect(self._save)
        btn_del.clicked.connect(self._delete)

        f.addWidget(QLabel('کد:')); f.addWidget(self.code)
        f.addWidget(QLabel('نام:')); f.addWidget(self.name)
        f.addWidget(QLabel('گروه:')); f.addWidget(self.group)
        f.addWidget(QLabel('قیمت پایه:')); f.addWidget(self.price)
        f.addWidget(btn_save); f.addWidget(btn_del)
        form.setLayout(f)
        root.addWidget(form)

    def _reload_groups(self):
        self.group.clear()
        self.group.addItem('—', None)
        for g in list_groups(None):
            g = dict(g) if not isinstance(g, dict) else g
            self.group.addItem(g.get('name', ''), g.get('id'))

    def _load(self):
        q = self.q.text().strip()
        rows = search_services(q) if q else list_services()
        self.table.setRowCount(0)

        for r, row in enumerate(rows):
            if not isinstance(row, dict):
                row = dict(row)

            self.table.insertRow(r)

            # ============================================
            # 🔽 اصلاح code برای float
            # ============================================
            code_val = row.get('code', '')
            if code_val is None:
                code_val = ''
            elif isinstance(code_val, float):
                code_val = str(int(code_val)) if code_val.is_integer() else str(code_val)
            else:
                code_val = str(code_val)
            item_code = QTableWidgetItem(code_val)
            item_code.setFont(self.persian_font)
            self.table.setItem(r, 0, item_code)

            item_name = QTableWidgetItem(str(row.get('name', '') or ''))
            item_name.setFont(self.persian_font)
            self.table.setItem(r, 1, item_name)

            private_price = row.get('private_price', 0) or row.get('base_price', 0)
            if isinstance(private_price, float):
                private_price = int(private_price)
            item_private = QTableWidgetItem(f"{private_price:,}")
            item_private.setFont(self.persian_font)
            self.table.setItem(r, 2, item_private)

            govt_price = row.get('govt_price', 0) or row.get('base_price', 0)
            if isinstance(govt_price, float):
                govt_price = int(govt_price)
            item_govt = QTableWidgetItem(f"{govt_price:,}")
            item_govt.setFont(self.persian_font)
            self.table.setItem(r, 3, item_govt)

            tech_comp = row.get('tech_comp', 0.0) or 0.0
            item_tech = QTableWidgetItem(str(tech_comp))
            item_tech.setFont(self.persian_font)
            self.table.setItem(r, 4, item_tech)

            prof_comp = row.get('prof_comp', 0.0) or 0.0
            item_prof = QTableWidgetItem(str(prof_comp))
            item_prof.setFont(self.persian_font)
            self.table.setItem(r, 5, item_prof)

            insurance_share = row.get('insurance_share', 0) or 0
            if isinstance(insurance_share, float):
                insurance_share = int(insurance_share)
            item_insurance = QTableWidgetItem(f"{insurance_share:,}")
            item_insurance.setFont(self.persian_font)
            self.table.setItem(r, 6, item_insurance)

            patient_share = row.get('patient_share', 0) or 0
            if isinstance(patient_share, float):
                patient_share = int(patient_share)
            item_patient = QTableWidgetItem(f"{patient_share:,}")
            item_patient.setFont(self.persian_font)
            self.table.setItem(r, 7, item_patient)

            item_code.setData(Qt.UserRole, row.get('id'))

    def _current_id(self):
        r = self.table.currentRow()
        if r < 0:
            return None
        item = self.table.item(r, 0)
        if item:
            return item.data(Qt.UserRole)
        return None

    def _pick(self):
        r = self.table.currentRow()
        if r < 0:
            return

        code_item = self.table.item(r, 0)
        if code_item:
            self.code.setText(code_item.text())

        name_item = self.table.item(r, 1)
        if name_item:
            self.name.setText(name_item.text())

        sid = self._current_id()
        if sid:
            rows = list_services()
            for row in rows:
                row = dict(row) if not isinstance(row, dict) else row
                if row.get('id') == sid:
                    group_id = row.get('group_id')
                    if group_id:
                        groups = list_groups(None)
                        for g in groups:
                            g = dict(g) if not isinstance(g, dict) else g
                            if g.get('id') == group_id:
                                idx = self.group.findText(g.get('name', ''))
                                if idx >= 0:
                                    self.group.setCurrentIndex(idx)
                                    break
                    break

        price_item = self.table.item(r, 2)
        if price_item:
            price_txt = price_item.text().replace(',', '')
            try:
                self.price.setValue(int(float(price_txt)))
            except Exception:
                self.price.setValue(0)

    def _save(self):
        name = self.name.text().strip()
        if not name:
            QMessageBox.warning(self, 'هشدار', 'نام خدمت را وارد کنید')
            return

        upsert_service(
            name=name,
            base_price=int(self.price.value()),
            code=self.code.text().strip(),
            group_id=self.group.currentData(),
            service_id=self._current_id(),
        )

        self._load()
        self.code.clear()
        self.name.clear()
        self.group.setCurrentIndex(0)
        self.price.setValue(0)

    def _delete(self):
        sid = self._current_id()
        if sid is None:
            QMessageBox.warning(self, 'هشدار', 'یک ردیف را انتخاب کنید')
            return
        delete_service(sid)
        self._load()