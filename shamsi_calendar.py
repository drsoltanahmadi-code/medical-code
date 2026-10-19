# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                           QTableWidgetItem, QPushButton, QLabel, QFrame, QComboBox)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
import jdatetime

class ShamsiCalendarDialog(QDialog):
    """دیالوگ تقویم شمسی فشرده"""
    
    def __init__(self, parent=None, current_date=None):
        super().__init__(parent)
        self.setWindowTitle("تقویم شمسی")
        self.setFixedSize(480, 500)  # عرض بیشتر برای 7 ستون
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet("""
            QDialog {
                background: #f8f9fa;
                font-family: Tahoma;
            }
        """)
        
        # تنظیم تاریخ فعلی
        self._setup_initial_date(current_date)
        self._build_ui()
        self._update_calendar()
    
    def _setup_initial_date(self, current_date):
        """تنظیم تاریخ اولیه"""
        today = jdatetime.date.today()
        
        if current_date:
            try:
                if isinstance(current_date, str):
                    year, month, day = map(int, current_date.split('/'))
                    self.current_year = year
                    self.current_month = month
                    self.selected_day = day
                else:
                    self.current_year = current_date.year
                    self.current_month = current_date.month
                    self.selected_day = current_date.day
            except:
                self.current_year = today.year
                self.current_month = today.month
                self.selected_day = today.day
        else:
            self.current_year = today.year
            self.current_month = today.month
            self.selected_day = today.day
    
    def _build_ui(self):
        """ساخت رابط کاربری"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # هدر با ماه و سال
        header_frame = self._create_header()
        main_layout.addWidget(header_frame)
        
        # کنترل‌های ناوبری
        controls_frame = self._create_controls()
        main_layout.addWidget(controls_frame)
        
        # جدول تقویم
        calendar_frame = self._create_calendar()
        main_layout.addWidget(calendar_frame)
        
        # نمایش تاریخ انتخابی
        selection_frame = self._create_selection_display()
        main_layout.addWidget(selection_frame)
        
        # دکمه‌ها
        buttons_frame = self._create_buttons()
        main_layout.addWidget(buttons_frame)
        
        self.setLayout(main_layout)
        self._connect_signals()
    
    def _create_header(self):
        """ایجاد هدر"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: #2c3e50;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        frame.setFixedHeight(70)
        
        layout = QVBoxLayout(frame)
        
        self.calendar_title = QLabel()
        self.calendar_title.setFont(QFont("Tahoma", 16, QFont.Bold))
        self.calendar_title.setAlignment(Qt.AlignCenter)
        self.calendar_title.setStyleSheet("""
            QLabel {
                color: white;
                background: transparent;
            }
        """)
        
        layout.addWidget(self.calendar_title)
        return frame
    
    def _create_controls(self):
        """ایجاد کنترل‌ها"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 6px;
                padding: 6px;
                border: 1px solid #bdc3c7;
            }
        """)
        
        layout = QHBoxLayout(frame)
        
        # کامبوباکس سال
        layout.addWidget(QLabel("سال:"))
        self.year_combo = QComboBox()
        self.year_combo.setFixedWidth(80)
        self.year_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #95a5a6;
                border-radius: 4px;
                background: white;
                font-size: 11px;
            }
        """)
        
        current_year = jdatetime.date.today().year
        for year in range(current_year - 5, current_year + 6):
            self.year_combo.addItem(str(year))
        
        self.year_combo.setCurrentText(str(self.current_year))
        layout.addWidget(self.year_combo)
        
        # کامبوباکس ماه
        layout.addWidget(QLabel("ماه:"))
        self.month_combo = QComboBox()
        self.month_combo.setFixedWidth(90)
        self.month_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #95a5a6;
                border-radius: 4px;
                background: white;
                font-size: 11px;
            }
        """)
        
        month_names = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", 
                      "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
        for month in month_names:
            self.month_combo.addItem(month)
        
        self.month_combo.setCurrentIndex(self.current_month - 1)
        layout.addWidget(self.month_combo)
        
        layout.addStretch()
        
        # دکمه‌های ناوبری
        self.btn_prev = QPushButton("◀ ماه قبل")
        self.btn_next = QPushButton("ماه بعد ▶")
        self.btn_today = QPushButton("امروز")
        
        for btn in [self.btn_prev, self.btn_next, self.btn_today]:
            btn.setFixedHeight(30)
            btn.setStyleSheet("""
                QPushButton {
                    background: #3498db;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 5px 10px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #2980b9;
                }
            """)
        
        layout.addWidget(self.btn_today)
        layout.addWidget(self.btn_prev)
        layout.addWidget(self.btn_next)
        
        return frame
    
    def _create_calendar(self):
        """ایجاد جدول تقویم با 7 ستون کامل"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 8px;
                padding: 10px;
                border: 1px solid #bdc3c7;
            }
        """)
        
        layout = QVBoxLayout(frame)
        
        # هدر روزهای هفته
        days_header = QHBoxLayout()
        days_header.setSpacing(2)
        days = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
        
        for day in days:
            label = QLabel(day)
            label.setAlignment(Qt.AlignCenter)
            label.setFont(QFont("Tahoma", 9, QFont.Bold))
            label.setStyleSheet("""
                QLabel {
                    background: #34495e;
                    color: white;
                    padding: 6px 2px;
                    border-radius: 4px;
                    margin: 1px;
                }
            """)
            label.setMinimumHeight(30)
            days_header.addWidget(label)
        
        layout.addLayout(days_header)
        
        # جدول تقویم با 7 ستون کامل
        self.calendar_table = QTableWidget(6, 7)
        self.calendar_table.setHorizontalHeaderLabels([])
        self.calendar_table.horizontalHeader().setVisible(False)
        self.calendar_table.verticalHeader().setVisible(False)
        self.calendar_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.calendar_table.setSelectionMode(QTableWidget.SingleSelection)
        self.calendar_table.setFocusPolicy(Qt.NoFocus)
        
        # تنظیم استایل جدول
        self.calendar_table.setStyleSheet("""
            QTableWidget {
                background: white;
                border: none;
                gridline-color: #bdc3c7;
                font-size: 11px;
            }
            QTableWidget::item {
                border: 1px solid #bdc3c7;
                margin: 1px;
                padding: 3px;
                text-align: center;
            }
            QTableWidget::item:selected {
                background: #3498db;
                color: white;
                border: 2px solid #2980b9;
            }
        """)
        
        # تنظیم ارتفاع و عرض برای 7 ستون کامل
        for i in range(6):
            self.calendar_table.setRowHeight(i, 32)
        for i in range(7):
            self.calendar_table.setColumnWidth(i, 48)  # عرض بیشتر برای 7 ستون
        
        self.calendar_table.setFixedSize(400, 210)  # سایز بزرگتر برای 7 ستون
        
        layout.addWidget(self.calendar_table)
        return frame
    
    def _create_selection_display(self):
        """ایجاد نمایش تاریخ انتخابی - مانند قبلی"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: #27ae60;
                border-radius: 6px;
                padding: 3 px;                 
            }
        """)
        frame.setFixedHeight(45)
        
        layout = QHBoxLayout(frame)
        
        self.selected_date_label = QLabel()
        self.selected_date_label.setFont(QFont("Tahoma", 12, QFont.Bold))
        self.selected_date_label.setAlignment(Qt.AlignCenter)
        self.selected_date_label.setStyleSheet("""
            QLabel {
                color: white;
                background: transparent;
            }
        """)
        
        layout.addWidget(self.selected_date_label)
        return frame
    
    def _create_buttons(self):
        """ایجاد دکمه‌ها"""
        frame = QFrame()
        
        layout = QHBoxLayout(frame)
        
        self.btn_confirm = QPushButton("تایید و انتخاب")
        self.btn_cancel = QPushButton("انصراف")
        
        for btn in [self.btn_confirm, self.btn_cancel]:
            btn.setFixedHeight(35)
            btn.setFont(QFont("Tahoma", 11, QFont.Bold))
        
        self.btn_confirm.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background: #219a52;
            }
        """)
        
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background: #c0392b;
            }
        """)
        
        layout.addStretch()
        layout.addWidget(self.btn_confirm)
        layout.addWidget(self.btn_cancel)
        
        return frame
    
    def _connect_signals(self):
        """اتصال سیگنال‌ها"""
        self.calendar_table.cellClicked.connect(self._on_cell_clicked)
        self.btn_prev.clicked.connect(self._go_prev_month)
        self.btn_next.clicked.connect(self._go_next_month)
        self.btn_today.clicked.connect(self._set_today)
        self.btn_confirm.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.year_combo.currentTextChanged.connect(self._on_year_changed)
        self.month_combo.currentIndexChanged.connect(self._on_month_changed)
    
    def _update_calendar(self):
        """بروزرسانی نمایش تقویم"""
        # به روزرسانی عنوان
        month_names = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", 
                      "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
        self.calendar_title.setText(f"تقویم {month_names[self.current_month-1]} {self.current_year}")
        
        # به روزرسانی کامبوباکس‌ها
        self.year_combo.setCurrentText(str(self.current_year))
        self.month_combo.setCurrentIndex(self.current_month - 1)
        self.calendar_table.setRowCount(6)
        self.calendar_table.setColumnCount(7)
        # پاک کردن تقویم و ایجاد آیتم‌های جدید
        for i in range(6):
            for j in range(7):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            
                
                # تنظیم رنگ پیش‌فرض
                item.setBackground(QColor(255, 255, 255))
                item.setForeground(QColor(149, 165, 166))  # رنگ خاکستری برای سلول‌های خالی
                item.setFont(QFont("Tahoma", 9))
                #item.setText("")
                self.calendar_table.setItem(i, j, item)
        # محاسبه اولین روز ماه
        first_day = jdatetime.date(self.current_year, self.current_month, 1)
        weekdays_map = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6}
        start_col = weekdays_map[first_day.weekday()]
        
        # پر کردن تقویم
        row, col = 0, start_col
        today = jdatetime.date.today()
        
        for day in range(1, 32):
            try:
                current_date = jdatetime.date(self.current_year, self.current_month, day)
                item = self.calendar_table.item(row, col)
                item.setText(str(day))
                item.setForeground(QColor(44, 62, 80))
                    
                # رنگ‌بندی هوشمند
                if day == self.selected_day:
                    item.setBackground(QColor(52, 152, 219))
                    item.setForeground(QColor(255, 255, 255))
                    item.setFont(QFont("Tahoma", 10, QFont.Bold))
                    
                elif current_date == today:
                    item.setBackground(QColor(46, 204, 113))
                    item.setForeground(QColor(255, 255, 255))
                    item.setFont(QFont("Tahoma", 10, QFont.Bold))
                    
                elif current_date.weekday() == 6:
                    item.setBackground(QColor(231, 76, 60))
                    item.setForeground(QColor(255, 255, 255))
                    item.setFont(QFont("Tahoma", 9, QFont.Bold))
                    
                elif current_date.weekday() == 5:
                    item.setBackground(QColor(243, 156, 18))
                    item.setForeground(QColor(255, 255, 255))
                    item.setFont(QFont("Tahoma", 9))
                    
                else:
                    item.setBackground(QColor(255, 255, 255))
                    item.setForeground(QColor(44, 62, 80))
                    item.setFont(QFont("Tahoma", 9))
                
                col += 1
                if col > 6:
                    col = 0
                    row += 1
                    if row > 5:
                        break
                        
            except ValueError:
                break
        
        # به روزرسانی نمایش تاریخ انتخابی
        self._update_selected_display()
    
    def _update_selected_display(self):
        """به روزرسانی نمایش تاریخ انتخابی"""
        month_names = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", 
                      "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
        
        selected_date = jdatetime.date(self.current_year, self.current_month, self.selected_day)
        day_name = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"][selected_date.weekday()]
        
        self.selected_date_label.setText(
            f"تاریخ انتخاب شده: {self.current_year}/{self.current_month:02d}/{self.selected_day:02d} - {day_name}"
        )
    
    def _on_cell_clicked(self, row, col):
        """وقتی روی سلول تقویم کلیک شد"""
        item = self.calendar_table.item(row, col)
        if item and item.text().strip():
            self.selected_day = int(item.text())
            self._update_calendar()
    
    def _go_prev_month(self):
        """ماه قبل"""
        if self.current_month == 1:
            self.current_year -= 1
            self.current_month = 12
        else:
            self.current_month -= 1
        self.selected_day = 1
        self._update_calendar()
    
    def _go_next_month(self):
        """ماه بعد"""
        if self.current_month == 12:
            self.current_year += 1
            self.current_month = 1
        else:
            self.current_month += 1
        self.selected_day = 1
        self._update_calendar()
    
    def _set_today(self):
        """تنظیم روی تاریخ امروز"""
        today = jdatetime.date.today()
        self.current_year = today.year
        self.current_month = today.month
        self.selected_day = today.day
        self._update_calendar()
    
    def _on_year_changed(self, year_text):
        """وقتی سال تغییر کرد"""
        if year_text:
            self.current_year = int(year_text)
            self._update_calendar()
    
    def _on_month_changed(self, month_index):
        """وقتی ماه تغییر کرد"""
        if month_index >= 0:
            self.current_month = month_index + 1
            self._update_calendar()
    
    def get_selected_date(self):
        """دریافت تاریخ انتخاب شده"""
        return jdatetime.date(self.current_year, self.current_month, self.selected_day)
    
    def get_selected_date_string(self, format="%Y/%m/%d"):
        """دریافت تاریخ انتخاب شده به صورت رشته"""
        return self.get_selected_date().strftime(format)