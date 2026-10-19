# -*- coding: utf-8 -*-
import os
import sys
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QPushButton, QTextEdit,
    QGroupBox, QMessageBox, QFileDialog, QApplication, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QComboBox, QDialogButtonBox, QFontComboBox, QColorDialog, QFrame,
    QToolBar, QAction
)
from PyQt5.QtCore import Qt, QBuffer, QTimer, QSizeF, QSize
from PyQt5.QtGui import QTextDocument, QFont, QTextCharFormat, QColor, QImage, QIcon,QFontDatabase
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog
from qt_db import (
    list_admissions_with_answer_status,
    get_answer_text,
    upsert_answer,
    delete_answer,
    get_admission_with_items,
)
from qt_templates import ModernTemplatePicker
from date_utils import format_date_jalali
import base64
import sqlite3
import jdatetime
import urllib.parse

# --- منطق مدیریت تنظیمات ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(os.path.dirname(__file__), 'report_settings.json')
if os.path.exists(SETTINGS_PATH):
    
    with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
else:
    print("❌ فایل تنظیمات وجود ندارد!")
DEFAULTS = {
    "header_title1": "مرکز رادیولوژی و سونوگرافی",
    "header_title2": "دکتر یوسف سلطان احمدی",
    "header_subtitle": "متخصص تصویربرداری پزشکی (رادیولوژی)",
    "footer_line": "با تشکر — دکتر یوسف سلطان احمدی",
    "address_line": "آدرس و شماره تماس مرکز",
    "logo_path": os.path.join(os.path.dirname(__file__), "logo.png"),
    "report_font": "Vazirmatn",
    "font_path": "",
    "watermark_text": ""
}

def load_settings() -> dict:
    if not os.path.exists(SETTINGS_PATH):
        
        save_settings(DEFAULTS)
        return DEFAULTS.copy()
    try:
        with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
       
        return data
    except Exception as e:
        print(f"❌ خطا: {e}")
        return DEFAULTS.copy()

def save_settings(data: dict) -> None:
    try:
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
    except Exception as e:
        print(f"❌ خطا در ذخیره: {e}")
# ------------------------------------------------------------------

