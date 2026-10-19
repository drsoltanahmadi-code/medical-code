# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QMessageBox, QTableWidget, QTableWidgetItem, QLineEdit, QSpinBox, QGroupBox,
    QDialog, QTextEdit, QInputDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from qt_db import upsert_service, list_services, search_services, get_conn
import os
import json


class TariffUploadWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('آپلود تعرفه‌ها از PDF')
        self.setLayoutDirection(Qt.RightToLeft)
        self.tariff_data = []
        self.raw_table_data = []
        self.selected_columns = {}
        self.debug_data = []
        self.last_col_indices = {}
        self._build_ui()

    # ============================================================
    # UI
    # ============================================================

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # بخش آپلود
        upload_box = QGroupBox('آپلود فایل PDF تعرفه‌ها')
        upload_layout = QVBoxLayout()

        file_layout = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        self.file_path.setPlaceholderText('مسیر فایل PDF را انتخاب کنید...')
        btn_browse = QPushButton('انتخاب فایل PDF')
        btn_browse.clicked.connect(self._browse_file)
        file_layout.addWidget(QLabel('فایل:'))
        file_layout.addWidget(self.file_path)
        file_layout.addWidget(btn_browse)
        upload_layout.addLayout(file_layout)

        year_layout = QHBoxLayout()
        year_layout.addWidget(QLabel('سال تعرفه:'))
        self.year_spin = QSpinBox()
        self.year_spin.setRange(1390, 1500)
        self.year_spin.setValue(1404)
        year_layout.addWidget(self.year_spin)
        year_layout.addStretch(1)
        upload_layout.addLayout(year_layout)

        btn_read = QPushButton('خواندن PDF و نمایش جدول')
        btn_read.clicked.connect(self._read_pdf)
        upload_layout.addWidget(btn_read)

        btn_upload = QPushButton('بارگذاری مستقیم تعرفه‌ها در دیتابیس')
        btn_upload.clicked.connect(self._upload_tariffs)
        upload_layout.addWidget(btn_upload)

        upload_box.setLayout(upload_layout)
        root.addWidget(upload_box)

        # جدول خام PDF
        preview_box = QGroupBox('جدول PDF (روی هدر کلیک کنید تا ستون را انتخاب کنید)')
        preview_layout = QVBoxLayout()
        self.raw_table = QTableWidget(0, 0)
        self.raw_table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        preview_layout.addWidget(self.raw_table)

        selected_layout = QHBoxLayout()
        selected_layout.addWidget(QLabel('ستون‌های انتخاب شده:'))
        self.selected_cols_label = QLabel('هیچ ستونی انتخاب نشده')
        self.selected_cols_label.setStyleSheet("color: blue; font-weight: bold;")
        selected_layout.addWidget(self.selected_cols_label)
        selected_layout.addStretch(1)
        preview_layout.addLayout(selected_layout)

        preview_box.setLayout(preview_layout)
        root.addWidget(preview_box)

        # جدول پیش‌نمایش نهایی
        final_box = QGroupBox('پیش‌نمایش نهایی (برای ذخیره)')
        final_layout = QVBoxLayout()
        self.preview_table = QTableWidget(0, 8)
        self.preview_table.setHorizontalHeaderLabels([
            'کد خدمت', 'نام خدمت', 'قیمت خصوصی', 'قیمت دولتی',
            'جزء فنی', 'جزء حرفه‌ای', 'سهم بیمه', 'سهم بیمار'
        ])
        final_layout.addWidget(self.preview_table)
        final_box.setLayout(final_layout)
        root.addWidget(final_box)

        # دکمه‌های پایین
        btn_layout = QHBoxLayout()
        btn_save = QPushButton('💾 ذخیره در دیتابیس')
        btn_save.clicked.connect(self._save_to_db)
        btn_save.setStyleSheet("background-color: #10b981; color: white; font-weight: bold; padding: 8px 16px;")
        btn_cancel = QPushButton('❌ انصراف')
        btn_cancel.clicked.connect(self.close)
        btn_layout.addStretch(1)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        root.addLayout(btn_layout)

    # ============================================================
    # توابع اصلی
    # ============================================================

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, 'انتخاب فایل PDF', '', 'PDF Files (*.pdf)')
        if path:
            self.file_path.setText(path)

    def _read_pdf(self):
        pdf_path = self.file_path.text().strip()
        if not pdf_path or not os.path.exists(pdf_path):
            QMessageBox.warning(self, 'خطا', 'فایل PDF معتبر انتخاب کنید.')
            return

        try:
            import pdfplumber
            self.raw_table_data = []

            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        if table and len(table) > 1:
                            self.raw_table_data.append(table)

            if not self.raw_table_data:
                QMessageBox.warning(self, 'خطا', 'جدولی در PDF پیدا نشد.')
                return

            # ترکیب همه جداول
            combined = []
            for table in self.raw_table_data:
                combined.extend(table)

            self.raw_table_data = combined
            self._display_raw_table()

            QMessageBox.information(self, 'موفق',
                f'{len(combined)} ردیف خوانده شد.\n'
                'حالا روی هدر ستون‌ها کلیک کنید و نوع هر ستون را انتخاب کنید.')

        except ImportError:
            QMessageBox.warning(self, 'خطا', 'کتابخانه pdfplumber نصب نیست.\npip install pdfplumber')
        except Exception as e:
            QMessageBox.critical(self, 'خطا', f'خطا در خواندن PDF:\n{str(e)}')

    def _display_raw_table(self):
        if not self.raw_table_data:
            return
        max_cols = max(len(row) for row in self.raw_table_data)
        self.raw_table.setRowCount(len(self.raw_table_data))
        self.raw_table.setColumnCount(max_cols)
        for r, row in enumerate(self.raw_table_data):
            for c in range(max_cols):
                val = str(row[c] or '').strip() if c < len(row) else ''
                self.raw_table.setItem(r, c, QTableWidgetItem(val))
        self.raw_table.setHorizontalHeaderLabels([f'ستون {i}' for i in range(max_cols)])
        self.raw_table.resizeColumnsToContents()

    def _on_header_clicked(self, column):
        options = ['کد خدمت', 'نام خدمت', 'قیمت خصوصی', 'قیمت دولتی',
                    'جزء فنی', 'جزء حرفه‌ای', 'سهم بیمه', 'سهم بیمار', 'لغو']
        choice, ok = QInputDialog.getItem(self, 'انتخاب نوع ستون',
            f'ستون {column} را به عنوان چه چیزی انتخاب می‌کنید؟', options, 0, False)

        if ok and choice != 'لغو':
            field_map = {'کد خدمت': 'code', 'نام خدمت': 'name', 'قیمت خصوصی': 'private',
                         'قیمت دولتی': 'govt', 'جزء فنی': 'tech', 'جزء حرفه‌ای': 'prof',
                         'سهم بیمه': 'insurance', 'سهم بیمار': 'patient'}
            self.selected_columns[field_map[choice]] = column
            self._update_selected_cols_label()
            self._update_preview()

    def _update_selected_cols_label(self):
        names = {'code': 'کد', 'name': 'نام', 'private': 'خصوصی', 'govt': 'دولتی',
                 'tech': 'فنی', 'prof': 'حرفه‌ای', 'insurance': 'بیمه', 'patient': 'بیمار'}
        labels = [f"{names.get(k, k)}: ستون {v}" for k, v in sorted(self.selected_columns.items(), key=lambda x: x[1])]
        self.selected_cols_label.setText(' | '.join(labels) if labels else 'هیچ ستونی انتخاب نشده')
    def _update_preview(self):
        if not self.raw_table_data or 'code' not in self.selected_columns or 'name' not in self.selected_columns:
            return

        self.tariff_data = []
        for row in self.raw_table_data:
            if not row:
                continue
            try:
                # کد - فقط اعداد
                code = str(row[self.selected_columns['code']] or '').strip()
                code = ''.join(c for c in code if c.isdigit())
            
                # نام - برعکس کل متن
                name = str(row[self.selected_columns['name']] or '').strip()
                words = name.split()
                name = ' '.join(w[::-1] for w in words[::-1])
            
                # کد باید حداقل ۴ رقم باشه
                if not code or len(code) < 4 or not name:
                    continue

                def get_val(key):
                    if key in self.selected_columns:
                        col = self.selected_columns[key]
                        if col < len(row):
                            return str(row[col] or '').strip()
                    return '0'

                self.tariff_data.append({
                    'code': code,
                    'name': name,
                    'private_price': self._parse_price(get_val('private')),
                    'govt_price': self._parse_price(get_val('govt')),
                    'tech_comp': self._parse_float(get_val('tech')),
                    'prof_comp': self._parse_float(get_val('prof')),
                    'insurance_share': self._parse_price(get_val('insurance')),
                    'patient_share': self._parse_price(get_val('patient')),
                })
            except:
                continue

        self._show_preview()
    def _show_preview(self):
        self.preview_table.setRowCount(len(self.tariff_data))
        for r, item in enumerate(self.tariff_data):
            vals = [item['code'], item['name'], f"{item['private_price']:,}",
                    f"{item['govt_price']:,}", str(item['tech_comp']), str(item['prof_comp']),
                    f"{item['insurance_share']:,}", f"{item['patient_share']:,}"]
            for c, val in enumerate(vals):
                it = QTableWidgetItem(str(val))
                it.setTextAlignment(Qt.AlignCenter)
                self.preview_table.setItem(r, c, it)

    def _upload_tariffs(self):
        if not self.tariff_data:
            QMessageBox.warning(self, 'خطا', 'ابتدا PDF را بخوانید و ستون‌ها را انتخاب کنید.')
            return
        reply = QMessageBox.question(self, 'تأیید',
            f'{len(self.tariff_data)} تعرفه در دیتابیس ذخیره شود؟', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self._save_to_db()

    def _save_to_db(self):
        if not self.tariff_data:
            QMessageBox.warning(self, 'هشدار', 'هیچ داده‌ای برای ذخیره وجود ندارد.')
            return

        saved, updated = 0, 0
        for item in self.tariff_data:
            try:
                existing = search_services(item['code'])
                if existing:
                    upsert_service(
                        code=item['code'],
                        name=item['name'],
                        base_price=item['private_price'],
                        service_id=existing[0]['id'] if existing else None,
                        private_price=item['private_price'],
                        govt_price=item['govt_price'],
                        tech_comp=item['tech_comp'],
                        prof_comp=item['prof_comp'],
                        insurance_share=item['insurance_share'],
                        patient_share=item['patient_share']
                    )
                    updated += 1
                else:
                    upsert_service(
                        code=item['code'],
                        name=item['name'],
                        base_price=item['private_price'],
                        private_price=item['private_price'],
                        govt_price=item['govt_price'],
                        tech_comp=item['tech_comp'],
                        prof_comp=item['prof_comp'],
                        insurance_share=item['insurance_share'],
                        patient_share=item['patient_share']
                    )
                    saved += 1
            except Exception as e:
                print(f"خطا در ذخیره {item['code']}: {e}")

        QMessageBox.information(self, 'ذخیره شد', f'{saved} خدمت جدید افزوده شد.\n{updated} خدمت به‌روزرسانی شد.')
        self.tariff_data.clear()
        self.preview_table.setRowCount(0)

    # ============================================================
    # توابع کمکی
    # ============================================================

    def _parse_price(self, text):
        if not text:
            return 0
        try:
            return int(float(str(text).replace(',', '').replace(' ', '').strip()))
        except:
            return 0

    def _parse_float(self, text):
        if not text:
            return 0.0
        try:
            return float(str(text).replace(',', '').strip())
        except:
            return 0.0