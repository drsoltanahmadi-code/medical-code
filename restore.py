import os
import shutil
from datetime import datetime
from qt_db import DB_PATHS
def restore_backup(backup_file=None):
    """بازیابی دیتابیس از پشتیبان"""
    try:
        backup_dir = './backups'
        if backup_file is None:
            backup_files = []
            for file in os.listdir(backup_dir):
                if file.startswith("backup_") and file.endswith(".db"):
                    file_path = os.path.join(backup_dir, file)
                    backup_files.append(file_path)
            
            if not backup_files:
                return False
            backup_file = max(backup_files, key=os.path.getctime)
        
        if not os.path.exists(backup_file):
            return False
        
        backup_name = os.path.basename(backup_file)
        if 'config' in backup_name:
            db_path = DB_PATHS.get('config', 'data/config.db')
        elif 'patients' in backup_name:
            db_path = DB_PATHS.get('patients', 'data/patients.db')
        elif 'templates' in backup_name:
            db_path = DB_PATHS.get('templates', 'data/templates.db')
        elif 'reports' in backup_name:
            db_path = DB_PATHS.get('reports', 'data/reports.db')
        elif 'financial' in backup_name:
            db_path = DB_PATHS.get('financial', 'data/financial.db')
        else:
        
            if os.path.exists(db_path):
                emergency_backup = f"{db_path}.emergency_backup"
                shutil.copy2(db_path, emergency_backup)
        
        shutil.copy2(backup_file, db_path)
        return True
        
    except Exception as e:
        print(f"❌ خطا در بازیابی: {e}")
        return False