class AnswerForm(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = load_settings()
        self.setWindowTitle('جواب‌دهی رادیولوژی')
        self.setMinimumSize(800, 600)
        self.resize(1200, 700)
        self.current_admission_id = None
        self._rows = []
        self._index = -1
        self.auto_save_enabled = True
        self.auto_save_timer = QTimer()
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.timeout.connect(self._auto_save)
        
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._reload)
        
        self._build_ui()
        self._reload()
        
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(15000)

    def refresh_data(self):
        if hasattr(self, 'search_input'):
            current_search = self.search_input.text()
            self._search_admissions(current_search)

    def _search_admissions(self, search_text=""):
        try:
            admissions_data = list_admissions_with_answer_status()
            if search_text.strip():
                filtered_admissions = []
                for admission in admissions_data:
                    first_name = self._safe_get(admission, 'first_name')
                    last_name = self._safe_get(admission, 'last_name')
                    code = self._safe_get(admission, 'code')
                    national_id = self._safe_get(admission, 'national_id')
                    name = f"{first_name} {last_name}".strip()
                    if (search_text in code or search_text in name or search_text in national_id):
                        filtered_admissions.append(admission)
                self._rows = filtered_admissions
            else:
                self._rows = admissions_data[:50]
            if hasattr(self, '_load_current_patient'):
                self._load_current_patient()
        except Exception as e:
            print(f"خطا در جستجوی پذیرش‌ها: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در جستجوی پذیرش‌ها: {str(e)}")

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(6, 6, 6, 6)

        # ========== بخش جستجو ==========
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('جستجو بر اساس کد پذیرش یا نام بیمار...')
        self.search_input.textChanged.connect(self._on_search_changed)
        search_btn = QPushButton('جستجو')
        search_btn.setStyleSheet("""
            QPushButton {
                background: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover { background: #106ebe; }
        """)
        search_btn.clicked.connect(self._reload)
        search_layout.addWidget(QLabel('جستجو:'))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        search_layout.addStretch()
        root.addLayout(search_layout)

        # ========== نمایش اطلاعات بیمار ==========
        self.patient_info = QLabel('هیچ بیمار انتخاب نشده است')
        self.patient_info.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 2px solid #0078d4;
                border-radius: 5px;
                padding: 5px;
                font-weight: bold;
                font-size: 10pt;
                color: #1a1a1a;
            }
        """)
        self.patient_info.setAlignment(Qt.AlignCenter)
        root.addWidget(self.patient_info)

        # ========== نوار ناوبری ==========
        nav_layout = QHBoxLayout()
        nav_buttons = [
            ('<< اولین', self._first),
            ('< قبلی', self._prev),
            ('بعدی >', self._next),
            ('آخرین >>', self._last),
        ]
        for text, slot in nav_buttons:
            btn = QPushButton(text)
            btn.setFixedSize(65, 26)
            btn.setStyleSheet("""
                QPushButton {
                    background: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 9px;
                    font-weight: bold;
                }
                QPushButton:hover { background: #5a6268; }
            """)
            btn.clicked.connect(slot)
            nav_layout.addWidget(btn)
        nav_layout.addStretch()
        self.nav_info = QLabel('0/0')
        self.nav_info.setStyleSheet("font-size: 10px; font-weight: bold; color: #1a1a1a;")
        nav_layout.addWidget(self.nav_info)
        root.addLayout(nav_layout)

        # ========== ویرایشگر ==========
        editor_box = QGroupBox('متن جواب')
        editor_layout = QVBoxLayout(editor_box)
        editor_layout.setSpacing(2)
        editor_layout.setContentsMargins(4, 4, 4, 4)

        # ===== نوار ابزار =====
        toolbar = QHBoxLayout()
        toolbar.setSpacing(2)

        # ----- کلیپ بورد -----
        self.copy_btn = QPushButton("کپی")
        self.copy_btn.setFixedSize(38, 26)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover { background: #5a6268; }
        """)
        self.copy_btn.setToolTip("کپی (Ctrl+C)")
        self.copy_btn.clicked.connect(self._copy_text)
        toolbar.addWidget(self.copy_btn)

        self.cut_btn = QPushButton("برش")
        self.cut_btn.setFixedSize(38, 26)
        self.cut_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover { background: #5a6268; }
        """)
        self.cut_btn.setToolTip("برش (Ctrl+X)")
        self.cut_btn.clicked.connect(self._cut_text)
        toolbar.addWidget(self.cut_btn)

        self.paste_btn = QPushButton("چسباندن")
        self.paste_btn.setFixedSize(48, 26)
        self.paste_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover { background: #5a6268; }
        """)
        self.paste_btn.setToolTip("چسباندن (Ctrl+V)")
        self.paste_btn.clicked.connect(self._paste_text)
        toolbar.addWidget(self.paste_btn)

        # جداکننده
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setFixedSize(2, 20)
        toolbar.addWidget(sep)

        # ----- واگرد/بازگردانی -----
        self.undo_btn = QPushButton("واگرد")
        self.undo_btn.setFixedSize(42, 26)
        self.undo_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover { background: #5a6268; }
        """)
        self.undo_btn.setToolTip("واگرد (Ctrl+Z)")
        self.undo_btn.clicked.connect(self._undo)
        toolbar.addWidget(self.undo_btn)

        self.redo_btn = QPushButton("بازگرد")
        self.redo_btn.setFixedSize(45, 26)
        self.redo_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover { background: #5a6268; }
        """)
        self.redo_btn.setToolTip("بازگردانی (Ctrl+Y)")
        self.redo_btn.clicked.connect(self._redo)
        toolbar.addWidget(self.redo_btn)

        # جداکننده
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setFixedSize(2, 20)
        toolbar.addWidget(sep)

        # ----- فونت و سایز -----
        toolbar.addWidget(QLabel("فونت:"))
        self.font_combo = QFontComboBox()
        self.font_combo.setFixedHeight(22)
        self.font_combo.setMaximumWidth(90)
        self.font_combo.setStyleSheet("font-size: 9px;")
        self.font_combo.currentFontChanged.connect(self._on_font_changed)
        toolbar.addWidget(self.font_combo)

        toolbar.addWidget(QLabel("سایز:"))
        self.size_combo = QComboBox()
        self.size_combo.addItems(['8', '9', '10', '11', '12', '14', '16', '18', '20', '24'])
        self.size_combo.setCurrentText('12')
        self.size_combo.setFixedHeight(22)
        self.size_combo.setMaximumWidth(45)
        self.size_combo.currentTextChanged.connect(self._on_size_changed)
        toolbar.addWidget(self.size_combo)

        # جداکننده
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setFixedSize(2, 20)
        toolbar.addWidget(sep)

        # ----- استایل B, I, U -----
        self.bold_btn = QPushButton("پررنگ")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setFixedSize(42, 26)
        self.bold_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:checked { background: #0d6efd; }
            QPushButton:hover { background: #5a6268; }
        """)
        self.bold_btn.setToolTip("پررنگ (Ctrl+B)")
        self.bold_btn.clicked.connect(self._toggle_bold)
        toolbar.addWidget(self.bold_btn)

        self.italic_btn = QPushButton("کج")
        self.italic_btn.setCheckable(True)
        self.italic_btn.setFixedSize(38, 26)
        self.italic_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:checked { background: #0d6efd; }
            QPushButton:hover { background: #5a6268; }
        """)
        self.italic_btn.setToolTip("کج (Ctrl+I)")
        self.italic_btn.clicked.connect(self._toggle_italic)
        toolbar.addWidget(self.italic_btn)

        self.underline_btn = QPushButton("زیرخط")
        self.underline_btn.setCheckable(True)
        self.underline_btn.setFixedSize(45, 26)
        self.underline_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:checked { background: #0d6efd; }
            QPushButton:hover { background: #5a6268; }
        """)
        self.underline_btn.setToolTip("زیرخط (Ctrl+U)")
        self.underline_btn.clicked.connect(self._toggle_underline)
        toolbar.addWidget(self.underline_btn)

        # جداکننده
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setFixedSize(2, 20)
        toolbar.addWidget(sep)

        # ----- رنگ -----
        self.color_btn = QPushButton("رنگ")
        self.color_btn.setFixedSize(38, 26)
        self.color_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover { background: #5a6268; }
        """)
        self.color_btn.setToolTip("رنگ متن")
        self.color_btn.clicked.connect(self._choose_color)
        toolbar.addWidget(self.color_btn)

        # جداکننده
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setFixedSize(2, 20)
        toolbar.addWidget(sep)

        # ----- تراز -----
        self.align_left_btn = QPushButton("چپ")
        self.align_left_btn.setFixedSize(32, 26)
        self.align_left_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover { background: #5a6268; }
        """)
        self.align_left_btn.setToolTip("تراز چپ")
        self.align_left_btn.clicked.connect(self._align_left)
        toolbar.addWidget(self.align_left_btn)

        self.align_center_btn = QPushButton("وسط")
        self.align_center_btn.setFixedSize(32, 26)
        self.align_center_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover { background: #5a6268; }
        """)
        self.align_center_btn.setToolTip("تراز وسط")
        self.align_center_btn.clicked.connect(self._align_center)
        toolbar.addWidget(self.align_center_btn)

        self.align_right_btn = QPushButton("راست")
        self.align_right_btn.setFixedSize(32, 26)
        self.align_right_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover { background: #5a6268; }
        """)
        self.align_right_btn.setToolTip("تراز راست")
        self.align_right_btn.clicked.connect(self._align_right)
        toolbar.addWidget(self.align_right_btn)

        toolbar.addStretch()

        # ----- پاک‌سازی -----
        self.clear_format_btn = QPushButton("پاک")
        self.clear_format_btn.setFixedSize(32, 26)
        self.clear_format_btn.setStyleSheet("""
            QPushButton {
                background: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover { background: #c82333; }
        """)
        self.clear_format_btn.setToolTip("پاک‌سازی قالب")
        self.clear_format_btn.clicked.connect(self._clear_formatting)
        toolbar.addWidget(self.clear_format_btn)

        # ===== ویرایشگر =====
        self.editor = QTextEdit()
        self.editor.setAcceptRichText(True)
        self.editor.textChanged.connect(self._on_editor_changed)
        font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'BNazanin.ttf')
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            self.editor.setFont(QFont(font_family, 12))
        else:
            self.editor.setFont(QFont("Vazirmatn", 12))
        self.editor.setLayoutDirection(Qt.RightToLeft)

        # ===== اضافه کردن به ویرایشگر =====
        editor_layout.addLayout(toolbar)
        editor_layout.addWidget(self.editor)

        # ========== دکمه‌های پایین ==========
        button_layout = QHBoxLayout()
        buttons = [
            ('ذخیره', self._save, '#0078d4'),
            ('افزودن تصویر', self._add_image, '#6c757d'),
            ('قالب آماده', self._insert_template, '#6c757d'),
            ('حذف جواب', self._delete_answer, '#dc3545'),
            ('چاپ', self._print, '#6c757d'),
            ('بارگذاری مجدد', self._reload, '#6c757d'),
        ]

        for title, slot, color in buttons:
            btn = QPushButton(title)
            btn.clicked.connect(slot)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 12px;
                    font-size: 9px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ opacity: 0.9; }}
            """)
            btn.setFixedHeight(26)
            button_layout.addWidget(btn)

        self.auto_save_btn = QPushButton('ذخیره خودکار: فعال')
        self.auto_save_btn.clicked.connect(self._toggle_auto_save)
        self.auto_save_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover { background: #218838; }
        """)
        self.auto_save_btn.setFixedHeight(26)
        button_layout.addWidget(self.auto_save_btn)

        settings_btn = QPushButton('تنظیمات')
        settings_btn.clicked.connect(self._open_report_settings)
        settings_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover { background: #5a6268; }
        """)
        settings_btn.setFixedHeight(26)
        button_layout.addWidget(settings_btn)

        button_layout.addStretch()
        editor_layout.addLayout(button_layout)
        root.addWidget(editor_box)
    # ========== توابع نوار ابزار ==========
    def _on_font_changed(self, font):
        self.editor.setCurrentFont(font)

    def _on_size_changed(self, size):
        if size:
            self.editor.setFontPointSize(float(size))

    def _toggle_bold(self):
        if self.bold_btn.isChecked():
            self.editor.setFontWeight(QFont.Bold)
        else:
            self.editor.setFontWeight(QFont.Normal)

    def _toggle_italic(self):
        self.editor.setFontItalic(self.italic_btn.isChecked())

    def _toggle_underline(self):
        self.editor.setFontUnderline(self.underline_btn.isChecked())

    def _choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.editor.setTextColor(color)

    def _clear_formatting(self):
        cursor = self.editor.textCursor()
        cursor.select(cursor.Document)
        cursor.setCharFormat(QTextCharFormat())
        self.editor.setTextCursor(cursor)
    def _copy_text(self):
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            clipboard = QApplication.clipboard()
            clipboard.setText(cursor.selectedText())

    def _cut_text(self):
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            clipboard = QApplication.clipboard()
            clipboard.setText(cursor.selectedText())
            cursor.removeSelectedText()

    def _paste_text(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.editor.insertPlainText(text)

    def _undo(self):
        self.editor.undo()

    def _redo(self):
        self.editor.redo()

    def _align_left(self):
        self.editor.setAlignment(Qt.AlignLeft)

    def _align_center(self):
        self.editor.setAlignment(Qt.AlignCenter)

    def _align_right(self):
        self.editor.setAlignment(Qt.AlignRight)
    # ========== توابع دیگر ==========
    def _on_search_changed(self):
        self.search_timer.start(800)

    def _on_editor_changed(self):
        if self.auto_save_enabled and self.current_admission_id:
            self.auto_save_timer.start(3000)

    def _toggle_auto_save(self):
        self.auto_save_enabled = not self.auto_save_enabled
        if self.auto_save_enabled:
            self.auto_save_btn.setText('ذخیره خودکار: فعال')
        else:
            self.auto_save_btn.setText('ذخیره خودکار: غیرفعال')

    def _auto_save(self):
        if self.current_admission_id and self.auto_save_enabled:
            body_html = self.editor.toHtml()
            upsert_answer(self.current_admission_id, body_html)
            self._update_nav_info()

    def _safe_get(self, row, key, default=''):
        try:
            if hasattr(row, 'keys') and callable(row.keys):
                keys = row.keys()
                if key in keys:
                    return row[key] or default
                else:
                    return default
            else:
                return row.get(key, default) or default
        except (KeyError, AttributeError, TypeError):
            return default

    def _reload(self):
        try:
            self._rows = list_admissions_with_answer_status()
            self._rows.sort(key=lambda x: x.get('admission_date', ''), reverse=True)
            q = self.search_input.text().strip()
            if q:
                filtered_rows = []
                for row in self._rows:
                    first_name = self._safe_get(row, 'first_name')
                    last_name = self._safe_get(row, 'last_name')
                    code = self._safe_get(row, 'code')
                    name = f"{first_name} {last_name}".strip()
                    if q in code or q in name:
                        filtered_rows.append(row)
                self._rows = filtered_rows
            if self._rows:
                current_id = self.current_admission_id
                if current_id:
                    for i, row in enumerate(self._rows):
                        if self._safe_get(row, 'id') == current_id:
                            self._index = i
                            break
                    else:
                        self._index = 0
                else:
                    self._index = 0
                self._load_current_patient()
            else:
                self._index = -1
                self.current_admission_id = None
                self.editor.clear()
                self.patient_info.setText('هیچ بیمار یافت نشد')
                self.nav_info.setText('0/0')
        except Exception as e:
            QMessageBox.critical(self, 'خطا', f'خطا در بارگذاری داده‌ها: {str(e)}')

    def _load_current_patient(self):
        if self._index < 0 or self._index >= len(self._rows):
            return
        row = self._rows[self._index]
        self.current_admission_id = self._safe_get(row, 'id')
        first_name = self._safe_get(row, 'first_name')
        last_name = self._safe_get(row, 'last_name')
        name = f"{first_name} {last_name}".strip()
        code = self._safe_get(row, 'code')
        admission_date = self._safe_get(row, 'admission_date')
        date_jalali = format_date_jalali(admission_date)
        time = self._safe_get(row, 'admission_time')
        insurance = self._safe_get(row, 'insurance_name', 'بدون بیمه')
        status = self._safe_get(row, 'status', 'unknown')
        doctor_first = self._safe_get(row, 'doctor_first_name')
        doctor_last = self._safe_get(row, 'doctor_last_name')
        doctor_full = self._safe_get(row, 'doctor_full_name')
        doctor_gender = self._safe_get(row, 'doctor_gender', 'male')
        doctor_name = doctor_full if doctor_full else f"{doctor_first} {doctor_last}".strip()
        if doctor_name and doctor_name != 'نامشخص':
            if doctor_gender in ['female', 'زن', 'ز', 'خانم', 'F', 'f']:
                doctor_name = f"خانم دکتر {doctor_name}"
            else:
                doctor_name = f"آقای دکتر {doctor_name}"
        info_text = f"""
        بیمار: <font color="#0078d4"><b>{name}</b></font> | 
        کد پذیرش: <font color="#107c10"><b>{code}</b></font> | 
        تاریخ: <b>{date_jalali}</b> | 
        پزشک ارجاع دهنده: <b>{doctor_name}</b> |
        ساعت: <b>{time}</b> | 
        بیمه: <b>{insurance}</b> | 
        وضعیت: <b>{'دارای جواب' if status == 'answered' else 'بدون جواب'}</b>
        """
        self.patient_info.setText(info_text)
        txt = get_answer_text(self.current_admission_id)
        if txt:
            self.editor.setHtml(txt)
        else:
            self.editor.clear()
        self._update_nav_info()

    def _update_nav_info(self):
        if self._rows:
            total = len(self._rows)
            current = self._index + 1
            self.nav_info.setText(f'{current}/{total}')
        else:
            self.nav_info.setText('0/0')

    def _first(self):
        if self._rows:
            self._index = len(self._rows) - 1
            self._load_current_patient()

    def _prev(self):
        if self._rows and self._index < len(self._rows) - 1:
            self._index += 1
            self._load_current_patient()

    def _next(self):
        if self._rows and self._index > 0:
            self._index -= 1
            self._load_current_patient()

    def _last(self):
        if self._rows:
            self._index = 0
            self._load_current_patient()

    def _save(self):
        if not self.current_admission_id:
            QMessageBox.warning(self, 'ذخیره', 'هیچ بیمار انتخاب نشده است.')
            return
        try:
            body_html = self.editor.toHtml()
            upsert_answer(self.current_admission_id, body_html)
            QMessageBox.information(self, 'ذخیره', 'جواب با موفقیت ذخیره شد.')
            self._reload()
        except Exception as e:
            QMessageBox.critical(self, 'خطا', f'خطا در ذخیره جواب: {str(e)}')

    def _add_image(self):
        path, _ = QFileDialog.getOpenFileName(self, 'انتخاب تصویر', '', 'Images (*.png *.jpg *.jpeg *.bmp)')
        if not path:
            return
        img = QImage(path)
        if img.isNull():
            QMessageBox.warning(self, 'تصویر', 'بارگذاری تصویر ناموفق بود.')
            return
        if img.width() > 200:
            img = img.scaledToWidth(200, Qt.SmoothTransformation)
        buf = QBuffer()
        buf.open(QBuffer.WriteOnly)
        img.save(buf, 'PNG')
        b64 = base64.b64encode(bytes(buf.data())).decode('ascii')
        data_uri = f"data:image/png;base64,{b64}"
        self.editor.insertHtml(f"<p><img src='{data_uri}' /></p>")

    def _insert_template(self):
        dlg = ModernTemplatePicker(self)
        if dlg.exec_() == dlg.Accepted and dlg.selected_text:
            self.editor.insertHtml(dlg.selected_text)

    def _delete_answer(self):
        if not self.current_admission_id:
            return
        reply = QMessageBox.question(self, 'حذف جواب', 'آیا از حذف جواب این بیمار مطمئن هستید؟', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            delete_answer(self.current_admission_id)
            self.editor.clear()
            self._reload()

    def _print(self):
        if not self.current_admission_id:
            QMessageBox.warning(self, 'چاپ', 'هیچ بیمار انتخاب نشده است.')
            return
        try:
            data = get_admission_with_items(self.current_admission_id)
            adm = data.get('admission', {})
            body_html = self.editor.toHtml()
            class PageSizeDialog(QDialog):
                def __init__(self, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle('انتخاب سایز چاپ')
                    self.setModal(True)
                    self.setMinimumWidth(300)
                    layout = QVBoxLayout(self)
                    layout.addWidget(QLabel('سایز صفحه را انتخاب کنید:'))
                    self.size_combo = QComboBox()
                    self.size_combo.addItems(['A4', 'A5'])
                    layout.addWidget(self.size_combo)
                    button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                    button_box.accepted.connect(self.accept)
                    button_box.rejected.connect(self.reject)
                    layout.addWidget(button_box)
                    self.setLayout(layout)
            dialog = PageSizeDialog(self)
            if dialog.exec_() != QDialog.Accepted:
                return
            selected_size = dialog.size_combo.currentText()
            html = self._build_report_html(adm, body_html, selected_size)
            doc = QTextDocument()
            doc.setHtml(html)
            printer = QPrinter()
            if selected_size == 'A4':
                printer.setPageSize(QPrinter.A4)
            else:
                printer.setPageSize(QPrinter.A5)
            printer.setPageMargins(8, 5, 8, 5, QPrinter.Millimeter)
            page_size = printer.pageRect().size()
            doc.setPageSize(QSizeF(page_size))
            dlg = QPrintPreviewDialog(printer, self)
            dlg.setWindowTitle(f'پیش‌نمایش چاپ - {selected_size}')
            dlg.paintRequested.connect(lambda p: doc.print_(p))
            dlg.exec_()
        except Exception as e:
            print(f"❌ خطای چاپ: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, 'خطای چاپ', f'خطا در آماده‌سازی چاپ: {str(e)}')

    def _open_report_settings(self):
        class ReportSettingsDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.settings = load_settings()
                self.setWindowTitle('تنظیمات گزارش')
                self.setMinimumWidth(500)
                self._setup_ui()
            def _setup_ui(self):
                layout = QVBoxLayout(self)
                form_layout = QFormLayout()
                self.title1_edit = QLineEdit()
                self.title1_edit.setText(self.settings.get('header_title1', ''))
                form_layout.addRow('عنوان اول:', self.title1_edit)
                self.title2_edit = QLineEdit()
                self.title2_edit.setText(self.settings.get('header_title2', ''))
                form_layout.addRow('عنوان دوم:', self.title2_edit)
                self.subtitle_edit = QLineEdit()
                self.subtitle_edit.setText(self.settings.get('header_subtitle', ''))
                form_layout.addRow('زیرعنوان:', self.subtitle_edit)
                self.footer_edit = QLineEdit()
                self.footer_edit.setText(self.settings.get('footer_line', ''))
                form_layout.addRow('خط فوتر:', self.footer_edit)
                self.address_edit = QLineEdit()
                self.address_edit.setText(self.settings.get('address_line', ''))
                form_layout.addRow('آدرس:', self.address_edit)
                font_layout = QHBoxLayout()
                self.font_edit = QLineEdit()
                self.font_edit.setText(self.settings.get('report_font', 'Vazirmatn'))
                self.font_edit.setReadOnly(True)
                font_btn = QPushButton('انتخاب فونت')
                font_btn.clicked.connect(self._select_font)
                font_layout.addWidget(self.font_edit)
                font_layout.addWidget(font_btn)
                form_layout.addRow('فونت گزارش:', font_layout)
                logo_layout = QHBoxLayout()
                self.logo_edit = QLineEdit()
                self.logo_edit.setText(self.settings.get('logo_path', ''))
                self.logo_edit.setReadOnly(True)
                logo_btn = QPushButton('انتخاب لوگو')
                logo_btn.clicked.connect(self._select_logo)
                logo_layout.addWidget(self.logo_edit)
                logo_layout.addWidget(logo_btn)
                form_layout.addRow('لوگو:', logo_layout)
                self.watermark_edit = QLineEdit()
                self.watermark_edit.setText(self.settings.get('watermark_text', ''))
                form_layout.addRow('متن واترمارک:', self.watermark_edit)
                layout.addLayout(form_layout)
                button_layout = QHBoxLayout()
                save_btn = QPushButton('💾 ذخیره')
                save_btn.clicked.connect(self._save_settings)
                cancel_btn = QPushButton('لغو')
                cancel_btn.clicked.connect(self.reject)
                button_layout.addWidget(save_btn)
                button_layout.addWidget(cancel_btn)
                layout.addLayout(button_layout)
            def _select_font(self):
                font_path, _ = QFileDialog.getOpenFileName(
                    self, 'انتخاب فونت فارسی', '', 
                    'فونت‌های فارسی (*.ttf *.otf);;همه فایل‌ها (*.*)'
                )
                if font_path:
                    # ۱. استخراج نام فونت از اسم فایل
                    font_name = os.path.splitext(os.path.basename(font_path))[0]
        
                    # ۲. اگر اسم فایل شامل BNazanin هست، نام رو به "B Nazanin" تغییر بده
                    if "BNazanin" in font_name or "BNazanin" in font_name:
                        font_name = "B Nazanin"
        
                    # ۳. ذخیره در تنظیمات
                    self.font_edit.setText(font_name)
                    self.settings['report_font'] = font_name  # ← مهم
                    self.settings['font_path'] = font_path
        
                    # ۴. بارگذاری فونت برای استفاده در برنامه
                    font_id = QFontDatabase.addApplicationFont(font_path)
                    if font_id != -1:
                        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
                        self.font_edit.setText(font_family)
                        self.settings['report_font'] = font_family
        
                  
            def _select_logo(self):
                logo_path, _ = QFileDialog.getOpenFileName(self, 'انتخاب لوگو', '', 'تصاویر (*.png *.jpg *.jpeg);;همه فایل‌ها (*.*)')
                if logo_path:
                    self.logo_edit.setText(logo_path)
            def _save_settings(self):
                self.settings['header_title1'] = self.title1_edit.text()
                self.settings['header_title2'] = self.title2_edit.text()
                self.settings['header_subtitle'] = self.subtitle_edit.text()
                self.settings['footer_line'] = self.footer_edit.text()
                self.settings['address_line'] = self.address_edit.text()
                self.settings['report_font'] = self.font_edit.text()
                self.settings['logo_path'] = self.logo_edit.text()
                self.settings['watermark_text'] = self.watermark_edit.text()
                self.settings['font_path'] = self.settings.get('font_path', '')
                if hasattr(self, 'settings') and 'font_path' in self.settings:
                    pass  # قبلاً ذخیره شده
    
                save_settings(self.settings)
               
                self.accept()
        dialog = ReportSettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.settings = load_settings()
            QMessageBox.information(self, 'ذخیره شد', 'تنظیمات گزارش با موفقیت ذخیره شد.')

    def _build_report_html(self, adm, body_html: str, page_size='A4') -> str:
        s = self.settings
        try:
            first_name = adm.get('first_name', '')
            last_name = adm.get('last_name', '')
            code = adm.get('code', '')
            admission_date = adm.get('admission_date', '')
            insurance_name = adm.get('insurance_name', '')
            doctor_id = adm.get('doctor_id')
        except Exception:
            first_name = last_name = code = admission_date = insurance_name = 'خطا در بارگذاری اطلاعات'
            doctor_id = None
        referring_doctor = 'نامشخص'
        if doctor_id:
            try:
                conn = sqlite3.connect('data/config.db')
                cursor = conn.cursor()
                cursor.execute("SELECT name, family, full_name FROM doctors WHERE id = ?", (doctor_id,))
                result = cursor.fetchone()
                conn.close()

                if result:
                    name, family, full_name = result
                    gender = 'male'  # مقدار پیش‌فرض
                    doctor_name = full_name if full_name else f"{name} {family}".strip()
                    if gender in ['female', 'زن', 'ز', 'خانم', 'F', 'f']:
                        referring_doctor = f"خانم دکتر {doctor_name}"
                    else:
                        referring_doctor = f"آقای دکتر {doctor_name}"
            except Exception as e:
                referring_doctor = f"پزشک (ID: {doctor_id})"

        full_name = f"{first_name or ''} {last_name or ''}".strip()
        date = format_date_jalali(admission_date or '')
        ins = insurance_name or ''
        font_name = s.get('report_font', 'B-NAZANIN')
        font_path = s.get('font_path', '')
        font_face = f"@font-face {{font-family: '{font_name}'; src: url('{font_path}');}}" if font_path and os.path.exists(font_path) else ""
        watermark_text = s.get('watermark_text', '')
        watermark_html = ""
        if watermark_text:
            watermark_html = f"""
            <div style='position:absolute; top:50%; left:50%; 
                 transform:translate(-50%,-50%) rotate(-30deg); 
                 font-size:45px; color:rgba(200,200,200,0.12); 
                 font-weight:bold; pointer-events:none; 
                 z-index:0; white-space:nowrap;'>
                {watermark_text}
            </div>
            """
        logo_path = s.get('logo_path', '')
        logo_html = ""
        if logo_path and os.path.exists(logo_path):
            try:
                with open(logo_path, 'rb') as f:
                    logo_data = base64.b64encode(f.read()).decode('utf-8')
                    ext = os.path.splitext(logo_path)[1].lower()
                    mime_type = 'image/png' if ext == '.png' else 'image/jpeg' if ext in ['.jpg', '.jpeg'] else 'image/png'
                    logo_html = f"<img src='data:{mime_type};base64,{logo_data}' style='height:6px; width:auto;'/>"
            except Exception as e:
                print(f"خطا در بارگذاری لوگو: {e}")
        if page_size == 'A5':
            margins = "0mm 1mm"
            body_font = 5
            body_line = 0.9
            pad = "0px"
            mg = "0px"
            header_font = 10
            header_sub_font = 10
            info_font = 10
            title_font = 10
            footer_font = 10
            address_font = 8
            name_limit = 25
            doctor_limit = 35
        else:
            margins = "5mm 8mm"
            header_font = 10
            header_sub_font = 9
            info_font = 8
            title_font = 10
            body_font = 12
            body_line = 1.5
            footer_font = 9
            address_font = 7
            name_limit = 15
            doctor_limit = 25
        logo_left = f"""
        <div style='text-align:left; margin:0; padding:0;'>
            {logo_html if logo_html else ''}
        </div>
        """
        header = f"""
        <div style='text-align:right; margin:-20px 0 0 0; padding:0; line-height:1;'>
            {logo_left}
            <div style='font-size:{header_font}px; font-weight:bold; margin:0; padding:0;'>
                {s.get('header_title1','')}
            </div>
            <div style='font-size:{header_sub_font}px; margin:0; padding:0;'>
                {s.get('header_title2','')}
            </div>
            <div style='font-size:{header_sub_font - 1}px; color:#555; margin:0; padding:0;'>
                {s.get('header_subtitle','')}
            </div>
        </div>
        <hr style='margin: 0;'/>
        <div style='font-size:{info_font}px; text-align:center; margin:0; line-height:1;'>
            <span style='padding:0 1px;'><b>نام:</b> {full_name[:name_limit]}</span>
            <span style='padding:0 1px;'><b>تاریخ:</b> {date}</span>
            <span style='padding:0 1px;'><b>پزشک:</b> {referring_doctor[:doctor_limit]}</span>
        </div>
        """
        body = f"<div style='font-size:{body_font}px; line-height:{body_line}; padding:0; margin:0;'>{body_html}</div>"
        footer = f"""
        <hr style='margin:0;'/>
        <div style='margin-top:0; font-size:{footer_font}px; text-align:left; font-weight:bold;'>
            {s.get('footer_line','')}
        </div>
        <div style='font-size:{address_font}px; color:#666; text-align:center;'>
            {s.get('address_line','')}
        </div>
        """
        watermark_css = ""
        if watermark_text:
            svg_text = f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">
                <text x="50%" y="50%" font-size="40" fill="%23999999" opacity="0.15" 
                      font-weight="bold" text-anchor="middle" dominant-baseline="middle"
                      transform="rotate(-35, 50%, 50%)" font-family="{font_name}, Vazirmatn, sans-serif;">
                    {watermark_text}
                </text>
            </svg>'''
            svg_encoded = urllib.parse.quote(svg_text)
            watermark_css = f"""
            body {{
                background-image: url("data:image/svg+xml,{svg_encoded}");
                background-repeat: repeat;
                background-position: center;
                background-size: 700px 350px;
            }}
            """
        return f"""<html><head><meta charset='utf-8'><style>
            {font_face}
            {watermark_css}
            body {{ 
                margin: {margins}; 
                padding: 0; 
                font-family: '{font_name}', Arial, sans-serif;
            }}      
        </style></head><body>
            {header}
            {body}
            {footer}
        </body></html>"""

    def closeEvent(self, event):
        if self.editor.document().isModified():
            reply = QMessageBox.question(self, 'خروج', 'تغییرات ذخیره نشده وجود دارد. آیا مطمئن هستید؟', QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                event.ignore()
                return
        event.accept()