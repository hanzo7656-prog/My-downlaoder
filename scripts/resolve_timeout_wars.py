#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
حل خودکار جنگ‌های بی‌پاسخ بر اساس مهلت‌های تنظیم شده
هر 4 ساعت یکبار اجرا می‌شود (توسط GitHub Actions)

مهلت‌ها:
- پاسخ به اعلان جنگ: 8 ساعت
- استقرار نیرو: 12 ساعت
- عقب‌نشینی: 6 ساعت
- پیشنهاد صلح: 12 ساعت

سرعت بازی روی این مهلت‌ها تأثیر می‌گذارد (get_adjusted_deadline)
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

# مهلت‌های پایه (به ساعت)
DEADLINES = {
    "declaration": 8,      # پاسخ به اعلان جنگ
    "deploy": 12,          # استقرار نیرو
    "retreat": 6,          # عقب‌نشینی
    "peace": 12,           # پیشنهاد صلح
    "attack": 24,          # نوبت حمله (کل جنگ)
}

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
            "message": f"[auto] resolve wars {datetime.now().strftime('%Y-%m-%d %H:%M')}",
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


def get_speed_multiplier(state: Dict[str, Any]) -> int:
    """دریافت ضریب سرعت بازی"""
    return state.get("admin", {}).get("game_speed", 1)


def get_adjusted_deadline(base_hours: int, state: Dict[str, Any]) -> float:
    """محاسبه مهلت بر اساس سرعت بازی"""
    speed = get_speed_multiplier(state)
    adjusted = base_hours / speed
    return max(adjusted, 2)  # حداقل 2 ساعت


def get_player_name(state: Dict[str, Any], user_id: str) -> str:
    """دریافت نام کشور از روی user_id"""
    for country_key, player in state.get("countries", {}).items():
        if player.get("user_id") == user_id:
            return player.get("name_fa", country_key)
    return f"کاربر {user_id[:6]}"


def get_country_key_by_user(state: Dict[str, Any], user_id: str) -> str:
    """دریافت کلید کشور از روی user_id"""
    for country_key, player in state.get("countries", {}).items():
        if player.get("user_id") == user_id:
            return country_key
    return None


# ==================== منطق حل جنگ ====================

def resolve_war(war: Dict[str, Any], attacker_key: str, defender_key: str, 
                attacker_name: str, defender_name: str, state: Dict[str, Any]) -> Tuple[bool, str]:
    """
    حل یک جنگ منفرد
    بازگشت: (آیا جنگی تمام شد، نتیجه)
    """
    now = datetime.now()
    last_move = war.get("last_move")
    phase = war.get("current_phase", "declaration")
    
    if not last_move:
        war["last_move"] = now.isoformat()
        return False, ""
    
    last = datetime.fromisoformat(last_move)
    deadline_hours = DEADLINES.get(phase, 24)
    adjusted_deadline = get_adjusted_deadline(deadline_hours, state)
    
    # اگر مهلت تمام نشده
    if now - last < timedelta(hours=adjusted_deadline):
        return False, ""
    
    # مهلت تمام شده - حل خودکار
    if phase == "declaration":
        # مدافع پاسخ نداد -> جنگ لغو می‌شود
        war["status"] = "cancelled"
        war["ended_at"] = now.isoformat()
        result = f"⚔️ *جنگ لغو شد*\n{attacker_name} → {defender_name}\nعلت: عدم پاسخ مدافع در مهلت {adjusted_deadline:.0f} ساعت"
        return True, result
    
    elif phase == "deploy":
        # استقرار نیرو تمام شد -> مرحله بعد (حمله)
        war["current_phase"] = "attack"
        war["last_move"] = now.isoformat()
        result = f"⚔️ *مرحله استقرار پایان یافت*\n{attacker_name} vs {defender_name}\nوارد مرحله حمله شدید."
        return False, result
    
    elif phase == "attack":
        # نوبت حمله تمام شد -> برنده مشخص می‌شود
        attacker_power = war.get("attacker_power", 0)
        defender_power = war.get("defender_power", 0)
        
        if attacker_power > defender_power:
            winner = attacker_name
            loser = defender_name
            war["winner"] = attacker_key
            # تصرف بخش
            sector = war.get("current_sector", 1)
            war["captured_sectors"] = war.get("captured_sectors", []) + [sector]
            war["current_sector"] = sector + 1
            
            result = f"⚔️ *بخش {sector} تصرف شد*\n{attacker_name} پیروز شد! {defender_name} بخش {sector} را از دست داد."
            
            # اگر همه بخش‌ها تصرف شد
            if war["current_sector"] > 3:
                war["status"] = "ended"
                war["ended_at"] = now.isoformat()
                result = f"🏆 *پیروزی کامل*\n{attacker_name} {defender_name} را به طور کامل شکست داد و تصرف کرد!"
                return True, result
        else:
            winner = defender_name
            loser = attacker_name
            result = f"⚔️ *دفاع موفق*\n{defender_name} در برابر {attacker_name} مقاومت کرد و پیروز شد."
            war["status"] = "ended"
            war["ended_at"] = now.isoformat()
            return True, result
        
        war["last_move"] = now.isoformat()
        return False, result
    
    elif phase == "retreat":
        # عقب‌نشینی تمام شد -> جنگ تمام می‌شود
        war["status"] = "ended"
        war["ended_at"] = now.isoformat()
        result = f"🕊️ *جنگ پایان یافت*\n{attacker_name} در مقابل {defender_name} عقب‌نشینی کرد."
        return True, result
    
    elif phase == "peace":
        # پیشنهاد صلح تمام شد -> رد خودکار
        war["current_phase"] = "attack"
        war["last_move"] = now.isoformat()
        result = f"⚔️ *پیشنهاد صلح رد شد*\n{defender_name} به درخواست صلح {attacker_name} پاسخی نداد. جنگ ادامه دارد."
        return False, result
    
    return False, ""


