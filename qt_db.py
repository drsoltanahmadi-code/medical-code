import sqlite3
import random
from typing import List, Dict, Any, Optional
import jdatetime
import os
import sys

# تابع برای تشخیص مسیر صحیح در حالت EXE
def get_base_path():
    """دریافت مسیر پایه بسته به حالت اجرا"""
    if getattr(sys, 'frozen', False):
        # در حالت EXE هستیم - مسیر پوشه حاوی EXE
        return os.path.dirname(sys.executable)
    else:
        # در حالت اسکریپت هستیم - مسیر جاری
        return os.path.dirname(os.path.abspath(__file__))

# ایجاد پوشه data اگر وجود ندارد
BASE_PATH = get_base_path()
DATA_PATH = os.path.join(BASE_PATH, 'data')
os.makedirs(DATA_PATH, exist_ok=True)

# تغییر مسیرها به پوشه data (با مسیر کامل)
DB_PATHS = {
    'config': os.path.join(DATA_PATH, 'config.db'),
    'patients': os.path.join(DATA_PATH, 'patients.db'),
    'templates': os.path.join(DATA_PATH, 'templates.db'),
    'reports': os.path.join(DATA_PATH, 'reports.db'),
    'financial': os.path.join(DATA_PATH, 'financial.db')
}

print(f"📂 مسیر پایه: {BASE_PATH}")
print(f"📁 مسیر دیتابیس‌ها: {DATA_PATH}")

def get_conn(db_name):
    """اتصال به دیتابیس با مدیریت مسیر صحیح"""
    if db_name not in DB_PATHS:
        raise ValueError(f"دیتابیس {db_name} معتبر نیست")
    
    db_path = DB_PATHS[db_name]
    
    # اطمینان از وجود پوشه
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    #print(f"🔗 اتصال به: {db_path}")
    conn = sqlite3.connect(db_path)

    return conn

# ==================== توابع اصلی ====================

def get_dashboard_stats():
    """آمار داشبورد"""
    try:
        conn = get_conn('patients')
        cursor = conn.cursor()
        
        today = jdatetime.date.today().strftime("%Y/%m/%d")
        cursor.execute("SELECT COUNT(*) FROM admissions WHERE admission_date = ?", (today,))
        admissions_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM admissions WHERE admission_date = ? AND total_price > 0", (today,))
        services_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT doctor_id) FROM admissions WHERE admission_date = ?", (today,))
        doctors_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(total_price) FROM admissions WHERE admission_date = ?", (today,))
        total_income = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'admissions_count': admissions_count,
            'services_count': services_count,
            'doctors_count': doctors_count,
            'total_income': total_income
        }
        
    except Exception as e:
        print(f"خطا در دریافت آمار داشبورد: {e}")
        return {}

