# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QComboBox, QMessageBox, QLabel, QLineEdit,
    QGroupBox, QCheckBox, QListWidget, QListWidgetItem, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from qt_db import get_conn


class PermissionsManager:
    def __init__(self, db_path='config.db'):
        self.db_path = db_path
        self._create_tables()
    
    def _create_tables(self):
        """ایجاد جداول مدیریت دسترسی"""
        conn = get_conn('config')
        cursor = conn.cursor()
        
        # جدول کاربران
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول نقش‌ها
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT UNIQUE NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # جدول دسترسی‌ها
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                permission_code TEXT UNIQUE NOT NULL,
                permission_name TEXT NOT NULL,
                module TEXT NOT NULL,
                description TEXT
            )
        ''')
        
        # جدول نقش-دسترسی
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS role_permissions (
                role_id INTEGER,
                permission_id INTEGER,
                PRIMARY KEY (role_id, permission_id),
                FOREIGN KEY (role_id) REFERENCES roles (id),
                FOREIGN KEY (permission_id) REFERENCES permissions (id)
            )
        ''')
        
        # جدول کاربر-نقش
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id INTEGER,
                role_id INTEGER,
                PRIMARY KEY (user_id, role_id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (role_id) REFERENCES roles (id)
            )
        ''')
        
        # درج دسترسی‌های پیش‌فرض
        default_permissions = [
            # ماژول پذیرش
            ('ADM_CREATE', 'ایجاد پذیرش', 'admission', 'امکان ایجاد پذیرش جدید'),
            ('ADM_EDIT', 'ویرایش پذیرش', 'admission', 'امکان ویرایش پذیرش‌ها'),
            ('ADM_DELETE', 'حذف پذیرش', 'admission', 'امکان حذف پذیرش‌ها'),
            ('ADM_VIEW', 'مشاهده پذیرش', 'admission', 'امکان مشاهده لیست پذیرش‌ها'),
            ('ADM_SEARCH', 'جستجوی پذیرش', 'admission', 'امکان جستجو در پذیرش‌ها'),
            
            # ماژول بیماران
            ('PAT_CREATE', 'ایجاد بیمار', 'patients', 'امکان ایجاد بیمار جدید'),
            ('PAT_EDIT', 'ویرایش بیمار', 'patients', 'امکان ویرایش اطلاعات بیمار'),
            ('PAT_DELETE', 'حذف بیمار', 'patients', 'امکان حذف بیمار'),
            ('PAT_VIEW', 'مشاهده بیماران', 'patients', 'امکان مشاهده لیست بیماران'),
            
            # ماژول پزشکان
            ('DOC_CREATE', 'ایجاد پزشک', 'doctors', 'امکان ایجاد پزشک جدید'),
            ('DOC_EDIT', 'ویرایش پزشک', 'doctors', 'امکان ویرایش اطلاعات پزشک'),
            ('DOC_DELETE', 'حذف پزشک', 'doctors', 'امکان حذف پزشک'),
            ('DOC_VIEW', 'مشاهده پزشکان', 'doctors', 'امکان مشاهده لیست پزشکان'),
            
            # ماژول خدمات
            ('SRV_CREATE', 'ایجاد خدمت', 'services', 'امکان ایجاد خدمت جدید'),
            ('SRV_EDIT', 'ویرایش خدمت', 'services', 'امکان ویرایش خدمات'),
            ('SRV_DELETE', 'حذف خدمت', 'services', 'امکان حذف خدمات'),
            ('SRV_VIEW', 'مشاهده خدمات', 'services', 'امکان مشاهده لیست خدمات'),
            
            # ماژول بیمه
            ('INS_CREATE', 'ایجاد بیمه', 'insurance', 'امکان ایجاد بیمه جدید'),
            ('INS_EDIT', 'ویرایش بیمه', 'insurance', 'امکان ویرایش اطلاعات بیمه'),
            ('INS_DELETE', 'حذف بیمه', 'insurance', 'امکان حذف بیمه'),
            ('INS_VIEW', 'مشاهده بیمه‌ها', 'insurance', 'امکان مشاهده لیست بیمه‌ها'),
            
            # ماژول گزارش‌ها
            ('REP_VIEW', 'مشاهده گزارش‌ها', 'reports', 'امکان مشاهده گزارش‌ها'),
            ('REP_CREATE', 'ایجاد گزارش', 'reports', 'امکان ایجاد گزارش جدید'),
            ('REP_EXPORT', 'خروجی گزارش', 'reports', 'امکان گرفتن خروجی از گزارش‌ها'),
            
            # ماژول مالی
            ('FIN_VIEW', 'مشاهده مالی', 'financial', 'امکان مشاهده اطلاعات مالی'),
            ('FIN_EDIT', 'ویرایش مالی', 'financial', 'امکان ویرایش اطلاعات مالی'),
            
            # ماژول تنظیمات
            ('SET_VIEW', 'مشاهده تنظیمات', 'settings', 'امکان مشاهده تنظیمات سیستم'),
            ('SET_EDIT', 'ویرایش تنظیمات', 'settings', 'امکان ویرایش تنظیمات سیستم'),

            # دسترسی‌های مدیریت کاربران
            ('USR_CREATE', 'ایجاد کاربر', 'users', 'امکان ایجاد کاربر جدید'),
            ('USR_EDIT', 'ویرایش کاربر', 'users', 'امکان ویرایش کاربران'),
            ('USR_DELETE', 'حذف کاربر', 'users', 'امکان حذف کاربران'),
            ('USR_VIEW', 'مشاهده کاربران', 'users', 'امکان مشاهده لیست کاربران'),
            
            # دسترسی‌های مدیریت نقش‌ها
            ('ROL_CREATE', 'ایجاد نقش', 'roles', 'امکان ایجاد نقش جدید'),
            ('ROL_EDIT', 'ویرایش نقش', 'roles', 'امکان ویرایش نقش‌ها'),
            ('ROL_DELETE', 'حذف نقش', 'roles', 'امکان حذف نقش‌ها'),
            ('ROL_VIEW', 'مشاهده نقش‌ها', 'roles', 'امکان مشاهده لیست نقش‌ها'),
        ]
        
        for perm_code, perm_name, module, description in default_permissions:
            cursor.execute('''
                INSERT OR IGNORE INTO permissions (permission_code, permission_name, module, description)
                VALUES (?, ?, ?, ?)
            ''', (perm_code, perm_name, module, description))
        
        # درج نقش‌های پیش‌فرض
        default_roles = [
            ('admin', 'مدیر سیستم', 'دسترسی کامل به تمام بخش‌های سیستم'),
            ('operator', 'اپراتور', 'دسترسی به بخش‌های پذیرش، بیماران و گزارش‌ها'),
            ('doctor', 'پزشک', 'دسترسی به بخش‌های پذیرش و گزارش‌های مربوطه'),
            ('viewer', 'ناظر', 'دسترسی فقط مشاهده به تمام بخش‌ها'),
        ]
        
        for role_name, description, notes in default_roles:
            cursor.execute('''
                INSERT OR IGNORE INTO roles (role_name, description)
                VALUES (?, ?)
            ''', (role_name, description))
        
        conn.commit()
        conn.close()


class UsersDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('مدیریت کاربران و دسترسی‌ها')
        self.resize(900, 600)
        self.permissions_manager = PermissionsManager()
        self.current_user = None
        self._build_ui()
        self._load_data()
        
    def _build_ui(self):
        layout = QVBoxLayout()
        
        # تب‌ها
        tabs_layout = QHBoxLayout()
        
        btn_users = QPushButton('👥 کاربران')
        btn_roles = QPushButton('🎭 نقش‌ها')
        btn_permissions = QPushButton('🔐 دسترسی‌ها')
        
        for btn in [btn_users, btn_roles, btn_permissions]:
            btn.setMaximumHeight(30)
            btn.setStyleSheet("QPushButton { padding: 8px 15px; margin: 2px; }")
        
        btn_users.clicked.connect(lambda: self._show_tab('users'))
        btn_roles.clicked.connect(lambda: self._show_tab('roles'))
        btn_permissions.clicked.connect(lambda: self._show_tab('permissions'))
        
        tabs_layout.addWidget(btn_users)
        tabs_layout.addWidget(btn_roles)
        tabs_layout.addWidget(btn_permissions)
        tabs_layout.addStretch(1)
        
        layout.addLayout(tabs_layout)
        
        # ایجاد ویجت اصلی برای تب‌ها
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)
        
        # بخش کاربران
        self.users_widget = self._build_users_tab()
        layout.addWidget(self.users_widget)
        
        # بخش نقش‌ها (مخفی)
        self.roles_widget = self._build_roles_tab()
        self.roles_widget.hide()
        layout.addWidget(self.roles_widget)
        
        # بخش دسترسی‌ها (مخفی)
        self.permissions_widget = self._build_permissions_tab()
        self.permissions_widget.hide()
        layout.addWidget(self.permissions_widget)
        layout.addWidget(self.main_widget)
        self.setLayout(layout)
    
    def _build_users_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # دکمه‌های مدیریت کاربران
        buttons_layout = QHBoxLayout()
        btn_add_user = QPushButton('➕ افزودن کاربر')
        btn_edit_user = QPushButton('✏️ ویرایش کاربر')
        btn_delete_user = QPushButton('🗑️ حذف کاربر')
        btn_reset_pass = QPushButton('🔑 بازنشانی رمز')
        
        for btn in [btn_add_user, btn_edit_user, btn_delete_user, btn_reset_pass]:
            btn.setMaximumHeight(30)
        
        btn_add_user.clicked.connect(self._add_user)
        btn_edit_user.clicked.connect(self._edit_user)
        btn_delete_user.clicked.connect(self._delete_user)
        btn_reset_pass.clicked.connect(self._reset_password)
        
        buttons_layout.addWidget(btn_add_user)
        buttons_layout.addWidget(btn_edit_user)
        buttons_layout.addWidget(btn_delete_user)
        buttons_layout.addWidget(btn_reset_pass)
        buttons_layout.addStretch(1)
        
        layout.addLayout(buttons_layout)
        
        # جدول کاربران
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels(['ID', 'نام کاربری', 'نام کامل', 'نقش', 'وضعیت'])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.users_table)
        
        widget.setLayout(layout)
        return widget
    
    def _build_roles_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # دکمه‌های مدیریت نقش‌ها
        buttons_layout = QHBoxLayout()
        btn_add_role = QPushButton('➕ افزودن نقش')
        btn_edit_role = QPushButton('✏️ ویرایش نقش')
        btn_delete_role = QPushButton('🗑️ حذف نقش')
        btn_manage_perms = QPushButton('🔐 مدیریت دسترسی‌ها')
        
        for btn in [btn_add_role, btn_edit_role, btn_delete_role, btn_manage_perms]:
            btn.setMaximumHeight(30)
        
        btn_add_role.clicked.connect(self._add_role)
        btn_edit_role.clicked.connect(self._edit_role)
        btn_delete_role.clicked.connect(self._delete_role)
        btn_manage_perms.clicked.connect(self._manage_role_permissions)
        
        buttons_layout.addWidget(btn_add_role)
        buttons_layout.addWidget(btn_edit_role)
        buttons_layout.addWidget(btn_delete_role)
        buttons_layout.addWidget(btn_manage_perms)
        buttons_layout.addStretch(1)
        
        layout.addLayout(buttons_layout)
        
        # جدول نقش‌ها
        self.roles_table = QTableWidget()
        self.roles_table.setColumnCount(3)
        self.roles_table.setHorizontalHeaderLabels(['ID', 'نام نقش', 'توضیحات'])
        self.roles_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.roles_table)
        
        widget.setLayout(layout)
        return widget
    
    def _build_permissions_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # لیست دسترسی‌ها
        self.permissions_list = QListWidget()
        layout.addWidget(self.permissions_list)
        
        widget.setLayout(layout)
        return widget

    def _manage_role_permissions(self):
        """مدیریت دسترسی‌های نقش"""
        current_row = self.roles_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, 'خطا', 'لطفاً یک نقش را انتخاب کنید')
            return
            
        role_id = int(self.roles_table.item(current_row, 0).text())
        role_name = self.roles_table.item(current_row, 1).text()
        
        # باز کردن دیالوگ مدیریت دسترسی
        dlg = RolePermissionsDialog(role_id, role_name, self)
        dlg.exec_()
        
    def _show_tab(self, tab_name):
        """نمایش تب انتخاب شده"""
        self.users_widget.setVisible(tab_name == 'users')
        self.roles_widget.setVisible(tab_name == 'roles')
        self.permissions_widget.setVisible(tab_name == 'permissions')
    
    def _load_data(self):
        """بارگذاری داده‌ها"""
        self._load_users()
        self._load_roles()
        self._load_permissions()

    def _check_permission(self, permission_code):
        """بررسی دسترسی کاربر جاری"""
        if not self.current_user:
            return False
            
        checker = PermissionChecker(self.current_user['id'])
        return checker.has_permission(permission_code)
        
    def _load_users(self):
        """بارگذاری کاربران"""
        try:
            conn = get_conn('config')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT u.id, u.username, u.full_name, 
                       GROUP_CONCAT(r.role_name, ', ') as roles,
                       CASE WHEN u.is_active = 1 THEN 'فعال' ELSE 'غیرفعال' END as status
                FROM users u
                LEFT JOIN user_roles ur ON u.id = ur.user_id
                LEFT JOIN roles r ON ur.role_id = r.id
                GROUP BY u.id
                ORDER BY u.id
            ''')
            users = cursor.fetchall()
            
            self.users_table.setRowCount(len(users))
            for row, user in enumerate(users):
                for col, value in enumerate(user):
                    item = QTableWidgetItem(str(value))
                    self.users_table.setItem(row, col, item)
            
            conn.close()
                        
        except Exception as e:
            print(f"خطا در بارگذاری کاربران: {e}")
    
    def _load_roles(self):
        """بارگذاری نقش‌ها"""
        try:
            conn = get_conn('config')
            cursor = conn.cursor()
            cursor.execute('SELECT id, role_name, description FROM roles ORDER BY id')
            roles = cursor.fetchall()
            
            self.roles_table.setRowCount(len(roles))
            for row, role in enumerate(roles):
                for col, value in enumerate(role):
                    item = QTableWidgetItem(str(value))
                    self.roles_table.setItem(row, col, item)
            
            conn.close()
                        
        except Exception as e:
            print(f"خطا در بارگذاری نقش‌ها: {e}")
    
    def _load_permissions(self):
        """بارگذاری دسترسی‌ها"""
        try:
            conn = get_conn('config')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT module, permission_code, permission_name, description 
                FROM permissions 
                ORDER BY module, permission_code
            ''')
            permissions = cursor.fetchall()
            
            self.permissions_list.clear()
            current_module = ""
            
            for module, code, name, description in permissions:
                if module != current_module:
                    current_module = module
                    module_item = QListWidgetItem(f"📁 {module.upper()}")
                    module_item.setBackground(QColor(240, 240, 240))
                    self.permissions_list.addItem(module_item)
                
                perm_item = QListWidgetItem(f"   ✅ {name} ({code}) - {description}")
                self.permissions_list.addItem(perm_item)
            
            conn.close()
                        
        except Exception as e:
            print(f"خطا در بارگذاری دسترسی‌ها: {e}")
    
    def _add_role(self):
        """افزودن نقش جدید"""
        pass
    
    def _edit_role(self):
        """ویرایش نقش"""
        pass
    
    def _delete_role(self):
        """حذف نقش"""
        pass

    def _edit_user(self):
        """ویرایش کاربر"""
        if not self._check_permission('USR_EDIT'):
            QMessageBox.warning(self, 'خطا', 'شما دسترسی ویرایش کاربر را ندارید')
            return
            
        current_row = self.users_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, 'خطا', 'لطفاً یک کاربر را انتخاب کنید')
            return
            
        user_id = int(self.users_table.item(current_row, 0).text())
        
        try:
            from PyQt5.QtWidgets import QInputDialog, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QCheckBox
            
            # دریافت اطلاعات کاربر از دیتابیس
            conn = get_conn('config')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT username, full_name, is_active FROM users WHERE id = ?
            ''', (user_id,))
            user_data = cursor.fetchone()
            
            cursor.execute('''
                SELECT role_id FROM user_roles WHERE user_id = ?
            ''', (user_id,))
            user_role = cursor.fetchone()
            conn.close()
            
            dlg = QDialog(self)
            dlg.setWindowTitle('ویرایش کاربر')
            dlg.setFixedSize(400, 300)
            layout = QVBoxLayout()
            
            # فیلدها
            layout.addWidget(QLabel('نام کاربری:'))
            username_edit = QLineEdit(user_data[0])
            username_edit.setReadOnly(True)
            layout.addWidget(username_edit)
            
            layout.addWidget(QLabel('رمز عبور جدید (اختیاری):'))
            password_edit = QLineEdit()
            password_edit.setEchoMode(QLineEdit.Password)
            password_edit.setPlaceholderText('در صورت تغییر رمز پر شود')
            layout.addWidget(password_edit)
            
            layout.addWidget(QLabel('نام کامل:'))
            fullname_edit = QLineEdit(user_data[1])
            layout.addWidget(fullname_edit)
            
            layout.addWidget(QLabel('نقش:'))
            role_combo = QComboBox()
            # بارگذاری نقش‌ها
            conn = get_conn('config')
            cursor = conn.cursor()
            cursor.execute('SELECT id, role_name FROM roles WHERE is_active = 1')
            roles = cursor.fetchall()
            for role_id, role_name in roles:
                role_combo.addItem(role_name, role_id)
                if user_role and role_id == user_role[0]:
                    role_combo.setCurrentText(role_name)
            conn.close()
            layout.addWidget(role_combo)
            
            active_check = QCheckBox('کاربر فعال')
            active_check.setChecked(bool(user_data[2]))
            layout.addWidget(active_check)
            
            # دکمه‌ها
            btn_layout = QHBoxLayout()
            btn_save = QPushButton('💾 ذخیره تغییرات')
            btn_cancel = QPushButton('❌ انصراف')
            
            btn_save.clicked.connect(lambda: self._save_edit_user(dlg, user_id, password_edit.text(), fullname_edit.text(), role_combo.currentData(), active_check.isChecked()))
            btn_cancel.clicked.connect(dlg.reject)
            
            btn_layout.addWidget(btn_save)
            btn_layout.addWidget(btn_cancel)
            layout.addLayout(btn_layout)
            
            dlg.setLayout(layout)
            dlg.exec_()
            
        except Exception as e:
            print(f"خطا در ویرایش کاربر: {e}")

    def _save_edit_user(self, dlg, user_id, new_password, fullname, role_id, is_active):
        """ذخیره تغییرات کاربر"""
        try:
            if not fullname:
                QMessageBox.warning(self, 'خطا', 'لطفا نام کامل را وارد کنید')
                return
                
            conn = get_conn('config')
            cursor = conn.cursor()
            
            if new_password:
                cursor.execute('''
                    UPDATE users SET password = ?, full_name = ?, is_active = ?
                    WHERE id = ?
                ''', (new_password, fullname, 1 if is_active else 0, user_id))
            else:
                cursor.execute('''
                    UPDATE users SET full_name = ?, is_active = ? WHERE id = ?
                ''', (fullname, 1 if is_active else 0, user_id))
            
            cursor.execute('DELETE FROM user_roles WHERE user_id = ?', (user_id,))
            if role_id:
                cursor.execute('INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)', (user_id, role_id))
            
            conn.commit()
            conn.close()
                
            QMessageBox.information(self, 'موفق', 'تغییرات کاربر با موفقیت ذخیره شد')
            dlg.accept()
            self._load_users()
            
        except Exception as e:
            print(f"خطا در ذخیره تغییرات کاربر: {e}")
            
    def _add_user(self):
        """افزودن کاربر جدید"""
        try:
            from PyQt5.QtWidgets import QInputDialog, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QCheckBox
            
            dlg = QDialog(self)
            dlg.setWindowTitle('افزودن کاربر جدید')
            dlg.setFixedSize(400, 300)
            layout = QVBoxLayout()
            
            # فیلدها
            layout.addWidget(QLabel('نام کاربری:'))
            username_edit = QLineEdit()
            layout.addWidget(username_edit)
            
            layout.addWidget(QLabel('رمز عبور:'))
            password_edit = QLineEdit()
            password_edit.setEchoMode(QLineEdit.Password)
            layout.addWidget(password_edit)
            
            layout.addWidget(QLabel('تکرار رمز عبور:'))
            confirm_edit = QLineEdit()
            confirm_edit.setEchoMode(QLineEdit.Password)
            layout.addWidget(confirm_edit)
            
            layout.addWidget(QLabel('نام کامل:'))
            fullname_edit = QLineEdit()
            layout.addWidget(fullname_edit)
            
            layout.addWidget(QLabel('نقش:'))
            role_combo = QComboBox()
            # بارگذاری نقش‌ها
            conn = get_conn('config')
            cursor = conn.cursor()
            cursor.execute('SELECT id, role_name FROM roles WHERE is_active = 1')
            roles = cursor.fetchall()
            for role_id, role_name in roles:
                role_combo.addItem(role_name, role_id)
            conn.close()
            layout.addWidget(role_combo)
            
            active_check = QCheckBox('کاربر فعال')
            active_check.setChecked(True)
            layout.addWidget(active_check)
            
            # دکمه‌ها
            btn_layout = QHBoxLayout()
            btn_save = QPushButton('💾 ذخیره')
            btn_cancel = QPushButton('❌ انصراف')
            
            btn_save.clicked.connect(lambda: self._save_new_user(dlg, username_edit.text(), password_edit.text(), confirm_edit.text(), fullname_edit.text(), role_combo.currentData(), active_check.isChecked()))
            btn_cancel.clicked.connect(dlg.reject)
            
            btn_layout.addWidget(btn_save)
            btn_layout.addWidget(btn_cancel)
            layout.addLayout(btn_layout)
            
            dlg.setLayout(layout)
            dlg.exec_()
            
        except Exception as e:
            print(f"خطا در افزودن کاربر: {e}")

    def _save_new_user(self, dlg, username, password, confirm, fullname, role_id, is_active):
        """ذخیره کاربر جدید"""
        try:
            if not all([username, password, confirm, fullname]):
                QMessageBox.warning(self, 'خطا', 'لطفا تمام فیلدها را پر کنید')
                return
                
            if password != confirm:
                QMessageBox.warning(self, 'خطا', 'رمز عبور و تکرار آن مطابقت ندارند')
                return
                
            conn = get_conn('config')
            cursor = conn.cursor()
            
            # بررسی تکراری نبودن نام کاربری
            cursor.execute('SELECT 1 FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                QMessageBox.warning(self, 'خطا', 'این نام کاربری قبلاً استفاده شده است')
                conn.close()
                return
            
            # ایجاد کاربر
            cursor.execute('''
                INSERT INTO users (username, password, full_name, is_active)
                VALUES (?, ?, ?, ?)
            ''', (username, password, fullname, 1 if is_active else 0))
            
            user_id = cursor.lastrowid
            
            # اختصاص نقش
            if role_id:
                cursor.execute('INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)', (user_id, role_id))
            
            conn.commit()
            conn.close()
                
            QMessageBox.information(self, 'موفق', 'کاربر با موفقیت ایجاد شد')
            dlg.accept()
            self._load_users()
            
        except Exception as e:
            print(f"خطا در ذخیره کاربر: {e}")

    def _delete_user(self):
        """حذف کاربر"""
        current_row = self.users_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, 'خطا', 'لطفاً یک کاربر را انتخاب کنید')
            return
            
        user_id = int(self.users_table.item(current_row, 0).text())
        username = self.users_table.item(current_row, 1).text()
        
        reply = QMessageBox.question(self, 'تأیید حذف', 
                                    f'آیا از حذف کاربر "{username}" مطمئن هستید؟',
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                conn = get_conn('config')
                cursor = conn.cursor()
                cursor.execute('DELETE FROM user_roles WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
                conn.commit()
                conn.close()
                    
                QMessageBox.information(self, 'موفق', 'کاربر با موفقیت حذف شد')
                self._load_users()
                
            except Exception as e:
                print(f"خطا در حذف کاربر: {e}")

    def _reset_password(self):
        """بازنشانی رمز عبور"""
        try:
            from PyQt5.QtWidgets import QInputDialog
            from PyQt5.QtWidgets import QLineEdit
            current_row = self.users_table.currentRow()
            if current_row < 0:
                QMessageBox.warning(self, 'خطا', 'لطفاً یک کاربر را انتخاب کنید')
                return
                
            user_id = int(self.users_table.item(current_row, 0).text())
            username = self.users_table.item(current_row, 1).text()
            
            new_password, ok = QInputDialog.getText(self, 'بازنشانی رمز', 
                                                f'رمز جدید برای کاربر "{username}":',
                                                QLineEdit.Password)
            if ok and new_password:
                try:
                    conn = get_conn('config')
                    cursor = conn.cursor()
                    cursor.execute('UPDATE users SET password = ? WHERE id = ?', (new_password, user_id))
                    conn.commit()
                    conn.close()
                        
                    QMessageBox.information(self, 'موفق', 'رمز عبور با موفقیت تغییر کرد')
                    
                except Exception as e:
                    print(f"خطا در تغییر رمز: {e}")
        except Exception as e:
            print(f"خطا در بازنشانی رمز: {e}")


class RolePermissionsDialog(QDialog):
    def __init__(self, role_id, role_name, parent=None):
        super().__init__(parent)
        self.role_id = role_id
        self.role_name = role_name
        self.setWindowTitle(f'مدیریت دسترسی‌های نقش: {role_name}')
        self.resize(600, 500)
        self._build_ui()
        self._load_permissions()
    
    def _build_ui(self):
        layout = QVBoxLayout()
        
        # لیست دسترسی‌ها
        self.permissions_list = QListWidget()
        self.permissions_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.permissions_list)
        
        # دکمه‌ها
        btn_layout = QHBoxLayout()
        btn_save = QPushButton('💾 ذخیره دسترسی‌ها')
        btn_select_all = QPushButton('✅ انتخاب همه')
        btn_deselect_all = QPushButton('❌ لغو همه')
        btn_cancel = QPushButton('❌ انصراف')
        
        btn_save.clicked.connect(self._save_permissions)
        btn_select_all.clicked.connect(self._select_all)
        btn_deselect_all.clicked.connect(self._deselect_all)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_select_all)
        btn_layout.addWidget(btn_deselect_all)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def _load_permissions(self):
        """بارگذاری دسترسی‌ها"""
        try:
            conn = get_conn('config')
            cursor = conn.cursor()
            
            # دریافت تمام دسترسی‌ها
            cursor.execute('''
                SELECT id, permission_code, permission_name, module 
                FROM permissions ORDER BY module, permission_code
            ''')
            permissions = cursor.fetchall()
            
            # دریافت دسترسی‌های فعلی نقش
            cursor.execute('''
                SELECT permission_id FROM role_permissions WHERE role_id = ?
            ''', (self.role_id,))
            role_perms = {row[0] for row in cursor.fetchall()}
            
            self.permissions_list.clear()
            current_module = ""
            
            for perm_id, code, name, module in permissions:
                if module != current_module:
                    current_module = module
                    module_item = QListWidgetItem(f"📁 {module.upper()}")
                    module_item.setBackground(QColor(240, 240, 240))
                    module_item.setFlags(Qt.NoItemFlags)
                    self.permissions_list.addItem(module_item)
                
                perm_item = QListWidgetItem(f"   ✅ {name} ({code})")
                perm_item.setData(Qt.UserRole, perm_id)
                if perm_id in role_perms:
                    perm_item.setCheckState(Qt.Checked)
                else:
                    perm_item.setCheckState(Qt.Unchecked)
                self.permissions_list.addItem(perm_item)
            
            conn.close()
                        
        except Exception as e:
            print(f"خطا در بارگذاری دسترسی‌ها: {e}")
    
    def _select_all(self):
        """انتخاب همه دسترسی‌ها"""
        for i in range(self.permissions_list.count()):
            item = self.permissions_list.item(i)
            if item.flags() & Qt.ItemIsUserCheckable:
                item.setCheckState(Qt.Checked)
    
    def _deselect_all(self):
        """لغو انتخاب همه دسترسی‌ها"""
        for i in range(self.permissions_list.count()):
            item = self.permissions_list.item(i)
            if item.flags() & Qt.ItemIsUserCheckable:
                item.setCheckState(Qt.Unchecked)
    
    def _save_permissions(self):
        """ذخیره دسترسی‌های نقش"""
        try:
            conn = get_conn('config')
            cursor = conn.cursor()
            
            # حذف دسترسی‌های قبلی
            cursor.execute('DELETE FROM role_permissions WHERE role_id = ?', (self.role_id,))
            
            # اضافه کردن دسترسی‌های جدید
            for i in range(self.permissions_list.count()):
                item = self.permissions_list.item(i)
                if item.flags() & Qt.ItemIsUserCheckable and item.checkState() == Qt.Checked:
                    perm_id = item.data(Qt.UserRole)
                    cursor.execute('INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)', 
                                 (self.role_id, perm_id))
            
            conn.commit()
            conn.close()
            QMessageBox.information(self, 'موفق', 'دسترسی‌های نقش با موفقیت ذخیره شد')
            self.accept()
                
        except Exception as e:
            print(f"خطا در ذخیره دسترسی‌ها: {e}")


# کلاس کمکی برای بررسی دسترسی‌ها
class PermissionChecker:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.permissions_manager = PermissionsManager()
    
    def has_permission(self, permission_code):
        """بررسی آیا کاربر دسترسی دارد"""
        if not self.user_id:
            return False
        
        try:
            conn = get_conn('config')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 1 FROM user_roles ur
                JOIN role_permissions rp ON ur.role_id = rp.role_id
                JOIN permissions p ON rp.permission_id = p.id
                WHERE ur.user_id = ? AND p.permission_code = ?
            ''', (self.user_id, permission_code))
            
            result = cursor.fetchone() is not None
            conn.close()
            return result
                
        except Exception as e:
            print(f"خطا در بررسی دسترسی: {e}")
            return False


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dlg = UsersDialog()
    dlg.exec_()