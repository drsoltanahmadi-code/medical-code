# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QMessageBox)
from PyQt5.QtCore import Qt,QTimer
from PyQt5.QtGui import QFont, QPixmap
import os
from qt_db import get_conn

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('ورود به سیستم - پیشرو طب رها')
        self.setFixedSize(800, 600)
        self.current_user = None
        self._build_ui()
    
    def _build_ui(self):
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:0.5 #764ba2, stop:1 #f093fb);
            }
            QFrame#login_frame {
                background: rgba(255, 255, 255, 0.98);
                border-radius: 25px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                padding: 40px;
            }
            QLabel#title {
                color: #2c3e50;
                font-size: 26px;
                font-weight: bold;
                padding: 10px;
            }
            QLabel#subtitle {
                color: #7f8c8d;
                font-size: 14px;
                padding: 5px;
                font-weight: 500;
            }
            QLineEdit {
                border: 2px solid #e0e0e0;
                border-radius: 15px;
                padding: 8px 15px;
                font-size: 15px;
                background: rgba(248, 249, 250, 0.8);
                min-height: 20px;
                color: #2c3e50;
                font-weight: 500;
            }
            QLineEdit:focus {
                border-color: #667eea;
                background: white;
            }
            QPushButton#login_btn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px;
                font-size: 16px;
                font-weight: bold;
                min-height: 12px;
            }
            QPushButton#login_btn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a6fd8, stop:1 #6a4190);
            }
        """)

        layout = QVBoxLayout()
        
        # فریم اصلی
        frame = QFrame()
        frame.setObjectName("login_frame")
        frame_layout = QVBoxLayout()
        frame_layout.setSpacing(25)
        
        # ✅ هدر با لوگو و نام شرکت (به سبک کد دوم)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(25)
        logo_frame = QFrame()
        logo_frame.setFixedSize(150, 150)
        logo_frame.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #667eea, stop:1 #764ba2);
            border-radius: 75px;
            border: 5px solid white;
        """)
        
        logo_layout = QVBoxLayout()
        logo_layout.setContentsMargins(5, 5, 5, 5)
        
        logo_path = "logo.png"
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            if not logo_pixmap.isNull():
                logo_pixmap = logo_pixmap.scaled(140, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo_label = QLabel()
                logo_label.setPixmap(logo_pixmap)
                print(f"لوگو با موفقیت لود شد")
            else:
                logo_label = QLabel("🏥")
                logo_label.setStyleSheet("font-size: 48px; color: white; font-weight: bold;")
        else:
            logo_label = QLabel("🏥")
            logo_label.setStyleSheet("font-size: 48px; color: white; font-weight: bold;")
        
        logo_label.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo_label)
        logo_frame.setLayout(logo_layout)
       
        
        # ✅ نام شرکت (به سبک کد دوم - بزرگتر و زیباتر)
        company_layout = QVBoxLayout()
        company_layout.setSpacing(1)
        company_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        company_name = QLabel("پیشرو طب رها")
        company_name.setStyleSheet("""
            color: #667eea;
            font-size: 28px;
            font-weight: bold;
            padding: 12px 25px;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 30px;
        """)
        
        company_slogan = QLabel("مرکز تخصصی سونوگرافی و رادیولوژی")
        company_slogan.setStyleSheet("color: #7f8c8d; font-size: 14px; font-weight: 500; padding-top: 5px;")
        
        company_layout.addWidget(company_name)
        company_layout.addWidget(company_slogan)
        
        header_layout.addWidget(logo_frame)
        header_layout.addLayout(company_layout)
        header_layout.addStretch()
        
        # ✅ عنوان فرم (به سبک کد اول)
        login_title = QLabel("ورود به پنل مدیریت")
        login_title.setStyleSheet("color: #2c3e50; font-size: 20px; font-weight: bold; padding: 20px 0px 10px 0px;")
        login_title.setAlignment(Qt.AlignCenter)
        
        # فیلدهای ورود (به سبک کد اول - ساده و تمیز)
        form_layout = QVBoxLayout()
        form_layout.setSpacing(1)
        
        username_label = QLabel('👤 نام کاربری')
        username_label.setStyleSheet("color: #2c3e50; font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText('نام کاربری خود را وارد کنید...')
        
        password_label = QLabel('🔒 رمز عبور')
        password_label.setStyleSheet("color: #2c3e50; font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText('رمز عبور خود را وارد کنید...')
        
        # دکمه ورود (به سبک کد اول)
        login_btn = QPushButton('🚀 ورود به سیستم')
        login_btn.setObjectName("login_btn")
        login_btn.setCursor(Qt.PointingHandCursor)
        
        # ✅ کپی رایت (به سبک کد اول)
        copyright_label = QLabel("© 2024 پیشرو طب رها - تمام حقوق محفوظ است")
        copyright_label.setStyleSheet("color: #95a5a6; font-size: 10px; padding: 10px 0px 0px 0px;")
        copyright_label.setAlignment(Qt.AlignCenter)
        
        # ✅ چیدمان نهایی (ترکیب بهترین‌ها)
        frame_layout.addLayout(header_layout)
        frame_layout.addWidget(login_title)
        frame_layout.addSpacing(1)
        frame_layout.addLayout(form_layout)
        form_layout.addWidget(username_label)
        form_layout.addWidget(self.username_edit)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_edit)
        frame_layout.addSpacing(1)
        frame_layout.addWidget(login_btn)
        frame_layout.addWidget(copyright_label)
        
        frame.setLayout(frame_layout)
        layout.addWidget(frame)
        self.setLayout(layout)
        
        # اتصال events (به سبک کد اول با بهبود از کد دوم)
        login_btn.clicked.connect(self._do_login)
     

    def keyPressEvent(self, event):
        """مدیریت کلید Enter در کل فرم"""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # اگه روی username هستیم، فقط برو به password
            if self.username_edit.hasFocus():
                self.password_edit.setFocus()
                return  # مهم: اجازه نده رویداد پردازش بشه
            # اگه روی password هستیم، لاگین رو انجام بده
            elif self.password_edit.hasFocus():
                self._do_login()
                return
        super().keyPressEvent(event)

    def _do_login(self):
        """تابع ورود به سیستم"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
    
        if not username or not password:
            QMessageBox.warning(self, 'خطا', 'لطفاً نام کاربری و رمز عبور را وارد کنید')
            return
    
        conn = get_conn('config')
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, full_name FROM users 
                WHERE username = ? AND password = ? AND is_active = 1
            ''', (username, password))
            user = cursor.fetchone()

            if user:
                self.current_user = {
                    'id': user[0],
                    'username': user[1],
                    'full_name': user[2]
                }
                print(f"✅ کاربر وارد شد: {user[2]}")
                self.accept()
            else:
                QMessageBox.warning(self, 'خطا', 'نام کاربری یا رمز عبور اشتباه است')
                self.password_edit.clear()
                self.password_edit.setFocus()
    
        except Exception as e:
            QMessageBox.critical(self, 'خطا', f'خطا در ورود به سیستم:\n{str(e)}')
            print(f"❌ خطا: {e}")
        finally:
            conn.close()

    def get_current_user(self):
        """برگرداندن اطلاعات کاربر فعلی"""
        return self.current_user