#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بازی جنگ جهانی: رمز و فرماندهی
هندلر اصلی بات بله
"""

import json
import os
import requests
import base64
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

# ==================== تنظیمات اولیه ====================

BALE_TOKEN = os.environ.get("BALE_TOKEN", "YOUR_BOT_TOKEN_HERE")
GITHUB_TOKEN = os.environ.get("GH_TOKEN", "")
REPO_OWNER = os.environ.get("REPO_OWNER", "your-username")
REPO_NAME = os.environ.get("REPO_NAME", "your-repo")
GAME_STATE_PATH = "game_state.json"

GCC_CHAT_ID = os.environ.get("GCC_CHAT_ID", "")

# آدرس‌های API بله
BALE_API_URL = f"https://bale.ai/api/bot{BALE_TOKEN}"
BALE_GET_UPDATES = f"{BALE_API_URL}/getUpdates"
BALE_SEND_MESSAGE = f"{BALE_API_URL}/sendMessage"
BALE_SEND_TO_GCC = f"{BALE_API_URL}/sendMessage"

# آدرس‌های API گیت‌هاب
GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{GAME_STATE_PATH}"

# ==================== توابع کمکی ====================

def load_game_state() -> Dict[str, Any]:
    """بارگذاری فایل game_state.json از گیت‌هاب"""
    try:
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        response = requests.get(GITHUB_API_URL, headers=headers)
        if response.status_code == 200:
            content = response.json()["content"]
            decoded = base64.b64decode(content).decode("utf-8")
            return json.loads(decoded)
        else:
            print(f"Error loading state: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error loading game state: {e}")
        return {}


def save_game_state(state: Dict[str, Any]) -> bool:
    """ذخیره فایل game_state.json در گیت‌هاب"""
    try:
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # دریافت sha فعلی
        response = requests.get(GITHUB_API_URL, headers=headers)
        current_sha = response.json().get("sha", "")
        
        # آماده‌سازی محتوای جدید
        new_content = json.dumps(state, indent=2, ensure_ascii=False)
        encoded_content = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")
        
        payload = {
            "message": f"update game state - {datetime.now().isoformat()}",
            "content": encoded_content,
            "sha": current_sha
        }
        
        response = requests.put(GITHUB_API_URL, headers=headers, json=payload)
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error saving game state: {e}")
        return False


def send_message(chat_id: str, text: str, parse_mode: str = "Markdown") -> bool:
    """ارسال پیام به کاربر یا گروه"""
    try:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        response = requests.post(BALE_SEND_MESSAGE, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending message: {e}")
        return False


def send_to_gcc(text: str) -> bool:
    """ارسال پیام به GCC (کانال خبری بازی)"""
    if not GCC_CHAT_ID:
        return False
    return send_message(GCC_CHAT_ID, text)


def get_user_data(state: Dict[str, Any], user_id: str) -> Optional[Dict[str, Any]]:
    """دریافت اطلاعات بازیکن با user_id"""
    players = state.get("countries", {})
    for country_key, player_data in players.items():
        if player_data.get("user_id") == user_id:
            return player_data
    return None


def get_user_id_by_country(state: Dict[str, Any], country_name: str) -> Optional[str]:
    """دریافت user_id با نام کشور"""
    for country_key, player_data in state.get("countries", {}).items():
        if player_data.get("name_fa") == country_name or player_data.get("name_en") == country_name:
            return player_data.get("user_id")
    return None


def get_country_key_by_user(state: Dict[str, Any], user_id: str) -> Optional[str]:
    """دریافت کلید کشور (مثل usa, russia) با user_id"""
    for country_key, player_data in state.get("countries", {}).items():
        if player_data.get("user_id") == user_id:
            return country_key
    return None


def add_log(state: Dict[str, Any], log_type: str, message: str):
    """افزودن لاگ به بازی"""
    if "logs" not in state:
        state["logs"] = []
    state["logs"].append({
        "timestamp": datetime.now().isoformat(),
        "type": log_type,
        "message": message
    })
    # نگهداری فقط ۱۰۰۰ لاگ آخر
    if len(state["logs"]) > 1000:
        state["logs"] = state["logs"][-1000:]


def update_last_login(state: Dict[str, Any], user_id: str):
    """به‌روزرسانی زمان آخرین ورود"""
    country_key = get_country_key_by_user(state, user_id)
    if country_key:
        state["countries"][country_key]["last_login"] = datetime.now().isoformat()


def get_daily_income(player_data: Dict[str, Any]) -> int:
    """محاسبه درآمد روزانه نفوذ"""
    industry = player_data.get("industry", 0)
    trade = player_data.get("trade", 0)
    stability = player_data.get("stability", 5)
    
    base_income = (trade * 15) + (industry * 5) + (stability * 2)
    
    # پاداش ثبات بالا
    if stability >= 8:
        base_income = int(base_income * 1.2)
    elif stability <= 2:
        base_income = int(base_income * 0.5)
    
    return base_income


# ==================== دستورات اصلی بازی ====================

def handle_start(state: Dict[str, Any], user_id: str) -> str:
    """دستور /start - شروع بازی و انتخاب کشور"""
    # بررسی اینکه آیا قبلاً کشوری انتخاب کرده
    existing = get_user_data(state, user_id)
    if existing:
        return f"شما قبلاً به عنوان {existing.get('name_fa', '')} وارد بازی شده‌اید.\nبرای مشاهده وضعیت: /status"
    
    # پیدا کردن اولین کشور بدون بازیکن
    for country_key, country_data in state.get("countries", {}).items():
        if country_data.get("user_id") is None:
            country_data["user_id"] = user_id
            country_data["last_login"] = datetime.now().isoformat()
            add_log(state, "player_joined", f"{country_data['name_fa']} به بازی پیوست.")
            save_game_state(state)
            
            return f"""
