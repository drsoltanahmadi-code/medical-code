# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QSpinBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont 
from qt_db import search_services, list_services


class ServicePicker(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('انتخاب خدمت')
        self.resize(900, 500)
        self.persian_font = QFont('Tahoma', 9)
        self._build_ui(); self._load()
        self.selected = None  # (id, code, name, price, count)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self.q = QLineEdit(); self.q.setPlaceholderText('نام/کد خدمت...')
        btn = QPushButton('جستجو'); btn.clicked.connect(self._load)
        top.addWidget(QLabel('جستجو:'))
        top.addWidget(self.q); top.addWidget(btn)
        layout.addLayout(top)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(['شناسه', 'کد', 'نام خدمت', 'قیمت'])
        layout.addWidget(self.table)

        bottom = QHBoxLayout()
        bottom.addWidget(QLabel('تعداد:'))
        self.count = QSpinBox(); self.count.setRange(1, 99); self.count.setValue(1)
        bottom.addWidget(self.count)
        btn_ok = QPushButton('افزودن')
        btn_ok.clicked.connect(self._choose)
        btn_cancel = QPushButton('انصراف'); btn_cancel.clicked.connect(self.reject)
        bottom.addStretch(1)
        bottom.addWidget(btn_ok)
        bottom.addWidget(btn_cancel)
        layout.addLayout(bottom)
    
    def _load(self):
 
        q = self.q.text().strip()
        rows = search_services(q) if q else list_services()

        self.table.setRowCount(0)
        for r, row in enumerate(rows):
       
            self.table.insertRow(r)
        
            # ستون 0: id
            self.table.setItem(r, 0, QTableWidgetItem(str(row.get('id', ''))))
        
            # ستون 1: code (حتماً به str تبدیل کن)
            code_val = row.get('code', '')
            if code_val is None:
                code_val = ''
            elif isinstance(code_val, float):
                code_val = str(int(code_val))  # 701615.0 → "701615"
            else:
                code_val = str(code_val)
            self.table.setItem(r, 1, QTableWidgetItem(code_val))
        
            # ستون 2: name
            name_val = row.get('name', '')
            if name_val is None:
                name_val = ''
            self.table.setItem(r, 2, QTableWidgetItem(str(name_val)))
        
            # ستون 3: price (با فرمت هزارگان)
            price_val = row.get('private_price', 0)
            if price_val is None:
                price_val = 0
            try:
                price_val = int(price_val)
            except:
                price_val = 0
            self.table.setItem(r, 3, QTableWidgetItem(f"{price_val:,}"))

    def _choose(self):
        r = self.table.currentRow()
        if r < 0:
            self.reject()
            return
    
        try:
            # ستون 0: id
            id_item = self.table.item(r, 0)
            if not id_item or not id_item.text().strip():
                self.reject()
                return
            sid = int(str(id_item.text()).strip())
        
            # ستون 1: code (با اولویت code، اگر خالی بود از sid استفاده کن)
            code = str(self.table.item(r, 1).text()).strip()
            if code == 'service_code' or not code:
                code = str(sid)
        
            # ستون 2: name
            name_item = self.table.item(r, 2)
            name = str(name_item.text()).strip() if name_item else ""
        
            # ستون 3: price
            price_item = self.table.item(r, 3)
            price_text = str(price_item.text()).strip() if price_item else "0"
            price_text = price_text.replace(',', '').strip()
            price = int(price_text) if price_text.isdigit() else 0
        
            count = int(self.count.value())
        
            self.selected = (sid, code, name, price, count)
            self.accept()
        
        except Exception as e:
            print(f"❌ خطا در انتخاب خدمت: {e}")
            self.reject()


