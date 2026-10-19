# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QComboBox, QDateEdit, QTimeEdit, QTableWidget, QTableWidgetItem,
    QPushButton, QGroupBox, QSpinBox, QDialog, QMessageBox,QCalendarWidget,QHeaderView
)
from PyQt5.QtCore import Qt, QDate, QTime
from PyQt5.QtGui import QFont, QColor, QIcon
from PyQt5.QtCore import QDate, QTime, Qt
from qt_insurance import load_insurance_percents,load_supp_insurance_percents
from qt_service_picker import ServicePicker
from qt_db import create_admission, admission_code_exists, get_admission_with_items, list_admissions, search_services, list_doctors, get_doctor_by_code, get_doctor_by_id, get_conn
from qt_admission_search import AdmissionSearchDialog
from date_utils import gregorian_to_jalali, parse_jalali_date, get_current_jalali_date
from datetime import datetime
from shamsi_calendar import ShamsiCalendarDialog
import jdatetime 
from qt_db import get_conn
from qt_pacs import send_to_worklist, send_to_orthanc, generate_unique_code, persian_to_english
class AdmissionForm(QWidget):

   def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 16px;
                font-family: Tahoma;
                font-size: 10pt;
                font-weight: bold;
                color: #424242;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
            QLineEdit, QSpinBox, QComboBox {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
                font-family: Tahoma;
                font-size: 10pt;
                color: #212121;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border: 1px solid #1976D2;
            }
            QLineEdit[readOnly="true"] {
                background-color: #fafafa;
                color: #616161;
            }
            QPushButton {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 6px 12px;
                background-color: #fafafa;
                font-family: Tahoma;
                font-size: 9pt;
                color: #424242;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border: 1px solid #bdbdbd;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
            QTableWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                gridline-color: #f0f0f0;
                font-family: Tahoma;
                font-size: 9pt;
                background-color: white;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #212121;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                border: none;
                border-bottom: 2px solid #e0e0e0;
                padding: 6px;
                font-family: Tahoma;
                font-size: 9pt;
                font-weight: bold;
                color: #424242;
            }
            QLabel {
                font-family: Tahoma;
                font-size: 10pt;
                color: #616161;
            }
        """)
        self.persian_font = QFont('Tahoma', 9)
        self.persian_font.setStyleHint(QFont.SansSerif)
        self.conn = get_conn('patients')
        self._percents = load_insurance_percents()
        self._supp_percents = load_supp_insurance_percents()
        self._admission_ids = []
        self._admission_index = -1
        self._build_ui()
        self._load_doctors_combo()
      
   def _build_ui(self):
        if self.layout():
            old_layout = self.layout()
            for i in reversed(range(old_layout.count())):
                old_layout.itemAt(i).widget().setParent(None)
        
        root = QVBoxLayout()
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        root.addWidget(self._build_header())
        root.addWidget(self._build_services_table())
        root.addWidget(self._build_totals())
        root.addLayout(self._build_actions_bar())
       
        self.setLayout(root)

   def _build_header(self):
        box = QGroupBox("اطلاعات پذیرش")
        box.setMaximumHeight(180)
        grid = QGridLayout()
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(4)

        grid.addWidget(QLabel("کد پذیرش"), 0, 0)
        self.code_edit = QLineEdit()
        self.code_edit.setReadOnly(True)
        self.code_edit.setMaximumHeight(28)
        grid.addWidget(self.code_edit, 0, 1)

        grid.addWidget(QLabel("نام بیمه"), 0, 2)
        self.ins_combo = QComboBox()
        self.ins_combo.addItems(["آزاد", "تامین اجتماعی", "خدمات درمانی", "نیروهای مسلح"])
        self.ins_combo.setMaximumHeight(28)
        self.ins_combo.currentTextChanged.connect(self._recalc)
        grid.addWidget(self.ins_combo, 0, 3)

        grid.addWidget(QLabel("بیمه تکمیلی"), 0, 4)
        self.supp_ins_combo = QComboBox()
        supp_insurances = list(self._supp_percents.keys())
        self.supp_ins_combo.addItems(supp_insurances if supp_insurances else ["ندارد", "بیمه تکمیلی نیروهای مسلح", "بیمه تکمیلی تامین اجتماعی", "سایر"])
        self.supp_ins_combo.setMaximumHeight(28)
        self.supp_ins_combo.currentTextChanged.connect(self._on_supp_insurance_changed)
        grid.addWidget(self.supp_ins_combo, 0, 5)

        grid.addWidget(QLabel("نام"), 1, 0)
        self.first_name = QLineEdit()
        self.first_name.setMaximumHeight(30)
        self.first_name.setMinimumWidth(120)
        grid.addWidget(self.first_name, 1, 1)
        
        grid.addWidget(QLabel("نام خانوادگی"), 1, 2)
        self.last_name = QLineEdit()
        self.last_name.setMaximumHeight(30)
        self.last_name.setMinimumWidth(120)
        grid.addWidget(self.last_name, 1, 3)
        
        grid.addWidget(QLabel("کد ملی"), 1, 4)
        self.national_id = QLineEdit()
        self.national_id.setMaximumHeight(30)
        self.national_id.setMinimumWidth(100)
        self.national_id.setFont(QFont("Segoe UI", 10))
        self.national_id.editingFinished.connect(self._search_patient_by_national_id)
        grid.addWidget(self.national_id, 1, 5)

        grid.addWidget(QLabel("تلفن"), 1, 6)
        self.patient_phone = QLineEdit()
        self.patient_phone.setMaximumHeight(30)
        self.patient_phone.setMinimumWidth(100)
        self.patient_phone.setFont(QFont("Segoe UI", 10))
        grid.addWidget(self.patient_phone, 1, 7)

        grid.addWidget(QLabel("سن"), 0, 6)
        self.patient_age = QSpinBox()
        self.patient_age.setRange(0, 150)
        self.patient_age.setValue(0)
        self.patient_age.setMaximumHeight(28)
        self.patient_age.setMaximumWidth(50)
        self.patient_age.setMinimumWidth(70)
        self.patient_age.setFont(QFont("Segoe UI", 10))
        grid.addWidget(self.patient_age, 0, 7)

        grid.addWidget(QLabel("جنسیت"), 0, 8)
        self.patient_gender = QComboBox()
        self.patient_gender.addItems(["", "مرد", "زن"])
        self.patient_gender.setMaximumHeight(28)
        self.patient_gender.setMaximumWidth(50)
        self.patient_gender.setMinimumWidth(70)
        self.patient_gender.setFont(QFont("Segoe UI", 10)) 
        grid.addWidget(self.patient_gender, 0, 9)

        grid.addWidget(QLabel("کد نظام پزشکی"), 2, 5)
        self.doctor_code_input = QLineEdit()
        self.doctor_code_input.setPlaceholderText("کد نظام پزشکی را وارد کنید")
        self.doctor_code_input.setMaximumHeight(30)
        self.doctor_code_input.textChanged.connect(self._on_doctor_code_changed)
        grid.addWidget(self.doctor_code_input, 2, 6)

        grid.addWidget(QLabel("پزشک ارجاع"), 2, 3)
        self.doctor_combo = QComboBox()
        self.doctor_combo.setMinimumWidth(180)
        self.doctor_combo.setMaximumHeight(28)
        self.doctor_combo.currentIndexChanged.connect(self._on_doctor_combo_changed)
        grid.addWidget(self.doctor_combo, 2, 4)

        grid.addWidget(QLabel("تاریخ پذیرش"), 2, 0)
        
        today_shamsi = jdatetime.date.today()
        self.adm_date_text = QLineEdit()
        self.adm_date_text.setText(today_shamsi.strftime("%Y/%m/%d"))
        self.adm_date_text.setReadOnly(True)
        self.adm_date_text.setMaximumHeight(30)

        date_btn = QPushButton("📅")
        date_btn.setMaximumWidth(40)
        date_btn.setMaximumHeight(28)
        date_btn.clicked.connect(self._open_shamsi_calendar)

        layout = QHBoxLayout()
        layout.addWidget(self.adm_date_text)
        layout.addWidget(date_btn)
        layout.setSpacing(6)

        date_widget = QWidget()
        date_widget.setLayout(layout)
        grid.addWidget(date_widget, 2, 1, 1, 2)
        
        box.setLayout(grid) 
        box.setStyleSheet("""
            QLineEdit, QSpinBox, QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px;
                background-color: white;
                font-family: Tahoma;
                font-size: 10pt;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border: 1px solid #3498db;
            }
            QLineEdit[readOnly="true"] {
                background-color: #f5f5f5;
            }
        """)
        return box

   def _build_services_table(self):
        box = QGroupBox("خدمات")
        v = QVBoxLayout()
        v.setContentsMargins(4, 8, 4, 4)
        v.setSpacing(6)
        
        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels([
            "کد خدمت", "نام خدمت", "تعداد", "قیمت خصوصی", "قیمت دولتی",
            "سهم بیمه", "سهم بیمار", "درصد تکمیلی", "سهم تکمیلی", "قابل پرداخت"
        ])
        
        header = self.table.horizontalHeader()
        header.setFont(self.persian_font)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)
        
        self.table.setMaximumHeight(300)
        v.addWidget(self.table)

        buttons = QHBoxLayout()
        buttons.setSpacing(6)
        
        btn_add = QPushButton("➕ افزودن خدمت")
        btn_add.setMaximumHeight(28)
        btn_add.setMinimumHeight(32)
        btn_add.setFont(QFont("Tahoma", 9))
        btn_add.clicked.connect(self._add_service_from_db)
        
        btn_del = QPushButton("🗑️ حذف")
        btn_del.setMaximumHeight(28)
        btn_del.setMinimumHeight(32)
        btn_del.setFont(QFont("Tahoma", 9))
        btn_del.clicked.connect(self._remove_selected)
        
        btn_edit = QPushButton("✏️ ویرایش")
        btn_edit.setMaximumHeight(28)
        btn_edit.setMinimumHeight(32)
        btn_edit.setFont(QFont("Tahoma", 9))
        btn_edit.clicked.connect(self._edit_row)
        
        btn_worklist = QPushButton("📋 ورک لیست")
        btn_worklist.setMaximumHeight(28)
        btn_worklist.setMinimumHeight(32)
        btn_worklist.setFont(QFont("Tahoma", 9))
        btn_worklist.clicked.connect(self._send_to_worklist)

        btn_pacs = QPushButton("🖼️ پکس")
        btn_pacs.setMaximumHeight(28)
        btn_pacs.setMinimumHeight(32)
        btn_pacs.setFont(QFont("Tahoma", 9))
        btn_pacs.clicked.connect(self._send_to_pacs)

        buttons.addWidget(btn_add)
        buttons.addWidget(btn_del)
        buttons.addWidget(btn_edit)
        buttons.addWidget(btn_worklist)
        buttons.addWidget(btn_pacs)
        buttons.addStretch(1)
        v.addLayout(buttons)
        box.setLayout(v)
        return box
    
   def _build_totals(self):
        box = QGroupBox("محاسبات")
        box.setMaximumHeight(150)
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("سهم بیمه اصلی"), 0, 0)
        self.total_ins = QLineEdit()
        self.total_ins.setReadOnly(True)
        self.total_ins.setMaximumHeight(30)
        self.total_ins.setStyleSheet("font-size: 10pt; padding: 4px;")
        grid.addWidget(self.total_ins, 0, 1)

        grid.addWidget(QLabel("درصد بیمه تکمیلی"), 1, 0)
        self.supp_percent = QSpinBox()
        self.supp_percent.setRange(0, 100)
        self.supp_percent.setValue(0)
        self.supp_percent.setMaximumHeight(28)
        self.supp_percent.setMaximumWidth(80)
        self.supp_percent.valueChanged.connect(self._recalc)
        grid.addWidget(self.supp_percent, 1, 1)

        grid.addWidget(QLabel("سهم بیمه تکمیلی"), 2, 0)
        self.total_supp = QLineEdit()
        self.total_supp.setReadOnly(True)
        self.total_supp.setMaximumHeight(32)
        grid.addWidget(self.total_supp, 2, 1)

        grid.addWidget(QLabel("کسورات"), 0, 2)
        self.deductions_btn = QPushButton("💰 مدیریت کسورات")
        self.deductions_btn.setMinimumHeight(35)
        self.deductions_btn.setMinimumWidth(150)
        self.deductions_btn.clicked.connect(self._open_deductions_dialog)
        grid.addWidget(self.deductions_btn, 0, 3)

        grid.addWidget(QLabel("مبلغ کسورات"), 1, 2)
        self.deductions_amount = QLineEdit()
        self.deductions_amount.setReadOnly(True)
        self.deductions_amount.setText("0")
        self.deductions_amount.setMaximumHeight(30)
        self.deductions_amount.setStyleSheet("font-size: 10pt; font-weight: bold; padding: 4px;")
        grid.addWidget(self.deductions_amount, 1, 3)

        grid.addWidget(QLabel("قابل پرداخت نهایی"), 2, 2)
        self.payable = QLineEdit()
        self.payable.setReadOnly(True)
        self.payable.setMaximumHeight(30)
        self.payable.setStyleSheet("font-size: 10pt;  padding: 4px;")
        grid.addWidget(self.payable, 2, 3)

        btn_calc = QPushButton("🧮 محاسبه")
        btn_calc.setMaximumHeight(28)
        btn_calc.clicked.connect(self._recalc)
        grid.addWidget(btn_calc, 0, 4, 3, 1)

        box.setLayout(grid)
        return box

   def _build_actions_bar(self):
        bar = QHBoxLayout()
        bar.setSpacing(6)
        
        buttons = [
            ("⏮️ اولین", self._first),
            ("◀️ قبلی", self._prev),
            ("▶️ بعدی", self._next),
            ("⏭️ آخرین", self._last),
            ("🆕 جدید", self._new_admission),
            ("💾 ذخیره", self._save_stub),
            ("✏️ ویرایش پذیرش", self._edit_admission),  
            ("🗑️ حذف پذیرش", self._delete_admission),
            ("🔍 جستجو", self._search_dialog),
            ("🧮 بروزرسانی", self._recalc),
            ("🖨️ چاپ", self._stub),
            ("❌ خروج", self._exit_stub),
        ]
        
        for text, slot in buttons:
            btn = QPushButton(text)
            btn.setMinimumHeight(32)
            btn.setMinimumWidth(90)
            btn.setFont(QFont("Tahoma", 9))
            btn.clicked.connect(slot)
            bar.addWidget(btn)
            
        bar.addStretch(1)
        return bar

   def _load_doctors_combo(self):
        try:
            from qt_db import list_doctors
            doctors = list_doctors()
            
            self.doctor_combo.clear()
            self.doctor_combo.addItem('-- انتخاب پزشک --', None)
            
            for doctor in doctors:
                doctor_id = doctor.get('id')
                name = doctor.get('name', '')
                family = doctor.get('family', '')
                specialty = doctor.get('specialty', '')
                
                full_name = f"{name} {family}" if name and family else name or family or "نامشخص"
                display_text = f"{full_name} - {specialty or 'تخصص نامشخص'}"
                self.doctor_combo.addItem(display_text, doctor_id)
                
        except Exception as e:
            print(f"❌ خطا در بارگذاری پزشکان: {e}")

   def _open_shamsi_calendar(self):
        try:
            current_text = self.adm_date_text.text().strip()
            from shamsi_calendar import ShamsiCalendarDialog
            calendar_dialog = ShamsiCalendarDialog(self, current_text)
            
            if calendar_dialog.exec_() == QDialog.Accepted:
                selected_date_str = calendar_dialog.get_selected_date_string()
                self.adm_date_text.setText(selected_date_str)
                    
        except Exception as e:
            print(f"❌ خطا در انتخاب تاریخ: {e}")
            QMessageBox.warning(self, "خطا", "خطا در انتخاب تاریخ")

   def _generate_code(self):
        try:
            from qt_db import generate_admission_code
            return generate_admission_code()
        except Exception as e:
            print(f"خطا در تولید کد: {e}")
            return "1001"

   def _on_doctor_combo_changed(self, index):
        if index > 0:
            doctor_id = self.doctor_combo.currentData()
            try:
                from qt_db import get_doctor_by_id
                doctor = get_doctor_by_id(doctor_id)
                if doctor:
                    self.doctor_code_input.setText(doctor.get('code_nezam', ''))
            except:
                pass
        elif index == 0:
            self.doctor_code_input.clear()

   def _on_doctor_code_changed(self, text):
        if not text.strip():
            return
            
        try:
            from qt_db import get_doctor_by_code
            doctor = get_doctor_by_code(text.strip())
            
            if doctor:
                doctor_id = doctor.get('id')
                name = doctor.get('name', '')
                family = doctor.get('family', '')
                specialty = doctor.get('specialty', '')
                full_name = f"{name} {family}"
                
                for i in range(self.doctor_combo.count()):
                    if self.doctor_combo.itemData(i) == doctor_id:
                        self.doctor_combo.setCurrentIndex(i)
                        return
                
                display_text = f"{full_name} - {specialty}"
                self.doctor_combo.addItem(display_text, doctor_id)
                self.doctor_combo.setCurrentIndex(self.doctor_combo.count() - 1)
            else:
                self._search_doctor_by_name(text.strip())
                    
        except Exception as e:
            print(f"❌ خطا در جستجو: {e}")

   def _search_doctor_by_name(self, search_text):
        try:
            from qt_db import search_doctors_by_name
            doctors = search_doctors_by_name(search_text)
            
            if doctors:
                if len(doctors) == 1:
                    doctor = doctors[0]
                    doctor_id = doctor.get('id')
                    name = doctor.get('name', '')
                    family = doctor.get('family', '')
                    specialty = doctor.get('specialty', '')
                    
                    for i in range(self.doctor_combo.count()):
                        if self.doctor_combo.itemData(i) == doctor_id:
                            self.doctor_combo.setCurrentIndex(i)
                            self.doctor_code_input.setText(doctor.get('code_nezam', ''))
                            return
                    
                    display_text = f"{name} {family} - {specialty}"
                    self.doctor_combo.addItem(display_text, doctor_id)
                    self.doctor_combo.setCurrentIndex(self.doctor_combo.count() - 1)
                    self.doctor_code_input.setText(doctor.get('code_nezam', ''))
                    
        except Exception as e:
            print(f"❌ خطا در جستجو با نام: {e}")

   def _on_supp_insurance_changed(self, text):
        if text in self._supp_percents:
            percent = self._supp_percents[text]
            self.supp_percent.setValue(percent)
        self._recalc()

   def _add_service_from_db(self):
        try:
            from tariff_config import get_service_prices
            
            dlg = ServicePicker(self)
            if dlg.exec_() == dlg.Accepted and dlg.selected:
                sid, code, name, price, count = dlg.selected
                 
                if not code or code == str(sid) or code == 'service_code':
                    import re
                    match = re.search(r'\d+', name)
                    if match:
                        code = match.group()
                       
                    else:
                        code = str(sid)
                       
            
                if not code:
                    code = str(sid)
             
                prices = get_service_prices(str(code))
  
                r = self.table.rowCount()
                self.table.insertRow(r)
                    
                for c in range(10):
                    item = QTableWidgetItem("")
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    item.setFont(self.persian_font)
                    self.table.setItem(r, c, item)
                
                self.table.item(r, 0).setText(str(code))
                self.table.item(r, 1).setText(name)
                self.table.item(r, 2).setText(str(count))
                    
                if prices:
                    self.table.item(r, 3).setText(f"{prices['private_price']:,}")
                    self.table.item(r, 4).setText(f"{prices['govt_price']:,}")
                else:
                    self.table.item(r, 3).setText(str(price))
                    self.table.item(r, 4).setText(str(price))
                    
                self.table.item(r, 5).setText("0")
                self.table.item(r, 6).setText("0")
                self.table.item(r, 7).setText("0")
                self.table.item(r, 8).setText("0")
                self.table.item(r, 9).setText("0")
                    
                self._recalc()
        except Exception as e:
            print(f"❌ خطا در افزودن خدمت: {e}")

   def _remove_selected(self):
        try:
            rows = sorted({idx.row() for idx in self.table.selectedIndexes()}, reverse=True)
            for r in rows:
                self.table.removeRow(r)
            self._recalc()
        except Exception as e:
            print(f"❌ خطا در حذف: {e}")

   def _recalc(self):
        try:
            from tariff_config import calculate_insurance
            
            insurance_name = str(self.ins_combo.currentText())
            supp_insurance_name = str(self.supp_ins_combo.currentText())
            supp_percent = self.supp_percent.value()
            
            total_free = 0
            total_public = 0
            total_ins = 0
            total_patient = 0
            total_supp = 0
            total_final = 0
            
            for r in range(self.table.rowCount()):
                try:
                    item = self.table.item(r, 0)
                    if not item:
                        print(f"⚠️ ردیف {r}: آیتم ستون 0 وجود ندارد")
                        continue
            
                    service_code = str(item.text()).strip()
                    if not service_code:
                        print(f"⚠️ ردیف {r}: service_code خالی است")
                        continue
            
                    if service_code in ['id', 'service_code', '']:
                        print(f"⚠️ ردیف {r}: service_code معتبر نیست ('{service_code}')")
                        continue
                    count_text = self.table.item(r, 2).text().strip() if self.table.item(r, 2) else "0"
                    if not count_text.isdigit():
                        count_text = "1"
                    count = int(count_text)
                    
                    if not service_code:
                        continue
                    result = calculate_insurance(service_code, count, insurance_name, supp_insurance_name, supp_percent)
                  
                    if not result:
                        continue
                    
                    self.table.item(r, 3).setText(f"{result['private_price']:,}")
                    self.table.item(r, 4).setText(f"{result['govt_price']:,}")
                    self.table.item(r, 5).setText(f"{result['insurance_share']:,}")
                    self.table.item(r, 7).setText(f"{supp_percent}%")
                    self.table.item(r, 6).setText(f"{result['patient_share']:,}")
                    self.table.item(r, 8).setText(f"{result['supp_share']:,}")
                    self.table.item(r, 9).setText(f"{result['final_payable']:,}")
                    
                    total_free += result['private_price']
                    total_public += result['govt_price']
                    total_ins += result['insurance_share']
                    total_patient += result['patient_share']
                    total_supp += result['supp_share']
                    total_final += result['final_payable']
                    
                except Exception as e:
                    print(f"خطا در ردیف {r}: {e}")
                    continue
            
            # این قسمت رو پیدا کن (حدود خط ۴۳۲-۴۳۴):
            deductions = int(self.deductions_amount.text().replace(',', '') or '0')
            final_payable = max(total_final - deductions, 0)

            # با این جایگزین کن:
            deductions_text = self.deductions_amount.text().replace(',', '').strip()
            if deductions_text.startswith('+'):
                deductions = int(deductions_text.replace('+', '') or '0')
                final_payable = total_final + deductions  # اضافه به فاکتور
            elif deductions_text.startswith('-'):
                deductions = int(deductions_text.replace('-', '') or '0')
                final_payable = max(total_final - deductions, 0)  # کسر از فاکتور
            else:
                deductions = int(deductions_text or '0')
                final_payable = max(total_final - deductions, 0)  # حالت پیش‌فرض: کسر
            
            self.payable.setText(f"{final_payable:,}")
            self.total_ins.setText(f"{total_ins:,}")
            self.total_supp.setText(f"{total_supp:,}")
            
        except Exception as e:
            print(f"❌ خطا در محاسبات: {e}")

   def _new_admission(self):
        try:
            self.table.setRowCount(0)
            self.first_name.clear()
            self.last_name.clear()
            self.national_id.clear()
            self.patient_age.setValue(0)
            self.patient_gender.setCurrentIndex(0)
            self.doctor_code_input.clear()
            self.doctor_combo.setCurrentIndex(0)
            self.total_ins.clear()
            self.total_supp.clear()
            self.payable.clear()
            self.deductions_amount.setText("0")
            self.code_edit.clear()
            self.patient_phone.clear()
            today_jalali = get_current_jalali_date()
            parsed = parse_jalali_date(today_jalali)
            if parsed:
                gyear, gmonth, gday = parsed
        except Exception as e:
            print(f"❌ خطا در ایجاد پذیرش جدید: {e}")
   def _edit_admission(self):
        try:
            code = self.code_edit.text().strip()
            if not code:
                QMessageBox.warning(self, 'هشدار', 'ابتدا یک پذیرش را بارگذاری کنید.')
                return
        
            # جستجوی پذیرش با کد
            conn = self.conn
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM admissions WHERE code = ?", (code,))
            result = cursor.fetchone()
        
            if result:
                adm_id = result[0]
                # فعال کردن فیلدها برای ویرایش
                self.first_name.setReadOnly(False)
                self.last_name.setReadOnly(False)
                self.national_id.setReadOnly(False)
                self.patient_phone.setReadOnly(False)
                self.ins_combo.setEnabled(True)
                self.supp_ins_combo.setEnabled(True)
                self.doctor_combo.setEnabled(True)
                self.doctor_code_input.setReadOnly(False)
                self.patient_age.setEnabled(True)
                self.patient_gender.setEnabled(True)
            
                QMessageBox.information(self, 'ویرایش', 'فیلدها فعال شدند. پس از ویرایش، دکمه ذخیره را بزنید.')
            else:
                QMessageBox.warning(self, 'هشدار', 'پذیرشی با این کد یافت نشد.')
        except Exception as e:
            QMessageBox.critical(self, 'خطا', f'خطا در ویرایش: {str(e)}')

   def _delete_admission(self):
        try:
            code = self.code_edit.text().strip()
            if not code:
                QMessageBox.warning(self, 'هشدار', 'ابتدا یک پذیرش را بارگذاری کنید.')
                return
        
            reply = QMessageBox.question(
                self, 
                'تأیید حذف', 
                f'آیا از حذف پذیرش با کد {code} اطمینان دارید؟',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
        
            if reply == QMessageBox.Yes:
                conn = self.conn
                cursor = conn.cursor()
            
                # حذف آیتم‌های پذیرش
                cursor.execute("""
                    DELETE FROM admission_items 
                    WHERE admission_id IN (
                        SELECT id FROM admissions WHERE code = ?
                    )
                """, (code,))
            
                # حذف خود پذیرش
                cursor.execute("DELETE FROM admissions WHERE code = ?", (code,))
                conn.commit()
            
                # پاک کردن فرم
                self._new_admission()
                self._refresh_admission_ids()
            
                QMessageBox.information(self, 'موفق', f'پذیرش با کد {code} حذف شد.')
        except Exception as e:
            QMessageBox.critical(self, 'خطا', f'خطا در حذف: {str(e)}')
   def _search_patient_by_national_id(self):
        try:
            national_id = self.national_id.text().strip()
            if not national_id or len(national_id) < 10:
                return
        
            conn = self.conn
            cursor = conn.cursor()
            cursor.execute("""
                SELECT first_name, last_name, patient_age, patient_gender, 
                       patient_phone, insurance_name, supp_insurance_name
                FROM admissions 
                WHERE national_id = ? 
                ORDER BY id DESC 
                LIMIT 1
            """, (national_id,))
        
            result = cursor.fetchone()
        
            if result:
                # پر کردن فیلدها با اطلاعات قبلی
                self.first_name.setText(str(result['first_name'] or ''))
                self.last_name.setText(str(result['last_name'] or ''))
            
                age = result['patient_age']
                if age:
                    self.patient_age.setValue(int(age))
            
                gender = str(result['patient_gender'] or '')
                idx = self.patient_gender.findText(gender)
                if idx >= 0:
                    self.patient_gender.setCurrentIndex(idx)
            
                phone = str(result['patient_phone'] or '')
                self.patient_phone.setText(phone)
            
                # بیمه اصلی
                insurance = str(result['insurance_name'] or '')
                idx = self.ins_combo.findText(insurance)
                if idx >= 0:
                    self.ins_combo.setCurrentIndex(idx)
            
                # بیمه تکمیلی
                supp_insurance = str(result['supp_insurance_name'] or '')
                idx = self.supp_ins_combo.findText(supp_insurance)
                if idx >= 0:
                    self.supp_ins_combo.setCurrentIndex(idx)
            
                return True
            return False
        except Exception as e:
            print(f"خطا در جستجوی بیمار: {e}")
            return False
   def _send_to_worklist(self):
        try:
            code = self.code_edit.text().strip()
            if not code:
                QMessageBox.warning(self, 'هشدار', 'ابتدا پذیرش را ذخیره کنید.')
                return
        
            menu = QDialog(self)
            menu.setWindowTitle("انتخاب نوع ورک لیست")
            menu.setLayoutDirection(Qt.RightToLeft)
            menu.setFixedSize(300, 200)
        
            layout = QVBoxLayout()
            layout.addWidget(QLabel("نوع ورک لیست را انتخاب کنید:"))
        
            btn_sono = QPushButton("🔊 سونوگرافی")
            btn_sono.setMinimumHeight(40)
            btn_sono.clicked.connect(lambda: self._process_worklist(menu, code, 'SON'))
        
            btn_radio = QPushButton("☢️ رادیولوژی")
            btn_radio.setMinimumHeight(40)
            btn_radio.clicked.connect(lambda: self._process_worklist(menu, code, 'RAD'))
        
            btn_dental = QPushButton("🦷 دندان")
            btn_dental.setMinimumHeight(40)
            btn_dental.clicked.connect(lambda: self._process_worklist(menu, code, 'DENTAL'))
        
            layout.addWidget(btn_sono)
            layout.addWidget(btn_radio)
            layout.addWidget(btn_dental)
        
            menu.setLayout(layout)
            menu.exec_()
        
        except Exception as e:
            QMessageBox.critical(self, 'خطا', f'خطا: {str(e)}')

   def _process_worklist(self, dialog, admission_code, modality):
        try:
            first_name = self.first_name.text().strip()
            last_name = self.last_name.text().strip()
            national_id = self.national_id.text().strip()
            patient_phone = self.patient_phone.text().strip()
        
            full_name_fa = f"{first_name} {last_name}"
            patient_name_en = persian_to_english(full_name_fa)
        
            confirm_dialog = QDialog(self)
            confirm_dialog.setWindowTitle("تأیید نام انگلیسی")
            confirm_dialog.setLayoutDirection(Qt.RightToLeft)
            confirm_dialog.setFixedSize(400, 200)
        
            layout = QVBoxLayout()
            layout.addWidget(QLabel("نام فارسی:"))
            lbl_fa = QLabel(full_name_fa)
            lbl_fa.setStyleSheet("font-weight: bold; font-size: 11pt;")
            layout.addWidget(lbl_fa)
        
            layout.addWidget(QLabel("نام انگلیسی (قابل ویرایش):"))
            txt_en = QLineEdit(patient_name_en)
            txt_en.setFont(QFont("Segoe UI", 10))
            txt_en.setMinimumHeight(30)
            layout.addWidget(txt_en)
        
            btn_layout = QHBoxLayout()
            btn_ok = QPushButton("✅ تأیید و ارسال")
            btn_ok.setMinimumHeight(32)
            btn_ok.clicked.connect(lambda: self._send_to_worklist_confirm(
                confirm_dialog, dialog, admission_code, modality,
                full_name_fa, txt_en.text().strip(), national_id, patient_phone
            ))
            btn_cancel = QPushButton("❌ انصراف")
            btn_cancel.setMinimumHeight(32)
            btn_cancel.clicked.connect(confirm_dialog.reject)
            btn_layout.addWidget(btn_ok)
            btn_layout.addWidget(btn_cancel)
            layout.addLayout(btn_layout)
        
            confirm_dialog.setLayout(layout)
            confirm_dialog.exec_()
        
        except Exception as e:
            QMessageBox.critical(self, 'خطا', f'خطا: {str(e)}')

   def _send_to_pacs(self):
        try:
            code = self.code_edit.text().strip()
            if not code:
                QMessageBox.warning(self, 'هشدار', 'ابتدا پذیرش را ذخیره کنید.')
                return
        
            first_name = self.first_name.text().strip()
            last_name = self.last_name.text().strip()
            national_id = self.national_id.text().strip()
            patient_phone = self.patient_phone.text().strip()
        
            full_name_fa = f"{first_name} {last_name}"
            patient_name_en = persian_to_english(full_name_fa)
            accession_number = generate_unique_code()
        
            study_id = send_to_orthanc(full_name_fa, patient_name_en, national_id, patient_phone, accession_number)
        
            if study_id:
                QMessageBox.information(self, 'موفق', f'پذیرش {code} به پکس ارسال شد.\nStudy ID: {study_id}')
            else:
                QMessageBox.warning(self, 'خطا', 'ارسال به پکس با مشکل مواجه شد.')
        
        except Exception as e:
            QMessageBox.critical(self, 'خطا', f'خطا: {str(e)}')
   def _send_to_worklist_confirm(self, confirm_dialog, parent_dialog, admission_code, modality, full_name_fa, patient_name_en, national_id, patient_phone):
        try:
            accession_number = generate_unique_code(modality)
            results = send_to_worklist(patient_name_en, national_id, accession_number, patient_phone, modality)
        
            conn = self.conn
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patient_english_names (
                    national_id TEXT PRIMARY KEY,
                    full_name_fa TEXT,
                    full_name_en TEXT,
                    updated_at TEXT
                )
            ''')
            now = datetime.now()
            cursor.execute('''
                INSERT OR REPLACE INTO patient_english_names (national_id, full_name_fa, full_name_en, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (national_id, full_name_fa, patient_name_en, now.strftime("%Y/%m/%d %H:%M:%S")))
            conn.commit()
        
            confirm_dialog.accept()
            parent_dialog.accept()
            QMessageBox.information(self, 'موفق', f'پذیرش {admission_code} به ورک لیست ارسال شد.\nکد: {accession_number}')
        
        except Exception as e:
            QMessageBox.critical(self, 'خطا', f'خطا: {str(e)}')
   def _save_stub(self):
        try:
            code = self.code_edit.text().strip() or self._generate_code()
            items = []
            
            def to_int(text: str) -> int:
                try:
                    return int(str(text).replace(',', '').strip() or '0')
                except:
                    return 0
            
            if self.table.rowCount() == 0:
                QMessageBox.warning(self, 'هشدار', 'هیچ خدمتی در لیست نیست.')
                return
            
            for r in range(self.table.rowCount()):
                try:
                    service_code_item = self.table.item(r, 0)
                    service_name_item = self.table.item(r, 1)
                    count_item = self.table.item(r, 2)
                    price_item = self.table.item(r, 3)
                    
                    if not service_code_item or not service_name_item:
                        continue
                    
                    service_code = service_code_item.text().strip()
                    service_name = service_name_item.text().strip()
                    
                    if not service_code or service_code in ['service_code', 'id']:
                        # اگر کد معتبر نبود، از name استخراج کن
                        import re
                        match = re.search(r'\d+', service_name)
                        if match:
                            service_code = match.group()
                        
                        else:
                            continue
                    
                    count = 1
                    price = 0
                    if count_item and count_item.text().strip():
                        count = to_int(count_item.text())
                    if price_item and price_item.text().strip():
                        price_text = price_item.text().replace(',', '').strip()
                        price = to_int(price_text) if price_text else 0
                    
                    if price == 0:
                        continue
                    
                    if count == 0:
                        count = 1
                    
                    base_percent = int(self._percents.get(self.ins_combo.currentText(), 0))
                    supp_percent = int(self.supp_percent.value())
                    
                    total_price = count * price
                    base_share = (total_price * base_percent) // 100
                    patient_share = total_price - base_share
                    supp_share = (patient_share * supp_percent) // 100
                    payable = patient_share - supp_share
                    
                    items.append({
                        'code': service_code,
                        'name': service_name,
                        'count': count,
                        'price': price,
                        'total': total_price,
                        'base_percent': base_percent,
                        'base_share': base_share,
                        'patient_share': patient_share,
                        'payable': payable,
                        'supp_percent': supp_percent,
                        'supp_share': supp_share,
                    })
                    
                except Exception as e:
                    print(f"خطا در ذخیره ردیف {r}: {e}")
                    continue
            
            if not items:
                QMessageBox.warning(self, 'هشدار', 'هیچ خدمت معتبری در لیست نیست.')
                return
            
            tries = 0
            while admission_code_exists(code):
                code = self._generate_code()
                tries += 1
                if tries > 3:
                    QMessageBox.warning(self, 'هشدار', 'امکان تولید کد غیرتکراری وجود ندارد.')
                    return
            
            try:
                admission_date = self.adm_date_text.text().strip()
                admission_time = QTime.currentTime().toString("HH:mm")
                
                doctor_id = self.doctor_combo.currentData()
                if not doctor_id:
                    QMessageBox.warning(self, 'هشدار', 'لطفا پزشک را انتخاب کنید.')
                    return
                
                first_name = self.first_name.text().strip()
                last_name = self.last_name.text().strip()
                national_id = self.national_id.text().strip()
                insurance_name = self.ins_combo.currentText()
                
                if not all([first_name, last_name, national_id, insurance_name]):
                    QMessageBox.warning(self, 'هشدار', 'لطفا تمام اطلاعات ضروری را پر کنید.')
                    return
                
                total_price = sum(item['payable'] for item in items)
                
                admission_data = {
                    'code': code,
                    'first_name': first_name,
                    'last_name': last_name,
                    'national_id': national_id,
                    'insurance_name': insurance_name,
                    'supp_insurance_name': self.supp_ins_combo.currentText(), 
                    'doctor_id': doctor_id,
                    'admission_date': admission_date,
                    'admission_time': admission_time,
                    'total_price': total_price,
                    'patient_age': self.patient_age.value(),
                    'patient_gender': self.patient_gender.currentText(),
                    'patient_phone': self.patient_phone.text().strip(),
                    'service_type': '',
                    'description': ''
                }
                adm_id = create_admission(admission_data, items)
                
                self.code_edit.setText(code)
                QMessageBox.information(self, 'ذخیره شد', f'پذیرش با شناسه {adm_id} و کد {code} ذخیره شد.')
                
            except Exception as e:
                new_code = self._generate_code()
                admission_data['code'] = new_code
                adm_id = create_admission(admission_data, items)
                self.code_edit.setText(new_code)
                QMessageBox.information(self, 'ذخیره شد', f'پذیرش با شناسه {adm_id} و کد {new_code} ذخیره شد.')
                
        except Exception as e:
            print(f"❌ خطا در ذخیره: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در ثبت پذیرش: {str(e)}")

   def _open_deductions_dialog(self):
    try:
        dlg = QDialog(self)
        dlg.setWindowTitle("مدیریت کسورات و اضافات")
        dlg.setLayoutDirection(Qt.RightToLeft)
        dlg.setFixedSize(350, 200)
        
        layout = QVBoxLayout()
        
        # توضیح
        layout.addWidget(QLabel("مبلغ مثبت = اضافه به فاکتور\nمبلغ منفی = کسر از فاکتور"))
        
        # انتخاب نوع
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("نوع:"))
        deductions_type = QComboBox()
        deductions_type.addItems(["کسورات (کسر از فاکتور)", "اضافات (اضافه به فاکتور)"])
        deductions_type.setMaximumHeight(30)
        type_layout.addWidget(deductions_type)
        layout.addLayout(type_layout)
        
        # مبلغ
        amount_layout = QHBoxLayout()
        amount_layout.addWidget(QLabel("مبلغ:"))
        deductions_edit = QLineEdit()
        current_amount = self.deductions_amount.text().replace(',', '').replace('+', '').replace('-', '')
        deductions_edit.setText(current_amount)
        deductions_edit.setMaximumHeight(30)
        amount_layout.addWidget(deductions_edit)
        layout.addLayout(amount_layout)
        
        # تنظیم نوع بر اساس مقدار قبلی
        if self.deductions_amount.text().startswith('+'):
            deductions_type.setCurrentIndex(1)
        else:
            deductions_type.setCurrentIndex(0)
        
        # دکمه‌ها
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("💾 ذخیره")
        btn_cancel = QPushButton("❌ انصراف")
        btn_save.setMinimumHeight(35)
        btn_cancel.setMinimumHeight(35)
        btn_save.clicked.connect(lambda: self._save_deductions(dlg, deductions_edit, deductions_type))
        btn_cancel.clicked.connect(dlg.reject)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        dlg.setLayout(layout)
        dlg.exec_()
    except Exception as e:
        print(f"❌ خطا در مدیریت کسورات: {e}")

   def _save_deductions(self, dlg, deductions_edit, deductions_type):
    try:
        amount = int(deductions_edit.text().replace(',', ''))
        is_addition = (deductions_type.currentIndex() == 1)  # True برای اضافات
        
        if is_addition:
            # اضافات با علامت +
            self.deductions_amount.setText(f"+{amount:,}")
        else:
            # کسورات با علامت -
            self.deductions_amount.setText(f"-{amount:,}")
        
        dlg.accept()
        self._recalc()
    except ValueError:
        QMessageBox.warning(self, "خطا", "لطفاً مبلغ معتبر وارد کنید")

   def _refresh_admission_ids(self):
        try:
            admissions = list_admissions(500)
            self._admission_ids = [row['id'] for row in admissions][::-1]
            return True
        except Exception as e:
            print(f"❌ خطا در بارگذاری لیست پذیرش‌ها: {e}")
            return False

   def _search_dialog(self):
        try:
            from qt_admission_search import AdmissionSearchDialog
            dlg = AdmissionSearchDialog(self)
            if dlg.exec_() == QDialog.Accepted and dlg.selected_id:
                self._load_admission(dlg.selected_id)
                if hasattr(self, '_admission_ids'):
                    for i, adm_id in enumerate(self._admission_ids):
                        if adm_id == dlg.selected_id:
                            self._admission_index = i
                            break
        except Exception as e:
            print(f"❌ خطا در باز کردن دیالوگ جستجو: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در باز کردن پنجره جستجو: {str(e)}")

   def _first(self):
        try:
            if not self._admission_ids and not self._refresh_admission_ids():
                return
            if self._admission_ids:
                self._admission_index = 0
                self._load_admission(self._admission_ids[0])
            else:
                QMessageBox.information(self, "اطلاع", "هیچ پذیرشی یافت نشد")
        except Exception as e:
            print(f"❌ خطا در اولین پذیرش: {e}")

   def _next(self):
        try:
            if not self._admission_ids and not self._refresh_admission_ids():
                return
            if self._admission_ids and self._admission_index < len(self._admission_ids) - 1:
                self._admission_index += 1
                self._load_admission(self._admission_ids[self._admission_index])
            elif self._admission_ids:
                QMessageBox.information(self, "اطلاع", "این آخرین پذیرش است")
        except Exception as e:
            print(f"❌ خطا در پذیرش بعدی: {e}")

   def _prev(self):
        try:
            if not self._admission_ids and not self._refresh_admission_ids():
                return
            if self._admission_ids and self._admission_index > 0:
                self._admission_index -= 1
                self._load_admission(self._admission_ids[self._admission_index])
            elif self._admission_ids:
                QMessageBox.information(self, "اطلاع", "این اولین پذیرش است")
        except Exception as e:
            print(f"❌ خطا در پذیرش قبلی: {e}")

   def _last(self):
        try:
            if not self._admission_ids and not self._refresh_admission_ids():
                return
            if self._admission_ids:
                self._admission_index = len(self._admission_ids) - 1
                self._load_admission(self._admission_ids[self._admission_index])
        except Exception as e:
            print(f"❌ خطا در آخرین پذیرش: {e}")

   def _edit_row(self):
        try:
            r = self.table.currentRow()
            if r < 0:
                return
                
            dlg = ServicePicker(self)
            if dlg.exec_() == dlg.Accepted and dlg.selected:
                sid, code, name, price, count = dlg.selected
                
                self.table.item(r, 0).setText(str(code))
                self.table.item(r, 1).setText(name)
                self.table.item(r, 2).setText(str(count))
                self.table.item(r, 3).setText(str(price))
                self.table.item(r, 4).setText(str(price))
                
                self._recalc()
        except Exception as e:
            print(f"❌ خطا در ویرایش: {e}")

   def _stub(self):
        QMessageBox.information(self, "چاپ", "امکان چاپ به زودی اضافه خواهد شد.")

   def _exit_stub(self):
        self.setParent(None)

   def _load_admission(self, adm_id: int):
    try:
        self.table.setRowCount(0)
    
        data = get_admission_with_items(adm_id)
        if not data or not data.get('admission'):
            return
    
        adm = data['admission']
    
        self.code_edit.setText(str(adm.get('code', '')))
        self.first_name.setText(str(adm.get('first_name', '')))
        self.last_name.setText(str(adm.get('last_name', '')))
        self.national_id.setText(str(adm.get('national_id', '')))
    
        patient_age = adm.get('patient_age')
        if patient_age is None:
            patient_age = 0
        else:
            try:
                patient_age = int(patient_age)
            except:
                patient_age = 0
        self.patient_age.setValue(patient_age)
    
        patient_phone = adm.get('patient_phone') or ''
        self.patient_phone.setText(str(patient_phone))
    
        gender_text = str(adm.get('patient_gender', ''))
        gender_index = self.patient_gender.findText(gender_text)
        if gender_index >= 0:
            self.patient_gender.setCurrentIndex(gender_index)
        else:
            self.patient_gender.setCurrentIndex(0)
    
        insurance = str(adm.get('insurance_name', ''))
        idx = self.ins_combo.findText(insurance)
        if idx >= 0:
            self.ins_combo.setCurrentIndex(idx)
        else:
            self.ins_combo.setCurrentIndex(0)
    
        doctor_id = adm.get('doctor_id')
        if doctor_id:
            from qt_db import get_doctor_by_id
            doctor = get_doctor_by_id(doctor_id)
            if doctor:
                found = False
                for i in range(self.doctor_combo.count()):
                    if self.doctor_combo.itemData(i) == doctor_id:
                        self.doctor_combo.setCurrentIndex(i)
                        found = True
                        break
                if not found:
                    self.doctor_combo.setCurrentIndex(0)
                self.doctor_code_input.setText(str(doctor.get('code_nezam', '') or ''))
            else:
                self.doctor_combo.setCurrentIndex(0)
                self.doctor_code_input.clear()
        else:
            self.doctor_combo.setCurrentIndex(0)
            self.doctor_code_input.clear()
    
        date_str = str(adm.get('admission_date', ''))
        if date_str:
            self.adm_date_text.setText(date_str)
    
        # ============================================
        # 🔽 فقط یک حلقه for
        # ============================================
        for it in data.get('items', []):
            row = self.table.rowCount()
            self.table.insertRow(row)
    
            # خواندن مقادیر از دیتابیس
            service_name = str(it.get('service_name', ''))
            service_code = it.get('service_code', '')

            # تبدیل به عدد صحیح
            if isinstance(service_code, float):
                service_code = str(int(service_code))
            elif isinstance(service_code, str) and '.' in service_code:
                try:
                    service_code = str(int(float(service_code)))
                except:
                    pass
            else:
                service_code = str(service_code)

            if service_code in ['service_code', 'id', '']:
                import re
                if service_name in ['service_name', '']:
                    service_id = it.get('service_id')
                    if service_id:
                        from qt_db import get_conn
                        conn = get_conn('config')
                        cur = conn.cursor()
                        cur.execute("SELECT code, name FROM services WHERE id = ?", (service_id,))
                        row_data = cur.fetchone()  # ← تغییر نام به row_data
                        conn.close()
                        if row_data:
                            service_code = str(row_data[0] or '')
                            service_name = str(row_data[1] or '')
                    else:
                        print("⚠️ service_id وجود ندارد!")
                else:
                    match = re.search(r'\d+', service_name)
                    if match:
                        service_code = match.group()
                    else:
                        service_code = str(it.get('service_id', ''))

            values = [
                service_code,                         # 0: کد خدمت
                service_name,                         # 1: نام خدمت
                str(it.get('count', 1)),              # 2: تعداد
                str(it.get('price', 0)),              # 3: قیمت خصوصی
                str(it.get('govt_price', 0)),         # 4: قیمت دولتی
                str(it.get('base_share', 0)),         # 5: سهم بیمه
                str(it.get('patient_share', 0)),      # 6: سهم بیمار
                str(it.get('supp_percent', 0)),       # 7: درصد تکمیلی
                str(it.get('supp_share', 0)),         # 8: سهم تکمیلی
                str(it.get('payable', 0))             # 9: قابل پرداخت
            ]

            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))

        self._recalc()
        
    except Exception as e:
        print(f"❌ خطا در بارگذاری پذیرش {adm_id}: {e}")
   def _calculate_totals(self):
        try:
            total_price = 0
            if hasattr(self, 'services_table') and self.services_table:
                for row in range(self.services_table.rowCount()):
                    count_item = self.services_table.item(row, 2)
                    price_item = self.services_table.item(row, 3)
                    total_item = self.services_table.item(row, 4)
                    
                    if count_item and price_item:
                        try:
                            count = int(count_item.text()) if count_item.text().strip() else 1
                            price = int(price_item.text().replace(',', '')) if price_item.text().strip() else 0
                            row_total = count * price
                            if total_item:
                                total_item.setText(f"{row_total:,}")
                            total_price += row_total
                        except ValueError:
                            continue
            
            if hasattr(self, 'total_price_input'):
                self.total_price_input.setText(f"{total_price:,}")
            if hasattr(self, 'total_price_label'):
                self.total_price_label.setText(f"{total_price:,} تومان")
        
            return total_price
            
        except Exception as e:
            print(f"❌ خطا در محاسبه جمع کل: {e}")
            return 0

   def _on_service_changed(self, row, column):
        if column in [2, 3]:
            self._calculate_totals()

   def _update_service_price(self, service_code, count=1):
        try:
            if not service_code:
                return 0
            service = self._find_service_by_code(service_code)
            if service:
                price = service.get('base_price', 0)
                return price * count
            return 0
        except Exception as e:
            print(f"❌ خطا در بروزرسانی قیمت: {e}")
            return 0

   def _find_service_by_code(self, service_code):
        try:
            import qt_db
            services = qt_db.list_services()
            for service in services:
                if service.get('code') == service_code:
                    return service
            return None
        except Exception as e:
            print(f"❌ خطا در پیدا کردن خدمت: {e}")
            return None

   def _connect_price_events(self):
        try:
            if hasattr(self, 'services_table'):
                self.services_table.cellChanged.connect(self._on_service_changed)
            if hasattr(self, 'count_input'):
                self.count_input.textChanged.connect(self._calculate_totals)
        except Exception as e:
            print(f"❌ خطا در اتصال event handlers: {e}")
        self._refresh_service_prices()

   def _refresh_service_prices(self):
        try:
            for row in range(self.table.rowCount()):
                service_code_item = self.table.item(row, 0)
                if service_code_item:
                    service_code = service_code_item.text().strip()
                    if service_code:
                        service = self._find_service_by_code(service_code)
                        if service:
                            price = service.get('base_price', 0)
                            if self.table.item(row, 3):
                                self.table.item(row, 3).setText(str(price))
                            if self.table.item(row, 4):
                                self.table.item(row, 4).setText(str(price))
            self._recalc()
        except Exception as e:
            print(f"❌ خطا در بروزرسانی قیمت‌ها: {e}")

   def show_service_prices(self):
        try:
            if not hasattr(self, 'services_table'):
                return
            row_count = self.services_table.rowCount()
            if row_count == 0:
                return
            
            total = 0
            for row in range(row_count):
                code_item = self.services_table.item(row, 1)
                if not code_item:
                    continue
                service_code = code_item.text().strip()
                if not service_code:
                    continue
                service = self._find_service_by_code(service_code)
                if service:
                    price = service.get('base_price', 0)
                    count_item = self.services_table.item(row, 2)
                    count = 1
                    if count_item and count_item.text().strip():
                        try:
                            count = int(count_item.text())
                        except:
                            count = 1
                    row_total = price * count
                    total += row_total
                    from PyQt5.QtWidgets import QTableWidgetItem
                    self.services_table.setItem(row, 3, QTableWidgetItem(f"{price:,}"))
                    self.services_table.setItem(row, 4, QTableWidgetItem(f"{row_total:,}"))
            
            if hasattr(self, 'total_price_label'):
                self.total_price_label.setText(f"{total:,} تومان")
            
        except Exception as e:
            print(f"❌ خطا: {e}")

   def calculate_final_price(self):
        try:
            base_total = self._calculate_totals()
            discount = 0
            if hasattr(self, 'discount_input') and self.discount_input.text().strip():
                try:
                    discount = int(self.discount_input.text().replace(',', ''))
                except:
                    discount = 0
            tax = 0
            if hasattr(self, 'tax_input') and self.tax_input.text().strip():
                try:
                    tax = int(self.tax_input.text().replace(',', ''))
                except:
                    tax = 0
            final_price = base_total - discount + tax
            if hasattr(self, 'final_price_label'):
                self.final_price_label.setText(f"{final_price:,} تومان")
            return final_price
        except Exception as e:
            print(f"❌ خطا در محاسبه قیمت نهایی: {e}")
            return 0