def remove_war_from_player(state: Dict[str, Any], country_key: str, war_to_remove: Dict[str, Any]):
    """حذف جنگ از لیست جنگ‌های یک کشور"""
    player = state["countries"].get(country_key)
    if not player:
        return
    
    wars = player.get("active_wars", [])
    new_wars = []
    for war in wars:
        if war.get("started_at") != war_to_remove.get("started_at"):
            new_wars.append(war)
    player["active_wars"] = new_wars


# ==================== تابع اصلی ====================

def resolve_timeout_wars():
    """حل تمام جنگ‌های بی‌پاسخ"""
    print(f"Checking for timeout wars at {datetime.now().isoformat()}")
    
    state = load_game_state()
    if not state:
        print("Failed to load game state")
        return
    
    players = state.get("countries", {})
    resolved_count = 0
    all_results = []
    
    # بررسی جنگ‌های هر کشور
    for country_key, player in players.items():
        wars = player.get("active_wars", [])
        if not wars:
            continue
        
        name = player.get("name_fa", country_key)
        
        for war in wars[:]:  # کپی برای امکان حذف در حین حلقه
            # پیدا کردن طرف مقابل
            opponent_id = war.get("with")
            opponent_key = get_country_key_by_user(state, opponent_id)
            opponent_name = get_player_name(state, opponent_id)
            
            # تعیین نقش این کشور در جنگ
            is_attacker = war.get("is_attacker", True)
            
            if is_attacker:
                attacker_key = country_key
                attacker_name = name
                defender_key = opponent_key
                defender_name = opponent_name
            else:
                attacker_key = opponent_key
                attacker_name = opponent_name
                defender_key = country_key
                defender_name = name
            
            # حل جنگ
            finished, result = resolve_war(war, attacker_key, defender_key, 
                                          attacker_name, defender_name, state)
            
            if result:
                all_results.append(result)
                send_to_gcc(result)
                resolved_count += 1
            
            if finished:
                # حذف جنگ از هر دو طرف
                remove_war_from_player(state, attacker_key, war)
                remove_war_from_player(state, defender_key, war)
    
    # اگر جنگی حل شد، وضعیت را ذخیره کن
    if resolved_count > 0:
        save_game_state(state)
        print(f"Resolved {resolved_count} wars")
        
        # ارسال خلاصه به GCC
        summary = f"⚙️ *خلاصه حل خودکار جنگ‌ها*\n• تعداد جنگ‌های حل شده: {resolved_count}\n• سرعت فعلی بازی: {get_speed_multiplier(state)} برابر"
        send_to_gcc(summary)
    else:
        print("No timeout wars found")


def get_active_wars_summary(state: Dict[str, Any]) -> str:
    """دریافت خلاصه جنگ‌های فعال برای گزارش"""
    players = state.get("countries", {})
    active_wars = []
    
    for country_key, player in players.items():
        for war in player.get("active_wars", []):
            opponent = get_player_name(state, war.get("with"))
            active_wars.append(f"{player.get('name_fa', country_key)} vs {opponent}")
    
    if not active_wars:
        return "هیچ جنگ فعالی وجود ندارد."
    
    return "⚔️ *جنگ‌های فعال:*\n" + "\n".join([f"• {w}" for w in set(active_wars)])


if __name__ == "__main__":
    resolve_timeout_wars()