def initialize_all_databases():
    
    
    # دیتابیس config
    try:
        with get_conn('config') as conn:
            cur = conn.cursor()
            
            cur.execute('''
                CREATE TABLE IF NOT EXISTS doctors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    family TEXT NOT NULL,
                    full_name TEXT,
                    gender TEXT DEFAULT 'male',
                    specialty TEXT,
                    phone TEXT,
                    email TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cur.execute('''
                CREATE TABLE IF NOT EXISTS insurance_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    insurance_name TEXT UNIQUE NOT NULL,
                    coverage_percent INTEGER NOT NULL,
                    insurance_type TEXT DEFAULT 'main',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cur.execute('''
                CREATE TABLE IF NOT EXISTS services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price INTEGER DEFAULT 0,
                    category TEXT DEFAULT 'عمومی',
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # جدول گروه‌ها (اگر وجود ندارد)
            cur.execute('''
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            cur.execute("INSERT OR IGNORE INTO doctors (name, family, specialty) VALUES ('دکتر', 'نمونه', 'رادیولوژی')")
            
            conn.commit()
            
    except Exception as e:
        print(f"❌ خطا در ایجاد دیتابیس config: {e}")
    
    # دیتابیس patients
    try:
        with get_conn('patients') as conn:
            cur = conn.cursor()
            
            cur.execute('''
                CREATE TABLE IF NOT EXISTS admissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    national_id TEXT,
                    insurance_name TEXT DEFAULT 'آزاد',
                    doctor_id INTEGER,
                    admission_date TEXT NOT NULL,
                    admission_time TEXT,
                    total_price INTEGER DEFAULT 0
                )
            ''')
            try:
                cur.execute("ALTER TABLE admissions ADD COLUMN supp_insurance_name TEXT")
            except:
                pass
            cur.execute('''
                CREATE TABLE IF NOT EXISTS admission_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admission_id INTEGER,
                    service_code TEXT,
                    service_name TEXT,
                    count INTEGER DEFAULT 1,
                    price INTEGER DEFAULT 0,
                    total INTEGER DEFAULT 0,
                    base_percent INTEGER DEFAULT 0,
                    base_share INTEGER DEFAULT 0,
                    patient_share INTEGER DEFAULT 0,
                    payable INTEGER DEFAULT 0,
                    supp_percent INTEGER DEFAULT 0,
                    supp_share INTEGER DEFAULT 0,
                    FOREIGN KEY (admission_id) REFERENCES admissions(id)
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS worklist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admission_code TEXT,
                    accession_number TEXT,
                    modality TEXT,
                    patient_name_en TEXT,
                    send_date TEXT,
                    send_time TEXT,
                    status TEXT DEFAULT 'ارسال شده',
                    FOREIGN KEY (admission_code) REFERENCES admissions(code)
                )
            ''')

            cur.execute('''
                CREATE TABLE IF NOT EXISTS pacs_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admission_code TEXT,
                    accession_number TEXT,
                    study_id TEXT,
                    patient_name_en TEXT,
                    send_date TEXT,
                    send_time TEXT,
                    status TEXT DEFAULT 'ارسال شده',
                    FOREIGN KEY (admission_code) REFERENCES admissions(code)
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS pacs_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_name_fa TEXT,
                    patient_name_en TEXT,
                    national_id TEXT,
                    phone TEXT,
                    accession_number TEXT,
                    modality TEXT,
                    created_date TEXT,
                    status TEXT DEFAULT 'pending'
                )
            ''')
            conn.commit()
            
    except Exception as e:
        print(f"❌ خطا در ایجاد دیتابیس patients: {e}")
    
    # دیتابیس reports
    try:
        with get_conn('reports') as conn:
            cur = conn.cursor()
            
            cur.execute('''
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admission_id INTEGER UNIQUE NOT NULL,
                    answer_text TEXT NOT NULL
                )
            ''')
            
            conn.commit()
            
    except Exception as e:
        print(f"❌ خطا در ایجاد دیتابیس reports: {e}")
    
    # دیتابیس templates
    try:
        with get_conn('templates') as conn:
            cur = conn.cursor()
            
            cur.execute('''
                CREATE TABLE IF NOT EXISTS template_subgroups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
            ''')
            
            cur.execute('''
                CREATE TABLE IF NOT EXISTS report_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    category TEXT,
                    subgroup_id INTEGER
                )
            ''')
            
            conn.commit()
            
    except Exception as e:
        print(f"❌ خطا در ایجاد دیتابیس templates: {e}")
    
    print("🎯 راه‌اندازی دیتابیس‌ها کامل شد")

# ==================== توابع پزشکان ====================

def search_doctors_by_name(search_text):
    """جستجوی پزشک با نام و نام خانوادگی"""
    try:
        conn = get_conn('config')
        cursor = conn.cursor()
        
        query = """
            SELECT id, name, family, specialty 
            FROM doctors 
            WHERE (name LIKE ? OR family LIKE ? OR name || ' ' || family LIKE ?)
            AND is_active = 1
            ORDER BY name, family
        """
        search_param = f"%{search_text}%"
        cursor.execute(query, (search_param, search_param, search_param))
        
        doctors = []
        for row in cursor.fetchall():
            doctors.append({
                'id': row[0],
                'name': row[1],
                'family': row[2],
                'specialty': row[3]
            })
        
        conn.close()
        return doctors
        
    except Exception as e:
        print(f"❌ خطا در جستجوی پزشک با نام: {e}")
        return []

def get_doctors_for_combo() -> List[Dict[str, Any]]:
    """لیست پزشکان برای کامبوباکس"""
    try:
        doctors = list_doctors()
        return [{'id': doc['id'], 'name': f"{doc.get('name', '')} {doc.get('family', '')}"} 
                for doc in doctors]
    except Exception as e:
        print(f"❌ خطا در تهیه لیست برای کامبوباکس: {e}")
        return []  # لیست خالی برگردان

def list_doctors(active_only=True):
    """لیست پزشکان"""
    try:
        with get_conn('config') as conn:
            cur = conn.cursor()
            
            # اول بررسی کن جدول وجود دارد
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='doctors'")
            if not cur.fetchone():
                print("⚠️ جدول doctors وجود ندارد")
                return []
            
            # حالا کوئری اصلی رو اجرا کن
            if active_only:
                cur.execute("SELECT * FROM doctors WHERE is_active = 1 ORDER BY name")
            else:
                cur.execute("SELECT * FROM doctors ORDER BY name")
            
            return [dict(row) for row in cur.fetchall()]
            
    except Exception as e:
        print(f"❌ خطا در دریافت لیست پزشکان: {e}")
        return []  # لیست خالی برگردان

def get_doctor_by_id(doctor_id):
    """دریافت پزشک بر اساس ID"""
    with get_conn('config') as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM doctors WHERE id = ?", (doctor_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def get_doctor_by_code(code_nezam: str) -> Optional[Dict[str, Any]]:
    """پیدا کردن پزشک بر اساس کد نظام پزشکی"""
    with get_conn('config') as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM doctors WHERE code_nezam = ?", (code_nezam,))
        row = cur.fetchone()
        return dict(row) if row else None

# ==================== توابع خدمات ====================

def list_services():
    """لیست خدمات"""
    with get_conn('config') as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM services WHERE is_active = 1")
        services = [dict(row) for row in cur.fetchall()]
        
        for service in services:
         return services

def list_services_table():
    """لیست خدمات - نام قدیمی برای سازگاری"""
    return list_services()

def search_services(search_term: str = "") -> List[Dict[str, Any]]:
    """جستجوی خدمات"""
    with get_conn('config') as conn:
        cur = conn.cursor()
        term = f"%{search_term}%"
        cur.execute("SELECT * FROM services WHERE name LIKE ? OR code LIKE ?", (term, term))
        services = [dict(row) for row in cur.fetchall()]
        
        for service in services:
            return services

def upsert_service(code=None, name=None, base_price=0, service_id=None,
                   private_price=None, govt_price=None, tech_comp=None,
                   prof_comp=None, insurance_share=None, patient_share=None,
                   private_technical=None, private_professional=None,
                   public_technical=None, public_professional=None,
                   technical_coef=None, professional_coef=None,
                   **kwargs):
    """افزودن/ویرایش خدمت با پشتیبانی از فیلدهای تعرفه"""
    try:
        with get_conn('config') as conn:
            cur = conn.cursor()
            
            # اطمینان از وجود ستون‌های جدید
            new_columns = {
                'private_technical': 'INTEGER DEFAULT 0',
                'private_professional': 'INTEGER DEFAULT 0',
                'public_technical': 'INTEGER DEFAULT 0',
                'public_professional': 'INTEGER DEFAULT 0',
                'technical_coef': 'REAL DEFAULT 2.13',
                'professional_coef': 'REAL DEFAULT 3.45',
                'private_price': 'INTEGER DEFAULT 0',
                'govt_price': 'INTEGER DEFAULT 0',
                'tech_comp': 'REAL DEFAULT 0.0',
                'prof_comp': 'REAL DEFAULT 0.0',
                'insurance_share': 'INTEGER DEFAULT 0',
                'patient_share': 'INTEGER DEFAULT 0'
            }
            
            for col_name, col_def in new_columns.items():
                try:
                    cur.execute(f"SELECT {col_name} FROM services LIMIT 1")
                except:
                    cur.execute(f"ALTER TABLE services ADD COLUMN {col_name} {col_def}")
            
            # اگر کد داده شده، بر اساس کد جستجو کن
            if code:
                cur.execute("SELECT id FROM services WHERE code = ?", (str(code),))
                existing = cur.fetchone()
                if existing:
                    service_id = existing[0]
            
            if service_id:
                cur.execute('''
                    UPDATE services SET 
                        name = COALESCE(?, name),
                        price = COALESCE(?, price),
                        code = COALESCE(?, code),
                        private_technical = COALESCE(?, private_technical),
                        private_professional = COALESCE(?, private_professional),
                        public_technical = COALESCE(?, public_technical),
                        public_professional = COALESCE(?, public_professional),
                        technical_coef = COALESCE(?, technical_coef),
                        professional_coef = COALESCE(?, professional_coef)
                    WHERE id = ?
                ''', (
                    name, base_price if base_price else None, code,
                    private_technical, private_professional,
                    public_technical, public_professional,
                    technical_coef, professional_coef,
                    service_id
                ))
                result_id = service_id
            else:
                cur.execute('''
                    INSERT INTO services 
                    (name, price, code, category, is_active,
                     private_technical, private_professional,
                     public_technical, public_professional,
                     technical_coef, professional_coef)
                    VALUES (?, ?, ?, 'عمومی', 1, ?, ?, ?, ?, ?, ?)
                ''', (
                    name, base_price, str(code) if code else None,
                    private_technical, private_professional,
                    public_technical, public_professional,
                    technical_coef or 2.13, professional_coef or 3.45
                ))
                result_id = cur.lastrowid
            
            conn.commit()
            return result_id
            
    except Exception as e:
        print(f"❌ خطا در upsert_service: {e}")
        return 0

def delete_service(service_id):
    """حذف خدمت"""
    with get_conn('config') as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM services WHERE id = ?", (service_id,))
        conn.commit()
        return cur.rowcount > 0

# ==================== توابع پذیرش ====================

def list_admissions(limit=100):
    """لیست پذیرش‌ها"""
    with get_conn('patients') as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM admissions ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(row) for row in cur.fetchall()]

def create_admission(admission_data: Dict[str, Any], items: List[Dict[str, Any]] = None) -> int:
    """ایجاد پذیرش جدید"""
    if items is None:
        items = []
    with get_conn('patients') as conn:
        cur = conn.cursor()
        code = f"ADM{random.randint(1000, 9999)}"
        
        while True:
            cur.execute("SELECT 1 FROM admissions WHERE code = ?", (code,))
            if not cur.fetchone():
                break
            code = f"ADM{random.randint(1000, 9999)}"
        
        cur.execute('''INSERT INTO admissions (code, first_name, last_name, national_id, 
                     insurance_name, doctor_id, admission_date,admission_time, total_price) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                   (code, 
                    admission_data.get('first_name', ''), 
                    admission_data.get('last_name', ''), 
                    admission_data.get('national_id', ''), 
                    admission_data.get('insurance_name', 'آزاد'), 
                    admission_data.get('doctor_id'), 
                    admission_data.get('admission_date', ''), 
                    admission_data.get('admission_time', ''),
                    admission_data.get('total_price', 0)))
        
        admission_id = cur.lastrowid
        
        for item in items:
            cur.execute('''
                INSERT INTO admission_items 
                (admission_id, service_code, service_name, count, price, total, 
                 base_percent, base_share, patient_share, payable, supp_percent, supp_share)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                admission_id,
                item.get('code', ''),
                item.get('name', ''),
                item.get('count', 1),
                item.get('price', 0),
                item.get('total', 0),
                item.get('base_percent', 0),
                item.get('base_share', 0),
                item.get('patient_share', 0),
                item.get('payable', 0),
                item.get('supp_percent', 0),
                item.get('supp_share', 0)
            ))
        
        conn.commit()
        return admission_id

