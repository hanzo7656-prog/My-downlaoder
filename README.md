# بازی جنگ جهانی: رمز و فرماندهی

## نصب و راه‌اندازی

1. کلون ریپازیتوری
2. نصب کتابخانه‌ها: `pip install -r requirements.txt`
3. تنظیم متغیرهای محیطی: `BALE_TOKEN`, `GCC_CHAT_ID`
4. اجرای بات: `python scripts/bale_bot_handler.py`

## دستورات اصلی

- `/start` - شروع بازی و انتخاب کشور
- `/status` - مشاهده وضعیت کشور خود
- `/attack [country]` - اعلان جنگ
- `/upgrade [industry/trade/diplomacy]` - ارتقاء شاخص‌ها
- `/buy [unit] [count]` - خرید تجهیزات
- `/research [branch] [level]` - تحقیق فناوری
- `/ally [country]` - پیشنهاد اتحاد

## ساختار پوشه‌ها

- `scripts/` - تمام منطق بازی
- `.github/workflows/` - وظایف خودکار
- `game_state.json` - دیتابیس اصلی بازی
