# -*- coding: utf-8 -*-
import os
import json
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), 'report_settings.json')
DEFAULTS = {
    "header_title1": "مرکز رادیولوژی و سونوگرافی",
    "header_title2": "دکتر یوسف سلطان احمدی",
    "header_subtitle": "متخصص تصویربرداری پزشکی (رادیولوژی)",
    "footer_line": "با تشکر — دکتر یوسف سلطان احمدی",
    "address_line": "آدرس و شماره تماس مرکز",
    "logo_path": os.path.join(os.path.dirname(__file__), "logo.png")  # لوگو پیش فرض
}

def load_settings() -> dict:
    """بارگذاری تنظیمات از فایل JSON"""
    if not os.path.exists(SETTINGS_PATH):
        save_settings(DEFAULTS)
        return DEFAULTS.copy()
    try:
        with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        data = DEFAULTS.copy()
    for k, v in DEFAULTS.items():
        data.setdefault(k, v)
    return data

def save_settings(data: dict) -> None:
    """ذخیره تنظیمات در فایل JSON"""
    with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class ReportSettings:
    def __init__(self):
        self.settings = load_settings()

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        save_settings(self.settings)

    def generate_pdf(self, output_path="advanced_report.pdf", body_text=""):
        """ایجاد PDF پیشرفته با لوگو و استایل مدرن"""
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4

        # پس‌زمینه رنگی
        c.setFillColorRGB(0.95, 0.97, 1)  # رنگ روشن آبی
        c.rect(0, 0, width, height, fill=True, stroke=False)

        # لوگو
        logo_path = self.get("logo_path")
        if os.path.exists(logo_path):
            logo = ImageReader(logo_path)
            c.drawImage(logo, width - 5*cm, height - 3*cm, width=3*cm, height=3*cm, mask='auto')

        # هدر
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(colors.darkblue)
        c.drawCentredString(width/2, height - 2*cm, self.get("header_title1"))
        c.setFont("Helvetica", 14)
        c.drawCentredString(width/2, height - 2.8*cm, self.get("header_title2"))
        c.setFont("Helvetica-Oblique", 12)
        c.setFillColor(colors.black)
        c.drawCentredString(width/2, height - 3.4*cm, self.get("header_subtitle"))

        # بدنه متن
        text = c.beginText(2*cm, height - 6*cm)
        text.setFont("Helvetica", 12)
        text.setFillColor(colors.black)
        for line in body_text.split('\n'):
            text.textLine(line)
        c.drawText(text)

        # خط افقی
        c.setStrokeColor(colors.darkblue)
        c.setLineWidth(1)
        c.line(2*cm, 3*cm, width - 2*cm, 3*cm)

        # فوتر
        c.setFont("Helvetica-Oblique", 10)
        c.setFillColor(colors.darkblue)
        c.drawCentredString(width/2, 2*cm, self.get("footer_line"))
        c.setFont("Helvetica", 9)
        c.drawCentredString(width/2, 1.5*cm, self.get("address_line"))

        c.showPage()
        c.save()
        print(f"✅ PDF گرافیکی پیشرفته ایجاد شد: {output_path}")

# تست سریع
if __name__ == "__main__":
    rs = ReportSettings()
    print(rs.settings)
    rs.generate_pdf(body_text="سلام!\nاین یک نمونه گزارش پیشرفته با لوگو و رنگ مدرن است.")


