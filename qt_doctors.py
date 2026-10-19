# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, 
    QFrame, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPainter, QLinearGradient, QColor
import sqlite3
import qt_db

class DoctorsWindow(QDialog):
    doctor_selected = pyqtSignal(dict)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('👨‍⚕️ انتخاب پزشک معالج')
        self.resize(1000, 700)
        self.setMinimumSize(900, 600)
        self.parent = parent
        self.conn = qt_db.get_conn('config')
        self.selected_doctor = None
        
        # تنظیم استایل مدرن
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
            QLabel#title {
                color: #2c3e50;
                font-size: 24px;
                font-weight: bold;
                padding: 15px;
            }
            QLineEdit {
                padding: 12px;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                font-size: 14px;
                background: #f8f9fa;
            }
            QLineEdit:focus {
                border-color: #3498db;
                background: white;
            }
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 8px;
                background: white;
                gridline-color: #e9ecef;
                alternate-background-color: #f8f9fa;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #e9ecef;
            }
            QTableWidget::item:selected {
                background: #3498db;
                color: white;
            }
            QHeaderView::section {
                background: #2c3e50;
                color: white;
                padding: 12px;
                border: none;
                font-weight: bold;
            }
        """)
        
        self._build_ui()
        self._load_doctors()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # فریم اصلی با پس‌زمینه سفید
        main_frame = QFrame()
        main_frame.setObjectName("main_frame")
        layout = QVBoxLayout(main_frame)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # عنوان
        title = QLabel('👨‍⚕️ مدیریت و انتخاب پزشکان')
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # جستجوی پیشرفته
        search_frame = QFrame()
        search_layout = QHBoxLayout(search_frame)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 جستجو بر اساس کد نظام پزشکی، نام، نام خانوادگی یا تخصص...")
        self.search_input.textChanged.connect(self._delayed_search)
        search_layout.addWidget(self.search_input)
        
        layout.addWidget(search_frame)
        
        # اطلاعات وضعیت
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 12px;
                padding: 5px;
                background: #ecf0f1;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.stats_label)
        
        # جدول مدرن
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["🆔 کد نظام پزشکی", "👤 نام", "👤 نام خانوادگی", "🎯 تخصص"])
        
        # تنظیم هدر
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._select_doctor)
        self.table.setSortingEnabled(True)
        
        layout.addWidget(self.table)
        
        # نوار پیشرفت
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                background: #ecf0f1;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2ecc71);
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # دکمه‌های عمل
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        
        btn_select = QPushButton('✅ انتخاب پزشک انتخاب شده')
        btn_select.setStyleSheet(self._get_button_style("#27ae60"))
        btn_select.clicked.connect(self._select_doctor)
        
        btn_refresh = QPushButton('🔄 بروزرسانی لیست')
        btn_refresh.setStyleSheet(self._get_button_style("#3498db"))
        btn_refresh.clicked.connect(self._refresh_list)
        
        btn_close = QPushButton('❌ بستن')
        btn_close.setStyleSheet(self._get_button_style("#e74c3c"))
        btn_close.clicked.connect(self.reject)
        
        button_layout.addWidget(btn_select)
        button_layout.addWidget(btn_refresh)
        button_layout.addStretch()
        button_layout.addWidget(btn_close)
        
        layout.addWidget(button_frame)
        main_layout.addWidget(main_frame)
        
        # تایمر برای جستجوی تاخیری
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)

    def _get_button_style(self, color):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(color)};
                transform: translateY(-1px);
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(color, 30)};
            }}
        """

    def _darken_color(self, color, percent=20):
        """تیره کردن رنگ برای افکت hover"""
        color = QColor(color)
        return color.darker(100 + percent).name()

    def _delayed_search(self):
        """جستجوی تاخیری برای عملکرد بهتر"""
        self.search_timer.stop()
        self.search_timer.start(500)  # 500ms delay

    def _perform_search(self):
        """انجام جستجو"""
        search_text = self.search_input.text().strip()
        self._load_doctors(search_text)

    # در کلاس DoctorsWindow تغییرات زیر را اعمال کن:

    def _load_doctors(self, search_text=""):
        """بارگذاری لیست پزشکان - نسخه بهبود یافته"""
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(30)
            
            cursor = self.conn.cursor()
            
            if search_text.strip():
                query = """
                    SELECT code_nezam, name, family, specialty 
                    FROM doctors 
                    WHERE (code_nezam LIKE ? OR name LIKE ? OR family LIKE ? OR specialty LIKE ?
                        OR name || ' ' || family LIKE ?)  -- 🔥 جستجو با نام کامل
                    AND is_active = 1
                    ORDER BY name, family
                """
                search_param = f"%{search_text}%"
                cursor.execute(query, (search_param, search_param, search_param, search_param, search_param))
            else:
                cursor.execute("""
                    SELECT code_nezam, name, family, specialty 
                    FROM doctors 
                    WHERE is_active = 1
                    ORDER BY name, family
                """)
            
            doctors = cursor.fetchall()
            
            self.progress_bar.setValue(70)
            self.table.setRowCount(len(doctors))
            
            for row, doctor in enumerate(doctors):
                code_nezam, name, family, specialty = doctor
                
                items_data = [
                    code_nezam,
                    name or "",
                    family or "", 
                    specialty or "---"
                ]
                
                for col, value in enumerate(items_data):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    
                    if row % 2 == 0:
                        item.setBackground(QColor('#f8f9fa'))
                    
                    self.table.setItem(row, col, item)
            
            # 🔥 آپدیت متن راهنما
            self.stats_label.setText(f"📊 نمایش {len(doctors)} پزشک فعال - جستجو با: کد نظام پزشکی، نام، نام خانوادگی، تخصص یا نام کامل")
            
            self.progress_bar.setValue(100)
            QTimer.singleShot(500, lambda: self.progress_bar.setVisible(False))
            
            print(f"✅ {len(doctors)} پزشک بارگذاری شد")
                    
        except Exception as e:
            print(f"❌ خطا در بارگذاری پزشکان: {e}")
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, 'خطا', f'خطا در بارگذاری پزشکان: {str(e)}')


    def _refresh_list(self):
        """بروزرسانی لیست"""
        self.search_input.clear()
        self._load_doctors()

    def _select_doctor(self):
        """انتخاب پزشک و بازگشت به فرم اصلی"""
        current_row = self.table.currentRow()
        
        if current_row >= 0:
            try:
                # خواندن اطلاعات از جدول
                code_nezam = self.table.item(current_row, 0).text()
                name = self.table.item(current_row, 1).text()
                family = self.table.item(current_row, 2).text()
                specialty = self.table.item(current_row, 3).text()
                
                # ذخیره اطلاعات پزشک انتخاب شده
                self.selected_doctor = {
                    'code_nezam': code_nezam,
                    'name': name,
                    'family': family,
                    'specialty': specialty
                }
                
                print(f"✅ پزشک انتخاب شد: {name} {family} - کد: {code_nezam}")
                
                # برجسته کردن سطر انتخاب شده
                for col in range(4):
                    item = self.table.item(current_row, col)
                    if item:
                        item.setBackground(QColor('#3498db'))
                        item.setForeground(QColor('white'))
                
                # تأخیر کوتاه برای نمایش انتخاب
                QTimer.singleShot(300, self._apply_selection)
                
            except Exception as e:
                print(f"❌ خطا در انتخاب پزشک: {e}")
                QMessageBox.critical(self, "خطا", f"خطا در انتخاب پزشک: {e}")
        else:
            QMessageBox.warning(self, "هشدار", "⚠️ لطفاً یک پزشک از لیست انتخاب کنید")

    def _apply_selection(self):
        """اعمال انتخاب پزشک به فرم اصلی"""
        if self.selected_doctor:
            code_nezam = self.selected_doctor['code_nezam']
            name = self.selected_doctor['name']
            family = self.selected_doctor['family']
            specialty = self.selected_doctor.get('specialty', '')
            
            # به‌روزرسانی فیلدهای فرم اصلی
            if hasattr(self.parent, 'doctor_code_input'):
                self.parent.doctor_code_input.setText(code_nezam)
                print("🔹 کد نظام پزشکی در فیلد قرار گرفت")
            
            if hasattr(self.parent, 'doctor_combo'):
                # پیدا کردن یا اضافه کردن به کامبوباکس
                found_index = -1
                for i in range(self.parent.doctor_combo.count()):
                    if self.parent.doctor_combo.itemData(i) == code_nezam:
                        found_index = i
                        break
                
                if found_index >= 0:
                    self.parent.doctor_combo.setCurrentIndex(found_index)
                else:
                    full_name = f"{name} {family}"
                    display_text = f"{full_name} - {specialty}" if specialty else full_name
                    self.parent.doctor_combo.addItem(display_text, code_nezam)
                    self.parent.doctor_combo.setCurrentIndex(self.parent.doctor_combo.count() - 1)
                
                print("🔹 کامبوباکس پزشک به‌روزرسانی شد")
            
            # بستن پنجره
            self.accept()

    def closeEvent(self, event):
        """هندل بسته شدن پنجره"""
        if self.conn:
            self.conn.close()
        event.accept()