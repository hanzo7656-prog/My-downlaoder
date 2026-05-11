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
from datetime import datetime

# ==================== import ادمین ====================
from admin_system import handle_admin_command, is_admin, admin_commands_list, get_adjusted_deadline, get_speed_multiplier

BALE_TOKEN = os.environ.get("BALE_TOKEN", "")
GH_TOKEN = os.environ.get("GH_TOKEN", "")
REPO_OWNER = os.environ.get("REPO_OWNER", "")
REPO_NAME = os.environ.get("REPO_NAME", "")
GCC_CHAT_ID = os.environ.get("GCC_CHAT_ID", "")

GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/game_state.json"
BALE_API_URL = f"https://tapi.bale.ai/bot{BALE_TOKEN}"

# ==================== توابع کمکی ====================

def load_game_state():
    try:
        headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        response = requests.get(GITHUB_API_URL, headers=headers)
        if response.status_code == 200:
            content = response.json()["content"]
            decoded = base64.b64decode(content).decode("utf-8")
            return json.loads(decoded)
        return {}
    except Exception as e:
        print(f"Error loading: {e}")
        return {}


def save_game_state(state):
    try:
        headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        response = requests.get(GITHUB_API_URL, headers=headers)
        current_sha = response.json().get("sha", "")
        
        new_content = json.dumps(state, indent=2, ensure_ascii=False)
        encoded = base64.b64encode(new_content.encode()).decode()
        
        payload = {"message": f"update {datetime.now().isoformat()}", "content": encoded, "sha": current_sha}
        response = requests.put(GITHUB_API_URL, headers=headers, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Error saving: {e}")
        return False


def send_message(chat_id, text):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(f"{BALE_API_URL}/sendMessage", json=payload)
    except Exception as e:
        print(f"Error: {e}")


def send_to_gcc(text):
    if GCC_CHAT_ID:
        send_message(GCC_CHAT_ID, text)


def get_user_data(state, user_id):
    for country_key, player_data in state.get("countries", {}).items():
        if player_data.get("user_id") == user_id:
            return player_data
    return None


def get_country_key_by_user(state, user_id):
    for country_key, player_data in state.get("countries", {}).items():
        if player_data.get("user_id") == user_id:
            return country_key
    return None


# ==================== دستورات اصلی ====================

def handle_start(state, user_id):
    existing = get_user_data(state, user_id)
    if existing:
        return f"❌ شما قبلاً به عنوان {existing.get('name_fa', '')} وارد شده‌اید.\nوضعیت: /status"
    
    for country_key, country_data in state.get("countries", {}).items():
        if country_data.get("user_id") is None:
            country_data["user_id"] = user_id
            country_data["last_login"] = datetime.now().isoformat()
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

برای مشاهده وضعیت کامل: /status
"""
    return "❌ همه کشورها پر شده‌اند. منتظر دور بعدی باشید."


def handle_status(state, user_id):
    player_data = get_user_data(state, user_id)
    if not player_data:
        return "❌ شما کشوری انتخاب نکرده‌اید. /start"
    
    name = player_data.get("name_fa", "ناشناس")
    flag = player_data.get("flag", "")
    industry = player_data.get("industry", 0)
    trade = player_data.get("trade", 0)
    diplomacy = player_data.get("diplomacy", 0)
    stability = player_data.get("stability", 5)
    
    resources = player_data.get("resources", {})
    influence = resources.get("influence", 0)
    tech = resources.get("tech_points", 0)
    ammo = resources.get("ammo", 0)
    fuel = resources.get("fuel", 0)
    prestige = resources.get("prestige", 0)
    
    industry_bar = "█" * min(industry, 10) + "░" * (10 - min(industry, 10))
    trade_bar = "█" * min(trade, 10) + "░" * (10 - min(trade, 10))
    
    return f"""
📊 *وضعیت {flag} {name}*

━━━━━━━━━━━━━━━━━━━━━
🏭 *صنعت:* {industry_bar} ({industry}/10)
💰 *تجارت:* {trade_bar} ({trade}/10)
🤝 *دیپلماسی:* {diplomacy}/10
📈 *ثبات:* {stability}/10

━━━━━━━━━━━━━━━━━━━━━
💎 نفوذ: {influence}
🔬 فناوری: {tech}
🔫 مهمات: {ammo}
⛽ سوخت: {fuel}
🏆 پرستیژ: {prestige}

دستورات: /help
"""


def handle_help(user_id):
    help_text = """
📚 *راهنمای بازی*

/start - شروع بازی
/status - وضعیت کشور
/upgrade [industry/trade/diplomacy] - ارتقاء
/buy [نام] [تعداد] - خرید تجهیزات
/attack [کشور] - اعلان جنگ
/ally [کشور] - درخواست اتحاد
/mission - مأموریت رمزنگاری
/solve [پاسخ] - حل مأموریت
/rank - جدول رتبه‌بندی
"""
    if is_admin(user_id):
        help_text += admin_commands_list()
    return help_text


# ==================== پردازش اصلی ====================

def process_update(update):
    message = update.get("message", {})
    if not message:
        return None
    
    chat_id = str(message.get("chat", {}).get("id", ""))
    text = message.get("text", "").strip()
    user_id = str(message.get("from", {}).get("id", ""))
    
    if not text:
        return None
    
    state = load_game_state()
    if not state:
        return "❌ خطا در بارگذاری بازی"
    
    response = None
    
    if text.startswith("/start"):
        response = handle_start(state, user_id)
    
    elif text.startswith("/status"):
        response = handle_status(state, user_id)
    
    elif text.startswith("/help"):
        response = handle_help(user_id)
    
    # ========== دستورات ادمین ==========
    elif text.startswith("/set_speed"):
        handle_admin_command(user_id, "set_speed", text[10:].strip(), chat_id)
        return None
    
    elif text.startswith("/game_speed"):
        handle_admin_command(user_id, "game_speed", "", chat_id)
        return None
    
    elif text.startswith("/all_stats"):
        handle_admin_command(user_id, "all_stats", "", chat_id)
        return None
    
    elif text.startswith("/player_stats"):
        handle_admin_command(user_id, "player_stats", text[13:].strip(), chat_id)
        return None
    
    elif text.startswith("/add_influence"):
        handle_admin_command(user_id, "add_influence", text[14:].strip(), chat_id)
        return None
    
    elif text.startswith("/reset_game"):
        handle_admin_command(user_id, "reset_game", "", chat_id)
        return None
    
    elif text.startswith("/admin_help"):
        handle_admin_command(user_id, "admin_help", "", chat_id)
        return None
    
    else:
        response = f"❌ دستور '{text}' شناسایی نشد.\n/help"
    
    save_game_state(state)
    return response


def main():
    print("Bot started. Waiting for updates...")
    last_update_id = 0
    
    while True:
        try:
            params = {"timeout": 30, "offset": last_update_id + 1}
            response = requests.get(f"{BALE_API_URL}/getUpdates", params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok") and data.get("result"):
                    for update in data["result"]:
                        update_id = update.get("update_id", 0)
                        if update_id > last_update_id:
                            last_update_id = update_id
                            reply = process_update(update)
                            if reply:
                                chat_id = update.get("message", {}).get("chat", {}).get("id")
                                if chat_id:
                                    send_message(str(chat_id), reply)
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(1)


if __name__ == "__main__":
    main()
