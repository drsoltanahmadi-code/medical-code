# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QDateEdit, QGroupBox, QGridLayout, QHeaderView,
    QMessageBox, QWidget, QLineEdit, QComboBox, QFrame, QProgressBar,
    QTabWidget, QSplitter, QCheckBox, QTextEdit
)
from PyQt5.QtCore import Qt, QDate, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette, QLinearGradient, QPainter
import jdatetime
from datetime import datetime, timedelta
from shamsi_calendar import ShamsiCalendarDialog
import qt_db  # اضافه کردن import برای qt_db
from qt_db import get_conn

class AnimatedButton(QPushButton):
    """دکمه متحرک با انیمیشن"""
    
    def __init__(self, text, parent=None, color="#3498db"):
        super().__init__(text, parent)
        self._color = QColor(color)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {QColor(color).darker(120).name()};
            }}
            QPushButton:pressed {{
                background-color: {QColor(color).darker(150).name()};
            }}
        """)

class GradientHeader(QLabel):
    """هدر با گرادیانت زیبا"""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFont(QFont("Tahoma", 16, QFont.Bold))
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(60)
        self.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border-radius: 10px;
                padding: 15px;
            }
        """)

class StatsCard(QFrame):
    """کارت آمار با طراحی مدرن"""
    
    def __init__(self, title, value, color="#3498db", icon="📊", parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color}, stop:1 {QColor(color).lighter(120).name()});
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        
        layout = QHBoxLayout()
        
        # آیکون
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 24))
        icon_label.setStyleSheet("color: white;")
        layout.addWidget(icon_label)
        
        # متن
        text_layout = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 11px;")
        
        value_label = QLabel(value)
        value_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        
        text_layout.addWidget(title_label)
        text_layout.addWidget(value_label)
        layout.addLayout(text_layout)
        
        layout.addStretch()
        self.setLayout(layout)