✅ شما به عنوان {country_data['name_fa']} وارد بازی شدید!

📊 وضعیت اولیه:
• صنعت: {country_data['industry']}
• تجارت: {country_data['trade']}
• دیپلماسی: {country_data['diplomacy']}
• ثبات: {country_data['stability']}

💰 منابع اولیه:
• نفوذ: {country_data['resources']['influence']}
• فناوری: {country_data['resources']['tech_points']}
• مهمات: {country_data['resources']['ammo']}
• سوخت: {country_data['resources']['fuel']}

برای مشاهده وضعیت کامل: /status
برای خرید تجهیزات: /buy
برای ارتقاء: /upgrade
"""
    
    return "❌ متأسفانه همه ۲۴ کشور پر شده‌اند. لطفاً منتظر دور بعدی بازی باشید."


def handle_status(state: Dict[str, Any], user_id: str) -> str:
    """دستور /status - نمایش وضعیت کامل کشور"""
    player_data = get_user_data(state, user_id)
    if not player_data:
        return "❌ شما هنوز کشوری انتخاب نکرده‌اید. لطفاً با /start شروع کنید."
    
    name = player_data.get("name_fa", "ناشناس")
    flag = player_data.get("flag", "")
    industry = player_data.get("industry", 0)
    trade = player_data.get("trade", 0)
    diplomacy = player_data.get("diplomacy", 0)
    stability = player_data.get("stability", 5)
    approval = player_data.get("approval", 5)
    corruption = player_data.get("corruption", 3)
    
    resources = player_data.get("resources", {})
    influence = resources.get("influence", 0)
    tech = resources.get("tech_points", 0)
    ammo = resources.get("ammo", 0)
    fuel = resources.get("fuel", 0)
    prestige = resources.get("prestige", 0)
    
    daily_income = get_daily_income(player_data)
    
    # ساخت نوار صنعت
    industry_bar = "█" * min(industry, 10) + "░" * (10 - min(industry, 10))
    trade_bar = "█" * min(trade, 10) + "░" * (10 - min(trade, 10))
    
    # تجهیزات
    units = player_data.get("units", {})
    air_count = sum(u.get("count", 0) for u in units.get("air", []))
    ground_count = sum(u.get("count", 0) for u in units.get("ground", []))
    naval_count = sum(u.get("count", 0) for u in units.get("naval", []))
    carrier_count = sum(u.get("count", 0) for u in units.get("carrier", []))
    sub_count = sum(u.get("count", 0) for u in units.get("submarine", []))
    
    # وضعیت ثبات
    stability_status = "🟢 پایدار" if stability >= 7 else "🟡 عادی" if stability >= 4 else "🔴 بحرانی"
    
    # وضعیت رضایت
    approval_status = "😊 خوب" if approval >= 7 else "😐 عادی" if approval >= 4 else "😠 بد"
    
    return f"""
