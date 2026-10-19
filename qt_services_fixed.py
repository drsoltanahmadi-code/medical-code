# -*- coding: utf-8 -*-
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QComboBox, QSpinBox, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase
from qt_db import list_services, search_services, upsert_service, delete_service, list_groups


class ServicesWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('تعریف خدمات')
        self.resize(1000, 600)

        # تنظیم فونت فارسی
        self._setup_persian_font()
        
        # تنظیم استایل برای نمایش صحیح فارسی
        self.setStyleSheet("""
            * {
                font-family: 'Vazirmatn', 'B Nazanin', 'Tahoma';
                direction: rtl;
            }
            QTableWidget {
                text-align: right;
            }
            QTableWidget::item {
                text-align: right;
                padding: 5px;
            }
            QLineEdit {
                text-align: right;
                padding: 5px;
            }
            QLabel {
                text-align: right;
            }
        """)

        self._build_ui()
        self._load()

    def _setup_persian_font(self):
        """تنظیم فونت فارسی"""
        # بررسی فونت از فایل
        font_path = os.path.join(os.path.dirname(__file__), "fonts", "Vazirmatn-Regular.ttf")
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
                self.persian_font = QFont(font_family, 10)
                self.setFont(self.persian_font)
                return
        
        # فونت های سیستم
        for font_name in ['B Nazanin', 'Tahoma', 'Arial Unicode MS']:
            if QFontDatabase().hasFamily(font_name):
                self.persian_font = QFont(font_name, 10)
                self.setFont(self.persian_font)
                return
        
        # پیشفرض
        self.persian_font = QFont('Arial', 10)
        self.setFont(self.persian_font)

    def _build_ui(self):
        root = QVBoxLayout(self)

        # --- نوار جستجو ---
        top = QHBoxLayout()
        self.q = QLineEdit()
        self.q.setPlaceholderText('نام/کد خدمت...')

        btn = QPushButton('جستجو')
        btn.clicked.connect(self._load)

        top.addWidget(QLabel('جستجو:'))
        top.addWidget(self.q)
        top.addWidget(btn)
        root.addLayout(top)

        # --- جدول خدمات ---
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            'کد خدمت', 'نام خدمت', 'قیمت خصوصی', 'قیمت دولتی',
            'جزء فنی', 'جزء حرفهای', 'سهم بیمه', 'سهم بیمار'
        ])
        self.table.cellClicked.connect(self._pick)
        root.addWidget(self.table)

        # --- فرم پایین برای افزودن/ویرایش ---
        form = QGroupBox('افزودن / ویرایش')
        f = QHBoxLayout()

        self.code = QLineEdit(); self.code.setPlaceholderText('کد')
        self.name = QLineEdit(); self.name.setPlaceholderText('نام خدمت')
        self.group = QComboBox()
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
        """بازخوانی لیست گروهها"""
        self.group.clear()
        self.group.addItem('—', None)
        for g in list_groups(None):
            # تبدیل به dict برای اطمینان
            g = dict(g) if not isinstance(g, dict) else g
            self.group.addItem(g.get('name', ''), g.get('id'))

    def _load(self):
        """بارگذاری لیست خدمات در جدول"""
        q = self.q.text().strip()
        rows = search_services(q) if q else list_services()
        self.table.setRowCount(0)

        for r, row in enumerate(rows):
            # ✅ تبدیل به دیکشنری برای جلوگیری از AttributeError
            if not isinstance(row, dict):
                row = dict(row)

            self.table.insertRow(r)

            # کد خدمت
            item_code = QTableWidgetItem(row.get('code', '') or '')
            self.table.setItem(r, 0, item_code)

            # نام خدمت
            item_name = QTableWidgetItem(row.get('name', '') or '')
            self.table.setItem(r, 1, item_name)

            # قیمت خصوصی
            private_price = row.get('private_price', 0) or row.get('base_price', 0)
            item_private = QTableWidgetItem(f"{private_price:,}")
            self.table.setItem(r, 2, item_private)

            # قیمت دولتی
            govt_price = row.get('govt_price', 0) or row.get('base_price', 0)
            item_govt = QTableWidgetItem(f"{govt_price:,}")
            self.table.setItem(r, 3, item_govt)

            # جزء فنی
            tech_comp = row.get('tech_comp', 0.0) or 0.0
            item_tech = QTableWidgetItem(f"{tech_comp}")
            self.table.setItem(r, 4, item_tech)

            # جزء حرفهای
            prof_comp = row.get('prof_comp', 0.0) or 0.0
            item_prof = QTableWidgetItem(f"{prof_comp}")
            self.table.setItem(r, 5, item_prof)

            # سهم بیمه
            insurance_share = row.get('insurance_share', 0) or 0
            item_insurance = QTableWidgetItem(f"{insurance_share:,}")
            self.table.setItem(r, 6, item_insurance)

            # سهم بیمار
            patient_share = row.get('patient_share', 0) or 0
            item_patient = QTableWidgetItem(f"{patient_share:,}")
            self.table.setItem(r, 7, item_patient)

            # ذخیره id در UserRole
            item_code.setData(Qt.UserRole, row.get('id'))

    def _current_id(self):
        r = self.table.currentRow()
        if r < 0:
            return None
        item = self.table.item(r, 0)
        if item:
            sid = item.data(Qt.UserRole)
            return sid
        return None

    def _pick(self):
        """انتخاب ردیف برای ویرایش"""
        r = self.table.currentRow()
        if r < 0:
            return

        # کد خدمت
        code_item = self.table.item(r, 0)
        if code_item:
            self.code.setText(code_item.text())

        # نام خدمت
        name_item = self.table.item(r, 1)
        if name_item:
            self.name.setText(name_item.text())

        # گروه خدمت
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

        # قیمت پایه
        price_item = self.table.item(r, 2)
        if price_item:
            price_txt = price_item.text().replace(',', '')
            try:
                self.price.setValue(int(float(price_txt)))
            except Exception:
                self.price.setValue(0)

    def _save(self):
        """ذخیره یا ویرایش خدمت"""
        name = self.name.text().strip()
        if not name:
            QMessageBox.warning(self, 'هشدار', 'نام خدمت را وارد کنید')
            return

        upsert_service(
            name=name,
            base_price=int(self.price.value()),
            code=self.code.text().strip(),
            group_id=self.group.currentData(),
            service_id=self._current_id()
        )

        self._load()
        self.code.clear()
        self.name.clear()
        self.group.setCurrentIndex(0)
        self.price.setValue(0)

    def _delete(self):
        """حذف خدمت انتخابشده"""
        sid = self._current_id()
        if sid is None:
            QMessageBox.warning(self, 'هشدار', 'یک ردیف را انتخاب کنید')
            return

        delete_service(sid)
        self._load()