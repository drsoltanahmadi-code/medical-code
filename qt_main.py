# -*- coding: utf-8 -*-
import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QMainWindow, QAction, QMessageBox, 
                            QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
                            QHeaderView, QDialog, QPushButton, QLineEdit, QFrame, 
                            QStackedWidget, QGraphicsDropShadowEffect, QToolButton)
from PyQt5.QtGui import (QFontDatabase, QFont, QColor, QPalette, QIcon, QPixmap, QLinearGradient, 
                        QPainter, QBrush)
from PyQt5.QtCore import (Qt, QDate, QPropertyAnimation, QEasingCurve, QTimer, 
                          QSize, QRect, pyqtProperty)
import sqlite3
import jdatetime
import shutil

# ===== Monkey Patch (Remote Database - Client) =====
import json as _json
import sqlite3 as _sqlite3_original
import requests as _requests

_CONFIG_FILE = "server_config.json"
_DEFAULT_CONFIG = {"server_ip": "127.0.0.1", "server_port": 5000}

if os.path.exists(_CONFIG_FILE):
    with open(_CONFIG_FILE, 'r', encoding='utf-8') as _f:
        _config = _json.load(_f)
else:
    _config = _DEFAULT_CONFIG
    with open(_CONFIG_FILE, 'w', encoding='utf-8') as _f:
        _json.dump(_DEFAULT_CONFIG, _f, indent=4)

_SERVER_URL = f"http://{_config['server_ip']}:{_config['server_port']}/query"

class _RemoteConnection:
    def __init__(self, database):
        self.db = os.path.basename(database).replace('.db', '').replace('.sqlite', '')
        self.closed = False
    def cursor(self):
        return _RemoteCursor(self.db)
    def commit(self): pass
    def close(self): self.closed = True
    def __enter__(self): return self
    def __exit__(self, *a): self.close()

class RowDict(dict):
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)
    
    def get(self, key, default=None):
        val = super().get(key, None)
        if val is not None:
            return val
        return default

class _RemoteCursor:
    def __init__(self, db):
        self.db = db
        self._rows = []
        self._idx = 0
        self.rowcount = 0
        self.lastrowid = 0
        self.description = None
        
    def execute(self, sql, params=None):
        r = _requests.post(_SERVER_URL, json={
            "sql": sql, 
            "params": params or [], 
            "db": self.db
        }, timeout=10)
        d = r.json()
        if isinstance(d, list):
            self._rows = d
            self.rowcount = len(d)
            if d and isinstance(d[0], dict):
                self.description = [(k, None, None, None, None, None, None) for k in d[0].keys()]
        else:
            self._rows = []
            self.rowcount = d.get('changes', 0)
            self.lastrowid = d.get('lastrowid', 0)
        self._idx = 0
    
    def fetchone(self):
        if self._idx < len(self._rows):
            r = self._rows[self._idx]
            self._idx += 1
            if isinstance(r, dict):
                return RowDict(r)
            return r
        return None

    def fetchall(self):
        return self._rows[self._idx:]

# فعال‌سازی دائم (برای کلاینت همیشه باید فعال باشه)
sqlite3.Connection = _RemoteConnection
sqlite3.connect = lambda path: _RemoteConnection(path)
# ===== End Monkey Patch =====

def get_base_path():
    """دریافت مسیر صحیح برنامه"""
    if getattr(sys, 'frozen', False):
        # در حالت EXE
        base_path = os.path.dirname(sys.executable)
    else:
        # در حالت اسکریپت
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return base_path

base_path = get_base_path()
print(f"📂 مسیر برنامه: {base_path}")

# ==== ایمپورت و پچ همه ماژول‌ها برای کلاینت ====
import qt_db
import qt_services
import qt_templates
import qt_ReportsManager
import qt_groups
import qt_insurance
import qt_report_answer
import qt_admission
import qt_doctors
import qt_permissions
import qt_tariff_upload
import qt_admission_search

all_modules = [
    qt_db, qt_services, qt_templates, qt_ReportsManager,
    qt_groups, qt_insurance, qt_report_answer, qt_admission,
    qt_doctors, qt_permissions, qt_tariff_upload, qt_admission_search
]