📊 *وضعیت {flag} {name}*

━━━━━━━━━━━━━━━━━━━━━

🏭 *صنعت:* {industry_bar} ({industry}/10)
   ظرفیت یگان: {industry * 8 + 5}

💰 *تجارت:* {trade_bar} ({trade}/10)
   درآمد روزانه: {daily_income} نفوذ

🤝 *دیپلماسی:* {diplomacy}/10

━━━━━━━━━━━━━━━━━━━━━

📈 *شاخص‌های داخلی:*
• ثبات: {stability}/10 {stability_status}
• رضایت: {approval}/10 {approval_status}
• فساد: {corruption}/10

━━━━━━━━━━━━━━━━━━━━━

💰 *منابع:*
• نفوذ: {influence} (+{daily_income}/روز)
• فناوری: {tech}
• مهمات: {ammo}
• سوخت: {fuel}
• پرستیژ: {prestige}

━━━━━━━━━━━━━━━━━━━━━

⚔️ *تجهیزات نظامی:*
• هوایی: {air_count} فروند
• زمینی: {ground_count} دستگاه
• دریایی: {naval_count} + {carrier_count} ناو + {sub_count} زیردریایی

━━━━━━━━━━━━━━━━━━━━━

📝 *دستورات مفید:*
/buy - خرید تجهیزات
/upgrade - ارتقاء شاخص‌ها
/attack [کشور] - اعلان جنگ
/ally [کشور] - درخواست اتحاد
"""


def handle_upgrade(state: Dict[str, Any], user_id: str, args: str) -> str:
    """دستور /upgrade [industry/trade/diplomacy] - ارتقاء شاخص"""
    player_data = get_user_data(state, user_id)
    if not player_data:
        return "❌ شما هنوز کشوری انتخاب نکرده‌اید."
    
    country_key = get_country_key_by_user(state, user_id)
    
    parts = args.strip().lower().split()
    if not parts:
        return """❌ لطفاً نوع ارتقاء را مشخص کنید:
• `/upgrade industry` - ارتقاء صنعت
• `/upgrade trade` - ارتقاء تجارت
• `/upgrade diplomacy` - ارتقاء دیپلماسی"""
    
    upgrade_type = parts[0]
    
    # قیمت‌های ارتقاء بر اساس سطح فعلی
    current_value = player_data.get(upgrade_type, 0)
    if current_value >= 10:
        return f"❌ سطح {upgrade_type} شما در حال حاضر حداکثر (۱۰) است."
    
    costs = {
        "industry": [50, 80, 120, 170, 230, 300, 380, 470, 570, 680],
        "trade": [40, 60, 90, 130, 180, 240, 310, 390, 480, 580],
        "diplomacy": [30, 50, 80, 120, 170, 230, 300, 380, 470, 570]
    }
    
    cost = costs.get(upgrade_type, [])[current_value]
    if not cost:
        return f"❌ نوع ارتقاء نامعتبر. انتخاب‌ها: industry, trade, diplomacy"
    
    influence = player_data["resources"]["influence"]
    if influence < cost:
        return f"❌ نفوذ کافی ندارید. نیاز: {cost} نفوذ (شما: {influence})"
    
    # اعمال ارتقاء
    player_data[upgrade_type] = current_value + 1
    player_data["resources"]["influence"] -= cost
    
    add_log(state, "upgrade", f"{player_data['name_fa']} {upgrade_type} را به سطح {current_value + 1} ارتقاء داد.")
    
    save_game_state(state)
    
    # نام فارسی شاخص
    persian_names = {
        "industry": "صنعت",
        "trade": "تجارت",
        "diplomacy": "دیپلماسی"
    }
    
    return f"✅ {persian_names.get(upgrade_type, upgrade_type)} شما به سطح {current_value + 1} ارتقاء یافت! هزینه: {cost} نفوذ"


def handle_buy(state: Dict[str, Any], user_id: str, args: str) -> str:
    """دستور /buy [unit_name] [count] - خرید تجهیزات"""
    player_data = get_user_data(state, user_id)
    if not player_data:
        return "❌ شما هنوز کشوری انتخاب نکرده‌اید."
    
    parts = args.strip().split()
    if len(parts) < 2:
        return """❌ لطفاً نام تجهیزات و تعداد را مشخص کنید.
