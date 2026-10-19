# ============================================================
# فایل: tariff_config.py - کامل
# ============================================================

import json, os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tariff_config.json")

DEFAULT_CONFIG = {
    "global_prices": {
        "private_technical": 5100000,
        "private_professional": 1850000,
        "public_technical": 1140000,
        "public_professional": 553500
    }
}

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()

def ensure_columns(cur):
    """اطمینان از وجود ستون‌های جدید"""
    columns = {
        'insurance_share': 'INTEGER DEFAULT 0',
        'patient_share': 'INTEGER DEFAULT 0',
    }
    for col_name, col_def in columns.items():
        try:
            cur.execute(f"SELECT {col_name} FROM services LIMIT 1")
        except:
            cur.execute(f"ALTER TABLE services ADD COLUMN {col_name} {col_def}")

def get_service_prices(service_code):
   
    from qt_db import get_conn
    
    # ============================================
    # 🔍 نرمال‌سازی کد سرویس
    # ============================================
    service_code = str(service_code).strip()
    # حذف صفرهای جلوی کد (مثلاً 00237 → 237)
    service_code = service_code.lstrip('0')
    # اگر خالی شد، برگردان 0
    if not service_code:
        service_code = '0'
   
    
    conn = get_conn('config')
    cur = conn.cursor()
    ensure_columns(cur)
    
    # ============================================
    # 🔍 جستجو با دو روش: دقیق و با حذف صفر
    # ============================================
    cur.execute("SELECT * FROM services WHERE code = ?", (service_code,))
    row = cur.fetchone()
    
    # اگر پیدا نشد، با کد اصلی (بدون حذف صفر) دوباره جستجو کن
    if not row:
        original_code = str(service_code).lstrip('0')
        if original_code != service_code:
            
            cur.execute("SELECT * FROM services WHERE code = ?", (original_code,))
            row = cur.fetchone()
            if row:
                service_code = original_code
    
    # ============================================
    # ❌ اگر پیدا نشد، خطا بده (نه ایجاد با 1.0)
    # ============================================
    if not row:
      
        cur.execute("SELECT code FROM services ORDER BY code")
        all_codes = cur.fetchall()
     
        conn.close()
        raise ValueError(f"سرویس با کد '{service_code}' وجود ندارد!")
    
    # ============================================
    # ✅ سرویس پیدا شد - ادامه محاسبات
    # ============================================
    service = dict(row)
    
    tech_coef = float(service.get('tech_comp', 1.0))
    prof_coef = float(service.get('prof_comp', 1.0))
  
    
    config = load_config()
    prices = config.get('global_prices', {})
    
    private_tech = int(prices.get('private_technical', 0))
    private_prof = int(prices.get('private_professional', 0))
    public_tech = int(prices.get('public_technical', 0))
    public_prof = int(prices.get('public_professional', 0))

    private_price = int(private_tech * tech_coef + private_prof * prof_coef)
    govt_price = int(public_tech * tech_coef + public_prof * prof_coef)

    
    # ذخیره قیمت‌های محاسبه شده در دیتابیس
    cur.execute('UPDATE services SET private_price = ?, govt_price = ? WHERE code = ?',
                (private_price, govt_price, service_code))
    
    # محاسبه و ذخیره سهم بیمه و بیمار (برای نیروهای مسلح)
    ins_share = int(private_price * 0.70)
    pat_share = private_price - ins_share
    cur.execute('UPDATE services SET insurance_share= ?, patient_share= ? WHERE code = ?',
                (ins_share, pat_share, service_code))
    
    conn.commit()
    conn.close()

    return {
        'private_price': private_price,
        'govt_price': govt_price,
        'technical_free': int(private_tech * tech_coef),
        'professional_free': int(private_prof * prof_coef),
        'name': service.get('name', '')
    }

def calculate_insurance(service_code, count, insurance_name, supp_insurance_name=None, supp_percent=0):
    prices = get_service_prices(service_code)
    if not prices:
        return None
    
    private_price = prices['private_price'] * count
    govt_price = prices['govt_price'] * count

    # نرمال‌سازی نام بیمه
    insurance_name = insurance_name.strip()
    
    if insurance_name == "آزاد":
        insurance_share, patient_share = 0, private_price
    elif insurance_name in ["تامین اجتماعی", "خدمات درمانی"]:
        insurance_share = int(govt_price * 0.70)
        patient_share = private_price - insurance_share
    elif insurance_name == "نیروهای مسلح":
        insurance_share = int(private_price * 0.70)
        patient_share = private_price - insurance_share
    else:
        print(f"⚠️ بیمه ناشناخته: '{insurance_name}' - محاسبه به صورت آزاد")
        insurance_share, patient_share = 0, private_price
    
    if supp_insurance_name and supp_insurance_name != "ندارد" and supp_percent > 0:
        supp_share = int(private_price * supp_percent / 100) if insurance_name == "آزاد" else int(patient_share * supp_percent / 100)
    else:
        supp_share = 0
  
    
    return {
        'private_price': private_price,
        'govt_price': govt_price,
        'insurance_share': insurance_share,
        'patient_share': patient_share,
        'supp_share': supp_share,
        'final_payable': patient_share - supp_share,
        'technical_free': prices['technical_free'] * count,
        'professional_free': prices['professional_free'] * count
    }