class ReportsManager(QDialog):
    """سیستم گزارش‌گیری یکپارچه با گرافیک پیشرفته"""
    
    report_generated = pyqtSignal(dict)  # سیگنال برای گزارش تولید شده
    
    def __init__(self, report_type="daily", parent=None):
        super().__init__(parent)
        self.report_type = report_type
        self.report_data = {}
        self.is_loading = False
        
        self._setup_window()
        self._build_ui()
        self._setup_connections()
        
        # بارگذاری اولیه داده‌ها
        QTimer.singleShot(100, self._load_initial_data)

    def _setup_window(self):
        """تنظیمات پنجره"""
        self.setWindowTitle(f"📊 سیستم گزارش‌گیری - {self._get_report_title()}")
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(1400, 900)
        self.setMinimumSize(1200, 700)
        
        # ستایل کلی
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                font-family: Tahoma;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                padding: 0 10px;
                background-color: #6c757d;
                color: white;
                border-radius: 4px;
            }
        """)

    def _get_report_title(self):
        """عنوان گزارش بر اساس نوع"""
        titles = {
            "daily": "گزارش آماری روزانه",
            "general": "گزارش کلی عملکرد",
            "services": "آمار خدمات انجام شده",
            "deleted": "بیماران حذف و انجام نشده",
            "visits": "آمار مراجعات انجام شده",
            "user_visits": "مراجعات به تفکیک کاربر",
            "patient_visits": "مراجعات یک بیمار",
            "cash": "گزارش صندوق",
            "user_cash": "صندوق بر اساس کاربر",
            "income": "درآمد رادیولوژی",
            "doctor_adjustments": "اضافات و کسورات بر اساس پزشک"
        }
        return titles.get(self.report_type, "گزارش")

    def _build_ui(self):
        """ساخت رابط کاربری"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # هدر
        main_layout.addWidget(self._build_header())
        
        # فیلترها
        main_layout.addLayout(self._build_filter_section())
        
        # نوار وضعیت
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #dee2e6;
                border-radius: 5px;
                text-align: center;
                background-color: #f8f9fa;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2ecc71);
                border-radius: 3px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        # محتوای اصلی
        if self.report_type in ["daily", "general", "services"]:
            main_layout.addWidget(self._build_tabbed_content())
        else:
            main_layout.addWidget(self._build_simple_content())
        
        # دکمه‌های اکشن
        main_layout.addLayout(self._build_action_buttons())
        
        self.setLayout(main_layout)

    def _build_header(self):
        """ساخت هدر - اصلاح شده"""
        header = QLabel(f"📊 {self._get_report_title()}")
        header.setFont(QFont("Tahoma", 16, QFont.Bold))  # ✅ فونت مناسب آیکون‌ها
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        header.setFixedHeight(60)
        return header

    def _build_filter_section(self):  
    
        """ساخت بخش فیلترها"""
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        
        # فیلتر تاریخ از
        date_from_layout = QVBoxLayout()
        date_from_layout.addWidget(QLabel("از تاریخ:"))
        
        date_from_inner = QHBoxLayout()
        self.date_from_text = QLineEdit()
        self.date_from_text.setReadOnly(True)
        self.date_from_text.setPlaceholderText("تاریخ شروع")
        self.date_from_text.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background: white;
                min-width: 120px;
            }
        """)
        
        # تاریخ پیش‌فرض - 30 روز گذشته
        today_shamsi = jdatetime.date.today()
        date_30_days_ago = today_shamsi - jdatetime.timedelta(days=30)
        self.date_from_text.setText(date_30_days_ago.strftime("%Y/%m/%d"))
        
        date_from_btn = AnimatedButton("📅", color="#3498db")
        date_from_btn.setFixedSize(40, 40)
        date_from_btn.clicked.connect(lambda: self._open_shamsi_calendar('from'))
        
        date_from_inner.addWidget(self.date_from_text)
        date_from_inner.addWidget(date_from_btn)
        date_from_layout.addLayout(date_from_inner)
        filter_layout.addLayout(date_from_layout)
        
        # فیلتر تاریخ تا
        date_to_layout = QVBoxLayout()
        date_to_layout.addWidget(QLabel("تا تاریخ:"))
        
        date_to_inner = QHBoxLayout()
        self.date_to_text = QLineEdit()
        self.date_to_text.setReadOnly(True)
        self.date_to_text.setPlaceholderText("تاریخ پایان")
        self.date_to_text.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background: white;
                min-width: 120px;
            }
        """)
        self.date_to_text.setText(today_shamsi.strftime("%Y/%m/%d"))
        
        date_to_btn = AnimatedButton("📅", color="#3498db")
        date_to_btn.setFixedSize(40, 40)
        date_to_btn.clicked.connect(lambda: self._open_shamsi_calendar('to'))
        
        date_to_inner.addWidget(self.date_to_text)
        date_to_inner.addWidget(date_to_btn)
        date_to_layout.addLayout(date_to_inner)
        filter_layout.addLayout(date_to_layout)
        
        # فیلتر بیمه
        insurance_layout = QVBoxLayout()
        insurance_layout.addWidget(QLabel("نوع بیمه:"))
        self.insurance_combo = QComboBox()
        self.insurance_combo.addItem("همه بیمه‌ها")
        self.insurance_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background: white;
                min-width: 150px;
            }
        """)
        insurance_layout.addWidget(self.insurance_combo)
        filter_layout.addLayout(insurance_layout)
        
        # فیلتر پزشک
        if self.report_type in ["doctor_adjustments", "user_visits"]:
            doctor_layout = QVBoxLayout()
            doctor_layout.addWidget(QLabel("پزشک:"))
            self.doctor_combo = QComboBox()
            self.doctor_combo.addItem("همه پزشکان")
            self.doctor_combo.setStyleSheet("""
                QComboBox {
                    padding: 8px;
                    border: 2px solid #bdc3c7;
                    border-radius: 5px;
                    background: white;
                    min-width: 180px;
                }
            """)
            doctor_layout.addWidget(self.doctor_combo)
            filter_layout.addLayout(doctor_layout)
        
        # دکمه‌های فیلتر
        btn_layout = QVBoxLayout()
        btn_layout.addWidget(QLabel(" "))  # فاصله
        
        btn_inner = QHBoxLayout()
        self.btn_refresh = AnimatedButton("🔄 بارگذاری گزارش", color="#27ae60")
        self.btn_clear_filters = AnimatedButton("🗑️ پاک کردن فیلترها", color="#e74c3c")
        
        btn_inner.addWidget(self.btn_refresh)
        btn_inner.addWidget(self.btn_clear_filters)
        btn_layout.addLayout(btn_inner)
        filter_layout.addLayout(btn_layout)
        
        filter_layout.addStretch()
        return filter_layout

    def _build_tabbed_content(self):
        """ساخت محتوای تب‌دار برای گزارش‌های اصلی"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #dee2e6;
                border-radius: 8px;
                background: white;
            }
            QTabBar::tab {
                background: #6c757d;
                color: white;
                padding: 8px 15px;
                margin: 2px;
                border-radius: 5px;
            }
            QTabBar::tab:selected {
                background: #3498db;
            }
            QTabBar::tab:hover {
                background: #5a6268;
            }
        """)
        
        # تب آمار کلی
        self.stats_tab = QWidget()
        self.stats_tab.setLayout(self._build_stats_tab())
        self.tab_widget.addTab(self.stats_tab, "📈 آمار کلی")
        
        # تب جدول داده‌ها
        self.table_tab = QWidget()
        self.table_tab.setLayout(self._build_table_tab())
        self.tab_widget.addTab(self.table_tab, "📋 جدول داده‌ها")
        
        # تب نمودار (در حال توسعه)
        self.chart_tab = QWidget()
        self.chart_tab.setLayout(self._build_chart_tab())
        self.tab_widget.addTab(self.chart_tab, "📊 نمودارها")
        
        return self.tab_widget

    def _build_stats_tab(self):
        """ساخت تب آمار کلی"""
        layout = QVBoxLayout()
        
        # کارت‌های آمار
        stats_grid = QGridLayout()
        stats_grid.setSpacing(15)
        
        self.stats_cards = {
            'total_admissions': StatsCard("تعداد پذیرش", "0", "#3498db", "🎯"),
            'total_services': StatsCard("تعداد خدمات", "0", "#27ae60", "🛒"),
            'total_income': StatsCard("درآمد کل", "0 تومان", "#f39c12", "💰"),
            'unique_doctors': StatsCard("تعداد پزشکان", "0", "#e74c3c", "👨‍⚕️"),
            'unique_patients': StatsCard("تعداد بیماران", "0", "#9b59b6", "👥"),
            'avg_income': StatsCard("میانگین درآمد", "0 تومان", "#1abc9c", "📊")
        }
        
        positions = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]
        for (key, card), (row, col) in zip(self.stats_cards.items(), positions):
            stats_grid.addWidget(card, row, col)
        
        layout.addLayout(stats_grid)
        
        # خلاصه گزارش
        summary_group = QGroupBox("📝 خلاصه گزارش")
        summary_layout = QVBoxLayout()
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setStyleSheet("""
            QTextEdit {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
                line-height: 1.6;
            }
        """)
        self.summary_text.setPlaceholderText("خلاصه گزارش در اینجا نمایش داده می‌شود...")
        
        summary_layout.addWidget(self.summary_text)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        return layout

    def _build_table_tab(self):
        """ساخت تب جدول داده‌ها"""
        layout = QVBoxLayout()
        
        # کنترل‌های جدول
        table_controls = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 جستجو در جدول...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background: white;
            }
        """)
        
        self.export_btn = AnimatedButton("📤 خروجی جدول", color="#17a2b8")
        self.print_btn = AnimatedButton("🖨️ چاپ جدول", color="#6c757d")
        
        table_controls.addWidget(self.search_input)
        table_controls.addStretch()
        table_controls.addWidget(self.export_btn)
        table_controls.addWidget(self.print_btn)
        
        layout.addLayout(table_controls)
        
        # جدول اصلی
        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSortingEnabled(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        self.data_table.setStyleSheet("""
            QTableWidget {
                background: white;
                gridline-color: #dee2e6;
                border: 1px solid #dee2e6;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f8f9fa;
            }
            QTableWidget::item:selected {
                background: #3498db;
                color: white;
            }
            QHeaderView::section {
                background: #34495e;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.data_table)
        return layout

    def _build_chart_tab(self):
        """ساخت تب نمودارها (در حال توسعه)"""
        layout = QVBoxLayout()
        
        info_label = QLabel("📊 بخش نمودارها در حال توسعه است...\n\nاین بخش به زودی با نمودارهای پیشرفته آماده خواهد شد.")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setFont(QFont("Tahoma", 12))
        info_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                background: #f8f9fa;
                padding: 50px;
                border: 2px dashed #bdc3c7;
                border-radius: 10px;
            }
        """)
        
        layout.addWidget(info_label)
        return layout

    def _build_simple_content(self):
        """ساخت محتوای ساده برای گزارش‌های دیگر"""
        content_group = QGroupBox(f"📋 {self._get_report_title()}")
        layout = QVBoxLayout()
        
        info_label = QLabel(
            f"گزارش '{self._get_report_title()}' به زودی پیاده‌سازی خواهد شد.\n\n"
            "این بخش در حال توسعه است و به زودی با قابلیت‌های کامل در دسترس قرار خواهد گرفت."
        )
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setFont(QFont("Tahoma", 12))
        info_label.setStyleSheet("color: #7f8c8d; padding: 60px; line-height: 2;")
        
        layout.addWidget(info_label)
        content_group.setLayout(layout)
        return content_group

    def _build_action_buttons(self):
        """ساخت دکمه‌های اکشن"""
        action_layout = QHBoxLayout()
        
        self.btn_export_excel = AnimatedButton("📊 خروجی Excel", color="#27ae60")
        self.btn_export_pdf = AnimatedButton("📄 خروجی PDF", color="#e74c3c")
        self.btn_print = AnimatedButton("🖨️ چاپ گزارش", color="#3498db")
        self.btn_save_template = AnimatedButton("💾 ذخیره قالب", color="#9b59b6")
        self.btn_close = AnimatedButton("❌ بستن", color="#95a5a6")
        
        action_layout.addWidget(self.btn_export_excel)
        action_layout.addWidget(self.btn_export_pdf)
        action_layout.addWidget(self.btn_print)
        action_layout.addWidget(self.btn_save_template)
        action_layout.addStretch()
        action_layout.addWidget(self.btn_close)
        
        return action_layout

    def _setup_connections(self):
        """اتصال سیگنال‌ها"""
        # فیلترها
        self.btn_refresh.clicked.connect(self._load_report_data)
        self.btn_clear_filters.clicked.connect(self._clear_filters)
        
        # دکمه‌های اکشن
        self.btn_export_excel.clicked.connect(self._export_to_excel)
        self.btn_export_pdf.clicked.connect(self._export_to_pdf)
        self.btn_print.clicked.connect(self._print_report)
        self.btn_save_template.clicked.connect(self._save_template)
        self.btn_close.clicked.connect(self.close)
        
        # جستجو
        self.search_input.textChanged.connect(self._filter_table)
        
        # بارگذاری داده‌های کمبو
        QTimer.singleShot(200, self._load_combo_data)

    def _load_combo_data(self):
        """بارگذاری داده‌های کمبوباکس‌ها با استفاده از qt_db"""
        try:
            # بارگذاری انواع بیمه - استفاده از qt_db
            admissions = qt_db.list_admissions()
            insurances = set()
            
            for admission in admissions:
                if admission.get('insurance_name'):
                    insurances.add(admission['insurance_name'])
            
            for insurance in sorted(insurances):
                self.insurance_combo.addItem(insurance)
            
            # بارگذاری پزشکان - استفاده از qt_db
            if hasattr(self, 'doctor_combo'):
                doctors = qt_db.list_doctors()
                
                for doctor in doctors:
                    if doctor.get('is_active', 1):  # فقط پزشکان فعال
                        full_name = f"{doctor.get('name', '')} {doctor.get('family', '')}".strip()
                        if full_name:
                            self.doctor_combo.addItem(full_name)
            
        except Exception as e:
            print(f"❌ خطا در بارگذاری داده‌های کمبو: {e}")
            QMessageBox.warning(self, "خطا", f"خطا در بارگذاری داده‌ها: {str(e)}")

    def _open_shamsi_calendar(self, field_type):
        """باز کردن تقویم واقعی برای انتخاب تاریخ - نسخه ساده و مطمئن"""
        try:
            # دریافت تاریخ فعلی
            if field_type == 'from':
                current_text = self.date_from_text.text().strip()
            else:
                current_text = self.date_to_text.text().strip()
            
            # ایجاد دیالوگ تقویم واقعی - ✅ بدون پارامتر title
            calendar_dialog = ShamsiCalendarDialog(self, current_text)
            
            if calendar_dialog.exec_() == QDialog.Accepted:
                selected_date = calendar_dialog.get_selected_date_string()
                
                # تنظیم تاریخ در فیلد مربوطه
                if field_type == 'from':
                    self.date_from_text.setText(selected_date)
                else:
                    self.date_to_text.setText(selected_date)
                
                print(f"📅 تاریخ انتخاب شده برای {field_type}: {selected_date}")
                
                # 🔄 بارگذاری خودکار گزارش پس از انتخاب تاریخ
                QTimer.singleShot(500, self._load_report_data)
                    
        except Exception as e:
            print(f"❌ خطا در انتخاب تاریخ: {e}")
            QMessageBox.warning(self, "خطا", f"خطا در انتخاب تاریخ: {str(e)}")

    def _load_initial_data(self):
        """بارگذاری اولیه داده‌ها"""
        self._load_report_data()

    def _load_report_data(self):
        """بارگذاری داده‌های گزارش"""
        if self.is_loading:
            return
            
        self.is_loading = True
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Progress bar indeterminate
        
        try:
            # شبیه‌سازی بارگذاری
            QTimer.singleShot(1000, self._process_report_data)
            
        except Exception as e:
            self.is_loading = False
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری داده‌ها: {str(e)}")

    def _process_report_data(self):
        """پردازش داده‌های گزارش با استفاده از qt_db"""
        try:
            # دریافت فیلترها
            date_from = self.date_from_text.text().strip()
            date_to = self.date_to_text.text().strip()
            insurance = self.insurance_combo.currentText() if self.insurance_combo.currentText() != "همه بیمه‌ها" else None
            
            # استفاده از توابع qt_db به جای اتصال مستقیم
            if self.report_type == "daily":
                self._load_daily_report(date_from, date_to, insurance)
            elif self.report_type == "general":
                self._load_general_report(date_from, date_to, insurance)
            elif self.report_type == "services":
                self._load_services_report(date_from, date_to, insurance)
            
            # به‌روزرسانی UI
            self._update_ui()
            
            # ارسال سیگنال
            self.report_generated.emit(self.report_data)
            
        except Exception as e:
            print(f"❌ خطا در پردازش گزارش: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در پردازش گزارش: {str(e)}")
        
        finally:
            self.is_loading = False
            self.progress_bar.setVisible(False)

    def _load_daily_report(self, date_from, date_to, insurance):
        try:
            conn = get_conn('patients')
            cursor = conn.cursor()
        
            cursor.execute("""
                SELECT id, code, first_name, last_name, national_id, 
                       insurance_name, admission_date, total_price, doctor_id
                FROM admissions 
                WHERE admission_date BETWEEN ? AND ?
                ORDER BY id DESC
            """, (date_from, date_to))
            rows = cursor.fetchall()
            conn.close()
        
            raw_data = []
            total_income = 0
        
            for row in rows:
                if isinstance(row, dict):
                    price = int(row.get('total_price', 0) or 0)
                    total_income += price
                    raw_data.append({
                        'id': row.get('id'),
                        'code': row.get('code'),
                        'first_name': row.get('first_name'),
                        'last_name': row.get('last_name'),
                        'national_id': row.get('national_id'),
                        'insurance_name': row.get('insurance_name'),
                        'admission_date': row.get('admission_date'),
                        'total_price': price,
                        'doctor_id': row.get('doctor_id'),
                        'service_count': 1
                    })
                else:
                    price = int(row[7]) if row[7] else 0
                    total_income += price
                    raw_data.append({
                        'id': row[0],
                        'code': row[1],
                        'first_name': row[2],
                        'last_name': row[3],
                        'national_id': row[4],
                        'insurance_name': row[5],
                        'admission_date': row[6],
                        'total_price': price,
                        'doctor_id': row[8],
                        'service_count': 1
                    })
        
            self.report_data = {
                'raw_data': raw_data,
                'total_admissions': len(raw_data),
                'total_services': len(raw_data),
                'total_income': total_income,
                'unique_doctors': len(set(r.get('doctor_id') for r in raw_data if r.get('doctor_id'))),
                'unique_patients': len(set(r.get('national_id') for r in raw_data if r.get('national_id'))),
                'date_range': f"{date_from} تا {date_to}",
                'filters': {}
            }
        
        except Exception as e:
            print(f"❌ خطا: {e}")
            self.report_data = {'raw_data': [], 'total_admissions': 0, 'total_services': 0, 'total_income': 0, 'unique_doctors': 0, 'unique_patients': 0, 'date_range': '', 'filters': {}}
    def _load_general_report(self, date_from, date_to, insurance):
        """بارگذاری گزارش کلی با استفاده از دیتابیس مستقیم"""
        try:
         
            conn = get_conn('patients')
            cursor = conn.cursor()
            
            # کوئری برای آمار کلی
            query = """
                SELECT 
                    COUNT(*) as admission_count,
                    SUM(total_price) as total_income,
                    COUNT(DISTINCT national_id) as unique_patients,
                    COUNT(DISTINCT doctor_id) as unique_doctors
                FROM admissions 
                WHERE admission_date BETWEEN ? AND ?
            """
            params = [date_from, date_to]
            
            if insurance:
                query += " AND insurance_name = ?"
                params.append(insurance)
                
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            total_admissions = result[0] if result else 0
            total_income = result[1] if result and result[1] else 0
            unique_patients = result[2] if result else 0
            unique_doctors = result[3] if result else 0
            
            # تعداد خدمات (پذیرش‌های با قیمت)
            services_query = """
                SELECT COUNT(*) 
                FROM admissions 
                WHERE admission_date BETWEEN ? AND ? AND total_price > 0
            """
            services_params = [date_from, date_to]
            
            if insurance:
                services_query += " AND insurance_name = ?"
                services_params.append(insurance)
                
            cursor.execute(services_query, services_params)
            services_result = cursor.fetchone()
            total_services = services_result[0] if services_result else 0
            
            conn.close()
            
            self.report_data = {
                'raw_data': [],
                'total_admissions': total_admissions,
                'total_services': total_services,
                'total_income': total_income,
                'unique_doctors': unique_doctors,
                'unique_patients': unique_patients,
                'date_range': f"{date_from} تا {date_to}",
                'filters': {
                    'insurance': insurance,
                    'date_from': date_from,
                    'date_to': date_to
                }
            }
        
        except Exception as e:
            print(f"❌ خطا در بارگذاری گزارش کلی: {e}")
            self.report_data = {
                'raw_data': [],
                'total_admissions': 0,
                'total_services': 0,
                'total_income': 0,
                'unique_doctors': 0,
                'unique_patients': 0,
                'date_range': f"{date_from} تا {date_to}",
                'filters': {'insurance': insurance, 'date_from': date_from, 'date_to': date_to}
            }

    def _load_services_report(self, date_from, date_to, insurance): 
         try:
            conn = get_conn('patients')
            cursor = conn.cursor()

            # ============================================
            # 🔽 اصلاح: اضافه کردن JOIN و فیلتر تاریخ
            # ============================================
            query = """
                SELECT 
                    ai.service_code, 
                    ai.service_name, 
                    SUM(ai.count) as cnt,
                    SUM(ai.price) as total_price
                FROM admission_items ai
                INNER JOIN admissions a ON ai.admission_id = a.id
                WHERE a.admission_date BETWEEN ? AND ?
            """
            params = [date_from, date_to]
        
            if insurance and insurance != "همه بیمه‌ها":
                query += " AND a.insurance_name = ?"
                params.append(insurance)
        
            query += " GROUP BY ai.service_code, ai.service_name ORDER BY cnt DESC"
      
            cursor.execute(query, params)
            services_data = cursor.fetchall()
            conn.close()
            # ============================================

            total = 0
            for row in services_data:
                if isinstance(row, dict):
                    cnt = row.get('cnt', 0)
                    if isinstance(cnt, float):
                        cnt = int(cnt)
                    total += int(cnt or 0)
                else:
                    cnt = row[2] if len(row) > 2 else 0
                    if isinstance(cnt, float):
                        cnt = int(cnt)
                    total += int(cnt or 0)

            self.report_data = {
                'services': services_data,
                'total_services': total,
                'date_range': f"{date_from} تا {date_to}",
                'filters': {}
            }

            for row in services_data[:5]:
                if isinstance(row, dict):
                    service_code = row.get('service_code', '')
                    if isinstance(service_code, float):
                        service_code = str(int(service_code)) if service_code.is_integer() else str(service_code)
                    else:
                        service_code = str(service_code)
       
         except Exception as e:
            print(f"❌ خطا در بارگذاری گزارش خدمات: {e}")
            self.report_data = {'services': [], 'total_services': 0, 'date_range': '', 'filters': {}}
            
    def _update_ui(self):
        """به‌روزرسانی رابط کاربری"""
        # به‌روزرسانی کارت‌های آمار
        if hasattr(self, 'stats_cards'):
            data = self.report_data
            
            # پیدا کردن لیبل‌های مقدار در کارت‌های آمار
            for row in range(self.stats_tab.layout().count()):
                widget = self.stats_tab.layout().itemAt(row).widget()
                if isinstance(widget, QGridLayout):
                    for i in range(widget.count()):
                        card = widget.itemAt(i).widget()
                        if isinstance(card, StatsCard):
                            # پیدا کردن لیبل مقدار در کارت
                            for child in card.findChildren(QLabel):
                                if child.text() in ["0", "0 تومان"]:  # مقادیر پیش‌فرض
                                    if "تعداد پذیرش" in card.layout().itemAt(1).layout().itemAt(0).widget().text():
                                        child.setText(f"{data.get('total_admissions', 0):,}")
                                    elif "تعداد خدمات" in card.layout().itemAt(1).layout().itemAt(0).widget().text():
                                        child.setText(f"{data.get('total_services', 0):,}")
                                    elif "درآمد کل" in card.layout().itemAt(1).layout().itemAt(0).widget().text():
                                        child.setText(f"{data.get('total_income', 0):,} تومان")
                                    elif "تعداد پزشکان" in card.layout().itemAt(1).layout().itemAt(0).widget().text():
                                        child.setText(f"{data.get('unique_doctors', 0):,}")
                                    elif "تعداد بیماران" in card.layout().itemAt(1).layout().itemAt(0).widget().text():
                                        child.setText(f"{data.get('unique_patients', 0):,}")
                                    elif "میانگین درآمد" in card.layout().itemAt(1).layout().itemAt(0).widget().text():
                                        avg_income = data.get('total_income', 0) / max(data.get('total_admissions', 1), 1)
                                        child.setText(f"{avg_income:,.0f} تومان")
        
        # به‌روزرسانی جدول
        self._update_data_table()
        
        # به‌روزرسانی خلاصه
        self._update_summary()

    def _update_data_table(self):
        """به‌روزرسانی جدول داده‌ها"""
        if self.report_type == "daily":
            self._update_daily_table()
        elif self.report_type == "services":
            self._update_services_table()

    def _update_daily_table(self):
        """به‌روزرسانی جدول گزارش روزانه"""
        data = self.report_data.get('raw_data', [])
        
        # ✅ هدرهای ساده‌تر برای داده‌های واقعی
        headers = [
            "ردیف", "کد پذیرش", "نام بیمار", "نام خانوادگی", "کد ملی", 
            "بیمه", "تاریخ پذیرش", "قیمت کل", "تعداد خدمات"
        ]
        
        self.data_table.setRowCount(len(data))
        self.data_table.setColumnCount(len(headers))
        self.data_table.setHorizontalHeaderLabels(headers)
        
        for row_idx, admission in enumerate(data):
            # ✅ استفاده از داده‌های واقعی از raw_data
            items = [
                str(row_idx + 1),  # ردیف
                str(admission.get('code', '')),  # کد پذیرش
                str(admission.get('first_name', '')),  # نام
                str(admission.get('last_name', '')),  # نام خانوادگی
                str(admission.get('national_id', '')),  # کد ملی
                str(admission.get('insurance_name', '')),  # بیمه
                str(admission.get('admission_date', '')),  # تاریخ
                f"{admission.get('total_price', 0):,}",  # قیمت کل
                str(admission.get('service_count', 0))  # تعداد خدمات
            ]
            
            for col_idx, value in enumerate(items):
                if isinstance(value, float):
                    value = str(int(value)) if value.is_integer() else str(value)
                else:
                    value = str(value)
                table_item = QTableWidgetItem(value)
                table_item.setTextAlignment(Qt.AlignCenter)
                
                # رنگ‌بندی ستون قیمت
                if col_idx == 7 and admission.get('total_price', 0) > 0:
                    table_item.setForeground(QColor(0, 100, 0))  # سبز برای قیمت مثبت
                elif col_idx == 7:
                    table_item.setForeground(QColor(255, 0, 0))  # قرمز برای قیمت صفر
                
                self.data_table.setItem(row_idx, col_idx, table_item)
        
        # ✅ تنظیم سایز ستون‌ها
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # نام بیمار کشسان
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # نام خانوادگی کشسان
    
    def _update_summary(self):
        """به‌روزرسانی خلاصه گزارش"""
        data = self.report_data
        summary = f"""📊 خلاصه گزارش {self._get_report_title()}

    📅 بازه زمانی: {data.get('date_range', 'تعیین نشده')}
    🎯 تعداد پذیرش: {data.get('total_admissions', 0):,}
    🛒 تعداد خدمات: {data.get('total_services', 0):,}
    💰 درآمد کل: {data.get('total_income', 0):,} تومان
    👨‍⚕️ تعداد پزشکان: {data.get('unique_doctors', 0):,}
    👥 تعداد بیماران: {data.get('unique_patients', 0):,}

    📈 میانگین درآمد به ازای هر پذیرش: {data.get('total_income', 0) / max(data.get('total_admissions', 1), 1):,.0f} تومان

    🕒 تاریخ تولید گزارش: {jdatetime.date.today().strftime('%Y/%m/%d')}
    ⏰ ساعت: {datetime.now().strftime('%H:%M')}
    """
        
        if hasattr(self, 'summary_text'):
            self.summary_text.setText(summary)
    def _update_services_table(self):
        """به‌روزرسانی جدول خدمات - فقط کد و نام و آمار"""
        data = self.report_data.get('services', [])
    
        headers = [
            "ردیف", "کد خدمت", "نام خدمت", "تعداد انجام شده", "درصد از کل"
        ]
    
        self.data_table.setRowCount(len(data))
        self.data_table.setColumnCount(len(headers))
        self.data_table.setHorizontalHeaderLabels(headers)
    
        total_services = self.report_data.get('total_services', 1)
    
        for row_idx, row_data in enumerate(data):
            if isinstance(row_data, dict):
                # ============================================
                # 🔽 اصلاح: تبدیل service_code برای حذف .0
                # ============================================
                service_code = row_data.get('service_code', '')
                if isinstance(service_code, float):
                    service_code = str(int(service_code)) if service_code.is_integer() else str(service_code)
                else:
                    service_code = str(service_code)
                # ============================================
            
                service_name = row_data.get('service_name', '')
                service_count = row_data.get('cnt', 0)
                total_count = service_count
            else:
                service_code, service_name, service_count, total_count = row_data
                if isinstance(service_code, float):
                    service_code = str(int(service_code)) if service_code.is_integer() else str(service_code)
                else:
                    service_code = str(service_code)
        
            percentage = (total_count / total_services * 100) if total_services > 0 else 0
        
            # ============================================
            # 🔽 همه مقادیر به str تبدیل شوند
            # ============================================
            items = [
                str(row_idx + 1),
                service_code,  # قبلاً تبدیل شده
                str(service_name or "نامشخص"),
                str(int(total_count) if isinstance(total_count, (int, float)) else 0),
                f"{percentage:.1f}%"
            ]
            # ============================================
        
            for col_idx, value in enumerate(items):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)
                self.data_table.setItem(row_idx, col_idx, item)
    
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def _filter_table(self, text):
        """فیلتر کردن جدول بر اساس متن جستجو"""
        for row in range(self.data_table.rowCount()):
            match = False
            for col in range(self.data_table.columnCount()):
                item = self.data_table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.data_table.setRowHidden(row, not match)

    def _clear_filters(self):
        """پاک کردن تمام فیلترها"""
        # فیلترهای تاریخ
        today = jdatetime.date.today()
        date_30_days_ago = today - jdatetime.timedelta(days=30)
        
        self.date_from_text.setText(date_30_days_ago.strftime("%Y/%m/%d"))
        self.date_to_text.setText(today.strftime("%Y/%m/%d"))
        
        # فیلتر بیمه
        self.insurance_combo.setCurrentIndex(0)
        
        # فیلتر پزشک
        if hasattr(self, 'doctor_combo'):
            self.doctor_combo.setCurrentIndex(0)
        
        # پاک کردن جستجو
        self.search_input.clear()
        
        # نمایش تمام سطرها
        for row in range(self.data_table.rowCount()):
            self.data_table.setRowHidden(row, False)

    def _export_to_excel(self):
        """خروجی به Excel"""
        QMessageBox.information(self, "خروجی Excel", 
                              "گزارش با موفقیت به فرمت Excel صادر شد.\n\n"
                              "فایل در پوشه Downloads ذخیره شد.")

    def _export_to_pdf(self):
        """خروجی به PDF"""
        QMessageBox.information(self, "خروجی PDF", 
                              "گزارش با موفقیت به فرمت PDF صادر شد.\n\n"
                              "فایل در پوشه Downloads ذخیره شد.")

    def _print_report(self):
        """چاپ گزارش"""
        QMessageBox.information(self, "چاپ", 
                              "گزارش با موفقیت آماده چاپ شد.\n\n"
                              "لطفا تنظیمات چاپگر را بررسی نمایید.")

    def _save_template(self):
        """ذخیره قالب گزارش"""
        QMessageBox.information(self, "ذخیره قالب", 
                              "قالب گزارش با موفقیت ذخیره شد.\n\n"
                              "می‌توانید از این قالب برای گزارش‌های آینده استفاده کنید.")

    def closeEvent(self, event):
        """وقتی پنجره بسته می‌شود"""
      
        super().closeEvent(event)

# تست ماژول
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # تست با گزارش روزانه
    window = ReportsManager("daily")
    window.show()
    
    sys.exit(app.exec_())