def generate_admission_code() -> str:
    """تولید کد پذیرش منحصربه‌فرد"""
    with get_conn('patients') as conn:
        cur = conn.cursor()
        while True:
            code = f"ADM{random.randint(1000, 9999)}"
            cur.execute("SELECT 1 FROM admissions WHERE code = ?", (code,))
            if not cur.fetchone():
                return code

def admission_code_exists(code):
    """بررسی وجود کد پذیرش"""
    with get_conn('patients') as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM admissions WHERE code = ?", (code,))
        return cur.fetchone() is not None

def get_admission_with_items(admission_id):
    """دریافت اطلاعات پذیرش به همراه آیتم‌های آن"""
    with get_conn('patients') as conn:
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM admissions WHERE id = ?", (admission_id,))
        admission_row = cur.fetchone()
        
        if not admission_row:
            return {}
        
        admission_dict = dict(admission_row) if admission_row else {}
        
        cur.execute("""
            SELECT 
                id, admission_id, service_code, service_name,
                count, price, base_percent, base_share,
                patient_share, payable, supp_percent, supp_share
            FROM admission_items 
            WHERE admission_id = ?
        """, (admission_id,))
        
        # ============================================
        # 🔍 لاگ برای دیباگ
        # ============================================
        rows = cur.fetchall()
  
        items = []
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        for item_row in rows:
            item_dict = dict(item_row)
           
            items.append(item_dict)
        
        return {
            'admission': admission_dict,
            'items': items
        }

