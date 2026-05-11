#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تشخیص بازیکنان غیرفعال و حذف خودکار
هر روز ساعت 00:00 اجرا می‌شود (توسط GitHub Actions)

قوانین:
- 5 روز آنلاین نبودن = غیرفعال موقت (قابل برگشت)
- 10 روز آنلاین نبودن = حذف کامل از بازی (کشور آزاد می‌شود)
- به متحد یا همسایه اعلان می‌رود
"""

import json
import os
import requests
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple

# ==================== تنظیمات ====================

GH_TOKEN = os.environ.get("GH_TOKEN", "")
REPO_OWNER = os.environ.get("REPO_OWNER", "")
REPO_NAME = os.environ.get("REPO_NAME", "")
BALE_TOKEN = os.environ.get("BALE_TOKEN", "")
GCC_CHAT_ID = os.environ.get("GCC_CHAT_ID", "")

GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/game_state.json"
BALE_API_URL = f"https://tapi.bale.ai/bot{BALE_TOKEN}"

# ==================== توابع کمکی ====================

def load_game_state() -> Dict[str, Any]:
    """بارگذاری game_state.json از گیت‌هاب"""
    try:
        headers = {
            "Authorization": f"token {GH_TOKEN}",
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
        print(f"Error loading: {e}")
        return {}


def save_game_state(state: Dict[str, Any]) -> bool:
    """ذخیره game_state.json در گیت‌هاب"""
    try:
        headers = {
            "Authorization": f"token {GH_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        response = requests.get(GITHUB_API_URL, headers=headers)
        current_sha = response.json().get("sha", "")
        
        new_content = json.dumps(state, indent=2, ensure_ascii=False)
        encoded_content = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")
        
        payload = {
            "message": f"[auto] inactivity check {datetime.now().strftime('%Y-%m-%d')}",
            "content": encoded_content,
            "sha": current_sha
        }
        
        response = requests.put(GITHUB_API_URL, headers=headers, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Error saving: {e}")
        return False


def send_to_gcc(message: str):
    """ارسال پیام به کانال GCC"""
    if not BALE_TOKEN or not GCC_CHAT_ID:
        print("BALE_TOKEN or GCC_CHAT_ID not set")
        return
    
    url = f"{BALE_API_URL}/sendMessage"
    payload = {
        "chat_id": GCC_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        print(f"Send to GCC: {response.status_code}")
    except Exception as e:
        print(f"Error sending to GCC: {e}")


def send_message(user_id: str, text: str):
    """ارسال پیام خصوصی به کاربر"""
    if not BALE_TOKEN:
        return
    
    url = f"{BALE_API_URL}/sendMessage"
    payload = {
        "chat_id": user_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending to user {user_id}: {e}")


def get_speed_multiplier(state: Dict[str, Any]) -> int:
    """دریافت ضریب سرعت بازی"""
    return state.get("admin", {}).get("game_speed", 1)


def get_inactivity_threshold(state: Dict[str, Any]) -> Tuple[int, int]:
    """
    دریافت آستانه‌های غیرفعالی بر اساس سرعت بازی
    بازگشت: (آستانه هشدار روز، آستانه حذف روز)
    """
    speed = get_speed_multiplier(state)
    # با افزایش سرعت، آستانه‌ها کاهش می‌یابد
    warning_days = max(3, int(5 / speed))
    removal_days = max(7, int(10 / speed))
    return warning_days, removal_days


def reset_country(country_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    ریست کردن یک کشور به حالت اولیه (برای بازیکن جدید)
    """
    # ذخیره نام و پرچم
    name_fa = country_data.get("name_fa", "")
    name_en = country_data.get("name_en", "")
    flag = country_data.get("flag", "")
    
    # وضعیت اولیه
    reset_data = {
        "name_fa": name_fa,
        "name_en": name_en,
        "flag": flag,
        "industry": 2,
        "trade": 2,
        "diplomacy": 2,
        "stability": 5,
        "approval": 5,
        "corruption": 3,
        "resources": {
            "influence": 200,
            "tech_points": 40,
            "ammo": 100,
            "fuel": 300,
            "prestige": 0
        },
        "units": {
            "air": [],
            "ground": [],
            "naval": [],
            "destroyer": [],
            "submarine": [],
            "carrier": [],
            "artillery": [],
            "air_defense": []
        },
        "research": {
            "military": 0,
            "industrial": 0,
            "economic": 0,
            "diplomacy": 0,
            "nuclear": 0
        },
        "structures": [],
        "infrastructure": {
            "road": 0,
            "port": 0,
            "airport": 0,
            "power": 0,
            "internet": 0
        },
        "treaties": [],
        "active_wars": [],
        "coordinates": country_data.get("coordinates", {"x": "E", "y": 4}),
        "last_login": None,
        "user_id": None,
        "away_mode": None,
        "is_active": True,
        "sanctioned": False,
        "used_nuclear": False
    }
    
    return reset_data


# ==================== تابع اصلی ====================

