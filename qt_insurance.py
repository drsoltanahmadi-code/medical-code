# -*- coding: utf-8 -*-
import json
import os
from typing import Dict
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QSpinBox, QWidget, QApplication, QLabel,
    QLineEdit, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'insurance_settings.json')
DEFAULT_INSURANCES = ["آزاد", "تامین اجتماعی", "خدمات درمانی", "نیروهای مسلح"]
DEFAULT_SUPP_INSURANCES = ["ندارد", "بیمه تکمیلی نیروهای مسلح", "بیمه تکمیلی تامین اجتماعی", "سایر"]


def load_insurance_percents() -> Dict[str, int]:
    """بارگذاری درصدهای بیمه اصلی از دیتابیس"""
    try:
        from qt_db import get_conn
        conn = get_conn('config')
        cursor = conn.cursor()
        
        cursor.execute("SELECT insurance_name, coverage_percent FROM insurance_settings WHERE insurance_type = 'main'")
        main_records = cursor.fetchall()
        conn.close()
        
        main_insurances = {}
        for record in main_records:
            if isinstance(record, dict):
                insurance_name = record.get('insurance_name', '')
                coverage_percent = record.get('coverage_percent', 0)
            else:
                insurance_name, coverage_percent = record
            main_insurances[insurance_name] = coverage_percent
        
        if main_insurances:
            return main_insurances
        
        return {name: (0 if name == "آزاد" else 70) for name in DEFAULT_INSURANCES}
            
    except Exception as e:
        return {name: (0 if name == "آزاد" else 70) for name in DEFAULT_INSURANCES}

def load_supp_insurance_percents() -> Dict[str, int]:
    """بارگذاری درصدهای بیمه تکمیلی از دیتابیس"""
    try:
        from qt_db import get_conn
        conn = get_conn('config')
        cursor = conn.cursor()
        
        cursor.execute("SELECT insurance_name, coverage_percent FROM insurance_settings WHERE insurance_type = 'supplementary'")
        supp_records = cursor.fetchall()
        conn.close()
        
        supp_insurances = {}
        for record in supp_records:
            if isinstance(record, dict):
                insurance_name = record.get('insurance_name', '')
                coverage_percent = record.get('coverage_percent', 0)
            else:
                insurance_name, coverage_percent = record
            supp_insurances[insurance_name] = coverage_percent
        
        if supp_insurances:
            return supp_insurances
        
        return {name: 0 if name == "ندارد" else 50 for name in DEFAULT_SUPP_INSURANCES}
            
    except Exception as e:
        return {name: 0 if name == "ندارد" else 50 for name in DEFAULT_SUPP_INSURANCES}


def save_insurance_percents(main_mapping: Dict[str, int], supp_mapping: Dict[str, int]) -> None:
    """ذخیره درصدهای بیمه در دیتابیس با تفکیک نوع"""
    try:
        from qt_db import save_insurance_settings_with_type
        save_insurance_settings_with_type(main_mapping, supp_mapping)
    except Exception as e:
        all_data = {}
        all_data.update(main_mapping)
        all_data.update(supp_mapping)
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)


class PercentEditor(QWidget):
    def __init__(self, value: int, parent=None):
        super().__init__(parent)
        self.spin = QSpinBox(self)
        self.spin.setRange(0, 100)
        self.spin.setSuffix('%')
        self.spin.setValue(value)

    def value(self) -> int:
        return self.spin.value()


class InsuranceSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('تنظیم درصد بیمه‌ها')
        self.resize(700, 600)
        QApplication.setFont(QFont('Tahoma', 9))
        
        self.main_mapping = {}
        self.supp_mapping = {}
        
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        
        main_label = QLabel('بیمه‌های اصلی')
        main_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: #2c3e50; padding: 10px;")
        layout.addWidget(main_label)
        
        main_buttons_layout = QHBoxLayout()
        btn_add_main = QPushButton('➕ افزودن بیمه اصلی')
        btn_edit_main = QPushButton('✏️ ویرایش بیمه اصلی')
        btn_delete_main = QPushButton('🗑️ حذف بیمه اصلی')
        
        for btn in [btn_add_main, btn_edit_main, btn_delete_main]:
            btn.setMaximumHeight(30)
            btn.setStyleSheet("QPushButton { padding: 5px 10px; }")
        
        btn_add_main.clicked.connect(self._add_main_insurance)
        btn_edit_main.clicked.connect(self._edit_main_insurance)
        btn_delete_main.clicked.connect(self._delete_main_insurance)
        
        main_buttons_layout.addWidget(btn_add_main)
        main_buttons_layout.addWidget(btn_edit_main)
        main_buttons_layout.addWidget(btn_delete_main)
        main_buttons_layout.addStretch(1)
        layout.addLayout(main_buttons_layout)
        
        self.main_table = QTableWidget(0, 2)
        self.main_table.setHorizontalHeaderLabels(['نام بیمه اصلی', 'درصد پوشش'])
        self.main_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.main_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        
        self._populate_main_table()
        layout.addWidget(self.main_table)
        
        layout.addSpacing(30)
        
        supp_label = QLabel('بیمه‌های تکمیلی')
        supp_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: #e74c3c; padding: 10px;")
        layout.addWidget(supp_label)
        
        supp_buttons_layout = QHBoxLayout()
        btn_add_supp = QPushButton('➕ افزودن بیمه تکمیلی')
        btn_edit_supp = QPushButton('✏️ ویرایش بیمه تکمیلی')
        btn_delete_supp = QPushButton('🗑️ حذف بیمه تکمیلی')
        
        for btn in [btn_add_supp, btn_edit_supp, btn_delete_supp]:
            btn.setMaximumHeight(30)
            btn.setStyleSheet("QPushButton { padding: 5px 10px; }")
        
        btn_add_supp.clicked.connect(self._add_supp_insurance)
        btn_edit_supp.clicked.connect(self._edit_supp_insurance)
        btn_delete_supp.clicked.connect(self._delete_supp_insurance)
        
        supp_buttons_layout.addWidget(btn_add_supp)
        supp_buttons_layout.addWidget(btn_edit_supp)
        supp_buttons_layout.addWidget(btn_delete_supp)
        supp_buttons_layout.addStretch(1)
        layout.addLayout(supp_buttons_layout)
        
        self.supp_table = QTableWidget(0, 2)
        self.supp_table.setHorizontalHeaderLabels(['نام بیمه تکمیلی', 'درصد پوشش (از سهم بیمار)'])
        self.supp_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.supp_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        
        self._populate_supp_table()
        layout.addWidget(self.supp_table)

        buttons = QHBoxLayout()
        btn_save = QPushButton('💾 ذخیره همه تغییرات')
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        
        btn_cancel = QPushButton('❌ انصراف')
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        btn_save.clicked.connect(self._save_all)
        btn_cancel.clicked.connect(self.reject)
        buttons.addStretch(1)
        buttons.addWidget(btn_save)
        buttons.addWidget(btn_cancel)
        layout.addLayout(buttons)
        self.setLayout(layout)

    def _populate_main_table(self):
        if not self.main_mapping:
            self.main_mapping = load_insurance_percents()
        
        self.main_table.setRowCount(0)
        for name, percent in self.main_mapping.items():
            r = self.main_table.rowCount()
            self.main_table.insertRow(r)
            item = QTableWidgetItem(name)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.main_table.setItem(r, 0, item)
            editor = PercentEditor(percent, self.main_table)
            self.main_table.setCellWidget(r, 1, editor.spin)

    def _populate_supp_table(self):
        if not self.supp_mapping:
            self.supp_mapping = load_supp_insurance_percents()
        
        self.supp_table.setRowCount(0)
        for name, percent in self.supp_mapping.items():
            r = self.supp_table.rowCount()
            self.supp_table.insertRow(r)
            item = QTableWidgetItem(name)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.supp_table.setItem(r, 0, item)
            editor = PercentEditor(percent, self.supp_table)
            self.supp_table.setCellWidget(r, 1, editor.spin)

    def _add_main_insurance(self):
        name, ok = QInputDialog.getText(self, 'افزودن بیمه اصلی', 'نام بیمه اصلی جدید:')
        if ok and name.strip():
            if name.strip() in self.main_mapping:
                QMessageBox.warning(self, "خطا", "این بیمه قبلاً وجود دارد!")
                return
            
            percent, ok = QInputDialog.getInt(self, 'درصد پوشش', 'درصد پوشش بیمه:', 70, 0, 100, 1)
            if ok:
                self.main_mapping[name.strip()] = percent
                self._populate_main_table()

    def _edit_main_insurance(self):
        current_row = self.main_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "خطا", "لطفاً یک بیمه را انتخاب کنید!")
            return
        
        old_name = self.main_table.item(current_row, 0).text()
        new_name, ok = QInputDialog.getText(self, 'ویرایش بیمه اصلی', 'نام جدید بیمه:', text=old_name)
        if ok and new_name.strip() and new_name != old_name:
            if new_name.strip() in self.main_mapping:
                QMessageBox.warning(self, "خطا", "این نام قبلاً وجود دارد!")
                return
            
            self.main_mapping[new_name.strip()] = self.main_mapping.pop(old_name)
            self._populate_main_table()

    def _delete_main_insurance(self):
        current_row = self.main_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "خطا", "لطفاً یک بیمه را انتخاب کنید!")
            return
        
        name = self.main_table.item(current_row, 0).text()
        
        if name in DEFAULT_INSURANCES:
            QMessageBox.warning(self, "خطا", "نمی‌توان بیمه پیش‌فرض را حذف کرد!")
            return
        
        reply = QMessageBox.question(self, "تأیید حذف", 
                                f"آیا از حذف بیمه '{name}' مطمئن هستید؟",
                                QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self.main_mapping[name]
            from qt_db import get_conn
            conn = get_conn('config')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM insurance_settings WHERE insurance_name = ?", (name,))
            conn.commit()
            conn.close()
            self._populate_main_table()

    def _add_supp_insurance(self):
        name, ok = QInputDialog.getText(self, 'افزودن بیمه تکمیلی', 'نام بیمه تکمیلی جدید:')
        if ok and name.strip():
            if name.strip() in self.supp_mapping:
                QMessageBox.warning(self, "خطا", "این بیمه قبلاً وجود دارد!")
                return
            
            percent, ok = QInputDialog.getInt(self, 'درصد پوشش', 'درصد پوشش از سهم بیمار:', 50, 0, 100, 1)
            if ok:
                self.supp_mapping[name.strip()] = percent
                self._populate_supp_table()

    def _delete_supp_insurance(self):
        current_row = self.supp_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "خطا", "لطفاً یک بیمه را انتخاب کنید!")
            return
        
        name = self.supp_table.item(current_row, 0).text()
        
        if name in DEFAULT_SUPP_INSURANCES:
            QMessageBox.warning(self, "خطا", "نمی‌توان بیمه پیش‌فرض را حذف کرد!")
            return
        
        reply = QMessageBox.question(self, "تأیید حذف", 
                                f"آیا از حذف بیمه تکمیلی '{name}' مطمئن هستید؟",
                                QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self.supp_mapping[name]
            from qt_db import get_conn
            conn = get_conn('config')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM insurance_settings WHERE insurance_name = ?", (name,))
            conn.commit()
            conn.close()
            self._populate_supp_table()

    def _edit_supp_insurance(self):
        current_row = self.supp_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "خطا", "لطفاً یک بیمه را انتخاب کنید!")
            return
        
        old_name = self.supp_table.item(current_row, 0).text()
        new_name, ok = QInputDialog.getText(self, 'ویرایش بیمه تکمیلی', 'نام جدید بیمه:', text=old_name)
        if ok and new_name.strip() and new_name != old_name:
            if new_name.strip() in self.supp_mapping:
                QMessageBox.warning(self, "خطا", "این نام قبلاً وجود دارد!")
                return
            
            self.supp_mapping[new_name.strip()] = self.supp_mapping.pop(old_name)
            from qt_db import get_conn
            conn = get_conn('config')
            cursor = conn.cursor()
            cursor.execute("UPDATE insurance_settings SET insurance_name = ? WHERE insurance_name = ?", (new_name.strip(), old_name))
            conn.commit()
            conn.close()
            self._populate_supp_table()

    def _save_all(self):
        try:
            updated_main_mapping = {}
            updated_supp_mapping = {}
            
            for row in range(self.main_table.rowCount()):
                name = self.main_table.item(row, 0).text()
                percent = self.main_table.cellWidget(row, 1).value()
                updated_main_mapping[name] = percent
            
            for row in range(self.supp_table.rowCount()):
                name = self.supp_table.item(row, 0).text()
                percent = self.supp_table.cellWidget(row, 1).value()
                updated_supp_mapping[name] = percent
            
            self.main_mapping = updated_main_mapping
            self.supp_mapping = updated_supp_mapping
            
            save_insurance_percents(self.main_mapping, self.supp_mapping)
            
            QMessageBox.information(self, "موفق", "تنظیمات بیمه‌ها با موفقیت ذخیره شد!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ذخیره تنظیمات: {str(e)}")


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    dlg = InsuranceSettingsDialog()
    dlg.exec_()