def list_admissions_with_answer_status():
    """دریافت لیست پذیرش‌ها با وضعیت جواب"""
    try:
        # 1. لیست پذیرش‌ها
        admissions = list_admissions(100)
        
        # 2. لیست دکترها از config.db
        doctors = []
        try:
            with get_conn('config') as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, name, family, gender FROM doctors WHERE is_active = 1")
                doctors = [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"خطا در دریافت لیست پزشکان: {e}")
        
        # 3. تبدیل به دیکشنری برای دسترسی سریع (با اطلاعات کامل)
        doctors_dict = {}
        for doc in doctors:
            doc_id = doc['id']
            full_name = doc.get('full_name', '')
            if not full_name:
                name = doc.get('name', '')
                family = doc.get('family', '')
                full_name = f"{name} {family}".strip()
            doctors_dict[doc_id] = {
                'full_name': full_name,
                'first_name': doc.get('name', ''),
                'last_name': doc.get('family', ''),
                'gender': doc.get('gender', 'male')
            }
        
        # 4. برای هر پذیرش
        results = []
        for admission in admissions:
            admission_dict = dict(admission)
            doctor_id = admission.get('doctor_id')
            if doctor_id and doctor_id in doctors_dict:
                doctor_info = doctors_dict[doctor_id]
                admission_dict['doctor_full_name'] = doctor_info['full_name']
                admission_dict['doctor_first_name'] = doctor_info['first_name']
                admission_dict['doctor_last_name'] = doctor_info['last_name']
                admission_dict['doctor_gender'] = doctor_info['gender']
            else:
                admission_dict['doctor_full_name'] = 'نامشخص'
                admission_dict['doctor_first_name'] = ''
                admission_dict['doctor_last_name'] = ''
      
            # 5. وضعیت جواب
            answer_status = 'pending'
            try:
                with get_conn('reports') as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT 1 FROM reports WHERE admission_id = ?", 
                                (admission.get('id'),))
                    if cur.fetchone():
                        answer_status = 'answered'
            except:
                pass
        
            admission['answer_status'] = answer_status
            
            results.append(admission)
        
        return results
        
    except Exception as e:
        print(f"خطا در دریافت لیست پذیرش‌ها: {e}")
        return []
