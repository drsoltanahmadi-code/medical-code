import requests
import json
import os
import re
import sqlite3
import threading
import time
from datetime import datetime
from difflib import SequenceMatcher

# ======================== تنظیمات اصلی ========================
ORTHANC_URL = "http://localhost:8042"
ORTHANC_USER = "orthanc"
ORTHANC_PASS = "orthanc"
WORKLIST_URL = "http://127.0.0.1:5001"

# ======================== بارگذاری دیکشنری از فایل JSON ========================
def load_word_map(json_file="persian_map.json"):
    """بارگذاری دیکشنری تبدیل فارسی به انگلیسی از فایل JSON"""
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ خطا در بارگذاری فایل JSON: {e}")
            return {}
    else:
        print(f"⚠️ فایل {json_file} پیدا نشد! از دیکشنری پیش‌فرض استفاده می‌شود.")
        return {}

# بارگذاری دیکشنری از فایل JSON
WORD_MAP = load_word_map()

# اگر فایل JSON وجود نداشت یا خالی بود، از دیکشنری پیش‌فرض استفاده کن
if not WORD_MAP:
    WORD_MAP = {
        'یوسف': 'yousef',
        'سلطان': 'soltan',
        'احمدی': 'ahmadi',
        'محمد': 'mohammad',
        'حسین': 'hossein',
        'علی': 'ali',
        'رضا': 'reza',
        'مریم': 'maryam',
        'زهرا': 'zahra',
        'فاطمه': 'fatemeh',
        'اکبر': 'akbar',
        'کریمی': 'karimi',
        'نادری': 'naderi',
        'محمدی': 'mohammadi',
        'حسینی': 'hosseini',
        'رضایی': 'rezaei',
        'محمدزاده': 'mohammadzade',
        'حسین زاده': 'hosseinzade',
        'علی پور': 'alipour',
        'عباسی': 'abbasi',
        'باقری': 'bagheri',
        'جعفری': 'jafari',
        'موسوی': 'mousavi',
        'صادقی': 'sadeghi',
        'طاهری': 'taheri',
        'نوری': 'nouri',
        'یزدی': 'yazdi',
        'سلیمانی': 'soleimani',
        'هاشمی': 'hashemi',
        'مهدوی': 'mehdavi',
        'حیدری': 'heydari',
        'قاسمی': 'ghasemi',
        'مرادی': 'moradi',
        'شیری': 'shiri',
        'سلطانی': 'soltani',
        'فتحی': 'fathi',
        'میرزایی': 'mirzaei',
        'رضوی': 'razavi',
        'نژاد': 'nejad',
        'زاده': 'zade',
        'پور': 'pour',
        'سارا': 'sara',
        'مهدی': 'mehdi',
        'امیر': 'amir',
        'حمید': 'hamid',
        'سعید': 'saeed',
        'حسن': 'hassan',
        'عباس': 'abbas',
        'بهنام': 'behnam',
        'پریسا': 'parisa',
        'نگار': 'negar',
        'نرگس': 'narges',
        'مونا': 'mona',
        'صمدی': 'samadi',
        'اکبری': 'akbari',
        'صمد': 'samad',
        'سیمین': 'simin',
        'مینا': 'mina',
        'میترا': 'mitra',
        'هما': 'homa'
    }
    # ذخیره دیکشنری پیش‌فرض در فایل JSON
    with open("persian_map.json", 'w', encoding='utf-8') as f:
        json.dump(WORD_MAP, f, indent=2, ensure_ascii=False)
    print("✅ فایل persian_map.json با دیکشنری پیش‌فرض ساخته شد.")