مثال: `/buy F22 2` یا `/buy رپتور 2`

لیست تجهیزات:
• هوایی: F22, F35, SU57, جی۲۰, تایفون, رافال, تمپست
• زمینی: آبرامز, آر ماتا, لئوپارد, چلنجر
• دریایی: نیمیتز, فورد, آرلی بروک, تایپ۵۵, یاسن"""
    
    unit_name = parts[0]
    try:
        count = int(parts[1])
    except ValueError:
        return "❌ تعداد باید عدد باشد."
    
    if count <= 0 or count > 100:
        return "❌ تعداد باید بین ۱ تا ۱۰۰ باشد."
    
    # قیمت‌های پایه تجهیزات
    prices = {
        "F22": 250, "رپتور": 250,
        "F35": 200, "لایتنینگ": 200,
        "SU57": 230, "فلون": 230,
        "جی۲۰": 180, "J20": 180,
        "تایفون": 150, "تایفون": 150,
        "رافال": 170,
        "تمپست": 280,
        "آبرامز": 180,
        "آر ماتا": 200,
        "لئوپارد": 170,
        "چلنجر": 155,
        "آرلی بروک": 250,
        "تایپ۵۵": 280,
        "یاسن": 350
    }
    
    price = prices.get(unit_name)
    if not price:
        return f"❌ تجهیزات '{unit_name}' شناسایی نشد. از /equipment لیست کامل را ببینید."
    
    total_cost = price * count
    influence = player_data["resources"]["influence"]
    
    if influence < total_cost:
        return f"❌ نفوذ کافی ندارید. نیاز: {total_cost} نفوذ (شما: {influence})"
    
    # تشخیص دسته تجهیزات و اضافه کردن
    air_units = ["F22", "رپتور", "F35", "لایتنینگ", "SU57", "فلون", "جی۲۰", "J20", "تایفون", "رافال", "تمپست"]
    ground_units = ["آبرامز", "آر ماتا", "لئوپارد", "چلنجر"]
    naval_units = ["آرلی بروک", "تایپ۵۵"]
    sub_units = ["یاسن"]
    carrier_units = ["نیمیتز", "فورد"]
    
    units = player_data.get("units", {})
    
    if unit_name in air_units:
        unit_list = units.get("air", [])
        found = False
        for u in unit_list:
            if u.get("name_fa") == unit_name or u.get("name_en") == unit_name:
                u["count"] += count
                found = True
                break
        if not found:
            unit_list.append({"name_fa": unit_name, "name_en": unit_name, "count": count, "health": 100, "experience": 0})
        units["air"] = unit_list
        
    elif unit_name in ground_units:
        unit_list = units.get("ground", [])
        found = False
        for u in unit_list:
            if u.get("name_fa") == unit_name or u.get("name_en") == unit_name:
                u["count"] += count
                found = True
                break
        if not found:
            unit_list.append({"name_fa": unit_name, "name_en": unit_name, "count": count, "health": 100, "experience": 0})
        units["ground"] = unit_list
        
    elif unit_name in naval_units:
        unit_list = units.get("destroyer", [])
        found = False
        for u in unit_list:
            if u.get("name_fa") == unit_name or u.get("name_en") == unit_name:
                u["count"] += count
                found = True
                break
        if not found:
            unit_list.append({"name_fa": unit_name, "name_en": unit_name, "count": count, "health": 100, "experience": 0})
        units["destroyer"] = unit_list
        
    elif unit_name in sub_units:
        unit_list = units.get("submarine", [])
        found = False
        for u in unit_list:
            if u.get("name_fa") == unit_name or u.get("name_en") == unit_name:
                u["count"] += count
                found = True
                break
        if not found:
            unit_list.append({"name_fa": unit_name, "name_en": unit_name, "count": count, "health": 100, "experience": 0})
        units["submarine"] = unit_list
        
    elif unit_name in carrier_units:
        unit_list = units.get("carrier", [])
        found = False
        for u in unit_list:
            if u.get("name_fa") == unit_name or u.get("name_en") == unit_name:
                u["count"] += count
                found = True
                break
        if not found:
            unit_list.append({"name_fa": unit_name, "name_en": unit_name, "count": count, "health": 100, "experience": 0})
        units["carrier"] = unit_list
        
    else:
        return f"❌ دسته تجهیزات '{unit_name}' شناسایی نشد."
    
    player_data["units"] = units
    player_data["resources"]["influence"] -= total_cost
    
    add_log(state, "purchase", f"{player_data['name_fa']} {count} عدد {unit_name} خریداری کرد. هزینه: {total_cost}")
    
    save_game_state(state)
    
    return f"✅ {count} عدد {unit_name} خریداری شد! هزینه: {total_cost} نفوذ"


def handle_attack(state: Dict[str, Any], user_id: str, args: str) -> str:
    """دستور /attack [country] - اعلان جنگ"""
    player_data = get_user_data(state, user_id)
    if not player_data:
        return "❌ شما هنوز کشوری انتخاب نکرده‌اید."
    
    if not args.strip():
        return "❌ لطفاً نام کشور هدف را مشخص کنید. مثال: `/attack آلمان`"
    
    target_country_name = args.strip()
    target_user_id = get_user_id_by_country(state, target_country_name)
    
    if not target_user_id:
        return f"❌ کشور '{target_country_name}' یافت نشد یا هنوز بازیکنی ندارد."
    
    if target_user_id == user_id:
        return "❌ نمی‌توانید به خودتان حمله کنید!"
    
    # بررسی جنگ فعال
    active_wars = player_data.get("active_wars", [])
    for war in active_wars:
        if war.get("with") == target_user_id and war.get("status") == "active":
            return "❌ شما در حال حاضر با این کشور در جنگ هستید!"
    
    # ایجاد جنگ جدید
    new_war = {
        "with": target_user_id,
        "started_at": datetime.now().isoformat(),
        "status": "active",
        "current_sector": 1,
        "current_phase": "declaration",
        "last_move": datetime.now().isoformat(),
        "attacker_sectors": [],
        "defender_sectors": []
    }
    
    active_wars.append(new_war)
    player_data["active_wars"] = active_wars
    
    # اضافه کردن به طرف مقابل
    target_player = get_user_data(state, target_user_id)
    if target_player:
        target_wars = target_player.get("active_wars", [])
        target_wars.append({
            "with": user_id,
            "started_at": datetime.now().isoformat(),
            "status": "active",
            "current_sector": 1,
            "current_phase": "declaration",
            "last_move": datetime.now().isoformat()
        })
        target_player["active_wars"] = target_wars
    
    add_log(state, "war_declared", f"{player_data['name_fa']} به {target_player.get('name_fa', 'نامشخص')} اعلام جنگ کرد.")
    
    save_game_state(state)
    
    # ارسال به GCC
    gcc_msg = f"⚔️ *اعلان جنگ*\n{player_data['flag']} {player_data['name_fa']} به {target_player.get('flag', '')} {target_country_name} اعلام جنگ داد. علت: اختلاف ارضی."
    send_to_gcc(gcc_msg)
    
    return f"""