def get_admission_by_code(code: str):
    """دریافت پذیرش بر اساس کد"""
    with get_conn('patients') as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM admissions WHERE code = ?", (code,))
        row = cur.fetchone()
        
        if not row:
            return None
            
        admission_dict = dict(row)
        
        # 🔧 اضافه کردن اسم دکتر
        doctor_id = admission_dict.get('doctor_id')
        if doctor_id:
            try:
                with get_conn('config') as conn2:
                    cur2 = conn2.cursor()
                    cur2.execute("SELECT name, family FROM doctors WHERE id = ?", (doctor_id,))
                    doctor_row = cur2.fetchone()
                    if doctor_row:
                        admission_dict['doctor_name'] = f"{doctor_row['name']} {doctor_row['family']}"
            except:
                admission_dict['doctor_name'] = 'نامشخص'
        
        return admission_dict

def get_admission_by_id(admission_id: int):
    """دریافت پذیرش بر اساس ID"""
    with get_conn('patients') as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM admissions WHERE id = ?", (admission_id,))
        row = cur.fetchone()
        
        if not row:
            return None
            
        admission_dict = dict(row)
        
        # 🔧 اضافه کردن اسم دکتر
        doctor_id = admission_dict.get('doctor_id')
        if doctor_id:
            try:
                with get_conn('config') as conn2:
                    cur2 = conn2.cursor()
                    cur2.execute("SELECT name, family FROM doctors WHERE id = ?", (doctor_id,))
                    doctor_row = cur2.fetchone()
                    if doctor_row:
                        admission_dict['doctor_name'] = f"{doctor_row['name']} {doctor_row['family']}"
            except:
                admission_dict['doctor_name'] = 'نامشخص'
        
        return admission_dict