def check_inactivity():
    """بررسی بازیکنان غیرفعال و اعمال قوانین"""
    print(f"Checking inactivity at {datetime.now().isoformat()}")
    
    state = load_game_state()
    if not state:
        print("Failed to load game state")
        return
    
    players = state.get("countries", {})
    warning_days, removal_days = get_inactivity_threshold(state)
    now = datetime.now()
    
    warnings_sent = []
    removed_players = []
    auto_reset_players = []
    
    for country_key, player in players.items():
        user_id = player.get("user_id")
        
        # رد کردن کشورهای بدون بازیکن
        if user_id is None:
            continue
        
        name = player.get("name_fa", country_key)
        last_login_str = player.get("last_login")
        
        # اگر هیچ وقت لاگین نکرده
        if not last_login_str:
            # غیرفعال در نظر گرفته می‌شود
            days_inactive = 999
        else:
            try:
                last_login = datetime.fromisoformat(last_login_str)
                days_inactive = (now - last_login).days
            except:
                days_inactive = 999
        
        # مرحله 1: هشدار به بازیکن (5 روز غیرفعال)
        if days_inactive >= warning_days and days_inactive < removal_days:
            if player.get("warning_sent", False):
                continue
            
            player["warning_sent"] = True
            
            # هشدار به خود بازیکن
            warning_msg = f"""⚠️ *اخطار غیرفعالی*
کشور {name} شما به مدت {warning_days} روز است که وارد بازی نشده‌اید.

اگر تا {removal_days - warning_days} روز دیگر وارد نشوید، کشور شما از بازی حذف می‌شود و یک بازیکن جدید جایگزین می‌شود.

برای ادامه بازی کافیست یک پیام خصوصی به بات بفرستید (مثلاً /status).

{removal_days - warning_days} روز فرصت دارید.
"""
            send_message(user_id, warning_msg)
            
            # اعلان به GCC (اختیاری)
            warnings_sent.append(f"• {name}: {warning_days} روز غیرفعال")
            
            print(f"Warning sent to {name} (user: {user_id})")
        
        # مرحله 2: حذف بازیکن (10 روز غیرفعال)
        elif days_inactive >= removal_days:
            # ذخیره اطلاعات برای گزارش
            removed_players.append(name)
            
            # ارسال اعلان خروج به بازیکن
            removal_msg = f"""❌ *حذف از بازی*
کشور {name} شما به دلیل {removal_days} روز عدم فعالیت از بازی حذف شد.

کشور شما برای بازیکنان جدید آزاد شد.
اگر می‌خواهید دوباره بازی کنید، می‌توانید با /start یک کشور جدید انتخاب کنید (در صورت وجود جای خالی).
"""
            send_message(user_id, removal_msg)
            
            # ریست کشور
            player = reset_country(player)
            players[country_key] = player
            
            auto_reset_players.append(name)
            print(f"Player {name} removed due to inactivity")
    
    # ارسال اعلان‌ها به GCC
    if warnings_sent:
        warning_text = f"⚠️ *بازیکنان در آستانه حذف*\n" + "\n".join(warnings_sent[:5])
        if len(warnings_sent) > 5:
            warning_text += f"\n... و {len(warnings_sent)-5} کشور دیگر"
        send_to_gcc(warning_text)
    
    if removed_players:
        removal_text = f"❌ *بازیکنان حذف شده*\n" + "\n".join([f"• {name}" for name in removed_players[:10]])
        removal_text += f"\n\nاین کشورها برای بازیکنان جدید آزاد شدند."
        send_to_gcc(removal_text)
    
    # ذخیره تغییرات
    if warnings_sent or removed_players:
        save_game_state(state)
        print(f"Inactivity check completed. Warnings: {len(warnings_sent)}, Removals: {len(removed_players)}")
    else:
        print("No inactive players found")


def get_inactive_players_list(state: Dict[str, Any]) -> List[Tuple[str, str, int]]:
    """
    دریافت لیست بازیکنان غیرفعال برای گزارش
    بازگشت: لیست (نام کشور، نام کاربری، روزهای غیرفعال)
    """
    players = state.get("countries", {})
    now = datetime.now()
    inactive = []
    
    for country_key, player in players.items():
        user_id = player.get("user_id")
        if user_id is None:
            continue
        
        last_login_str = player.get("last_login")
        if not last_login_str:
            inactive.append((player.get("name_fa", country_key), user_id, 999))
        else:
            try:
                last_login = datetime.fromisoformat(last_login_str)
                days = (now - last_login).days
                if days >= 3:
                    inactive.append((player.get("name_fa", country_key), user_id, days))
            except:
                pass
    
    inactive.sort(key=lambda x: x[2], reverse=True)
    return inactive


def get_available_countries(state: Dict[str, Any]) -> List[str]:
    """دریافت لیست کشورهای بدون بازیکن"""
    players = state.get("countries", {})
    available = []
    
    for country_key, player in players.items():
        if player.get("user_id") is None:
            available.append(player.get("name_fa", country_key))
    
    return available


if __name__ == "__main__":
    check_inactivity()