def add_name_to_json(persian, english, json_file="persian_map.json"):
    """اضافه کردن اسم جدید به فایل JSON"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        data = {}
    
    data[persian] = english
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # به‌روزرسانی دیکشنری در حافظه
    WORD_MAP[persian] = english
    print(f"✅ {persian} → {english} به فایل JSON اضافه شد")

# ======================== کاراکترهای فارسی به انگلیسی ========================
CHAR_MAP = {
    'ا': 'a', 'آ': 'a', 'ب': 'b', 'پ': 'p', 'ت': 't', 'ث': 's',
    'ج': 'j', 'چ': 'ch', 'ح': 'h', 'خ': 'kh', 'د': 'd', 'ذ': 'z',
    'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'sh', 'ص': 's', 'ض': 'z',
    'ط': 't', 'ظ': 'z', 'ع': 'a', 'غ': 'gh', 'ف': 'f', 'ق': 'gh',
    'ک': 'k', 'گ': 'g', 'ل': 'l', 'م': 'm', 'ن': 'n', 'و': 'v',
    'ه': 'h', 'ی': 'y', 'ئ': 'e', 'ء': 'a',
}

def persian_to_english(text, capitalize=True):
    """تبدیل فارسی به انگلیسی با استفاده از دیکشنری کامل اسامی"""
    if not text:
        return ""
    
    words = text.strip().split()
    result_words = []
    
    for word in words:
        if word in WORD_MAP:
            result_words.append(WORD_MAP[word])
        else:
            # تبدیل حرف به حرف برای کلماتی که در دیکشنری نیستند
            converted = ''
            for char in word:
                if char in CHAR_MAP:
                    converted += CHAR_MAP[char]
                else:
                    converted += char
            if converted:
                result_words.append(converted)
    
    result = ' '.join(result_words)
    
    if capitalize:
        result = result.title()
    
    return result
# ======================== تولید کد یکتا ========================
def generate_unique_code(modality='RAD'):
    """تولید کد یکتا برای پذیرش (مثلاً RAD-20250625-0001)"""
    now = datetime.now()
    config = load_pacs_config()
    counters = config.get('counters', {'rad': 1, 'son': 1})
    if modality == 'SON':
        code = f"SON-{now.strftime('%Y%m%d')}-{counters['son']:04d}"
        counters['son'] += 1
    else:
        code = f"RAD-{now.strftime('%Y%m%d')}-{counters['rad']:04d}"
        counters['rad'] += 1
    config['counters'] = counters
    save_pacs_config(config)
    return code

# ======================== مدیریت فایل پیکربندی ========================
PACS_CONFIG_PATH = "pacs_config.json"

DEFAULT_PACS_CONFIG = {
    "worklist_server": {"url": WORKLIST_URL, "timeout": 5},
    "modalities": {
        "radiology": ["rayscan", "agfa"],
        "sonography": ["sono"]
    },
    "counters": {"rad": 1, "son": 1}
}

def load_pacs_config():
    if os.path.exists(PACS_CONFIG_PATH):
        try:
            with open(PACS_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    with open(PACS_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(DEFAULT_PACS_CONFIG, f, indent=4, ensure_ascii=False)
    return DEFAULT_PACS_CONFIG.copy()

def save_pacs_config(config):
    with open(PACS_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

# ======================== ارسال به Worklist ========================
def send_to_worklist(patient_name_en, national_id, accession_number, patient_phone="", modality='RAD'):
    """ارسال اطلاعات به Worklist PACS"""
    config = load_pacs_config()
    wl_cfg = config.get('worklist_server', {})
    modalities_cfg = config.get('modalities', {})
    
    wl_data = {
        "acc": accession_number,
        "admission_code": accession_number,
        "name": patient_name_en,
        "date": datetime.now().strftime('%Y-%m-%d'),
        "exam": "",
        "phone": patient_phone,
        "national_id": national_id,
        "patient_id": national_id,
        "added_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    if modality == 'SON':
        targets = modalities_cfg.get('sonography', ['sono'])
    else:
        targets = modalities_cfg.get('radiology', ['rayscan', 'agfa'])
    
    results = []
    for target in targets:
        try:
            r = requests.post(
                f"{wl_cfg.get('url')}/worklist/{target}/add",
                json=wl_data,
                timeout=wl_cfg.get('timeout', 5)
            )
            results.append({"target": target, "status": r.status_code})
        except Exception as e:
            results.append({"target": target, "error": str(e)})
    
    return results

# ======================== ارسال به Orthanc (PACS) ========================
def send_to_orthanc(patient_name_fa, patient_name_en, national_id, phone="", accession_number="", modality='RAD'):
    try:
        import sqlite3
        
        conn = sqlite3.connect("data/patients.db")
        cursor = conn.cursor()
        
        now = datetime.now()
        cursor.execute('''
            INSERT INTO pacs_queue (patient_name_fa, patient_name_en, national_id, phone, accession_number, modality, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (patient_name_fa, patient_name_en, national_id, phone, accession_number, modality, now.strftime("%Y/%m/%d %H:%M:%S")))
        
        conn.commit()
        queue_id = cursor.lastrowid
        conn.close()
        
        return str(queue_id)
            
    except Exception as e:
        print(f"❌ خطا: {e}")
        return None

# ======================== اصلاح Study در Orthanc (افزودن کد ملی) ========================
def add_patient_info_to_orthanc(study_id, national_id, patient_name, phone=""):
    """اضافه کردن کد ملی و شماره تلفن به Study در Orthanc"""
    try:
        payload = {
            "Replace": {
                "PatientID": national_id,
                "PatientName": patient_name,
                "PatientPhone": phone
            },
            "Force": True
        }
        
        r = requests.post(
            f"{ORTHANC_URL}/studies/{study_id}/modify",
            json=payload,
            auth=(ORTHANC_USER, ORTHANC_PASS),
            timeout=30
        )
        
        return r.status_code == 200
        
    except Exception as e:
        print(f"❌ خطا: {e}")
        return False

# ======================== نرمال‌سازی نام برای مقایسه ========================
def normalize_name(name):
    """نرمال‌سازی نام برای مقایسه بهتر"""
    if not name:
        return ""
    name = name.lower()
    name = name.replace('^', '_')
    name = name.replace(' ', '_')
    name = name.replace('-', '_')
    name = re.sub(r'_+', '_', name)
    name = re.sub(r'[^a-z_]', '', name)
    return name

# ======================== همگام‌سازی خودکار (فقط بخش‌های ضروری) ========================
def sync_ultrasound_with_ris(db_path="patients.db"):
    """همگام‌سازی خودکار سونوگرافی با پذیرش"""
    processed = set()
    
    while True:
        try:
            r = requests.get(
                f"{ORTHANC_URL}/studies",
                params={"limit": 10, "orderby": "-LastUpdate"},
                auth=(ORTHANC_USER, ORTHANC_PASS),
                timeout=10
            )
            
            if r.status_code != 200:
                time.sleep(10)
                continue
            
            studies = r.json()
            
            for study_id in studies:
                if study_id in processed:
                    continue
                
                r = requests.get(
                    f"{ORTHANC_URL}/studies/{study_id}",
                    auth=(ORTHANC_USER, ORTHANC_PASS),
                    timeout=10
                )
                
                if r.status_code != 200:
                    continue
                
                data = r.json()
                patient_id = data.get('PatientMainDicomTags', {}).get('PatientID', '')
                
                if patient_id and patient_id != '':
                    processed.add(study_id)
                    continue
                
                patient_name = data.get('PatientMainDicomTags', {}).get('PatientName', '')
                
                if patient_name:
                    # پیدا کردن بیمار در دیتابیس پذیرش
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT first_name, last_name, national_id, phone FROM admissions")
                    rows = cursor.fetchall()
                    conn.close()
                    
                    best_match = None
                    best_score = 0
                    search_name = normalize_name(patient_name)
                    
                    for row in rows:
                        name_fa = f"{row[0]} {row[1]}"
                        name_en = persian_to_english(name_fa)
                        db_name_norm = normalize_name(name_en)
                        similarity = SequenceMatcher(None, search_name, db_name_norm).ratio()
                        
                        if similarity > best_score and similarity >= 0.6:
                            best_score = similarity
                            best_match = {
                                "national_id": row[2],
                                "phone": row[3] or '',
                                "name_fa": name_fa,
                                "similarity": similarity
                            }
                    
                    if best_match:
                        add_patient_info_to_orthanc(
                            study_id,
                            best_match['national_id'],
                            patient_name,
                            best_match['phone']
                        )
                
                processed.add(study_id)
                
        except Exception as e:
            print(f"⚠️ خطا: {e}")
        
        time.sleep(10)

# ======================== شروع همگام‌سازی ========================
def start_sync_thread(db_path="patients.db"):
    """شروع همگام‌سازی خودکار در یک ترد جداگانه"""
    thread = threading.Thread(target=sync_ultrasound_with_ris, args=(db_path,), daemon=True)
    thread.start()
    print("✅ همگام‌سازی خودکار شروع شد")