# ==================== توابع گزارش‌ها و جواب‌ها ====================

def get_answer_text(admission_id):
    """دریافت متن پاسخ برای یک پذیرش"""
    with get_conn('reports') as conn:
        cur = conn.cursor()
        cur.execute("SELECT answer_text FROM reports WHERE admission_id = ?", (admission_id,))
        row = cur.fetchone()
        return row['answer_text'] if row else None

def save_answer(admission_id, answer_text, doctor_id=None):
    """ذخیره پاسخ گزارش"""
    with get_conn('reports') as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM reports WHERE admission_id = ?", (admission_id,))
        existing = cur.fetchone()
        
        if existing:
            cur.execute('UPDATE reports SET answer_text = ?, answer_date = datetime("now"), doctor_id = ? WHERE admission_id = ?', 
                       (answer_text, doctor_id, admission_id))
        else:
            cur.execute('INSERT INTO reports (admission_id, answer_text, answer_date, doctor_id) VALUES (?, ?, datetime("now"), ?)', 
                       (admission_id, answer_text, doctor_id))
        
        conn.commit()
        return True

def delete_answer(admission_id: int) -> bool:
    """حذف جواب گزارش"""
    with get_conn('reports') as conn:
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM reports WHERE admission_id = ?", (admission_id,))
            conn.commit()
            return True
        except:
            return False

def get_report_by_admission(admission_id):
    """دریافت گزارش بر اساس admission_id"""
    with get_conn('reports') as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM reports WHERE admission_id = ?", (admission_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def report_exists(admission_id):
    """بررسی وجود گزارش برای پذیرش"""
    with get_conn('reports') as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM reports WHERE admission_id = ?", (admission_id,))
        return cur.fetchone() is not None

def upsert_answer(admission_id: int, answer_text: str) -> int:
    """ذخیره/ویرایش جواب گزارش"""
    with get_conn('reports') as conn:
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM reports WHERE admission_id = ?", (admission_id,))
        existing = cur.fetchone()
        
        if existing:
            cur.execute('UPDATE reports SET answer_text=? WHERE admission_id=?', 
                       (answer_text, admission_id))
            answer_id = existing['id']
        else:
            cur.execute('INSERT INTO reports (admission_id, answer_text) VALUES (?, ?)', 
                       (admission_id, answer_text))
            answer_id = cur.lastrowid
        
        conn.commit()
        return answer_id

# ==================== توابع قالب‌های گزارش ====================

def list_report_templates(search_query: Optional[str] = None, 
                         category_filter: Optional[str] = None, 
                         subgroup_filter_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """لیست قالب‌های گزارش"""
    with get_conn('templates') as conn:
        cur = conn.cursor()
        query = "SELECT * FROM report_templates WHERE 1=1"
        params = []
        
        if category_filter:
            query += " AND category = ?"
            params.append(category_filter)
            
        if subgroup_filter_id is not None:
            query += " AND subgroup_id = ?"
            params.append(subgroup_filter_id)
            
        if search_query:
            query += " AND (title LIKE ? OR body LIKE ?)"
            search_param = f"%{search_query}%"
            params.extend([search_param, search_param])
            
        query += " ORDER BY title"
        
        cur.execute(query, tuple(params))
        templates = [dict(row) for row in cur.fetchall()]
        return templates

def upsert_report_template(template_data: Dict[str, Any]) -> int:
    """ذخیره قالب"""
    with get_conn('templates') as conn:
        cur = conn.cursor()
        
        title = template_data.get('title', '')
        body = template_data.get('body', '')
        category = template_data.get('category', 'عمومی')
        subgroup_id = template_data.get('subgroup_id')
        
        if template_data.get('id'):
            cur.execute('''
                UPDATE report_templates 
                SET title=?, body=?, category=?, subgroup_id=?
                WHERE id=?
            ''', (title, body, category, subgroup_id, template_data['id']))
            template_id = template_data['id']
        else:
            cur.execute('''
                INSERT INTO report_templates (title, body, category, subgroup_id)
                VALUES (?, ?, ?, ?)
            ''', (title, body, category, subgroup_id))
            template_id = cur.lastrowid
        
        conn.commit()
        return template_id

def insert_report_template(title: str, category: str, body: str, subgroup_id: Optional[int] = None) -> int:
    """درج قالب جدید"""
    template_data = {
        'title': title,
        'body': body,
        'category': category,
        'subgroup_id': subgroup_id
    }
    return upsert_report_template(template_data)

def update_report_template(template_id: int, title: str, body: str, category: str, subgroup_id: Optional[int] = None) -> None:
    """به‌روزرسانی قالب"""
    template_data = {
        'id': template_id,
        'title': title,
        'body': body,
        'category': category,
        'subgroup_id': subgroup_id
    }
    upsert_report_template(template_data)

def get_template_by_id(template_id: int) -> Optional[Dict[str, Any]]:
    """دریافت قالب بر اساس ID"""
    with get_conn('templates') as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM report_templates WHERE id = ?", (template_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def get_template_by_id_old(template_id: int) -> Optional[Dict[str, Any]]:
    """دریافت قالب - نام قدیمی"""
    return get_template_by_id(template_id)

def delete_report_template(template_id: int) -> bool:
    """حذف قالب"""
    with get_conn('templates') as conn:
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM report_templates WHERE id = ?", (template_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ خطا در حذف قالب: {e}")
            return False

