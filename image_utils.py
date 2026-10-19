# -*- coding: utf-8 -*-
"""مدیریت تصاویر با قابلیت تنظیمات JSON"""

import os
import json
import base64
from PyQt5.QtWidgets import QDialog, QFormLayout, QSpinBox, QComboBox, QHBoxLayout, QPushButton, QMessageBox, QFileDialog, QLabel
from PyQt5.QtCore import Qt, QBuffer
from PyQt5.QtGui import QImage, QTextCursor

# مسیر فایل تنظیمات تصویر
IMAGE_SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'image_settings.json')

# تنظیمات پیش‌فرض
DEFAULT_IMAGE_SETTINGS = {
    "default_width": 400,
    "default_margin": 10,
    "default_alignment": "center",
    "image_quality": 85,
    "max_width": 800,
    "border_radius": 5,
    "shadow": True
}

def load_image_settings():
    """بارگذاری تنظیمات از فایل JSON"""
    if not os.path.exists(IMAGE_SETTINGS_FILE):
        save_image_settings(DEFAULT_IMAGE_SETTINGS)
        return DEFAULT_IMAGE_SETTINGS.copy()
    
    try:
        with open(IMAGE_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            for key, value in DEFAULT_IMAGE_SETTINGS.items():
                if key not in settings:
                    settings[key] = value
            return settings
    except:
        return DEFAULT_IMAGE_SETTINGS.copy()

def save_image_settings(settings):
    """ذخیره تنظیمات در فایل JSON"""
    try:
        with open(IMAGE_SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"خطا در ذخیره تنظیمات: {e}")
        return False


class ImageSettingsDialog(QDialog):
    """دیالوگ تنظیمات تصویر"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = load_image_settings()
        self.setWindowTitle("⚙ تنظیمات تصویر")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout(self)
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(100, 1200)
        self.width_spin.setValue(self.settings.get('default_width', 400))
        self.width_spin.setSuffix(" px")
        layout.addRow("عرض پیش‌فرض:", self.width_spin)
        
        self.margin_spin = QSpinBox()
        self.margin_spin.setRange(0, 50)
        self.margin_spin.setValue(self.settings.get('default_margin', 10))
        self.margin_spin.setSuffix(" px")
        layout.addRow("حاشیه:", self.margin_spin)
        
        self.align_combo = QComboBox()
        self.align_combo.addItems(["وسط", "چپ", "راست"])
        align_map = {"center": "وسط", "left": "چپ", "right": "راست"}
        current_align = self.settings.get('default_alignment', 'center')
        self.align_combo.setCurrentText(align_map.get(current_align, "وسط"))
        layout.addRow("ترازبندی:", self.align_combo)
        
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(30, 100)
        self.quality_spin.setValue(self.settings.get('image_quality', 85))
        self.quality_spin.setSuffix(" %")
        layout.addRow("کیفیت تصویر:", self.quality_spin)
        
        self.radius_spin = QSpinBox()
        self.radius_spin.setRange(0, 30)
        self.radius_spin.setValue(self.settings.get('border_radius', 5))
        self.radius_spin.setSuffix(" px")
        layout.addRow("گوشه گرد:", self.radius_spin)
        
        self.shadow_check = QPushButton()
        self.shadow_check.setCheckable(True)
        self.shadow_check.setChecked(self.settings.get('shadow', True))
        self.shadow_check.setText("غیرفعال" if not self.shadow_check.isChecked() else "فعال")
        self.shadow_check.clicked.connect(lambda: self.shadow_check.setText(
            "فعال" if self.shadow_check.isChecked() else "غیرفعال"
        ))
        layout.addRow("سایه:", self.shadow_check)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 ذخیره تنظیمات")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("لغو")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
    
    def save_settings(self):
        align_map = {"وسط": "center", "چپ": "left", "راست": "right"}
        
        new_settings = {
            "default_width": self.width_spin.value(),
            "default_margin": self.margin_spin.value(),
            "default_alignment": align_map.get(self.align_combo.currentText(), "center"),
            "image_quality": self.quality_spin.value(),
            "max_width": 800,
            "border_radius": self.radius_spin.value(),
            "shadow": self.shadow_check.isChecked()
        }
        
        if save_image_settings(new_settings):
            QMessageBox.information(self, "موفق", "تنظیمات تصویر ذخیره شد.")
            self.accept()
        else:
            QMessageBox.critical(self, "خطا", "خطا در ذخیره تنظیمات.")


class ImageManager:
    """مدیریت درج تصاویر در ویرایشگر"""
    
    def __init__(self, editor_widget):
        self.editor = editor_widget
        self.image_count = 0
    
    def add_image(self, parent_widget):
        """افزودن تصویر به انتهای متن"""
        path, _ = QFileDialog.getOpenFileName(
            parent_widget, 'انتخاب تصویر', '', 
            'Images (*.png *.jpg *.jpeg *.bmp *.gif)'
        )
        if not path:
            return False
        
        settings = load_image_settings()
        
        class QuickSettings(QDialog):
            def __init__(self):
                super().__init__(parent_widget)
                self.setWindowTitle("تنظیمات تصویر")
                self.setModal(True)
                layout = QFormLayout(self)
                
                self.width_spin = QSpinBox()
                self.width_spin.setRange(50, 1200)
                self.width_spin.setValue(settings.get('default_width', 400))
                layout.addRow("عرض:", self.width_spin)
                
                self.align_combo = QComboBox()
                self.align_combo.addItems(["وسط", "چپ", "راست"])
                layout.addRow("تراز:", self.align_combo)
                
                self.margin_spin = QSpinBox()
                self.margin_spin.setRange(0, 50)
                self.margin_spin.setValue(settings.get('default_margin', 10))
                layout.addRow("حاشیه:", self.margin_spin)
                
                btns = QHBoxLayout()
                ok_btn = QPushButton("درج")
                cancel_btn = QPushButton("انصراف")
                btns.addWidget(ok_btn)
                btns.addWidget(cancel_btn)
                layout.addRow(btns)
                
                ok_btn.clicked.connect(self.accept)
                cancel_btn.clicked.connect(self.reject)
        
        dlg = QuickSettings()
        if dlg.exec_() != QDialog.Accepted:
            return False
        
        width = dlg.width_spin.value()
        align_map = {"وسط": "center", "چپ": "left", "راست": "right"}
        alignment = align_map.get(dlg.align_combo.currentText(), "center")
        margin = dlg.margin_spin.value()
        
        img = QImage(path)
        if img.isNull():
            QMessageBox.warning(parent_widget, 'خطا', 'بارگذاری تصویر ناموفق بود.')
            return False
        
        max_width = settings.get('max_width', 800)
        if width > max_width:
            width = max_width
        
        if width > 0 and width < img.width():
            img = img.scaledToWidth(width, Qt.SmoothTransformation)
        
        buf = QBuffer()
        buf.open(QBuffer.WriteOnly)
        quality = settings.get('image_quality', 85)
        if path.lower().endswith('.png'):
            img.save(buf, 'PNG')
        else:
            img.save(buf, 'JPEG', quality)
        
        b64 = base64.b64encode(bytes(buf.data())).decode('ascii')
        ext = 'png' if path.lower().endswith('.png') else 'jpeg'
        data_uri = f"data:image/{ext};base64,{b64}"
        
        styles = []
        if alignment == 'center':
            styles.append(f"display: block; margin: {margin}px auto;")
        elif alignment == 'left':
            styles.append(f"float: left; margin: {margin}px {margin}px {margin}px 0;")
        elif alignment == 'right':
            styles.append(f"float: right; margin: {margin}px 0 {margin}px {margin}px;")
        
        styles.append(f"width: {width}px;")
        styles.append(f"height: auto;")
        styles.append(f"max-width: 100%;")
        styles.append(f"object-fit: contain;")
        
        if settings.get('border_radius', 0) > 0:
            styles.append(f"border-radius: {settings['border_radius']}px;")
        
        if settings.get('shadow', False):
            styles.append("box-shadow: 0 2px 8px rgba(0,0,0,0.15);")
        
        style_str = " ".join(styles)
        
        img_html = f"<div style='clear: both; margin: 10px 0;'><img src='{data_uri}' style='{style_str}' alt='تصویر' /></div>"
        
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.editor.setTextCursor(cursor)
        cursor.insertHtml("<br>")
        cursor.insertHtml(img_html)
        cursor.insertHtml("<br>")
        self.editor.insertHtml(img_html)
        
        self.image_count += 1
        return True
    
    def get_image_count(self):
        html = self.editor.toHtml()
        return html.lower().count('<img')


class ImageButtonPanel(QHBoxLayout):
    """پنل دکمه‌های مربوط به تصویر"""
    
    def __init__(self, image_manager, parent):
        super().__init__()
        self.image_manager = image_manager
        self.parent = parent
        
        self.add_btn = QPushButton('📷 افزودن تصویر')
        self.add_btn.clicked.connect(self.add_image)
        self.add_btn.setMinimumWidth(110)
        self.addWidget(self.add_btn)  # ✅ اصلاح شده
        
        self.settings_btn = QPushButton('⚙ تنظیمات تصویر')
        self.settings_btn.clicked.connect(self.open_settings)
        self.settings_btn.setMinimumWidth(110)
        self.addWidget(self.settings_btn)  # ✅ اصلاح شده
        
        self.count_label = QLabel('📷 تصاویر: 0')
        self.count_label.setStyleSheet("color: green; font-weight: bold;")
        self.addWidget(self.count_label)  # ✅ اصلاح شده
        
        self.addStretch()
    
    def add_image(self):
        if self.image_manager.add_image(self.parent):
            self.update_count()
    
    def open_settings(self):
        dialog = ImageSettingsDialog(self.parent)
        dialog.exec_()
    
    def update_count(self):
        count = self.image_manager.get_image_count()
        self.count_label.setText(f'📷 تصاویر: {count}')