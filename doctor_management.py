# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView,
    QFrame, QComboBox, QCheckBox, QGroupBox, QFormLayout, QRadioButton
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
import qt_db
import sqlite3

class DoctorManagementWindow(QDialog):
    doctors_updated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('⚙️ مدیریت پزشکان')
        self.resize(1200, 700)
        self.setMinimumSize(1000, 600)
        self.conn = qt_db.get_conn('config')
        self.current_doctor_id = None
        
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
            }
            QFrame#main_frame {
                background: white;
                border-radius: 15px;
                margin: 20px;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2c3e50;
            }
        """)
        
        self._build_ui()
        self._load_doctors()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        main_frame = QFrame()
        main_frame.setObjectName("main_frame")
        layout = QVBoxLayout(main_frame)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # عنوان
        title = QLabel('👨‍⚕️ مدیریت پزشکان')
        title.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 24px;
                font-weight: bold;
                padding: 10px;
                border-bottom: 2px solid #3498db;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # فرم پزشک جدید - فقط یک بار
        self._build_doctor_form(layout)
        
        # دکمه اضافه کردن پزشک جدید در بالای لیست
        btn_add_doctor = QPushButton('➕ افزودن پزشک جدید')
        btn_add_doctor.setStyleSheet(self._get_button_style("#27ae60"))
        btn_add_doctor.clicked.connect(self._show_add_doctor_dialog)
        layout.addWidget(btn_add_doctor)
        
        # نوار جستجو
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 جستجو:"))
        
        self.search_doctors_input = QLineEdit()
        self.search_doctors_input.setPlaceholderText("جستجو در بین پزشکان...")
        self.search_doctors_input.textChanged.connect(self._search_doctors)
        search_layout.addWidget(self.search_doctors_input)
        
        layout.addLayout(search_layout)
        
        # جدول پزشکان
        self.doctors_table = QTableWidget()
        self.doctors_table.setColumnCount(6)
        self.doctors_table.setHorizontalHeaderLabels([
            "🆔 کد نظام", "👤 نام", "👥 خانوادگی", "🎯 تخصص", "📞 تلفن", "✅ وضعیت"
        ])
        
        header = self.doctors_table.horizontalHeader()
        for i in range(6):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        
        self.doctors_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.doctors_table.doubleClicked.connect(self._load_selected_doctor)
        
        layout.addWidget(self.doctors_table)
        
        # دکمه‌های عمل در پایین
        btn_layout = QHBoxLayout()
        
        btn_edit = QPushButton('✏️ ویرایش انتخاب شده')
        btn_edit.setStyleSheet(self._get_button_style("#3498db"))
        btn_edit.clicked.connect(self._edit_selected_doctor)
        
        btn_delete = QPushButton('🗑️ حذف انتخاب شده')
        btn_delete.setStyleSheet(self._get_button_style("#e74c3c"))
        btn_delete.clicked.connect(self._delete_doctor)
        
        btn_refresh = QPushButton('🔄 بروزرسانی')
        btn_refresh.setStyleSheet(self._get_button_style("#f39c12"))
        btn_refresh.clicked.connect(self._load_doctors)
        
        btn_close = QPushButton('❌ بستن')
        btn_close.setStyleSheet(self._get_button_style("#95a5a6"))
        btn_close.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_delete)
        btn_layout.addWidget(btn_refresh)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
        
        main_layout.addWidget(main_frame)

    def _build_doctor_form(self, layout):
        """ساخت فرم اطلاعات پزشک - نسخه کامل"""
        print("🔨 ساخت فرم پزشک...")
        
        form_group = QGroupBox("📝 فرم ورود اطلاعات پزشک")
        form_layout = QFormLayout(form_group)
        
        # ردیف اول - فیلدهای اجباری
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("🆔 کد نظام پزشکی:*"))
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("کد نظام پزشکی")
        row1.addWidget(self.code_input)
        
        row1.addWidget(QLabel("👤 نام:*"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("نام")
        row1.addWidget(self.name_input)
        
        row1.addWidget(QLabel("👥 نام خانوادگی:*"))
        self.family_input = QLineEdit()
        self.family_input.setPlaceholderText("نام خانوادگی")
        row1.addWidget(self.family_input)
        form_layout.addRow(row1)
        
        # ردیف دوم - جنسیت و تخصص
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("👫 جنسیت:"))
        self.gender_combo = QComboBox()
        self.gender_combo.addItem("مرد", "male")    
        self.gender_combo.addItem("زن", "female") 
        row2.addWidget(self.gender_combo)
        
        row2.addWidget(QLabel("🎯 تخصص:*"))
        self.specialty_input = QLineEdit()
        self.specialty_input.setPlaceholderText("تخصص")
        row2.addWidget(self.specialty_input)
        form_layout.addRow(row2)
        
        # ردیف سوم - فیلدهای اختیاری
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("📚 زیرتخصص:"))
        self.sub_specialty_input = QLineEdit()
        self.sub_specialty_input.setPlaceholderText("زیرتخصص (اختیاری)")
        row3.addWidget(self.sub_specialty_input)
        
        row3.addWidget(QLabel("📞 تلفن:"))
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("تلفن (اختیاری)")
        row3.addWidget(self.phone_input)
        form_layout.addRow(row3)
        
        # ردیف چهارم - ایمیل و وضعیت
        row4 = QHBoxLayout()
        row4.addWidget(QLabel("📧 ایمیل:"))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("ایمیل (اختیاری)")
        row4.addWidget(self.email_input)
        
        self.active_check = QCheckBox("✅ پزشک فعال")
        self.active_check.setChecked(True)
        row4.addWidget(self.active_check)
        row4.addStretch()
        form_layout.addRow(row4)
        
        # دکمه‌های عمل فرم
        button_layout = QHBoxLayout()
        
        self.btn_save_new = QPushButton('💾 ذخیره پزشک جدید')
        self.btn_save_new.setStyleSheet(self._get_button_style("#27ae60"))
        self.btn_save_new.clicked.connect(self._save_doctor)
        
        self.btn_clear_form = QPushButton('🧹 پاک کردن فرم')
        self.btn_clear_form.setStyleSheet(self._get_button_style("#f39c12"))
        self.btn_clear_form.clicked.connect(self._clear_form)
        
        button_layout.addWidget(self.btn_save_new)
        button_layout.addWidget(self.btn_clear_form)
        form_layout.addRow(button_layout)
        
        layout.addWidget(form_group)
        print("✅ فرم پزشک ساخته شد")

    def _get_button_style(self, color):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: #219a52; 
            }}
            QPushButton:disabled {{
                background-color: #bdc3c7;
                color: #7f8c8d;
            }}
        """

    def _clear_form(self):
        """پاک کردن فرم"""
        print("🧹 پاک کردن فرم...")
        
        widgets_to_clear = [
            self.code_input, self.name_input, self.family_input,
            self.specialty_input, self.sub_specialty_input,
            self.phone_input, self.email_input
        ]
        
        for widget in widgets_to_clear:
            if widget:
                widget.clear()
        
        if hasattr(self, 'gender_combo'):
            self.gender_combo.setCurrentIndex(0)
        
        if hasattr(self, 'active_check'):
            self.active_check.setChecked(True)
        
        self.current_doctor_id = None
        print("✅ فرم پاک شد")

    def _show_add_doctor_dialog(self):
        """نمایش پنجره افزودن پزشک جدید"""
        dialog = QDialog(self)
        dialog.setWindowTitle('➕ افزودن پزشک جدید')
        dialog.resize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # فرم پزشک
        form_group = QGroupBox("اطلاعات پزشک")
        form_layout = QVBoxLayout(form_group)
        
        # فیلدها...
        fields = [
            ("کد نظام پزشکی:", QLineEdit()),
            ("نام:", QLineEdit()),
            ("نام خانوادگی:", QLineEdit()),
            ("تخصص:", QLineEdit()),
            ("تلفن:", QLineEdit()),
            ("ایمیل:", QLineEdit())
        ]
        
        for label_text, field in fields:
            row = QHBoxLayout()
            row.addWidget(QLabel(label_text))
            row.addWidget(field)
            form_layout.addLayout(row)
            # ذخیره رفرنس فیلدها
            setattr(dialog, f"new_{label_text.replace(':', '').replace(' ', '_')}", field)
        
        # جنسیت
        row_gender = QHBoxLayout()
        row_gender.addWidget(QLabel("جنسیت:"))
        dialog.new_gender = QComboBox()
        dialog.new_gender.addItems(["مرد", "زن"])
        row_gender.addWidget(dialog.new_gender)
        form_layout.addLayout(row_gender)
        
        layout.addWidget(form_group)
        
        # دکمه‌ها
        btn_layout = QHBoxLayout()
        btn_save = QPushButton('💾 ذخیره')
        btn_save.clicked.connect(lambda: self._save_new_doctor(dialog))
        btn_cancel = QPushButton('❌ لغو')
        btn_cancel.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        dialog.exec_()

    def _save_new_doctor(self, dialog):
        """ذخیره پزشک جدید از دیالوگ"""
        try:
            # جمع‌آوری داده‌ها از دیالوگ
            code = dialog.new_کد_نظام_پزشکی.text().strip()
            name = dialog.new_نام.text().strip()
            family = dialog.new_نام_خانوادگی.text().strip()
            specialty = dialog.new_تخصص.text().strip()
            phone = dialog.new_تلفن.text().strip()
            email = dialog.new_ایمیل.text().strip()
            gender = dialog.new_gender.currentText()
            
            # اعتبارسنجی
            if not code or not name or not family or not specialty:
                QMessageBox.warning(dialog, "خطا", "لطفاً فیلدهای الزامی را پر کنید")
                return
            
            full_name = f"{name} {family}"
            
            # ذخیره در دیتابیس
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO doctors 
                (code_nezam, name, family, full_name, gender, specialty, phone, email, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (code, name, family, full_name, gender, specialty, phone, email, True))
            
            self.conn.commit()
            
            QMessageBox.information(dialog, "موفقیت", "✅ پزشک جدید با موفقیت ذخیره شد")
            dialog.accept()
            self._load_doctors()
            
        except sqlite3.IntegrityError:
            QMessageBox.warning(dialog, "خطا", "❌ پزشکی با این کد نظام پزشکی قبلاً ثبت شده است")
        except Exception as e:
            QMessageBox.critical(dialog, "خطا", f"خطا در ذخیره پزشک: {str(e)}")

    # بقیه متدها بدون تغییر می‌مانند...
    def _load_doctors(self, search_text=""):
        try:
            cursor = self.conn.cursor()
            
            if search_text:
                query = """
                    SELECT code_nezam, name, family, gender, specialty, 
                           phone, is_active 
                    FROM doctors 
                    WHERE code_nezam LIKE ? OR name LIKE ? OR family LIKE ? 
                    OR specialty LIKE ? OR phone LIKE ?
                    ORDER BY is_active DESC, family, name
                """
                search_param = f"%{search_text}%"
                cursor.execute(query, [search_param] * 5)
            else:
                cursor.execute("""
                    SELECT code_nezam, name, family, gender, specialty, 
                           phone, is_active 
                    FROM doctors 
                    ORDER BY is_active DESC, family, name
                """)
            
            doctors = cursor.fetchall()
            self.doctors_table.setRowCount(len(doctors))
            
            for row, doctor in enumerate(doctors):
                for col, value in enumerate(doctor):
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    
                    if col == 6:  # ستون وضعیت
                        status = "✅ فعال" if value else "⏸️ غیرفعال"
                        item = QTableWidgetItem(status)
                        item.setForeground(QColor("#27ae60" if value else "#e74c3c"))
                    
                    item.setTextAlignment(Qt.AlignCenter)
                    self.doctors_table.setItem(row, col, item)
                    
        except Exception as e:
            QMessageBox.critical(self, 'خطا', f'خطا در بارگذاری پزشکان: {str(e)}')

    def _search_doctors(self):
        self._load_doctors(self.search_doctors_input.text().strip())

    def _save_doctor(self):
        """ذخیره پزشک جدید از فرم اصلی"""
        print("🔹 شروع ذخیره پزشک جدید...")
        
        try:
            # جمع‌آوری داده‌ها
            code = self.code_input.text().strip()
            name = self.name_input.text().strip()
            family = self.family_input.text().strip()
            specialty = self.specialty_input.text().strip()
            
            # اعتبارسنجی
            if not code or not name or not family or not specialty:
                QMessageBox.warning(self, "خطا", "لطفاً فیلدهای الزامی (*) را پر کنید")
                return
            
            full_name = f"{name} {family}"
            gender = self.gender_combo.currentData()
            sub_specialty = self.sub_specialty_input.text().strip()
            phone = self.phone_input.text().strip()
            email = self.email_input.text().strip()
            is_active = self.active_check.isChecked()
            
            print(f"🔹 ذخیره پزشک: {name} {family} - کد: {code}")
            
            # ذخیره در دیتابیس
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO doctors 
                (code_nezam, name, family, full_name, gender, specialty, 
                sub_specialty, phone, email, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (code, name, family, full_name, gender, specialty,
                sub_specialty, phone, email, is_active))
            
            self.conn.commit()
            
            print("✅ پزشک جدید ذخیره شد")
            QMessageBox.information(self, "موفقیت", "✅ پزشک جدید با موفقیت ذخیره شد")
            
            # پاک کردن فرم و بروزرسانی لیست
            self._clear_form()
            self._load_doctors()
            
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "خطا", "❌ پزشکی با این کد نظام پزشکی قبلاً ثبت شده است")
        except Exception as e:
            print(f"❌ خطا: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در ذخیره پزشک: {str(e)}")

    def _edit_selected_doctor(self):
        """ویرایش پزشک انتخاب شده"""
        selected = self.doctors_table.currentRow()
        if selected >= 0:
            code_nezam = self.doctors_table.item(selected, 0).text()
            self._show_edit_doctor_dialog(code_nezam)

    def _show_edit_doctor_dialog(self, code_nezam):
        """نمایش دیالوگ برای ویرایش اطلاعات پزشک"""
        try:
            print(f"🔧 در حال بارگذاری اطلاعات پزشک با کد: {code_nezam}")
            
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, code_nezam, name, family, full_name, specialty, 
                    sub_specialty, gender, phone, email, is_active
                FROM doctors WHERE code_nezam = ?
            """, (code_nezam,))
            
            doctor_row = cursor.fetchone()
            if not doctor_row:
                QMessageBox.warning(self, "خطا", "پزشک مورد نظر یافت نشد")
                return

            # تبدیل به دیکشنری
            doctor = {
                'id': doctor_row[0],
                'code_nezam': doctor_row[1],
                'name': doctor_row[2],
                'family': doctor_row[3],
                'full_name': doctor_row[4],
                'specialty': doctor_row[5] or '',
                'sub_specialty': doctor_row[6] or '',
                'gender': doctor_row[7] or 'مرد',
                'phone': doctor_row[8] or '',
                'email': doctor_row[9] or '',
                'is_active': bool(doctor_row[10]) if doctor_row[10] is not None else True
            }

            # ایجاد دیالوگ ویرایش
            dialog = QDialog(self)
            dialog.setWindowTitle("✏️ ویرایش اطلاعات پزشک")
            dialog.setModal(True)
            dialog.setFixedSize(500, 600)
            
            layout = QVBoxLayout(dialog)
            form_layout = QFormLayout()
            
            # فیلدهای ورودی
            edit_code_nezam = QLineEdit(str(doctor['code_nezam']))
            edit_name = QLineEdit(doctor['name'])
            edit_family = QLineEdit(doctor['family'])
            edit_specialty = QLineEdit(doctor['specialty'])
            edit_sub_specialty = QLineEdit(doctor['sub_specialty'])
            edit_phone = QLineEdit(doctor['phone'])
            edit_email = QLineEdit(doctor['email'])
            
            # جنسیت
            gender_layout = QHBoxLayout()
            edit_gender_male = QRadioButton("مرد")
            edit_gender_female = QRadioButton("زن")
            gender_layout.addWidget(edit_gender_male)
            gender_layout.addWidget(edit_gender_female)
            gender_layout.addStretch()
            
            if doctor.get('gender', 'مرد') == "مرد":
                edit_gender_male.setChecked(True)
            else:
                edit_gender_female.setChecked(True)
            
            # وضعیت فعال بودن
            edit_is_active = QCheckBox("پزشک فعال")
            edit_is_active.setChecked(doctor['is_active'])
            
            # افزودن فیلدها به فرم
            form_layout.addRow("کد نظام پزشکی:", edit_code_nezam)
            form_layout.addRow("نام:", edit_name)
            form_layout.addRow("نام خانوادگی:", edit_family)
            form_layout.addRow("جنسیت:", gender_layout)
            form_layout.addRow("تخصص:", edit_specialty)
            form_layout.addRow("زیرتخصص:", edit_sub_specialty)
            form_layout.addRow("تلفن:", edit_phone)
            form_layout.addRow("ایمیل:", edit_email)
            form_layout.addRow("وضعیت:", edit_is_active)
            
            # دکمه‌های اقدام
            button_layout = QHBoxLayout()
            
            btn_save = QPushButton("💾 ذخیره تغییرات")
            btn_save.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px; border-radius: 4px; }")
            btn_save.clicked.connect(lambda: self._save_doctor_changes(
                dialog, doctor['id'], edit_code_nezam, edit_name, edit_family, 
                edit_specialty, edit_sub_specialty, edit_gender_male, 
                edit_gender_female, edit_phone, edit_email, edit_is_active
            ))
            
            btn_cancel = QPushButton("❌ انصراف")
            btn_cancel.setStyleSheet("QPushButton { background-color: #f44336; color: white; padding: 8px; border-radius: 4px; }")
            btn_cancel.clicked.connect(dialog.reject)
            
            button_layout.addWidget(btn_save)
            button_layout.addWidget(btn_cancel)
            
            layout.addLayout(form_layout)
            layout.addLayout(button_layout)
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در نمایش فرم ویرایش: {str(e)}")

    def _save_doctor_changes(self, dialog, doctor_id, code_nezam_widget, name_widget, 
                        family_widget, specialty_widget, sub_specialty_widget,
                        gender_male_widget, gender_female_widget, phone_widget, 
                        email_widget, is_active_widget):
        """ذخیره تغییرات پزشک در دیتابیس"""
        try:
            # جمع‌آوری داده‌ها از فرم
            code_nezam = code_nezam_widget.text().strip()
            name = name_widget.text().strip()
            family = family_widget.text().strip()
            full_name = f"{name} {family}"
            specialty = specialty_widget.text().strip()
            sub_specialty = sub_specialty_widget.text().strip()
            gender = "مرد" if gender_male_widget.isChecked() else "زن"
            phone = phone_widget.text().strip()
            email = email_widget.text().strip()
            is_active = is_active_widget.isChecked()

            # اعتبارسنجی داده‌ها
            if not code_nezam:
                QMessageBox.warning(dialog, "خطا", "کد نظام پزشکی الزامی است")
                return
            if not name:
                QMessageBox.warning(dialog, "خطا", "نام پزشک الزامی است")
                return
            if not family:
                QMessageBox.warning(dialog, "خطا", "نام خانوادگی پزشک الزامی است")
                return
            if not specialty:
                QMessageBox.warning(dialog, "خطا", "تخصص پزشک الزامی است")
                return

            # بررسی یکتایی کد نظام پزشکی
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM doctors WHERE code_nezam = ? AND id != ?", 
                          (code_nezam, doctor_id))
            existing_doctor = cursor.fetchone()
            if existing_doctor:
                QMessageBox.warning(dialog, "خطا", "کد نظام پزشکی تکراری است")
                return

            # آپدیت اطلاعات در دیتابیس
            cursor.execute("""
                UPDATE doctors SET 
                    code_nezam = ?, name = ?, family = ?, full_name = ?, 
                    specialty = ?, sub_specialty = ?, gender = ?, 
                    phone = ?, email = ?, is_active = ?
                WHERE id = ?
            """, (
                code_nezam, name, family, full_name, specialty, 
                sub_specialty, gender, phone, email, is_active, doctor_id
            ))

            self.conn.commit()
            
            QMessageBox.information(dialog, "موفق", "✅ اطلاعات پزشک با موفقیت به‌روزرسانی شد")
            dialog.accept()
            self._load_doctors()
            self.doctors_updated.emit()
                
        except sqlite3.Error as e:
            QMessageBox.critical(dialog, "خطا", f"خطای دیتابیس: {str(e)}")
        except Exception as e:
            QMessageBox.critical(dialog, "خطا", f"خطا در ذخیره تغییرات: {str(e)}")

    def _delete_doctor(self):
        selected_items = self.doctors_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "هشدار", "لطفاً یک پزشک برای حذف انتخاب کنید")
            return
            
        code_to_delete = self.doctors_table.item(selected_items[0].row(), 0).text()
        doctor_name = f"{self.doctors_table.item(selected_items[0].row(), 1).text()} {self.doctors_table.item(selected_items[0].row(), 2).text()}"
        
        reply = QMessageBox.question(
            self, "تایید حذف",
            f"آیا از حذف پزشک '{doctor_name}' با کد {code_to_delete} مطمئنید؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM doctors WHERE code_nezam=?", (code_to_delete,))
                self.conn.commit()
                QMessageBox.information(self, "موفقیت", "✅ پزشک با موفقیت حذف شد")
                self._clear_form()
                self._load_doctors()
                self.doctors_updated.emit()
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در حذف پزشک: {str(e)}")

    def _load_selected_doctor(self, index):
        row = index.row()
        code_nezam = self.doctors_table.item(row, 0).text()
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT code_nezam, name, family, gender, specialty, 
                       sub_specialty, phone, email, is_active
                FROM doctors WHERE code_nezam=?
            """, (code_nezam,))
            
            doctor = cursor.fetchone()
            if doctor:
                self.current_doctor_id = doctor[0]
                self.code_input.setText(doctor[0])
                self.name_input.setText(doctor[1])
                self.family_input.setText(doctor[2])
                gender = doctor[3]
                index = self.gender_combo.findData(gender)
                if index >= 0:
                    self.gender_combo.setCurrentIndex(index)
                else:
                    # اگر مقدار فارسی بود
                    if gender == "مرد":
                        self.gender_combo.setCurrentIndex(0)
                    elif gender == "زن":
                        self.gender_combo.setCurrentIndex(1)
                self.specialty_input.setText(doctor[4] or "")
                self.sub_specialty_input.setText(doctor[5] or "")
                self.phone_input.setText(doctor[6] or "")
                self.email_input.setText(doctor[7] or "")
                self.active_check.setChecked(bool(doctor[8]))
                
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری اطلاعات پزشک: {str(e)}")

    def closeEvent(self, event):
        if self.conn:
            self.conn.close()
        event.accept()

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = DoctorManagementWindow()
    window.show()
    sys.exit(app.exec_())