# -*- coding: utf-8 -*-
"""
توابع تبدیل تاریخ میلادی به شمسی
"""
try:
    import jdatetime
except ImportError:
    jdatetime = None


def gregorian_to_jalali(year, month, day):
    """تبدیل تاریخ میلادی به شمسی"""
    if jdatetime is None:
        # اگر jdatetime نصب نشده، تاریخ میلادی را برمی‌گرداند
        return f"{year:04d}/{month:02d}/{day:02d}"
    try:
        jdate = jdatetime.date.fromgregorian(year=year, month=month, day=day)
        return f"{jdate.year:04d}/{jdate.month:02d}/{jdate.day:02d}"
    except:
        return f"{year:04d}/{month:02d}/{day:02d}"


def format_date_jalali(date_str):
    """تبدیل رشته تاریخ میلادی (YYYY-MM-DD) به شمسی"""
    if not date_str:
        return ''
    try:
        parts = date_str.split('-')
        if len(parts) == 3:
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            return gregorian_to_jalali(year, month, day)
        # اگر فرمت دیگری بود، سعی می‌کنیم پارس کنیم
        parts = date_str.split('/')
        if len(parts) == 3:
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            # اگر سال 4 رقمی و بزرگتر از 2000 باشد، میلادی است
            if year > 2000:
                return gregorian_to_jalali(year, month, day)
            # در غیر این صورت شمسی است
            return date_str
    except:
        pass
    return date_str


def get_current_jalali_date():
    """تاریخ شمسی امروز را برمی‌گرداند"""
    if jdatetime is None:
        from datetime import date
        today = date.today()
        return gregorian_to_jalali(today.year, today.month, today.day)
    today = jdatetime.date.today()
    return f"{today.year:04d}/{today.month:02d}/{today.day:02d}"


def jalali_to_gregorian(year, month, day):
    """تبدیل تاریخ شمسی به میلادی"""
    if jdatetime is None:
        # اگر jdatetime نصب نشده، همان تاریخ را برمی‌گرداند
        return year, month, day
    try:
        jdate = jdatetime.date(year, month, day)
        gdate = jdate.togregorian()
        return gdate.year, gdate.month, gdate.day
    except:
        return year, month, day


def parse_jalali_date(date_str):
    """پارس کردن رشته تاریخ شمسی (YYYY/MM/DD) و تبدیل به میلادی برای QDate"""
    if not date_str:
        return None
    try:
        parts = date_str.split('/')
        if len(parts) == 3:
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            # اگر سال بزرگتر از 2000 باشد، احتمالاً میلادی است
            if year > 2000:
                return year, month, day
            # در غیر این صورت شمسی است
            gyear, gmonth, gday = jalali_to_gregorian(year, month, day)
            return gyear, gmonth, gday
    except:
        pass
    return None

