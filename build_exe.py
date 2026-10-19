# save as: build_exe.py
import subprocess
import shutil
import os
import sys
from pathlib import Path
import tempfile

def find_project_root():
    """پیدا کردن مسیر پروژه با جستجوی فایل‌های خاص"""
    key_files = ['qt_main.py', 'data', 'fonts', 'templates']
    current_path = Path.cwd().absolute()
    max_depth = 5
    depth = 0
    
    while depth < max_depth:
        found_all = True
        for key_file in key_files:
            if not (current_path / key_file).exists():
                found_all = False
                break
        if found_all:
            return current_path
        parent = current_path.parent
        if parent == current_path:
            break
        current_path = parent
        depth += 1
    
    search_paths = [Path.cwd(), Path.home() / 'Desktop', Path.home() / 'Documents']
    for search_path in search_paths:
        if (search_path / 'qt_main.py').exists():
            return search_path
    
    print("❌ پروژه پیدا نشد!")
    print("\nلطفاً مسیر پروژه را وارد کنید:")
    user_input = input("\nمسیر پروژه (یا Enter برای خروج): ").strip()
    if not user_input:
        sys.exit(1)
    user_path = Path(user_input).absolute()
    if (user_path / 'qt_main.py').exists():
        return user_path
    else:
        print(f"❌ فایل qt_main.py در مسیر {user_path} یافت نشد!")
        sys.exit(1)

def validate_project_structure(project_root):
    """اعتبارسنجی ساختار پروژه"""
    print("\n🔍 بررسی ساختار پروژه...")
    required_files = ['qt_main.py']
    optional_files = ['data/', 'fonts/', 'templates/', 'reports/', 'logo.ico', 'logo.png']
    missing_required = []
    missing_optional = []
    
    for file in required_files:
        if not (project_root / file).exists():
            missing_required.append(file)
        else:
            print(f"✓ {file}")
    
    for file in optional_files:
        if file.endswith('/'):
            if not (project_root / file).exists():
                missing_optional.append(file)
            else:
                print(f"✓ {file}/")
        else:
            if not (project_root / file).exists():
                missing_optional.append(file)
            else:
                print(f"✓ {file}")
    
    if missing_required:
        print("\n❌ فایل‌های ضروری یافت نشد:")
        for file in missing_required:
            print(f"  - {file}")
        return False
    
    if missing_optional:
        print("\n⚠️  فایل‌های اختیاری یافت نشد:")
        for file in missing_optional:
            print(f"  - {file}")
        print("(برنامه اجرا می‌شود اما ممکن است برخی ویژگی‌ها کار نکند)")
    
    return True