# ==================== توابع زیرگروه‌ها ====================
def update_subgroups_table():
    """اضافه کردن فیلد category به جدول زیرگروه‌ها"""
    with get_conn('templates') as conn:
        cur = conn.cursor()
        try:
            cur.execute("ALTER TABLE template_subgroups ADD COLUMN category TEXT DEFAULT ''")
            conn.commit()
        except:
            pass
def add_subgroup(name: str, category: str = '') -> int:
    """افزودن زیرگروه با دسته‌بندی"""
    with get_conn('templates') as conn:
        cur = conn.cursor()
        try:
            cur.execute("INSERT OR IGNORE INTO template_subgroups (name, category) VALUES (?, ?)", (name, category))
            conn.commit()
            
            cur.execute("SELECT id FROM template_subgroups WHERE name = ? AND category = ?", (name, category))
            result = cur.fetchone()
            
            if result:
                return result[0]
            else:
                return -2
                
        except Exception as e:
            print(f"❌ خطا در افزودن زیرگروه: {e}")
            return -1

def delete_subgroup(subgroup_id: int) -> bool:
    """حذف زیرگروه"""
    with get_conn('templates') as conn:
        cur = conn.cursor()
        try:
            cur.execute("UPDATE report_templates SET subgroup_id = NULL WHERE subgroup_id = ?", (subgroup_id,))
            cur.execute("DELETE FROM template_subgroups WHERE id = ?", (subgroup_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ خطا در حذف زیرگروه: {e}")
            return False

def get_subgroups(category: str = None) -> List[Dict[str, Any]]:
    """دریافت لیست زیرگروه‌ها - می‌تونه بر اساس دسته‌بندی فیلتر بشه"""
    with get_conn('templates') as conn:
        cur = conn.cursor()
        if category:
            cur.execute("SELECT * FROM template_subgroups WHERE category = ? ORDER BY name", (category,))
        else:
            cur.execute("SELECT * FROM template_subgroups ORDER BY name")
        return [dict(row) for row in cur.fetchall()]

def update_template_subgroup(template_id: int, subgroup_id: Optional[int]) -> bool:
    """به‌روزرسانی زیرگروه قالب"""
    with get_conn('templates') as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE report_templates SET subgroup_id = ? WHERE id = ?",
                (subgroup_id, template_id)
            )
            conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            return False

# ==================== توابع گروه‌ها (برای سازگاری) ====================

def list_groups(parent_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """لیست گروه‌ها - برای سازگاری با qt_groups.py"""
    # در سیستم فعلی، گروه نداریم - لیست خالی برمی‌گردانیم
    return []

def upsert_group(group_data: Dict[str, Any]) -> int:
   
    return 1  # بازگرداندن یک ID فرضی

def delete_group(group_id: int) -> bool:
    
    return True

# ==================== توابع بیمه ====================

def save_insurance_settings(insurance_data: Dict[str, int]) -> None:
    """ذخیره تنظیمات بیمه در دیتابیس"""
    try:
        conn = get_conn('config')
        cursor = conn.cursor()
 
        for insurance_name, percent in insurance_data.items():
            insurance_type = "supplementary" if "تکمیلی" in insurance_name or insurance_name in ["ندارد", "سایر"] else "main"
            
            cursor.execute("SELECT 1 FROM insurance_settings WHERE insurance_name = ?", (insurance_name,))
            exists = cursor.fetchone()
            
            if exists:
                cursor.execute(
                    "UPDATE insurance_settings SET coverage_percent = ?, insurance_type = ? WHERE insurance_name = ?",
                    (percent, insurance_type, insurance_name)
                )
                
            else:
                cursor.execute(
                    "INSERT INTO insurance_settings (insurance_name, coverage_percent, insurance_type) VALUES (?, ?, ?)",
                    (insurance_name, percent, insurance_type)
                )

        conn.commit()
        conn.close()
 
    except Exception as e:
        print(f"❌ خطا در ذخیره تنظیمات بیمه: {e}")
        if conn:
            conn.rollback()
            conn.close()
        raise e

def save_insurance_settings_with_type(main_mapping: Dict[str, int], supp_mapping: Dict[str, int]) -> None:
    """ذخیره تنظیمات بیمه با تفکیک نوع در دیتابیس"""
    try:
        conn = get_conn('config')
        cursor = conn.cursor()

        
        for insurance_name, discount_percent in main_mapping.items():
            existing = cursor.execute(
                "SELECT id, insurance_type FROM insurance_settings WHERE insurance_name = ?", 
                (insurance_name,)
            ).fetchone()
            
            if existing:
                cursor.execute(
                    "UPDATE insurance_settings SET coverage_percent = ?, insurance_type = 'main' WHERE insurance_name = ?",
                    (discount_percent, insurance_name)
                )
               
            else:
                cursor.execute(
                    "INSERT INTO insurance_settings (insurance_name, coverage_percent, insurance_type) VALUES (?, ?, 'main')",
                    (insurance_name, discount_percent)
                )
               
        
        for insurance_name, discount_percent in supp_mapping.items():
            existing = cursor.execute(
                "SELECT id, insurance_type FROM insurance_settings WHERE insurance_name = ?", 
                (insurance_name,)
            ).fetchone()
            
            if existing:
                cursor.execute(
                    "UPDATE insurance_settings SET coverage_percent = ?, insurance_type = 'supplementary' WHERE insurance_name = ?",
                    (discount_percent, insurance_name)
                )
                
            else:
                cursor.execute(
                    "INSERT INTO insurance_settings (insurance_name, coverage_percent, insurance_type) VALUES (?, ?, 'supplementary')",
                    (insurance_name, discount_percent)
                )
               
        
        conn.commit()
        conn.close()
        
       
        
    except Exception as e:
        print(f"❌ خطا در ذخیره با تفکیک نوع: {e}")
        if conn:
            conn.rollback()
            conn.close()
        raise e

def load_insurance_settings() -> Dict[str, int]:
    """بارگذاری تنظیمات بیمه از دیتابیس"""
    try:
        conn = get_conn('config')
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='insurance_settings'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("⚠️ جدول insurance_settings وجود ندارد")
            conn.close()
            return {}
        
        cursor.execute("SELECT insurance_name, coverage_percent FROM insurance_settings")
        rows = cursor.fetchall()
        conn.close()
        
        insurance_data = {}
        for row in rows:
            insurance_name = row['insurance_name']
            coverage_percent = row['coverage_percent']
            insurance_data[insurance_name] = coverage_percent
        
        
        return insurance_data
        
    except Exception as e:
        print(f"❌ خطا در بارگذاری تنظیمات بیمه: {e}")
        return {}

# ==================== توابع سازگاری قدیمی ====================

def find_doctors_table():
    """پیدا کردن جدول doctors - برای سازگاری"""
    return "config"

def ensure_doctors_table():
    """اطمینان از وجود جدول doctors - برای سازگاری"""
    pass

# این فایل باید حاوی همه توابع مورد نیاز ماژول‌های دیگر باشد