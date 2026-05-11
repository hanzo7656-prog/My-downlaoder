#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
سیستم مدیریت ادمین بازی
امکانات: تغییر سرعت بازی، مشاهده آمار مخفی، کنترل روی همه کشورها
"""

import json
import os
import requests
import base64
from datetime import datetime, timedelta

GH_TOKEN = os.environ.get("GH_TOKEN", "")
REPO_OWNER = os.environ.get("REPO_OWNER", "")
REPO_NAME = os.environ.get("REPO_NAME", "")
BALE_TOKEN = os.environ.get("BALE_TOKEN", "")
ADMIN_IDS = [1221618094]  # ایدی عددی تو - می‌تونی بیشتر هم اضافه کنی

GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/game_state.json"
BALE_API_URL = f"https://tapi.bale.ai/bot{BALE_TOKEN}"


def load_game_state():
    """بارگذاری game_state.json"""
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    response = requests.get(GITHUB_API_URL, headers=headers)
    if response.status_code == 200:
        content = response.json()["content"]
        decoded = base64.b64decode(content).decode("utf-8")
        return json.loads(decoded)
    return None


def save_game_state(state):
    """ذخیره game_state.json"""
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    response = requests.get(GITHUB_API_URL, headers=headers)
    current_sha = response.json().get("sha", "")
    
    new_content = json.dumps(state, indent=2, ensure_ascii=False)
    encoded = base64.b64encode(new_content.encode()).decode()
    
    payload = {"message": "[admin] update", "content": encoded, "sha": current_sha}
    response = requests.put(GITHUB_API_URL, headers=headers, json=payload)
    return response.status_code == 200


def send_message(chat_id, text):
    """ارسال پیام به کاربر"""
    url = f"{BALE_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except:
        pass


def is_admin(user_id):
    """بررسی ادمین بودن کاربر"""
    return str(user_id) in [str(a) for a in ADMIN_IDS]


def get_all_players_stats(state):
    """دریافت آمار مخفی همه بازیکنان"""
    players = state.get("countries", {})
    stats = []
    for key, p in players.items():
        stats.append({
            "name": p.get("name_fa", key),
            "user_id": p.get("user_id", "无"),
            "industry": p.get("industry", 0),
            "trade": p.get("trade", 0),
            "diplomacy": p.get("diplomacy", 0),
            "stability": p.get("stability", 0),
            "influence": p.get("resources", {}).get("influence", 0),
            "tech": p.get("resources", {}).get("tech_points", 0),
            "units_count": sum(
                sum(u.get("count", 0) for u in p.get("units", {}).get(cat, []))
                for cat in ["air", "ground", "naval", "destroyer", "submarine", "carrier"]
            )
        })
    return stats


def set_game_speed(state, speed):
    """تنظیم سرعت بازی (1=عادی، 2=دو برابر، 3=سه برابر)"""
    if speed not in [1, 2, 3]:
        return False, "سرعت فقط می‌تواند 1، 2 یا 3 باشد."
    
    state["admin"]["game_speed"] = speed
    state["admin"]["last_speed_change"] = datetime.now().isoformat()
    return True, f"سرعت بازی به {speed} برابر تغییر کرد."


def get_speed_multiplier(state):
    """دریافت ضریب سرعت برای محاسبه مهلت‌ها"""
    speed = state.get("admin", {}).get("game_speed", 1)
    return speed


def get_adjusted_deadline(base_hours, state):
    """محاسبه مهلت بر اساس سرعت بازی"""
    speed = get_speed_multiplier(state)
    adjusted_hours = base_hours / speed
    return max(adjusted_hours, 2)  # حداقل 2 ساعت


# ==================== دستورات ادمین ====================

def handle_admin_command(user_id, command, args, chat_id):
    """پردازش دستورات ادمین"""
    if not is_admin(user_id):
        send_message(chat_id, "❌ شما دسترسی ادمین ندارید.")
        return
    
    state = load_game_state()
    if not state:
        send_message(chat_id, "❌ خطا در بارگذاری وضعیت بازی")
        return
    
    if command == "set_speed":
        try:
            speed = int(args)
            success, msg = set_game_speed(state, speed)
            if success:
                save_game_state(state)
            send_message(chat_id, msg)
        except:
            send_message(chat_id, "❌ فرمت صحیح: `/set_speed 2`")
    
    elif command == "game_speed":
        speed = state.get("admin", {}).get("game_speed", 1)
        send_message(chat_id, f"⚙️ سرعت فعلی بازی: {speed} برابر")
    
    elif command == "all_stats":
        stats = get_all_players_stats(state)
        msg = "📊 *آمار مخفی همه بازیکنان*\n\n"
        for s in stats:
            msg += f"• {s['name']}\n"
            msg += f"  👤 ایدی: {s['user_id']}\n"
            msg += f"  🏭 صنعت: {s['industry']} | 💰 تجارت: {s['trade']}\n"
            msg += f"  💎 نفوذ: {s['influence']} | 🔬 فناوری: {s['tech']}\n"
            msg += f"  ⚔️ تجهیزات: {s['units_count']} واحد\n\n"
        send_message(chat_id, msg[:4000])  # محدودیت کاراکتر
    
    elif command == "player_stats":
        if not args:
            send_message(chat_id, "❌ اسم کشور را وارد کنید: `/player_stats آلمان`")
            return
        target = args.strip()
        players = state.get("countries", {})
        found = None
        for key, p in players.items():
            if p.get("name_fa") == target or p.get("name_en") == target:
                found = p
                break
        if not found:
            send_message(chat_id, f"❌ کشور '{target}' یافت نشد.")
            return
        
        msg = f"📊 *آمار مخفی {found.get('name_fa')}*\n\n"
        msg += f"🏭 صنعت: {found.get('industry', 0)}\n"
        msg += f"💰 تجارت: {found.get('trade', 0)}\n"
        msg += f"🤝 دیپلماسی: {found.get('diplomacy', 0)}\n"
        msg += f"📈 ثبات: {found.get('stability', 0)}\n"
        msg += f"😊 رضایت: {found.get('approval', 0)}\n"
        msg += f"💀 فساد: {found.get('corruption', 0)}\n"
        msg += f"💎 نفوذ: {found.get('resources', {}).get('influence', 0)}\n"
        msg += f"🔬 فناوری: {found.get('resources', {}).get('tech_points', 0)}\n"
        msg += f"⚔️ قدرت نظامی: {found.get('resources', {}).get('prestige', 0)} پرستیژ\n"
        send_message(chat_id, msg)
    
    elif command == "add_influence":
        parts = args.split()
        if len(parts) < 2:
            send_message(chat_id, "❌ فرمت: `/add_influence آلمان 500`")
            return
        target = parts[0]
        try:
            amount = int(parts[1])
        except:
            send_message(chat_id, "❌ مقدار باید عدد باشد.")
            return
        
        players = state.get("countries", {})
        for key, p in players.items():
            if p.get("name_fa") == target or p.get("name_en") == target:
                p["resources"]["influence"] = p["resources"].get("influence", 0) + amount
                save_game_state(state)
                send_message(chat_id, f"✅ {amount} نفوذ به {target} اضافه شد.")
                return
        send_message(chat_id, f"❌ کشور '{target}' یافت نشد.")
    
    elif command == "reset_game":
        send_message(chat_id, "⚠️ این دستور کل بازی را ریست می‌کند. تأیید؟ /confirm_reset")
        # در یک پیام جداگانه تأیید می‌گیریم
    
    else:
        send_message(chat_id, "❌ دستور ادمین نامعتبر.")


def admin_commands_list():
    """لیست دستورات ادمین"""
    return """
👑 *دستورات ادمین*

/set_speed [1/2/3] - تنظیم سرعت بازی (1=عادی، 2=دو برابر، 3=سه برابر)
/game_speed - نمایش سرعت فعلی بازی
/all_stats - نمایش آمار مخفی همه بازیکنان
/player_stats [کشور] - نمایش آمار مخفی یک کشور خاص
/add_influence [کشور] [مقدار] - اضافه کردن نفوذ به یک کشور
/reset_game - ریست کامل بازی (نیاز به تأیید)
"""