def build_exe():
    """ساخت EXE برای سیستم رادیولوژی"""
    print("🔧 ساخت EXE برای سیستم رادیولوژی - نسخه نهایی")
    print("="*60)
    
    # پیدا کردن پروژه
    print("🔍 در حال یافتن پروژه...")
    project_root = find_project_root()
    print(f"✅ پروژه یافت شد: {project_root}")
    
    # اعتبارسنجی ساختار پروژه
    if not validate_project_structure(project_root):
        input("\n❌ ساختار پروژه نامعتبر است. Enter را بزنید برای خروج...")
        sys.exit(1)
    
    # ذخیره مسیر فعلی
    original_cwd = Path.cwd()
    print(f"\n📁 مسیر فعلی: {original_cwd}")
    print(f"📁 تغییر به: {project_root}")
    os.chdir(project_root)
    
    try:
        # پاکسازی فایل‌های قدیمی
        print("\n🧹 پاکسازی فایل‌های قدیمی...")
        cleanup_items = ['build', 'dist', '__pycache__']
        for item in cleanup_items:
            item_path = Path(item)
            if item_path.exists():
                try:
                    if item_path.is_file():
                        item_path.unlink()
                    else:
                        shutil.rmtree(item_path, ignore_errors=True)
                    print(f"✓ {item}")
                except Exception as e:
                    print(f"⚠️  خطا در پاکسازی {item}: {e}")
        
        for spec_file in project_root.glob('*.spec'):
            try:
                spec_file.unlink()
                print(f"✓ {spec_file.name}")
            except:
                pass
        
        # ساخت دستور PyInstaller
        print("\n⚙️  آماده‌سازی دستور ساخت...")
        cmd = [sys.executable, '-m', 'PyInstaller', '--onefile', '--noconsole', '--windowed', '--name', 'RadiologySystem', '--clean', '--noconfirm']
        
        # اضافه کردن فایل‌های داده (فقط خواندنی)
        read_only_folders = [('fonts', 'fonts'), ('templates', 'templates'), ('reports', 'reports')]
        for src, dst in read_only_folders:
            src_path = Path(src)
            if src_path.exists():
                separator = ';' if os.name == 'nt' else ':'
                cmd.extend(['--add-data', f'{src_path}{separator}{dst}'])
                print(f"✓ اضافه شد: {src} → {dst}")
        
        # آیکون
        icon_files = ['logo.ico', 'logo.png']
        for icon_file in icon_files:
            if Path(icon_file).exists():
                cmd.extend(['--icon', icon_file])
                print(f"✓ آیکون: {icon_file}")
                break
        
        # hidden imports
        hidden_imports = ['PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'sqlite3', 'json', 'os', 'sys', 'pathlib', 'jdatetime', 'shutil', 'datetime', 'time']
        for imp in hidden_imports:
            cmd.extend(['--hidden-import', imp])
        
        # فایل اصلی
        cmd.append('qt_main.py')
        print(f"\n🔨 دستور نهایی: {' '.join(cmd[:12])}...")
        
        # اجرای PyInstaller
        print("\n⏳ در حال ساخت EXE (این مرحله ممکن است چند دقیقه طول بکشد)...")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=300)
            if result.returncode == 0:
                print("✅ PyInstaller با موفقیت اجرا شد!")
                if result.stdout:
                    lines = result.stdout.strip().split('\n')
                    if lines:
                        print("📄 خروجی PyInstaller:")
                        for line in lines[-10:]:
                            if line.strip():
                                print(f"  {line}")
            else:
                print("❌ خطا در اجرای PyInstaller!")
                if result.stderr:
                    print("خطاها:")
                    error_lines = result.stderr.strip().split('\n')
                    for line in error_lines[-20:]:
                        if line.strip():
                            print(f"  {line}")
                return False
        except subprocess.TimeoutExpired:
            print("❌ ساخت EXE زمان‌بر شد (بیش از 5 دقیقه)")
            return False
        except Exception as e:
            print(f"❌ خطا در subprocess: {e}")
            return False
        
        # عملیات پس از ساخت
        print("\n📦 عملیات پس از ساخت...")
        post_build_success = post_build_operations(project_root)
        
        if post_build_success:
            # نمایش نتیجه نهایی
            print("\n" + "="*60)
            print("🎉 ساخت EXE با موفقیت تکمیل شد!")
            print("="*60)
            
            dist_dir = project_root / 'dist'
            exe_path = dist_dir / 'RadiologySystem.exe'
            
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"\n📊 اطلاعات فایل:")
                print(f"  📍 مسیر: {exe_path}")
                print(f"  📦 حجم: {size_mb:.2f} MB")
            
            print(f"\n📁 محتویات پوشه dist:")
            for item in sorted(dist_dir.iterdir()):
                if item.is_dir():
                    file_count = len(list(item.glob('*')))
                    print(f"  📁 {item.name}/ ({file_count} فایل)")
                else:
                    size_kb = item.stat().st_size / 1024
                    print(f"  📄 {item.name} ({size_kb:.1f} KB)")
            
            print(f"\n✅ آماده توزیع!")
            print(f"\n📌 دستورالعمل:")
            print(f"  1. پوشه '{dist_dir.name}' را کپی کنید")
            print(f"  2. در سیستم کاربر Paste کنید")
            print(f"  3. روی 'RadiologySystem.exe' دوبار کلیک کنید")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"\n❌ خطای غیرمنتظره: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        os.chdir(original_cwd)
        print(f"\n📁 بازگشت به مسیر اصلی: {original_cwd}")

