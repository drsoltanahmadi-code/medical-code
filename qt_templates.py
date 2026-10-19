# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel, 
    QLineEdit, QComboBox, QGroupBox, QSplitter, QMessageBox, QWidget, 
    QMenu, QFileDialog, QInputDialog, QListWidget, QListWidgetItem,
    QProgressBar, QShortcut, QCheckBox, QSpinBox, QToolBar, QAction,
    QFontComboBox, QColorDialog, QToolButton,QToolButton
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QKeySequence, QColor, QTextCharFormat, QTextCursor
from qt_db import (
    list_report_templates, delete_report_template, insert_report_template, 
    update_report_template, get_subgroups, add_subgroup, delete_subgroup,
    update_template_subgroup
)
import os
import re
from datetime import datetime

class ModernTemplatePicker(QDialog):
    template_selected = pyqtSignal(str, str)  # text, template_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('📋 کتابخانه قالب‌های آماده گزارش - پیشرفته')
        self.resize(1400, 750)
        self.setMinimumSize(1200, 650)
        self.selected_text = ''
        self.selected_template_name = ''
        self.current_template_id = None
        self.recent_templates = []
        self.favorite_templates = []
        self._is_inserting = False
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self._setup_styles()
        self._build_ui()
        self._setup_shortcuts()
        self._load_templates()
        self._refresh_subgroups()
        self._load_user_preferences()

    def _setup_styles(self):
        """تنظیم استایل‌های مدرن"""
        self.setStyleSheet("""
        QDialog { 
            background: #f5f6fa; 
            font-family: 'Tahoma', 'Segoe UI'; 
        }
        QGroupBox { 
            font-weight: bold; 
            border: 2px solid #dcdde1; 
            border-radius: 8px; 
            margin-top: 10px; 
            padding: 10px;
            background: white;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
            color: #2c3e50;
        }
        QListWidget { 
            border: 2px solid #dcdde1; 
            border-radius: 8px;
            padding: 5px;
            background: white;
            font-size: 11px;
        }
        QListWidget::item {
            padding: 8px;
            border-radius: 4px;
        }
        QListWidget::item:selected {
            background: #3498db;
            color: white;
        }
        QListWidget::item:hover {
            background: #ecf0f1;
        }
        QTextEdit { 
            border: 2px solid #3498db; 
            border-radius: 10px;
            padding: 20px;
            background: #fafafa;
            font-size: 13pt;
            line-height: 1.8;
        }
        QTextEdit:focus {
            border-color: #1abc9c;
            background: white;
        }
        QLineEdit, QComboBox { 
            border: 2px solid #dcdde1; 
            border-radius: 6px;
            padding: 8px;
            font-size: 12px;
            background: white;
        }
        QLineEdit:focus, QComboBox:focus {
            border-color: #3498db;
        }
        QPushButton { 
            border: none; 
            border-radius: 6px; 
            padding: 8px 15px;
            font-weight: bold;
            font-size: 12px;
            background: #3498db;
            color: white;
        }
        QPushButton:hover {
            background: #2980b9;
        }
        QPushButton#btn_delete {
            background: #e74c3c;
        }
        QPushButton#btn_delete:hover {
            background: #c0392b;
        }
        QPushButton#btn_save {
            background: #27ae60;
        }
        QPushButton#btn_save:hover {
            background: #229954;
        }
        QPushButton#btn_insert {
            background: #2ecc71;
            font-size: 14px;
            padding: 12px 25px;
        }
        QPushButton#btn_insert:hover {
            background: #27ae60;
        }
        QToolBar {
            background: #ecf0f1;
            border: 1px solid #bdc3c7;
            border-radius: 6px;
            padding: 2px;
            spacing: 2px;
        }
        QToolButton {
            border: 1px solid transparent;
            border-radius: 4px;
            padding: 3px;
            margin: 1px;
            background: transparent;
        }
        QToolButton:hover {
            background: #d5dbdb;
            border: 1px solid #bdc3c7;
        }
        QToolButton:checked {
            background: #3498db;
            color: white;
            border: 1px solid #2980b9;
        }
        QLabel {
            color: #2c3e50;
        }
        QProgressBar {
            border: 2px solid #3498db;
            border-radius: 5px;
            text-align: center;
        }
        QProgressBar::chunk {
            background: #3498db;
            border-radius: 3px;
        }
    """)

    def _build_ui(self):
        """ساخت رابط کاربری پیشرفته"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # هدر اصلی
        header_layout = self._create_header()
        main_layout.addLayout(header_layout)

        # نوار جستجو و فیلتر
        search_group = self._create_search_panel()
        main_layout.addWidget(search_group)

        # بخش اصلی با اسپلیتر (تمام فضای باقیمانده)
        main_splitter = self._create_main_splitter()
        main_layout.addWidget(main_splitter, 3)

        # نوار وضعیت
        status_layout = self._create_status_bar()
        main_layout.addLayout(status_layout)

        # نوار ابزار پایین
        toolbar_layout = self._create_bottom_toolbar()
        main_layout.addLayout(toolbar_layout)

    def _create_header(self):
        """ایجاد هدر ساده"""
        layout = QHBoxLayout()
        
        title_label = QLabel('📚 کتابخانه هوشمند قالب‌های گزارش پزشکی')
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #1abc9c;
                padding: 5px;
            }
        """)
        
        layout.addWidget(title_label)
        layout.addStretch()
        
        # دکمه‌های سریع
        btn_favorites = QPushButton('⭐ موارد دلخواه')
        btn_favorites.clicked.connect(self._show_favorites)
        btn_favorites.setMaximumWidth(120)
        
        btn_recent = QPushButton('🕒 اخیر')
        btn_recent.clicked.connect(self._show_recent)
        btn_recent.setMaximumWidth(100)
        
        btn_stats = QPushButton('📊 آمار')
        btn_stats.clicked.connect(self._show_statistics)
        btn_stats.setMaximumWidth(100)
        
        layout.addWidget(btn_favorites)
        layout.addWidget(btn_recent)
        layout.addWidget(btn_stats)
        
        return layout

    def _create_search_panel(self):
        """ایجاد پنل جستجو"""
        group = QGroupBox("🔍 جستجو و فیلتر")
        layout = QHBoxLayout(group)
        
        layout.addWidget(QLabel('📂 دسته:'))
        self.category_filter = QComboBox()
        self.category_filter.setMinimumWidth(120)
        self._load_categories_to_filter()
        self.category_filter.currentIndexChanged.connect(self._on_category_changed)
        
        btn_manage_cat = QPushButton('⚙️')
        btn_manage_cat.setToolTip('مدیریت دسته‌بندی‌ها')
        btn_manage_cat.clicked.connect(self._manage_categories)
        btn_manage_cat.setMaximumWidth(40)
        
        layout.addWidget(QLabel('🏷️ زیرگروه:'))
        self.subgroup_filter = QComboBox()
        self.subgroup_filter.setMinimumWidth(120)
        self.subgroup_filter.currentIndexChanged.connect(self._load_templates)
        
        btn_manage_sub = QPushButton('⚙️')
        btn_manage_sub.setToolTip('مدیریت زیرگروه‌ها')
        btn_manage_sub.clicked.connect(self._manage_subgroups)
        btn_manage_sub.setMaximumWidth(40)
        
        layout.addWidget(QLabel('🔎 جستجو:'))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('جستجو در قالب‌ها...')
        self.search_input.textChanged.connect(self._on_search_changed)
        
        layout.addWidget(self.category_filter)
        layout.addWidget(btn_manage_cat)
        layout.addWidget(self.subgroup_filter)
        layout.addWidget(btn_manage_sub)
        layout.addWidget(self.search_input, 2)
        
        return group

    def _load_categories_to_filter(self):
        """بارگذاری دسته‌بندی‌ها"""
        self.category_filter.clear()
        self.category_filter.addItem('📂 همه دسته‌ها', 'all')
    
        try:
            templates = list_report_templates()
            existing_categories = set(t.get('category', '') for t in templates if t.get('category'))
            for category in sorted(existing_categories):
                self.category_filter.addItem(f'📂 {category}', category)
        except Exception as e:
            pass

    def _create_main_splitter(self):
        """ایجاد اسپلیتر اصلی با پیش‌نمایش بزرگ"""
        splitter = QSplitter(Qt.Horizontal)
        
        # پنل چپ - لیست قالب‌ها (کوچک)
        left_panel = self._create_left_panel()
        left_panel.setMaximumWidth(350)
        splitter.addWidget(left_panel)

        # پنل راست - پیش‌نمایش (بزرگ)
        right_panel = self._create_preview_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([300, 1100])
        splitter.setHandleWidth(2)
        
        return splitter

    def _create_left_panel(self):
        """ایجاد پنل چپ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 5, 0)
        layout.setSpacing(3)
        
        # تب‌ها
        tabs_widget = QWidget()
        tabs_layout = QHBoxLayout(tabs_widget)
        tabs_layout.setContentsMargins(0, 0, 0, 0)
        tabs_layout.setSpacing(1)
        
        tabs = [
            ('📋 همه', self._show_all_templates),
            ('⭐ دلخواه', self._show_favorites),
            ('🕒 اخیر', self._show_recent),
        ]
        
        self.tab_buttons = {}
        for text, slot in tabs:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            btn.setCheckable(True)
            btn.setMaximumHeight(28)
            btn.setStyleSheet("""
                QPushButton {
                    background: #ecf0f1;
                    color: #2c3e50;
                    border: 1px solid #bdc3c7;
                    padding: 3px 6px;
                    font-size: 10px;
                }
                QPushButton:checked {
                    background: #3498db;
                    color: white;
                }
            """)
            tabs_layout.addWidget(btn)
            self.tab_buttons[text] = btn
        
        if tabs:
            self.tab_buttons[tabs[0][0]].setChecked(True)
        
        layout.addWidget(tabs_widget)
        
        # لیست قالب‌ها
        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self._on_template_selected)
        self.template_list.itemDoubleClicked.connect(self._insert_and_close)
        self.template_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.template_list.customContextMenuRequested.connect(self._show_context_menu)
        
        layout.addWidget(self.template_list)
        
        return widget

    def _create_preview_panel(self):
        """ایجاد پنل پیش‌نمایش با ابزارهای ویرایش متن"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 0, 0, 0)
        layout.setSpacing(5)
        
        # نوار ابزار ویرایش متن (مانند ورد)
        format_toolbar = self._create_text_format_toolbar()
        layout.addWidget(format_toolbar)
        
        # پیش‌نمایش بزرگ
        self.preview = QTextEdit()
        self.preview.setPlaceholderText('👈 یک قالب از لیست سمت چپ انتخاب کنید...')
        self.preview.setReadOnly(False)
        self.preview.setAcceptRichText(True)  # قبول متن غنی برای فرمت‌بندی
        
        font = QFont("Tahoma", 13)
        self.preview.setFont(font)
        
        layout.addWidget(self.preview, 1)
        
        # اطلاعات قالب
        self.template_info = QLabel('ℹ️ هیچ قالبی انتخاب نشده است')
        self.template_info.setStyleSheet("""
            QLabel {
                background: #f39c12;
                border-radius: 6px;
                padding: 6px;
                color: white;
                font-size: 11px;
            }
        """)
        self.template_info.setMaximumHeight(60)
        layout.addWidget(self.template_info)
        
        return widget

    def _create_text_format_toolbar(self):
        """ایجاد نوار ابزار فرمت‌بندی متن شبیه ورد"""
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        
        # فونت
        self.font_combo = QFontComboBox()
        self.font_combo.setMaximumWidth(150)
        self.font_combo.setCurrentFont(QFont("Tahoma"))
        self.font_combo.currentFontChanged.connect(self._change_font)
        toolbar.addWidget(self.font_combo)
        
        # سایز فونت
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 48)
        self.font_size.setValue(13)
        self.font_size.setMaximumWidth(50)
        self.font_size.valueChanged.connect(self._change_font_size)
        toolbar.addWidget(self.font_size)
        
        toolbar.addSeparator()
        
        # Bold
        btn_bold = QToolButton()
        btn_bold.setText("B")
        btn_bold.setToolTip("Bold (Ctrl+B)")
        btn_bold.setCheckable(True)
        btn_bold.clicked.connect(lambda: self._toggle_format('bold'))
        btn_bold.setStyleSheet("font-weight: bold; font-size: 14px;")
        toolbar.addWidget(btn_bold)
        
        # Italic
        btn_italic = QToolButton()
        btn_italic.setText("I")
        btn_italic.setToolTip("Italic (Ctrl+I)")
        btn_italic.setCheckable(True)
        btn_italic.clicked.connect(lambda: self._toggle_format('italic'))
        btn_italic.setStyleSheet("font-style: italic; font-size: 14px;")
        toolbar.addWidget(btn_italic)
        
        # Underline
        btn_underline = QToolButton()
        btn_underline.setText("U")
        btn_underline.setToolTip("Underline (Ctrl+U)")
        btn_underline.setCheckable(True)
        btn_underline.clicked.connect(lambda: self._toggle_format('underline'))
        btn_underline.setStyleSheet("text-decoration: underline; font-size: 14px;")
        toolbar.addWidget(btn_underline)
        
        # رنگ متن
        btn_color = QToolButton()
        btn_color.setText("🎨")
        btn_color.setToolTip("رنگ متن")
        btn_color.clicked.connect(self._change_text_color)
        toolbar.addWidget(btn_color)
        
        toolbar.addSeparator()
        
        # ترازبندی
        btn_align_right = QToolButton()
        btn_align_right.setText("➡️")
        btn_align_right.setToolTip("راست‌چین")
        btn_align_right.clicked.connect(lambda: self._set_alignment(Qt.AlignRight))
        toolbar.addWidget(btn_align_right)
        
        btn_align_center = QToolButton()
        btn_align_center.setText("⬅️➡️")
        btn_align_center.setToolTip("وسط‌چین")
        btn_align_center.clicked.connect(lambda: self._set_alignment(Qt.AlignCenter))
        toolbar.addWidget(btn_align_center)
        
        btn_align_left = QToolButton()
        btn_align_left.setText("⬅️")
        btn_align_left.setToolTip("چپ‌چین")
        btn_align_left.clicked.connect(lambda: self._set_alignment(Qt.AlignLeft))
        toolbar.addWidget(btn_align_left)
        
        toolbar.addSeparator()
        
        # لیست
        btn_list = QToolButton()
        btn_list.setText("• 📋")
        btn_list.setToolTip("لیست گلوله‌ای")
        btn_list.clicked.connect(self._insert_bullet_list)
        toolbar.addWidget(btn_list)
        
        btn_numbered = QToolButton()
        btn_numbered.setText("1. 📋")
        btn_numbered.setToolTip("لیست شماره‌دار")
        btn_numbered.clicked.connect(self._insert_numbered_list)
        toolbar.addWidget(btn_numbered)
        
        toolbar.addSeparator()
        
        # دکمه‌های پاکسازی
        btn_clean = QToolButton()
        btn_clean.setText("🧹")
        btn_clean.setToolTip("پاکسازی فرمت")
        btn_clean.clicked.connect(self._clean_text_formatting)
        toolbar.addWidget(btn_clean)
        
        btn_rtl_fix = QToolButton()
        btn_rtl_fix.setText("↔️")
        btn_rtl_fix.setToolTip("اصلاح راست‌چین")
        btn_rtl_fix.clicked.connect(self._fix_rtl_text)
        toolbar.addWidget(btn_rtl_fix)
        
        toolbar.addSeparator()
        
        # ذخیره سریع
        btn_save = QToolButton()
        btn_save.setText("💾")
        btn_save.setToolTip("ذخیره تغییرات (Ctrl+S)")
        btn_save.clicked.connect(self._save_current_changes)
        btn_save.setStyleSheet("background: #27ae60; color: white;")
        toolbar.addWidget(btn_save)
        
        return toolbar
  
    # ==================== توابع فرمت‌بندی متن ====================
    
    def _change_font(self, font):
        """تغییر فونت متن انتخاب شده"""
        cursor = self.preview.textCursor()
        if cursor.hasSelection():
            fmt = QTextCharFormat()
            fmt.setFontFamily(font.family())
            cursor.mergeCharFormat(fmt)
            self.preview.mergeCurrentCharFormat(fmt)
    
    def _change_font_size(self, size):
        """تغییر سایز فونت"""
        cursor = self.preview.textCursor()
        if cursor.hasSelection():
            fmt = QTextCharFormat()
            fmt.setFontPointSize(size)
            cursor.mergeCharFormat(fmt)
            self.preview.mergeCurrentCharFormat(fmt)
    
    def _toggle_format(self, format_type):
        cursor = self.preview.textCursor()
        fmt = QTextCharFormat()
    
        if format_type == 'bold':
            is_bold = cursor.charFormat().fontWeight() == QFont.Bold
            fmt.setFontWeight(QFont.Normal if is_bold else QFont.Bold)
        elif format_type == 'italic':
            is_italic = cursor.charFormat().fontItalic()
            fmt.setFontItalic(not is_italic)
        elif format_type == 'underline':
            is_underline = cursor.charFormat().fontUnderline()
            fmt.setFontUnderline(not is_underline)
    
        cursor.mergeCharFormat(fmt)
        self.preview.setTextCursor(cursor)
    
    def _change_text_color(self):
        """تغییر رنگ متن"""
        color = QColorDialog.getColor()
        if color.isValid():
            cursor = self.preview.textCursor()
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            cursor.mergeCharFormat(fmt)
            self.preview.mergeCurrentCharFormat(fmt)
    
    def _set_alignment(self, alignment):
        """تنظیم تراز متن"""
        cursor = self.preview.textCursor()
        block_format = cursor.blockFormat()
        block_format.setAlignment(alignment)
        cursor.mergeBlockFormat(block_format)
        self.preview.setTextCursor(cursor)
    
    def _insert_bullet_list(self):
        """درج لیست گلوله‌ای"""
        cursor = self.preview.textCursor()
        cursor.insertText("\n• ")
        self.preview.setTextCursor(cursor)
    
    def _insert_numbered_list(self):
        """درج لیست شماره‌دار"""
        cursor = self.preview.textCursor()
        current_block = cursor.blockNumber() + 1
        cursor.insertText(f"\n{current_block}. ")
        self.preview.setTextCursor(cursor)
    
    def _clean_text_formatting(self):
        """پاکسازی فرمت‌های اضافی"""
        current_text = self.preview.toPlainText()
        if not current_text:
            return
        
        cleaned_lines = [line.strip() for line in current_text.split('\n')]
        cleaned_text = '\n'.join(cleaned_lines)
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        
        self.preview.setPlainText(cleaned_text)
        self.status_label.setText('✅ فرمت متن پاکسازی شد')
    
    def _fix_rtl_text(self):
        """اصلاح راست‌چین"""
        current_text = self.preview.toPlainText()
        if not current_text:
            return
        
        replacements = {'ي': 'ی', 'ك': 'ک', 'ة': 'ه', 'ؤ': 'و', 'إ': 'ا', 'أ': 'ا'}
        for old, new in replacements.items():
            current_text = current_text.replace(old, new)
        
        current_text = re.sub(r'\bمی\s+', 'می‌', current_text)
        current_text = re.sub(r'\bنمی\s+', 'نمی‌', current_text)
        current_text = re.sub(r'\s+([،؛:؟!.])', r'\1', current_text)
        
        self.preview.setPlainText(current_text)
        self.status_label.setText('✅ اصلاحات راست‌چین اعمال شد')

    def _save_current_changes(self):
        """ذخیره تغییرات"""
        if not self.current_template_id:
            QMessageBox.warning(self, "هشدار", "ابتدا یک قالب انتخاب کنید.")
            return
        
        template_data = self._get_current_template_data()
        if not template_data:
            return
        
        # ذخیره به صورت HTML برای حفظ فرمت‌بندی
        new_body = self.preview.toHtml()
        
        try:
            update_report_template(
                self.current_template_id,
                template_data.get('title', ''),
                template_data.get('category', ''),
                new_body
            )
            
            current_item = self.template_list.currentItem()
            if current_item:
                template_data['body'] = new_body
                current_item.setData(Qt.UserRole, template_data)
            
            self.status_label.setText('✅ تغییرات با موفقیت ذخیره شدند')
            QMessageBox.information(self, "موفق", "تغییرات با موفقیت ذخیره شد.")
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ذخیره تغییرات: {str(e)}")

    # ==================== MANAGEMENT FUNCTIONS ====================

    def _manage_categories(self):
        """مدیریت دسته‌بندی‌ها"""
        dlg = CategoryManagerDialog(self)
        dlg.exec_() 
        self._load_categories_to_filter()
        self._load_templates()

    def _manage_subgroups(self):
        """مدیریت زیرگروه‌ها"""
        dlg = SubgroupManagerDialog(self)
        dlg.exec_() 
        self._load_categories_to_filter()
        self._load_templates()

    def _refresh_subgroups(self, category_name=None):
        """بروزرسانی لیست زیرگروه‌ها بر اساس دسته‌بندی"""
        try:
            subgroups = get_subgroups(category_name)
            self.subgroup_filter.clear()
            self.subgroup_filter.addItem('🏷️ همه زیرگروه‌ها', 'all')
            for subgroup in subgroups:
                self.subgroup_filter.addItem(f'🏷️ {subgroup["name"]}', subgroup['id'])
        except Exception as e:
            QMessageBox.warning(self, "خطا", f"خطا در بارگذاری زیرگروه‌ها: {str(e)}")

    # ==================== CORE FUNCTIONALITY ====================

    def _load_user_preferences(self):
        """بارگذاری تنظیمات کاربر"""
        self.favorite_templates = []
        self.recent_templates = []

    def _load_templates(self):
        """بارگذاری قالب‌ها"""
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(30)
            
            all_templates = list_report_templates()
            self.progress_bar.setValue(70)
            
            filtered_templates = self._apply_filters(all_templates)
            self._populate_list(filtered_templates)
            
            self.progress_bar.setValue(100)
            QTimer.singleShot(300, lambda: self.progress_bar.setVisible(False))
            
            self._update_realtime_stats(all_templates, filtered_templates)
            self.status_label.setText(f'✅ {len(filtered_templates)} قالب بارگذاری شد')
            
        except Exception as e:
            self.status_label.setText(f'❌ خطا در بارگذاری: {str(e)}')
            self.progress_bar.setVisible(False)

    def _apply_filters(self, templates):
        """اعمال فیلترها"""
        filtered = templates
        
        category = self.category_filter.currentData()
        if category and category != 'all':
            filtered = [t for t in filtered if t.get('category') == category]
        
        subgroup_id = self.subgroup_filter.currentData()
        if subgroup_id and subgroup_id != 'all':
            filtered = [t for t in filtered if t.get('subgroup_id') == subgroup_id]
        
        search_text = self.search_input.text().strip().lower()
        if search_text:
            filtered = [t for t in filtered if self._advanced_search(t, search_text)]
        
        return filtered

    def _advanced_search(self, template, search_text):
        """جستجو در قالب"""
        for field in [template.get('title', ''), template.get('body', ''), template.get('category', '')]:
            if search_text in str(field).lower():
                return True
        return False

    def _populate_list(self, templates):
        """پر کردن لیست"""
        self.template_list.clear()
        for template in templates:
            item = self._create_list_item(template)
            self.template_list.addItem(item)
        if self.template_list.count() > 0:
            self.template_list.setCurrentRow(0)

    def _create_list_item(self, template):
        """ایجاد آیتم لیست"""
        title = template.get('title', 'بدون عنوان')
        category = template.get('category', 'بدون دسته‌بندی')
        subgroup_name = self._get_subgroup_name(template.get('subgroup_id'))
        
        display_text = f"📝 {title}\n   📂 {category}"
        if subgroup_name != 'بدون زیرگروه':
            display_text += f" | 🏷️ {subgroup_name}"
        
        char_count = len(template.get('body', ''))
        display_text += f"\n   📏 {char_count} حرف"
        
        item = QListWidgetItem(display_text)
        item.setData(Qt.UserRole, template)
        
        if template.get('id') in self.favorite_templates:
            item.setBackground(QColor(241, 196, 15, 40))
        elif template.get('id') in self.recent_templates:
            item.setBackground(QColor(46, 204, 113, 40))
        
        return item

    def _update_realtime_stats(self, all_templates, filtered_templates):
        """به‌روزرسانی آمار"""
        self.realtime_stats.setText(f"📊 {len(filtered_templates)}/{len(all_templates)} قالب | 🕒 {datetime.now().strftime('%H:%M')}")

    # ==================== FEATURES ====================

    def _show_favorites(self):
        """نمایش موارد دلخواه"""
        for btn in self.tab_buttons.values():
            btn.setChecked(False)
        if '⭐ دلخواه' in self.tab_buttons:
            self.tab_buttons['⭐ دلخواه'].setChecked(True)
        
        all_templates = list_report_templates()
        filtered = [t for t in all_templates if t.get('id') in self.favorite_templates]
        self._populate_list(filtered)

    def _show_recent(self):
        """نمایش اخیر"""
        for btn in self.tab_buttons.values():
            btn.setChecked(False)
        if '🕒 اخیر' in self.tab_buttons:
            self.tab_buttons['🕒 اخیر'].setChecked(True)
        
        all_templates = list_report_templates()
        filtered = []
        for tid in self.recent_templates:
            for t in all_templates:
                if t.get('id') == tid:
                    filtered.append(t)
                    break
        self._populate_list(filtered)

    def _show_all_templates(self):
        """نمایش همه"""
        for btn in self.tab_buttons.values():
            btn.setChecked(False)
        if '📋 همه' in self.tab_buttons:
            self.tab_buttons['📋 همه'].setChecked(True)
        self._load_templates()

    def _show_statistics(self):
        """نمایش آمار"""
        templates = list_report_templates()
        QMessageBox.information(self, "آمار", 
            f"📊 کل قالب‌ها: {len(templates)}\n"
            f"⭐ موارد دلخواه: {len(self.favorite_templates)}\n"
            f"🕒 اخیر: {len(self.recent_templates)}"
        )

    def _toggle_favorite(self):
        """تغییر علاقه‌مندی"""
        template_data = self._get_current_template_data()
        if template_data:
            template_id = template_data.get('id')
            if template_id in self.favorite_templates:
                self.favorite_templates.remove(template_id)
            else:
                self.favorite_templates.append(template_id)
            self._load_templates()

    def _show_context_menu(self, position):
        """منوی راست کلیک"""
        menu = QMenu()
        menu.addAction('✅ درج قالب', self._insert_template)
        menu.addSeparator()
        menu.addAction('➕ قالب جدید', self._create_new_template)
        menu.addAction('📋 ایجاد کپی', self._duplicate_template)
        menu.addSeparator()
        
        template_data = self._get_current_template_data()
        if template_data:
            is_favorite = template_data.get('id') in self.favorite_templates
            menu.addAction('📝 ویرایش', self._quick_edit_template)
            menu.addAction('⭐ ' + ('حذف از دلخواه' if is_favorite else 'افزودن به دلخواه'), self._toggle_favorite)
            menu.addAction('📤 ذخیره در فایل', self._export_template)
            menu.addSeparator()
            menu.addAction('🗑️ حذف قالب', self._delete_template)
        
        menu.exec_(self.template_list.mapToGlobal(position))

    # ==================== BASIC FUNCTIONS ====================

    def _on_category_changed(self):
        """وقتی دسته‌بندی تغییر کرد"""
        category = self.category_filter.currentData()
        if category and category != 'all':
            self._refresh_subgroups(category)
        else:
            self._refresh_subgroups()
        self._load_templates()

    def _on_search_changed(self):
        if hasattr(self, 'search_timer'):
            self.search_timer.stop()
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._load_templates)
        self.search_timer.start(300)

    def _on_template_selected(self, current, previous):
        if current:
            template_data = current.data(Qt.UserRole)
            if template_data:
                self._preview_template(template_data)
                self._add_to_recent(template_data.get('id'))

    def _preview_template(self, template_data):
        """پیش‌نمایش قالب"""
        try:
            self.current_template_id = template_data.get('id')
            template_body = template_data.get('body', '')
            
            # تشخیص HTML یا متن ساده
            if template_body.startswith('<!DOCTYPE') or template_body.startswith('<html'):
                self.preview.setHtml(template_body)
            else:
                self.preview.setPlainText(template_body)
            
            char_count = len(self.preview.toPlainText())
            category = template_data.get('category', 'بدون دسته')
            
            info = f"📝 {template_data.get('title', '')} | 📂 {category} | 📏 {char_count} حرف"
            if template_data.get('id') in self.favorite_templates:
                info += " | ⭐"
            
            self.template_info.setText(info)
            
        except Exception as e:
            print(f"خطا در پیش‌نمایش: {e}")

    def _add_to_recent(self, template_id):
        if template_id in self.recent_templates:
            self.recent_templates.remove(template_id)
        self.recent_templates.insert(0, template_id)
        self.recent_templates = self.recent_templates[:10]

    def _get_subgroup_name(self, subgroup_id):
        if not subgroup_id:
            return 'بدون زیرگروه'
        try:
            for sg in get_subgroups():
                if sg['id'] == subgroup_id:
                    return sg['name']
        except:
            pass
        return 'بدون زیرگروه'

    def _get_current_template_data(self):
        current_item = self.template_list.currentItem()
        return current_item.data(Qt.UserRole) if current_item else None

    def _insert_template(self):
        if self._is_inserting:
            return
        
        current_item = self.template_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, 'هشدار', 'لطفاً یک قالب انتخاب کنید.')
            return
        
        self._is_inserting = True
        self.selected_text = self.preview.toHtml()  # HTML برای حفظ فرمت
        template_data = current_item.data(Qt.UserRole)
        self.selected_template_name = template_data.get('title', '')
        
        self.template_selected.emit(self.selected_text, self.selected_template_name)
        self.accept()
        self._is_inserting = False

    def _insert_and_close(self, item):
        if item:
            self.template_list.setCurrentItem(item)
            self._insert_template()

    # ==================== TEMPLATE MANAGEMENT ====================

    def _create_new_template(self):
        dlg = NewTemplateDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            if not data["title"]:
                QMessageBox.warning(self, "خطا", "عنوان نمی‌تواند خالی باشد.")
                return
            try:
                insert_report_template(data["title"], data["category"], data["body"], data["subgroup_id"])
                self._load_templates()
                self._load_categories_to_filter()
                self.status_label.setText('✅ قالب جدید ایجاد شد')
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا: {str(e)}")

    def _quick_edit_template(self):
        template_data = self._get_current_template_data()
        if not template_data:
            QMessageBox.warning(self, 'هشدار', 'یک قالب انتخاب کنید.')
            return
        
        dlg = NewTemplateDialog(self, title=template_data.get('title', ''),
                                category=template_data.get('category', ''),
                                subgroup_id=template_data.get('subgroup_id'),
                                body=self.preview.toHtml())
        
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            try:
                update_report_template(template_data['id'], data["title"], data["category"], data["body"])
                if data["subgroup_id"]:
                    update_template_subgroup(template_data['id'], data["subgroup_id"])
                self._load_templates()
                self._load_categories_to_filter()
                self.status_label.setText('✅ ویرایش شد')
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا: {str(e)}")

    def _duplicate_template(self):
        template_data = self._get_current_template_data()
        if not template_data:
            return
        
        try:
            new_id = insert_report_template(
                f"{template_data.get('title', '')} - کپی",
                template_data.get('category', ''),
                self.preview.toHtml()
            )
            if template_data.get('subgroup_id'):
                update_template_subgroup(new_id, template_data.get('subgroup_id'))
            self._load_templates()
            self.status_label.setText('✅ کپی ایجاد شد')
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا: {str(e)}")

    def _delete_template(self):
        template_data = self._get_current_template_data()
        if not template_data:
            return
        
        reply = QMessageBox.question(self, '⚠️ حذف قالب', 
            f'آیا از حذف "{template_data.get("title", "")}" مطمئنید؟',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                delete_report_template(template_data['id'])
                if template_data['id'] in self.favorite_templates:
                    self.favorite_templates.remove(template_data['id'])
                if template_data['id'] in self.recent_templates:
                    self.recent_templates.remove(template_data['id'])
                self.current_template_id = None
                self._load_templates()
                self._load_categories_to_filter()
                self.preview.clear()
                self.template_info.setText('ℹ️ هیچ قالبی انتخاب نشده')
                self.status_label.setText('✅ قالب حذف شد')
            except Exception as e:
                QMessageBox.critical(self, 'خطا', f'خطا: {str(e)}')

    def _export_template(self):
        template_data = self._get_current_template_data()
        if not template_data:
            return
        
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', template_data.get('title', 'قالب'))
        path, _ = QFileDialog.getSaveFileName(self, '💾 ذخیره', f'{safe_title}.html', 
                                               'HTML (*.html);;Text (*.txt)')
        if path:
            try:
                content = self.preview.toHtml() if path.endswith('.html') else self.preview.toPlainText()
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.status_label.setText('✅ ذخیره شد')
            except Exception as e:
                QMessageBox.critical(self, 'خطا', f'خطا: {str(e)}')

    def _export_all_templates(self):
        path = QFileDialog.getExistingDirectory(self, "انتخاب پوشه")
        if path:
            try:
                for template in list_report_templates():
                    safe_title = re.sub(r'[<>:"/\\|?*]', '_', template.get('title', 'قالب'))
                    with open(os.path.join(path, f"{safe_title}.html"), 'w', encoding='utf-8') as f:
                        f.write(template.get('body', ''))
                QMessageBox.information(self, "موفق", "همه قالب‌ها ذخیره شدند.")
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا: {str(e)}")

    def _show_settings(self):
        QMessageBox.information(self, "تنظیمات", "Ctrl+S: ذخیره | Ctrl+Enter: درج | Delete: حذف")

    def _create_quick_template(self):
        dlg = QuickTemplateDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            self._load_templates()

    def _create_status_bar(self):
        layout = QHBoxLayout()
        
        self.status_label = QLabel('🟢 آماده')
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 11px;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(150)
        self.progress_bar.setVisible(False)
        
        self.realtime_stats = QLabel('')
        self.realtime_stats.setStyleSheet("color: #3498db; font-size: 11px;")
        
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.realtime_stats)
        layout.addWidget(self.progress_bar)
        
        return layout

    def _create_bottom_toolbar(self):
        layout = QHBoxLayout()
        
        btn_insert = QPushButton("✅ درج قالب")
        btn_insert.setObjectName("btn_insert")
        btn_insert.clicked.connect(self._insert_template)
        btn_insert.setMinimumHeight(40)
        
        btn_new = QPushButton("➕ جدید")
        btn_new.clicked.connect(self._create_new_template)
        
        btn_edit = QPushButton("✏️ ویرایش")
        btn_edit.clicked.connect(self._quick_edit_template)
        
        btn_refresh = QPushButton("🔄 بروزرسانی")
        btn_refresh.clicked.connect(self._load_templates)
        
        btn_close = QPushButton("❌ خروج")
        btn_close.clicked.connect(self.reject)
        
        layout.addWidget(btn_insert)
        layout.addWidget(btn_new)
        layout.addWidget(btn_edit)
        layout.addWidget(btn_refresh)
        layout.addStretch()
        layout.addWidget(btn_close)
        
        return layout

    def _setup_shortcuts(self):
        shortcuts = [
            (QKeySequence("Ctrl+Return"), self._insert_template),
            (QKeySequence.New, self._create_new_template),
            (QKeySequence.Delete, self._delete_template),
            (QKeySequence("Ctrl+S"), self._save_current_changes),
            (QKeySequence("Ctrl+B"), lambda: self._toggle_format('bold')),
            (QKeySequence("Ctrl+I"), lambda: self._toggle_format('italic')),
            (QKeySequence("Ctrl+U"), lambda: self._toggle_format('underline')),
        ]
        for key, slot in shortcuts:
            QShortcut(key, self).activated.connect(slot)

    def get_selected_template(self):
        return self.selected_text, self.selected_template_name