⚔️ *اعلان جنگ به {target_country_name}*

جنگ آغاز شد! مراحل نبرد:

• مرحله ۱: پاسخ دشمن (۸ ساعت مهلت)
• مرحله ۲: استقرار نیروها (۱۲ ساعت مهلت)
• مرحله ۳: نبرد اصلی

برای استقرار نیروها:
/deploy [نیرو] [تعداد]

برای مشاهده وضعیت جنگ:
/war_status
"""


def handle_help(user_id: str) -> str:
    """دستور /help - راهنمای بازی"""
    return """
📚 *راهنمای بازی جنگ جهانی: رمز و فرماندهی*

━━━━━━━━━━━━━━━━━━━━━

*دستورات پایه:*
/start - شروع بازی و انتخاب کشور
/status - مشاهده وضعیت کشور خود
/help - نمایش همین راهنما

━━━━━━━━━━━━━━━━━━━━━

*اقتصاد و ارتقاء:*
/upgrade [industry/trade/diplomacy] - ارتقاء شاخص‌ها
/buy [نام] [تعداد] - خرید تجهیزات نظامی
/research [شاخه] [سطح] - تحقیق فناوری

━━━━━━━━━━━━━━━━━━━━━

*نظامی و جنگ:*
/attack [کشور] - اعلان جنگ
/deploy [نیرو] [تعداد] - استقرار نیرو در نبرد
/war_status - مشاهده وضعیت جنگ فعال