def post_build_operations(project_root):
    """عملیات پس از ساخت"""
    dist_dir = project_root / 'dist'
    dist_dir.mkdir(exist_ok=True)
    
    print("📋 کپی فایل‌های ضروری...")
    
    # کپی پوشه data (دیتابیس‌ها باید خارج از EXE باشند)
    data_src = project_root / 'data'
    data_dst = dist_dir / 'data'
    
    if data_src.exists():
        try:
            if data_dst.exists():
                shutil.rmtree(data_dst, ignore_errors=True)
            shutil.copytree(data_src, data_dst)
            
            # شمارش فایل‌های دیتابیس
            db_files = list(data_dst.glob('*.db'))
            print(f"✓ پوشه data/ ({len(db_files)} دیتابیس)")
            
        except Exception as e:
            print(f"⚠️  خطا در کپی دیتابیس‌ها: {e}")
            return False
    else:
        print("⚠️  پوشه data/ یافت نشد! ایجاد پوشه جدید...")
        data_dst.mkdir(exist_ok=True)
        print("✓ پوشه data/ ایجاد شد")
    
    # فایل‌های پیکربندی اضافی
    config_files = ['background.jpg', 'insurance_settings.json', 'report_settings.json', 'database_text_problems_report.json']
    for config_file in config_files:
        src = project_root / config_file
        if src.exists():
            try:
                shutil.copy2(src, dist_dir / config_file)
                size_kb = src.stat().st_size / 1024
                print(f"✓ فایل {config_file} ({size_kb:.1f} KB)")
            except Exception as e:
                print(f"⚠️  خطا در کپی {config_file}: {e}")
    
    # ایجاد پوشه‌های ضروری
    essential_folders = ['backups', 'logs', 'exports', 'temp']
    for folder in essential_folders:
        folder_path = dist_dir / folder
        folder_path.mkdir(exist_ok=True)
        print(f"✓ پوشه {folder}/ ایجاد شد")
    
    # ایجاد فایل README
    create_readme_file(dist_dir)
    
    print("✅ عملیات پس از ساخت تکمیل شد")
    return True

def create_readme_file(dist_dir):
    """ایجاد فایل راهنما"""
    readme_content = """🚀 سیستم مدیریت رادیولوژی - نسخه 2.0

✅ نصب و راه‌اندازی:
1. تمام محتوای این پوشه را در یک مکان دلخواه کپی کنید
2. روی فایل 'RadiologySystem.exe' دوبار کلیک کنید
3. منتظر بمانید تا برنامه اجرا شود

📁 ساختار پوشه:
• RadiologySystem.exe  - برنامه اصلی
• data/               - پایگاه داده‌ها (✅ قابل نوشتن)
• fonts/              - فونت‌های فارسی (داخل EXE)
• templates/          - قالب گزارش‌ها (داخل EXE)
• reports/            - گزارش‌های ذخیره شده (داخل EXE)
• backups/            - پشتیبان‌گیری
• logs/               - فایل‌های لاگ

⚠️ نکات مهم:
• برنامه به پوشه data/ نیاز دارد (برای ذخیره اطلاعات)
• از مسیرهای فارسی برای نصب استفاده نکنید
• اگر آنتی‌ویروس خطا داد، موقتاً غیرفعال کنید

🔄 نحوه به‌روزرسانی:
1. از پوشه data/ پشتیبان بگیرید
2. فایل‌های جدید را جایگزین کنید
3. پوشه data/ قدیمی را جایگزین کنید

📞 پشتیبانی:
در صورت بروز مشکل با واحد فناوری اطلاعات تماس بگیرید.

🩺 سیستم رادیولوژی - نسخه قابل حمل
"""
    
    readme_path = dist_dir / "!راهنمای نصب.txt"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✓ فایل راهنما ایجاد شد")

def main():
    """تابع اصلی"""
    print("\n" + "="*60)
    print("🏥 سیستم ساخت EXE - نسخه نهایی")
    print("🔧 دیتابیس خارج از EXE - قابل نوشتن")
    print("="*60)
    
    # بررسی PyInstaller
    try:
        import PyInstaller
        print("✓ PyInstaller نصب است")
    except ImportError:
        print("\n❌ PyInstaller نصب نیست!")
        print("لطفاً با دستور زیر نصب کنید:")
        print("pip install pyinstaller")
        input("\nEnter را بزنید برای خروج...")
        sys.exit(1)
    
    # ساخت EXE
    success = build_exe()
    
    # نتیجه نهایی
    if success:
        print("\n" + "="*60)
        print("✅ عملیات ساخت با موفقیت به پایان رسید!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ عملیات ساخت ناموفق بود!")
        print("="*60)
        print("\n🔧 عیب‌یابی:")
        print("1. مطمئن شوید Python و PyInstaller نصب هستند")
        print("2. فایل qt_main.py در مسیر پروژه وجود دارد")
        print("3. دایرکتوری پروژه دسترسی نوشتن دارد")
        print("4. آنتی‌ویروس را موقتاً غیرفعال کنید")
    
    input("\nبرای خروج Enter را بزنید...")

if __name__ == "__main__":
    main()