# ==================== DIALOG CLASSES ====================

class NewTemplateDialog(QDialog):
    def __init__(self, parent=None, title='', category='', subgroup_id=None, body=''):
        super().__init__(parent)
        self.setWindowTitle("✏️ ایجاد / ویرایش قالب")
        self.resize(600, 500)
        self._build_ui(title, category, subgroup_id, body)

    def _build_ui(self, title, category, subgroup_id, body):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        layout.addWidget(QLabel("📝 عنوان:"))
        self.title_input = QLineEdit(title)
        self.title_input.setPlaceholderText("عنوان قالب را وارد کنید...")
        layout.addWidget(self.title_input)
        
        layout.addWidget(QLabel("📂 دسته‌بندی:"))
        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.setPlaceholderText("انتخاب یا تایپ دسته‌بندی جدید...")
        
        # بارگذاری دسته‌بندی‌های موجود
        templates = list_report_templates()
        existing_categories = sorted(set(t.get('category', '') for t in templates if t.get('category')))
        for cat in existing_categories:
            self.category_input.addItem(f"📂 {cat}", cat)
        
        if category:
            idx = self.category_input.findData(category)
            if idx >= 0:
                self.category_input.setCurrentIndex(idx)
            else:
                self.category_input.addItem(f"📂 {category}", category)
                self.category_input.setCurrentIndex(self.category_input.count() - 1)
        
        self.category_input.currentIndexChanged.connect(self._update_subgroups)
        layout.addWidget(self.category_input)
        
        layout.addWidget(QLabel("🏷️ زیرگروه:"))
        self.subgroup_combo = QComboBox()
        layout.addWidget(self.subgroup_combo)
        
        # بارگذاری اولیه زیرگروه‌ها
        self._update_subgroups()
        if subgroup_id:
            idx = self.subgroup_combo.findData(subgroup_id)
            if idx >= 0:
                self.subgroup_combo.setCurrentIndex(idx)
        
        layout.addWidget(QLabel("📄 متن:"))
        self.body_input = QTextEdit()
        if body and (body.startswith('<!DOCTYPE') or body.startswith('<html')):
            self.body_input.setHtml(body)
        else:
            self.body_input.setPlainText(body if body else '')
        layout.addWidget(self.body_input)
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("💾 ذخیره")
        btn_save.setObjectName("btn_save")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("❌ انصراف")
        btn_cancel.setObjectName("btn_cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def _update_subgroups(self):
        """بروزرسانی زیرگروه‌ها بر اساس دسته انتخاب شده"""
        self.subgroup_combo.clear()
        self.subgroup_combo.addItem("بدون زیرگروه", None)
        
        category = self.category_input.currentData()
        if not category:
            category = self.category_input.currentText().replace("📂 ", "").strip()
        
        if category:
            subgroups = get_subgroups(category)
            for sg in subgroups:
                self.subgroup_combo.addItem(sg['name'], sg['id'])

    def get_data(self):
        category = self.category_input.currentData()
        if not category:
            category = self.category_input.currentText().replace("📂 ", "").strip()
        
        return {
            "title": self.title_input.text().strip(),
            "category": category,
            "body": self.body_input.toPlainText().strip(),
            "subgroup_id": self.subgroup_combo.currentData()
        }

class SubgroupManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('🏷️ مدیریت زیرگروه‌ها')
        self.resize(400, 300)
        self._setup_ui()
        self._load_subgroups()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.subgroup_list = QListWidget()
        layout.addWidget(self.subgroup_list)
        
        btn_layout = QHBoxLayout()
        btn_add = QPushButton('➕')
        btn_add.clicked.connect(self._add_subgroup)
        btn_delete = QPushButton('🗑️')
        btn_delete.clicked.connect(self._delete_subgroup)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_delete)
        layout.addLayout(btn_layout)
        
        layout.addWidget(QPushButton('✅ بستن', clicked=self.accept))

    def _load_subgroups(self):
        self.subgroup_list.clear()
        for sg in get_subgroups():
            self.subgroup_list.addItem(sg['name'])

    def _add_subgroup(self):
        name, ok = QInputDialog.getText(self, 'زیرگروه جدید', 'نام:')
        if ok and name.strip():
            add_subgroup(name.strip())
            self._load_subgroups()

    def _delete_subgroup(self):
        item = self.subgroup_list.currentItem()
        if item:
            reply = QMessageBox.question(self, 'حذف', f'حذف "{item.text()}"؟',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                subgroups = get_subgroups()
                for sg in subgroups:
                    if sg['name'] == item.text():
                        delete_subgroup(sg['id'])
                        break
                self._load_subgroups()


class CategoryManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('📂 مدیریت دسته‌بندی‌ها')
        self.resize(400, 300)
        self._setup_ui()
        self._load_categories()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
    
        layout.addWidget(QLabel('📂 دسته‌بندی‌ها:'))
        self.category_list = QListWidget()
        self.category_list.itemClicked.connect(self._on_category_selected)
        layout.addWidget(self.category_list)
    
        layout.addWidget(QLabel('🏷️ زیرگروه‌های این دسته:'))
        self.subgroup_list = QListWidget()
        self.subgroup_list.setMaximumHeight(120)
        layout.addWidget(self.subgroup_list)
    
        btn1 = QHBoxLayout()
        btn1.addWidget(QPushButton('➕ دسته جدید', clicked=self._add_category))
        btn1.addWidget(QPushButton('✏️ ویرایش دسته', clicked=self._edit_category))
        btn1.addWidget(QPushButton('🗑️ حذف دسته', clicked=self._delete_category))
        layout.addLayout(btn1)
    
        btn2 = QHBoxLayout()
        btn2.addWidget(QPushButton('➕ زیرگروه جدید', clicked=self._add_subgroup_to_category))
        btn2.addWidget(QPushButton('🗑️ حذف زیرگروه', clicked=self._delete_subgroup_from_category))
        layout.addLayout(btn2)
    
        layout.addWidget(QPushButton('✅ بستن', clicked=self.accept))

    def _load_categories(self):
        """بارگذاری دسته‌بندی‌ها از قالب‌های موجود"""
        self.category_list.clear()
        templates = list_report_templates()
        existing_categories = set(t.get('category', '') for t in templates if t.get('category'))
        for cat in sorted(existing_categories):
            item = QListWidgetItem(f"📂 {cat}")
            item.setData(Qt.UserRole, cat)
            self.category_list.addItem(item)

    def _add_category(self):
        """افزودن دسته‌بندی جدید"""
        name, ok = QInputDialog.getText(self, '➕ دسته‌بندی جدید', 'نام دسته‌بندی:')
        if ok and name.strip():
            name = name.strip()
            # چک تکراری
            for i in range(self.category_list.count()):
                if self.category_list.item(i).data(Qt.UserRole) == name:
                    QMessageBox.warning(self, 'خطا', 'این دسته‌بندی وجود دارد.')
                    return
        
            # 👈 یه قالب خالی با این دسته بساز تا ذخیره بشه
            insert_report_template(f"قالب تست {name}", name, "")
        
            # حالا لیست رو آپدیت کن
            self._load_categories()
            QMessageBox.information(self, 'موفق', f'دسته‌بندی "{name}" با موفقیت اضافه شد.')

    def _edit_category(self):
        """ویرایش نام دسته‌بندی"""
        item = self.category_list.currentItem()
        if not item:
            QMessageBox.warning(self, 'هشدار', 'یک دسته انتخاب کنید.')
            return
        old_name = item.data(Qt.UserRole)
        new_name, ok = QInputDialog.getText(self, '✏️ ویرایش', 'نام جدید:', text=old_name)
        if ok and new_name.strip() and new_name.strip() != old_name:
            new_name = new_name.strip()
            # آپدیت قالب‌ها
            templates = list_report_templates()
            for t in templates:
                if t.get('category') == old_name:
                    update_report_template(t['id'], t.get('title', ''), new_name, t.get('body', ''))
            self._load_categories()

    def _delete_category(self):
        """حذف دسته‌بندی و قالب‌هایش"""
        item = self.category_list.currentItem()
        if not item:
            QMessageBox.warning(self, 'هشدار', 'یک دسته انتخاب کنید.')
            return
        name = item.data(Qt.UserRole)
        reply = QMessageBox.question(self, '⚠️ حذف', f'حذف دسته "{name}" و تمام قالب‌هایش؟',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            templates = list_report_templates()
            for t in templates:
                if t.get('category') == name:
                    delete_report_template(t['id'])
            self._load_categories()
    def _on_category_selected(self, item):
        """وقتی روی دسته کلیک میشه، زیرگروه‌هاش نشون داده بشه"""
        if item:
            category_name = item.data(Qt.UserRole)
            print(f"کلیک روی دسته: {category_name}")
            self._load_subgroups_for_category(category_name)

    def _load_subgroups_for_category(self, category_name):
        """بارگذاری زیرگروه‌های یک دسته"""
        self.subgroup_list.clear()
        subgroups = get_subgroups(category_name)
        for sg in subgroups:
            item = QListWidgetItem(f"🏷️ {sg['name']}")
            item.setData(Qt.UserRole, sg)
            self.subgroup_list.addItem(item)

    def _add_subgroup_to_category(self):
        """افزودن زیرگروه"""
        current = self.category_list.currentItem()
        if not current:
            QMessageBox.warning(self, 'هشدار', 'اول یه دسته انتخاب کن.')
            return
    
        category_name = current.data(Qt.UserRole)
        name, ok = QInputDialog.getText(self, 'زیرگروه جدید', f'برای دسته "{category_name}":')
    
        if ok and name.strip():
            result = add_subgroup(name.strip(), category_name)
        
            if result == -2:
                QMessageBox.warning(self, 'خطا', f'زیرگروه "{name}" قبلاً وجود دارد!')
            elif result > 0:
                self._load_subgroups_for_category(category_name)
                QMessageBox.information(self, 'موفق', 'زیرگروه اضافه شد.')
            else:
                QMessageBox.critical(self, 'خطا', 'مشکل در ذخیره‌سازی!')

    def _delete_subgroup_from_category(self):
        """حذف زیرگروه انتخاب شده"""
        current = self.subgroup_list.currentItem()
        if not current:
            return
    
        sg_data = current.data(Qt.UserRole)
        delete_subgroup(sg_data['id'])
    
        cat_item = self.category_list.currentItem()
        if cat_item:
            self._load_subgroups_for_category(cat_item.data(Qt.UserRole))

class QuickTemplateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🚀 قالب سریع")
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("عنوان:"))
        self.title_input = QLineEdit()
        layout.addWidget(self.title_input)
        layout.addWidget(QLabel("متن:"))
        self.body_input = QTextEdit()
        layout.addWidget(self.body_input)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QPushButton("💾 ذخیره", clicked=self._save))
        btn_layout.addWidget(QPushButton("❌ انصراف", clicked=self.reject))
        layout.addLayout(btn_layout)
    
    def _save(self):
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "خطا", "عنوان لازم است.")
            return
        insert_report_template(title, '', self.body_input.toHtml())
        self.accept()


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    dialog = ModernTemplatePicker()
    dialog.show()
    sys.exit(app.exec_())