# اعمال remote database روی همه ماژول‌ها
for mod in all_modules:
    if hasattr(mod, 'sqlite3'):
        mod.sqlite3.Connection = _RemoteConnection
        mod.sqlite3.connect = lambda path: _RemoteConnection(path)
    if hasattr(mod, 'get_conn'):
        mod.get_conn = qt_db.get_conn

# Patch 1: رفع مشکل PercentEditor
_original_percent_editor = qt_insurance.PercentEditor
class _PatchedPercentEditor(_original_percent_editor):
    def __init__(self, value, parent=None):
        try:
            super().__init__(int(float(value)), parent)
        except (ValueError, TypeError):
            super().__init__(0, parent)
qt_insurance.PercentEditor = _PatchedPercentEditor

# Patch 2: لود درصدهای بیمه در AdmissionForm
_original_build_header = qt_admission.AdmissionForm._build_header
def _patched_build_header(self):
    self._supp_percents = qt_insurance.load_supp_insurance_percents()
    return _original_build_header(self)
qt_admission.AdmissionForm._build_header = _patched_build_header

# ایمپورت‌های معمولی (بدون تکرار import ماژول‌ها)
from qt_admission import AdmissionForm
from qt_insurance import InsuranceSettingsDialog
from qt_groups import GroupsWindow
from qt_services import ServicesWindow
from qt_report_answer import AnswerForm
from qt_doctors import DoctorsWindow
from qt_templates import ModernTemplatePicker
from qt_tariff_upload import TariffUploadWindow
from qt_ReportsManager import ReportsManager
from doctor_management import DoctorManagementWindow
from qt_permissions import UsersDialog


    
def main():
    # بررسی اتصال به سرور
    try:
        test_response = _requests.get(f"http://{_config['server_ip']}:{_config['server_port']}/health", timeout=5)
        if test_response.status_code != 200:
            app = QApplication(sys.argv)
            QMessageBox.critical(None, "خطای اتصال", "سرور در دسترس نیست! لطفاً سرور را راه‌اندازی کنید.")
            sys.exit(1)
    except Exception as e:
        app = QApplication(sys.argv)
        QMessageBox.critical(None, "خطای اتصال", f"عدم اتصال به سرور:\n{str(e)}")
        sys.exit(1)
    
    # راه‌اندازی دیتابیس (از طریق سرور انجام میشه)
    from qt_db import initialize_all_databases as db_setup  
    try:
        db_setup()
    except Exception as e:
        print(f"⚠️ خطا در راه‌اندازی دیتابیس‌ها: {e}")
    
    app = QApplication(sys.argv)
    
    # تنظیم فونت فارسی
    font_path = os.path.join(base_path, "fonts", "Vazirmatn-Regular.ttf")
    font_id = QFontDatabase.addApplicationFont(font_path)

    if font_id < 0:
        print("⚠️ فونت لود نشد")
    else:
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        app.setFont(QFont(font_family, 12))
    
    # صفحه لاگین
    from qt_login import LoginDialog
    login_dialog = LoginDialog()
    if login_dialog.exec_() != QDialog.Accepted:
        sys.exit()  # اگر کاربر لاگین نکرد برنامه بسته شود
    
    # ایجاد پنجره اصلی
    w = MainWindow()
    w.show()

    sys.exit(app.exec_())  # اجرای حلقه رویداد

class ModernButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(35)
          
    def enterEvent(self, event):
        self.animation = QPropertyAnimation(self, b"size")
        self.animation.setDuration(200)
        self.animation.setStartValue(self.size())
        self.animation.setEndValue(QSize(self.width() + 5, self.height() + 2))
        self.animation.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.animation = QPropertyAnimation(self, b"size")
        self.animation.setDuration(200)
        self.animation.setStartValue(self.size())
        self.animation.setEndValue(QSize(self.width() - 5, self.height() - 2))
        self.animation.start()
        super().leaveEvent(event)

