import os
import shutil
from datetime import datetime

class SQLiteBackupManager:
    def __init__(self, db_path, backup_dir, max_backups=10):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.max_backups = max_backups
        os.makedirs(backup_dir, exist_ok=True)
    
    def create_backup(self):
        """ایجاد پشتیبان از کل دیتابیس"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f"backup_{timestamp}.db")
            
            shutil.copy2(self.db_path, backup_file)
            self._cleanup_old_backups()
            
            print(f"✅ پشتیبان ایجاد شد: {backup_file}")
            return backup_file
            
        except Exception as e:
            print(f"❌ خطا در ایجاد پشتیبان: {e}")
            return None
    
    def _cleanup_old_backups(self):
        """حذف خودکار پشتیبان‌های قدیمی"""
        try:
            backups = []
            for file in os.listdir(self.backup_dir):
                if file.startswith("backup_") and file.endswith(".db"):
                    file_path = os.path.join(self.backup_dir, file)
                    file_time = os.path.getctime(file_path)
                    backups.append((file_path, file_time))
            
            backups.sort(key=lambda x: x[1], reverse=True)
            
            if len(backups) > self.max_backups:
                for old_backup in backups[self.max_backups:]:
                    os.remove(old_backup[0])
                    print(f"🗑️ پشتیبان قدیمی حذف شد: {os.path.basename(old_backup[0])}")
                    
        except Exception as e:
            print(f"⚠️ خطا در پاک‌سازی: {e}")

    def restore_backup(self, backup_file=None):
        """بازیابی دیتابیس از پشتیبان"""
        try:
            if backup_file is None:
                backups = self.list_backups()
                if not backups:
                    return False
                backup_file = backups[0]['path']
            
            if not os.path.exists(backup_file):
                return False
            
            if os.path.exists(self.db_path):
                emergency_backup = f"{self.db_path}.emergency_backup"
                shutil.copy2(self.db_path, emergency_backup)
            
            shutil.copy2(backup_file, self.db_path)
            return True
            
        except Exception as e:
            return False

    def list_backups(self):
        """لیست پشتیبان‌های موجود"""
        backups = []
        try:
            for file in os.listdir(self.backup_dir):
                if file.startswith("backup_") and file.endswith(".db"):
                    file_path = os.path.join(self.backup_dir, file)
                    file_time = os.path.getctime(file_path)
                    backups.append({
                        'file': file,
                        'path': file_path,
                        'created': datetime.fromtimestamp(file_time)
                    })
            
            return sorted(backups, key=lambda x: x['created'], reverse=True)
        except Exception as e:
            return []