━━━━━━━━━━━━━━━━━━━━━

*دیپلماسی:*
/ally [کشور] - درخواست اتحاد
/peace [کشور] - پیشنهاد صلح
/sanction [کشور] - اعمال تحریم

━━━━━━━━━━━━━━━━━━━━━

*ساخت و ساز:*
/build [سازه] - ساخت پایگاه یا کارخانه
/my_structures - مشاهده سازه‌های خود

━━━━━━━━━━━━━━━━━━━━━

*سایر:*
/mission - دریافت مأموریت رمزنگاری
/rank - مشاهده جدول پتانسیل
/statement [متن] - انتشار بیانیه در GCC

برای اطلاعات بیشتر به داکیومنت بازی مراجعه کنید.
"""


# ==================== تابع اصلی پردازش پیام ====================

def process_update(update: Dict[str, Any]) -> Optional[str]:
    """پردازش یک پیام دریافتی از بات بله"""
    message = update.get("message", {})
    if not message:
        return None
    
    chat_id = str(message.get("chat", {}).get("id", ""))
    text = message.get("text", "").strip()
    user_id = str(message.get("from", {}).get("id", ""))
    
    if not text or not user_id:
        return None
    
    # بارگذاری وضعیت بازی
    state = load_game_state()
    if not state:
        return "❌ خطا در بارگذاری وضعیت بازی. لطفاً بعداً تلاش کنید."
    
    # به‌روزرسانی زمان آخرین ورود
    update_last_login(state, user_id)
    
    # پردازش دستورات
    response = None
    
    if text.startswith("/start"):
        response = handle_start(state, user_id)
        
    elif text.startswith("/status"):
        response = handle_status(state, user_id)
        
    elif text.startswith("/upgrade"):
        args = text[8:].strip()
        response = handle_upgrade(state, user_id, args)
        
    elif text.startswith("/buy"):
        args = text[4:].strip()
        response = handle_buy(state, user_id, args)
        
    elif text.startswith("/attack"):
        args = text[7:].strip()
        response = handle_attack(state, user_id, args)
        
    elif text.startswith("/help"):
        response = handle_help(user_id)
        
    else:
        # پاسخ به پیام‌های ناشناس
        response = f"❌ دستور '{text}' شناسایی نشد.\nبرای مشاهده راهنما: /help"
    
    # ذخیره تغییرات در صورت نیاز
    save_game_state(state)
    
    return response


def main():
    """حلقه اصلی دریافت پیام‌ها از بات بله"""
    print("Bot started. Waiting for updates...")
    
    last_update_id = 0
    
    while True:
        try:
            # دریافت پیام‌های جدید
            params = {
                "timeout": 30,
                "offset": last_update_id + 1
            }
            response = requests.get(BALE_GET_UPDATES, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok") and data.get("result"):
                    for update in data["result"]:
                        update_id = update.get("update_id", 0)
                        if update_id > last_update_id:
                            last_update_id = update_id
                            
                            # پردازش پیام
                            reply = process_update(update)
                            
                            # ارسال پاسخ به کاربر
                            if reply:
                                chat_id = update.get("message", {}).get("chat", {}).get("id", "")
                                if chat_id:
                                    send_message(str(chat_id), reply)
            
        except Exception as e:
            print(f"Error in main loop: {e}")
        
        time.sleep(1)


if __name__ == "__main__":
    main()