class SidebarButton(QToolButton):
    def __init__(self, text, icon_path="", parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setMinimumHeight(40)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        if icon_path:
            self.setIcon(QIcon(icon_path))
        
    def enterEvent(self, event):
        self.setStyleSheet("""
            QToolButton {
                background-color: #2d8cff;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px;
                text-align: left;
                margin: 2px 5px;
            }
        """)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.setStyleSheet("""
            QToolButton {
                background-color: transparent;
                color: #64748b;
                border: none;
                border-radius: 8px;
                padding: 8px;
                text-align: left;
                margin: 1px 3px;
            }
        """)
        super().leaveEvent(event)

class DashboardWidget(QFrame):
    def __init__(self, title, value, color, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(40)
        self.setFrameStyle(QFrame.StyledPanel)
        
        layout = QVBoxLayout()
        
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")
        
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet("color: #334155; font-size: 24px; font-weight: bold;")
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()
        
        self.setLayout(layout)
        self._apply_style(color)
    
    def update_value(self, new_value):
        """به‌روزرسانی مقدار ویجت"""
        if hasattr(self, 'value_label'):
            self.value_label.setText(str(new_value))  
    
    def _apply_style(self, color):
        self.setStyleSheet(f"""
            DashboardWidget {{
                background: white;
                border-radius: 15px;
                border: 2px solid #e2e8f0;
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("سیستم مدیریت رادیولوژی - نسخه کلاینت")
        self.resize(1300, 800)
        self.setMinimumSize(1200, 700)
        self.stacked_widget = None
        
        # تنظیم تم روشن و مدرن
        self._set_modern_theme()

        self.dashboard_widgets = []
        
        # ایجاد رابط کاربری مدرن
        self._create_modern_ui()
        
        # تایمر برای بروزرسانی داشبورد
        self.dashboard_timer = QTimer()
        self.dashboard_timer.timeout.connect(self.refresh_dashboard)
        self.dashboard_timer.start(30000)  # هر 30 ثانیه

    def _set_modern_theme(self):
        """تنظیم تم روشن و مدرن"""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8fafc, stop:1 #e2e8f0);
            }
            
            QMenuBar {
                background: #ffffff;
                color: #334155;
                border-bottom: 2px solid #e2e8f0;
                padding: 5px;
                font-weight: bold;
            }
            
            QMenuBar::item {
                background: transparent;
                padding: 8px 15px;
                border-radius: 6px;
                margin: 2px;
            }
            
            QMenuBar::item:selected {
                background: #3b82f6;
                color: white;
            }
            
            QMenu {
                background: #ffffff;
                color: #334155;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 5px;
            }
            
            QMenu::item {
                padding: 8px 25px 8px 20px;
                border-radius: 4px;
            }
            
            QMenu::item:selected {
                background: #3b82f6;
                color: white;
            }
            
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2563eb, stop:1 #1d4ed8);
            }
            
            QPushButton:pressed {
                background: #1d4ed8;
            }
            
            QTableWidget {
                background: white;
                color: #334155;
                gridline-color: #e2e8f0;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                alternate-background-color: #f8fafc;
            }
            
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f1f5f9;
            }
            
            QTableWidget::item:selected {
                background: #dbeafe;
                color: #1e40af;
            }
            
            QHeaderView::section {
                background: #f1f5f9;
                color: #475569;
                padding: 10px;
                border: none;
                font-weight: bold;
                border-bottom: 2px solid #e2e8f0;
            }
            
            QLineEdit {
                background: white;
                color: #334155;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 12px;
            }
            
            QLineEdit:focus {
                border-color: #3b82f6;
            }
            
            QLabel {
                color: #334155;
            }
            
            QTabWidget::pane {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background: white;
            }
            
            QTabBar::tab {
                background: #f1f5f9;
                color: #64748b;
                padding: 10px 20px;
                margin: 2px;
                border-radius: 5px;
            }
            
            QTabBar::tab:selected {
                background: #3b82f6;
                color: white;
            }
        """)

    def _create_modern_ui(self):
        """ایجاد رابط کاربری مدرن با سایدبار و دشبورد"""
        
        # ویجت مرکزی
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # لایه اصلی
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ایجاد سایدبار
        self._create_sidebar(main_layout)
        
        # ایجاد ناحیه محتوا
        self._create_content_area(main_layout)
        
        # ایجاد منو
        self._create_menu()

    def _create_sidebar(self, main_layout):
        """ایجاد سایدبار مدرن"""
        sidebar = QFrame()
        sidebar.setMinimumWidth(100)
        sidebar.setMaximumWidth(120)
        sidebar.setStyleSheet("""
            QFrame {
                background: white;
                border-right: 2px solid #e2e8f0;
            }
        """)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(5, 10, 5, 10)
        sidebar_layout.setSpacing(5)
        
        # لوگو و عنوان
        logo_label = QLabel()
        logo_path = "logo.png"
        try:
            logo_pixmap = QPixmap(logo_path)
            if not logo_pixmap.isNull():
               
                logo_label.setPixmap(logo_pixmap.scaled(130, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                raise Exception("لوگو لود نشد")
        except:
            print(f"❌ لوگو لود نشد: {logo_path}")
            logo_label.setStyleSheet("""
                QLabel {
                    color: #3b82f6;
                    font-size: 18px;
                    font-weight: bold;
                    padding: 5px;
                    background: rgba(59, 130, 246, 0.1);
                    border-radius: 10px;
                    text-align: center;
                }
            """)
        logo_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(logo_label)
        logo_label.setMaximumHeight(220)
        
        # تاریخ شمسی
        jalali_date = jdatetime.date.today()
        date_label = QLabel(jalali_date.strftime("%Y/%m/%d"))
        date_label.setStyleSheet("""
            QLabel {
                color: #475569;
                font-size: 14px;
                text-align: center;
                padding: 5px;
                background: rgba(148, 163, 184, 0.1);
                border-radius: 8px;
            }
        """)
        date_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(date_label)
        
        home_btn = SidebarButton("🏠 صفحه اصلی")
        home_btn.clicked.connect(self._show_dashboard)
        sidebar_layout.addWidget(home_btn)
        
        # دکمه‌های سایدبار
        sidebar_buttons = [
            ("📋 پذیرش بیمار", self._open_admission),
            ("🩻 جواب‌دهی", self._open_answer),
            ("📊 گزارشات", self._show_reports_menu),
            ("👥 مدیریت بیماران", self._open_stub),
            ("💰 مالی", self._open_stub),
            ("⚙️ تنظیمات بیمه", self._open_insurance_settings)
        ]
        
        for text, callback in sidebar_buttons:
            btn = SidebarButton(text)
            btn.clicked.connect(callback)
            sidebar_layout.addWidget(btn)
        
        sidebar_layout.addStretch()
        
        # اطلاعات کاربر
        user_info = QLabel("👤 کاربر: مدیر سیستم")
        user_info.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-size: 12px;
                padding: 5px;
                background: rgba(100, 116, 139, 0.1);
                border-radius: 8px;
                text-align: center;
            }
        """)
        user_info.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(user_info)
        
        main_layout.addWidget(sidebar)

    def _create_content_area(self, main_layout):
        """ایجاد ناحیه محتوای اصلی با stacked widget"""
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8fafc, stop:1 #e2e8f0);
            }
        """)
        
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # ایجاد stacked widget برای مدیریت صفحات
        self.stacked_widget = QStackedWidget()
        
        # صفحه اصلی (دشبورد)
        self.dashboard_page = self._create_dashboard_page()
        self.stacked_widget.addWidget(self.dashboard_page)
        
        content_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(content_frame)

    def refresh_dashboard(self):
        """بروزرسانی کامل اطلاعات داشبورد"""
        try:
            if not hasattr(self, 'dashboard_widgets'):
                return
                
            from qt_db import get_dashboard_stats
            
            # دریافت آمار از دیتابیس
            stats_data = get_dashboard_stats()
            today_patients = stats_data.get('admissions_count', 0)
            active_services = stats_data.get('services_count', 0)
            active_doctors = stats_data.get('doctors_count', 0)
            today_income = stats_data.get('total_income', 0)
            
            def format_number(num):
                if num >= 1000000:
                    return f"{num/1000000:.1f}M"
                elif num >= 1000:
                    return f"{num/1000:.1f}K"
                return str(num)
            
            if len(self.dashboard_widgets) >= 4:
                self.dashboard_widgets[0].update_value(str(today_patients))
                self.dashboard_widgets[1].update_value(str(active_services))
                self.dashboard_widgets[2].update_value(f"{format_number(today_income)}")
                self.dashboard_widgets[3].update_value(str(active_doctors))
            
            # به‌روزرسانی جدول بیماران
            self._load_recent_patients()
            
        except Exception as e:
            print(f"خطا در به‌روزرسانی داشبورد: {e}")

    def _create_dashboard_page(self):
        """ایجاد صفحه دشبورد با اطلاعات واقعی از دیتابیس"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # هدر دشبورد
        header_label = QLabel("داشبورد مدیریت")
        header_label.setStyleSheet("""
            QLabel {
                color: #334155;
                font-size: 28px;
                font-weight: bold;
                padding: 10px 0;
            }
        """)
        layout.addWidget(header_label)
        
        # ویجت‌های دشبورد با اطلاعات واقعی
        dashboard_layout = QHBoxLayout()
        
        if hasattr(self, 'dashboard_widgets'):
            self.dashboard_widgets.clear()
        else:
            self.dashboard_widgets = []

        try:
            from qt_db import get_dashboard_stats
            
            stats_data = get_dashboard_stats()
            today_patients = stats_data.get('admissions_count', 0)
            active_services = stats_data.get('services_count', 0)
            active_doctors = stats_data.get('doctors_count', 0)
            today_income = stats_data.get('total_income', 0)
            
            # قالب‌بندی اعداد
            def format_number(num):
                if num >= 1000000:
                    return f"{num/1000000:.1f}M"
                elif num >= 1000:
                    return f"{num/1000:.1f}K"
                return str(num)
                    
            stats = [
                ("بیماران", str(today_patients), "#ef4444"),
                ("خدمات فعال", str(active_services), "#10b981"),
                ("درآمد کل", f"{format_number(today_income)}", "#f59e0b"),
                ("پزشکان", str(active_doctors), "#3ba2f6")
            ]
            
        except Exception as e:
            print(f"خطا در دریافت آمار داشبورد: {e}")
            # آمار پیش‌فرض در صورت خطا
            stats = [
                ("بیماران", "۰", "#ef4444"),
                ("خدمات فعال", "۰", "#10b981"),
                ("درآمد کل", "۰", "#f59e0b"),
                ("پزشکان", "۰", "#3b82f6")
            ]

        for title, value, color in stats:
            widget_stats = DashboardWidget(title, value, color)
            dashboard_layout.addWidget(widget_stats)
            self.dashboard_widgets.append(widget_stats)
        
        self.dashboard_layout = dashboard_layout
        layout.addLayout(dashboard_layout)

        # جدول آخرین بیماران
        recent_patients_label = QLabel("آخرین بیماران پذیرش شده")
        recent_patients_label.setStyleSheet("""
            QLabel {
                color: #334155;
                font-size: 18px;
                font-weight: bold;
                padding: 10px 0;
            }
        """)
        layout.addWidget(recent_patients_label)

        # ایجاد جدول آخرین بیماران
        self.recent_patients_table = QTableWidget()
        self.recent_patients_table.setColumnCount(5)
        self.recent_patients_table.setHorizontalHeaderLabels([
            "کد پذیرش", "نام", "نام خانوادگی", "تاریخ پذیرش", "پزشک"
        ])

        # پر کردن جدول با داده‌های واقعی
        self._load_recent_patients()

        self.recent_patients_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.recent_patients_table.setAlternatingRowColors(True)
        layout.addWidget(self.recent_patients_table)

        # منوهای سریع
        quick_actions_label = QLabel("دسترسی سریع")
        quick_actions_label.setStyleSheet("""
            QLabel {
                color: #334155;
                font-size: 18px;
                font-weight: bold;
                padding: 10px 0;
            }
        """)
        layout.addWidget(quick_actions_label)

        # دکمه‌های عمل سریع
        quick_actions_layout = QHBoxLayout()

        quick_actions = [
            ("🎯 پذیرش جدید", self._open_admission),
            ("📄 جواب‌دهی", self._open_answer),
            ("📈 گزارش روزانه", lambda: self._open_report("daily")),
            ("👨‍⚕️ مدیریت پزشکان", self._open_doctors)
        ]

        for text, callback in quick_actions:
            btn = ModernButton(text)
            btn.setMinimumWidth(150)
            btn.clicked.connect(callback)
            quick_actions_layout.addWidget(btn)

        layout.addLayout(quick_actions_layout)
        layout.addStretch()

        return widget

    def _load_recent_patients(self):
        """بارگذاری آخرین بیماران از دیتابیس"""
        try:
            from qt_db import list_admissions
        
            recent_patients = list_admissions(10)  # 10 پذیرش آخر
        
            self.recent_patients_table.setRowCount(len(recent_patients))
            self.recent_patients_table.setHorizontalHeaderLabels(["کد پذیرش", "نام", "نام خانوادگی", "تاریخ پذیرش", "پزشک"])
        
            for row, patient in enumerate(recent_patients):
                # ============================================
                # 🔽 همه را به str تبدیل کن
                # ============================================
                self.recent_patients_table.setItem(row, 0, QTableWidgetItem(str(patient.get('code', ''))))
                self.recent_patients_table.setItem(row, 1, QTableWidgetItem(str(patient.get('first_name', ''))))
                self.recent_patients_table.setItem(row, 2, QTableWidgetItem(str(patient.get('last_name', ''))))
                self.recent_patients_table.setItem(row, 3, QTableWidgetItem(str(patient.get('admission_date', ''))))
            
                doctor_name = patient.get('doctor_name', '')
                if not doctor_name or doctor_name == 'نامشخص':
                    doctor_id = patient.get('doctor_id')
                    if doctor_id:
                        from qt_db import get_doctor_by_id
                        doctor = get_doctor_by_id(doctor_id)
                        if doctor:
                            doctor_name = f"{doctor.get('name', '')} {doctor.get('family', '')}".strip()
                            if not doctor_name:
                                doctor_name = doctor.get('name', '') or doctor.get('family', '') or 'پزشک'
                        else:
                            doctor_name = 'پزشک'
                    else:
                        doctor_name = 'پزشک'
                self.recent_patients_table.setItem(row, 4, QTableWidgetItem(str(doctor_name)))
            
        except Exception as e:
            print(f"خطا در بارگذاری بیماران اخیر: {e}")
            self.recent_patients_table.setRowCount(0)
    def _show_dashboard(self):
        """نمایش صفحه اصلی"""
        if self.stacked_widget:
            self.refresh_dashboard()
            self.stacked_widget.setCurrentWidget(self.dashboard_page)

    def _add_page_to_stack(self, widget, title):
        """اضافه کردن صفحه جدید به stack"""
        # اگر ویجت قبلاً در stack هست، اون رو نشون بده
        for i in range(self.stacked_widget.count()):
            if self.stacked_widget.widget(i) == widget:
                self.stacked_widget.setCurrentWidget(widget)
                return
        
        # اگر جدید هست، اضافه کن و نشون بده
        self.stacked_widget.addWidget(widget)
        self.stacked_widget.setCurrentWidget(widget)

    def _create_radiology_menu(self, menubar):
        m_rad = menubar.addMenu("🩻 رادیولوژی")
        actions = [
            ("📋 پذیرش رادیولوژی", self._open_admission),
            ("📄 جواب‌دهی رادیولوژی", self._open_answer)
        ]
        self._add_menu_actions(m_rad, actions)

    def _create_reports_menu(self, menubar):
        m_reports = menubar.addMenu("📊 گزارشات")
        report_actions = [
            ("📊 گزارش آماری روزانه", "daily"),
            ("📋 گزارش کلی", "general"),
            ("🩺 گزارش آمار خدمات انجام شده", "services"), 
            ("🗑️ گزارش بیماران حذف و انجام نشده", "deleted"),
            ("👥 گزارش آمار مراجعات انجام شده", "visits"),
            ("👤 گزارش مراجعات به تفکیک کاربر", "user_visits"),
            ("🏥 گزارش مراجعات یک بیمار", "patient_visits"),
            ("💰 گزارش صندوق", "cash"),
            ("💳 گزارش صندوق بر اساس کاربر", "user_cash"),
            ("📈 گزارش درآمد رادیولوژی", "income"),
            ("⚖️ گزارش اضافات و کسورات بر اساس پزشک", "doctor_adjustments")
        ]
        
        for title, report_type in report_actions:
            act = QAction(title, self)
            act.triggered.connect(lambda checked, rt=report_type: self._open_report(rt))
            m_reports.addAction(act)

    def _create_system_menu(self, menubar):
        m_defs = menubar.addMenu("⚙️ ساختار سیستم")
        actions = [
            ("📁 مدیریت گروه‌ها", self._open_groups),
            ("🩺 مدیریت خدمات", self._open_services),
            ("👨‍⚕️ مدیریت پزشکان", self._open_doctors),
            ("📝 قالب‌های جواب", self._open_templates),
            ("💰 تعرفه‌ها", self._open_tariff_upload)
        ]
        self._add_menu_actions(m_defs, actions)

    def _create_tools_menu(self, menubar):
        m_tools = menubar.addMenu("🔧 امکانات سیستم")
        actions = [
            ("📊 تنظیم درصد بیمه", self._open_insurance_settings),
            ("🛡️ مدیریت دسترسی", self._open_permissions),
            ("💾 پشتیبان‌گیری", self._open_backup),
            ("🔄 بازیابی اطلاعات", self._open_restore), 
        ]
        for text, slot in actions:
            action = QAction(text, self)
            action.triggered.connect(slot)
            m_tools.addAction(action)
        
        # بخش‌های در دست توسعه
        for title in [
            "ℹ️ درباره نرم‌افزار",
            "🖨️ تنظیمات پرینتر",
            "🔖 نسخه نرم‌افزار",
            "⚙️ تنظیم سیستم جاری"
        ]:
            act = QAction(title, self)
            act.triggered.connect(lambda _, t=title: self._open_stub(t))
            m_tools.addAction(act)

    def _open_backup(self):
        """پشتیبان‌گیری از همه دیتابیس‌ها"""
        try:
            current_dir = os.getcwd()
            backup_dir = os.path.join(current_dir, 'backups')
            
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # لیست دیتابیس‌ها
            databases = {
                'config': 'config.db',
                'patients': 'patients.db',
                'templates': 'templates.db', 
                'reports': 'reports.db',
                'financial': 'financial.db'
            }
            
            results = []
            for db_name in databases.keys():
                db_path = os.path.join(current_dir, 'data', f"{db_name}.db")
                
                if os.path.exists(db_path):
                    backup_file = os.path.join(backup_dir, f"backup_{db_name}_{timestamp}.db")
                    shutil.copy2(db_path, backup_file)
                    results.append(f"✅ {db_name}")
                else:
                    results.append(f"❌ {db_name} (پیدا نشد)")
            
            message = "نتایج پشتیبان‌گیری:\n\n" + "\n".join(results)
            QMessageBox.information(self, "📊 نتیجه پشتیبان‌گیری", message)
            
        except Exception as e:
            QMessageBox.critical(self, "❌ خطا", f"خطا: {str(e)}")

    def _open_restore(self):
        """بازیابی دیتابیس‌ها"""
        try:
            current_dir = os.getcwd()
            backup_dir = os.path.join(current_dir, 'backups')
            
            if not os.path.exists(backup_dir):
                QMessageBox.warning(self, "خطا", "پوشه backups وجود ندارد")
                return
            
            # پیدا کردن آخرین پشتیبان
            backup_files = {}
            for file in os.listdir(backup_dir):
                if file.startswith("backup_") and file.endswith(".db"):
                    parts = file.replace("backup_", "").replace(".db", "").split("_")
                    if len(parts) >= 2:
                        db_name = parts[0]
                        timestamp_str = "_".join(parts[1:])
                        file_path = os.path.join(backup_dir, file)
                        
                        if db_name not in backup_files or timestamp_str > backup_files[db_name]['timestamp']:
                            backup_files[db_name] = {
                                'path': file_path,
                                'timestamp': timestamp_str
                            }
            
            if not backup_files:
                QMessageBox.information(self, "اطلاع", "هیچ پشتیبانی برای بازیابی وجود ندارد")
                return
            
            # تایید بازیابی
            db_list = "\n".join([f"• {db_name}" for db_name in backup_files.keys()])
            reply = QMessageBox.question(
                self, "تایید بازیابی",
                f"آیا از بازیابی اطمینان دارید؟\n\nدیتابیس‌ها:\n{db_list}",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                for db_name, backup_info in backup_files.items():
                    target_db = os.path.join(current_dir, 'data', f"{db_name}.db")
                    shutil.copy2(backup_info['path'], target_db)
                
                QMessageBox.information(self, "✅ موفق", "بازیابی انجام شد")
                
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا: {str(e)}")

    def _open_permissions(self):
        """باز کردن پنجره مدیریت دسترسی‌ها"""
        try:
            from qt_permissions import UsersDialog
            dlg = UsersDialog(self)
            dlg.exec_()
        except Exception as e:
            print(f"خطا در باز کردن مدیریت دسترسی: {e}")

    def _add_menu_actions(self, menu, actions):
        for title, callback in actions:
            act = QAction(title, self)
            act.triggered.connect(callback)
            menu.addAction(act)

    def _show_reports_menu(self):
        """نمایش منوی گزارشات در سایدبار"""
        self._open_report("daily")

    def _create_menu(self):
        """ایجاد منوی اصلی با استایل مدرن"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background: #ffffff;
                color: #334155;
                border-bottom: 2px solid #e2e8f0;
                padding: 5px;
            }
            
            QMenuBar::item {
                background: transparent;
                padding: 8px 15px;
                border-radius: 5px;
                margin: 2px;
            }
            
            QMenuBar::item:selected {
                background: #3b82f6;
                color: white;
            }
        """)
 
        self._create_radiology_menu(menubar)
        self._create_reports_menu(menubar)
        self._create_system_menu(menubar)
        self._create_tools_menu(menubar)

    def _open_admission(self):
        if not hasattr(self, 'admission_form'):
            from qt_admission import AdmissionForm
            self.admission_form = AdmissionForm(self)
        self._add_page_to_stack(self.admission_form, "پذیرش")

    def _open_answer(self):
        try:
            if not hasattr(self, 'answer_form'):
                from qt_report_answer import AnswerForm
                self.answer_form = AnswerForm(self)
            self._add_page_to_stack(self.answer_form, "جواب‌دهی")
        except Exception as e:
            
            QMessageBox.critical(self, "خطا", f"خطا در باز کردن فرم جواب‌دهی:\n{str(e)}")

    def _open_services(self):
        if not hasattr(self, 'services_window'):
            from qt_services import ServicesWindow
            self.services_window = ServicesWindow(self)
        self._add_page_to_stack(self.services_window, "مدیریت خدمات")

    def _open_doctors(self):
        if not hasattr(self, 'doctor_management_window'):
            from doctor_management import DoctorManagementWindow
            self.doctor_management_window = DoctorManagementWindow(self)
        self._add_page_to_stack(self.doctor_management_window, "مدیریت پزشکان")

    def _open_templates(self):
        if not hasattr(self, 'templates_window'):
            from qt_templates import ModernTemplatePicker
            self.templates_window = ModernTemplatePicker(self)
        self._add_page_to_stack(self.templates_window, "مدیریت قالب‌ها")

    def _open_tariff_upload(self):
        if not hasattr(self, 'tariff_window'):
            from qt_tariff_upload import TariffUploadWindow
            self.tariff_window = TariffUploadWindow(self)
        self._add_page_to_stack(self.tariff_window, "تعرفه‌ها")

    def _open_insurance_settings(self):
        from qt_insurance import InsuranceSettingsDialog
        dlg = InsuranceSettingsDialog(self)
        dlg.setStyleSheet(self.styleSheet())
        dlg.exec_()

    def _open_report(self, report_type):
        try:
            from qt_ReportsManager import ReportsManager
            report_dialog = ReportsManager(report_type, self)
            report_dialog.setStyleSheet(self.styleSheet())
            report_dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در باز کردن گزارش:\n{str(e)}")

    def _open_groups(self):
        """باز کردن پنجره مدیریت گروه‌ها"""
        if not hasattr(self, 'groups_window'):
            from qt_groups import GroupsWindow
            self.groups_window = GroupsWindow(self)
        self._add_page_to_stack(self.groups_window, "مدیریت گروه‌ها")

    def _open_stub(self, title: str = "در دست توسعه"):
        msg = QMessageBox(self)
        msg.setWindowTitle("در دست توسعه")
        msg.setText(f"🛠️ این بخش به زودی پیاده‌سازی خواهد شد\n({title})")
        msg.setIcon(QMessageBox.Information)
        msg.exec_()

if __name__ == "__main__":
    main()