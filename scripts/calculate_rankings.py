#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
محاسبه جدول پتانسیل روزانه و توزیع پاداش پرستیژ
هر روز ساعت 12 ظهر اجرا می‌شود (توسط GitHub Actions)
"""

import json
import os
import requests
import base64
from datetime import datetime
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
        print(f"Error: {e}")
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
            "message": f"[auto] daily rankings {datetime.now().strftime('%Y-%m-%d')}",
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


def calculate_military_power(player: Dict[str, Any]) -> int:
    """محاسبه قدرت نظامی بر اساس تجهیزات"""
    units = player.get("units", {})
    total_power = 0
    
    # قدرت پایه تجهیزات (مقادیر تقریبی)
    unit_powers = {
        "F22": 80, "رپتور": 80,
        "F35": 70, "لایتنینگ": 70,
        "SU57": 75, "فلون": 75,
        "جی۲۰": 65, "J20": 65,
        "تایفون": 58, "رافال": 57,
        "تمپست": 85,
        "آبرامز": 65, "آر ماتا": 68,
        "لئوپارد": 62, "چلنجر": 58,
        "آرلی بروک": 45, "تایپ۵۵": 48,
        "یاسن": 55, "اوهایو": 60,
        "نیمیتز": 70, "فورد": 85
    }
    
    for category in ["air", "ground", "naval", "destroyer", "submarine", "carrier"]:
        for unit in units.get(category, []):
            name_fa = unit.get("name_fa", "")
            name_en = unit.get("name_en", "")
            count = unit.get("count", 0)
            power = unit_powers.get(name_fa, unit_powers.get(name_en, 30))
            total_power += power * count
    
    return min(total_power // 10, 200)  # حداکثر 200


def calculate_potential(player: Dict[str, Any]) -> int:
    """محاسبه پتانسیل کلی کشور"""
    industry = player.get("industry", 0)
    trade = player.get("trade", 0)
    diplomacy = player.get("diplomacy", 0)
    stability = player.get("stability", 5)
    military_power = calculate_military_power(player)
    
    # فرمول: (صنعت × ۳) + (تجارت × ۲.۵) + (قدرت نظامی × ۲) + (دیپلماسی × ۱) + (ثبات × ۱)
    potential = (industry * 3) + (int(trade * 2.5)) + (military_power * 2) + diplomacy + stability
    
    return potential


def get_status_icons(player: Dict[str, Any]) -> str:
    """دریافت آیکون‌های وضعیت کشور"""
    icons = []
    
    # در جنگ
    if player.get("active_wars") and len(player.get("active_wars", [])) > 0:
        icons.append("⚔️")
    else:
        icons.append("🕊️")
    
    # در اتحاد کامل
    treaties = player.get("treaties", [])
    for treaty in treaties:
        if treaty.get("type") == "full_alliance":
            icons.append("🤝")
            break
    
    # تحریم شده
    if player.get("sanctioned", False):
        icons.append("💰")
    
    # بحران داخلی
    if player.get("stability", 5) < 3:
        icons.append("⚠️")
    
    # استفاده از سلاح هسته‌ای
    if player.get("used_nuclear", False):
        icons.append("🔥")
    
    return "".join(icons)


def get_country_flag(country_key: str) -> str:
    """دریافت ایموجی پرچم کشور"""
    flags = {
        "usa": "🇺🇸", "russia": "🇷🇺", "china": "🇨🇳",
        "germany": "🇩🇪", "france": "🇫🇷", "uk": "🇬🇧",
        "japan": "🇯🇵", "south_korea": "🇰🇷", "india": "🇮🇳",
        "turkey": "🇹🇷", "iran": "🇮🇷", "israel": "🇮🇱",
        "pakistan": "🇵🇰", "poland": "🇵🇱", "ukraine": "🇺🇦",
        "australia": "🇦🇺", "canada": "🇨🇦", "egypt": "🇪🇬",
        "vietnam": "🇻🇳", "indonesia": "🇮🇩", "kazakhstan": "🇰🇿",
        "brazil": "🇧🇷", "saudi": "🇸🇦", "south_africa": "🇿🇦"
    }
    return flags.get(country_key, "🏳️")


def generate_rankings_table(rankings: List[Tuple], game_day: int) -> str:
    """ساخت جدول رتبه‌بندی"""
    table = f"🏆 *جدول پتانسیل روزانه - روز {game_day}*\n"
    table += "═══════════════════════════════════════\n\n"
    
    for i, (country_key, name_fa, potential, icons) in enumerate(rankings[:24], 1):
        # محاسبه نوار (هر ۵۰ امتیاز = ۱ بلوک، حداکثر ۲۰ بلوک)
        blocks = max(0, int((potential - 100) / 50))
        blocks = min(blocks, 20)
        bar = "█" * blocks + "░" * (20 - blocks)
        
        flag = get_country_flag(country_key)
        line = f"*{i}. {flag} {name_fa}*" + " " * (15 - len(name_fa))
        line += f" {bar}  {potential}  {icons}\n"
        table += line
    
    table += "\n═══════════════════════════════════════\n"
    table += "📊 هر █ = ۵۰ امتیاز پتانسیل\n"
    table += "⚔️ جنگ | 🕊️ صلح | 🤝 متحد | 💰 تحریم | ⚠️ بحران | 🔥 هسته‌ای"
    
    return table


def distribute_prestige_rewards(rankings: List[Tuple], state: Dict[str, Any]):
    """توزیع پاداش پرستیژ به 3 کشور اول"""
    rewards = {1: 20, 2: 10, 3: 5}
    
    for i, (country_key, name_fa, potential, icons) in enumerate(rankings[:3], 1):
        reward = rewards.get(i, 0)
        if reward > 0:
            player = state["countries"].get(country_key)
            if player:
                player["resources"]["prestige"] = player["resources"].get("prestige", 0) + reward
                # اضافه کردن لاگ
                if "logs" not in state:
                    state["logs"] = []
                state["logs"].append({
                    "timestamp": datetime.now().isoformat(),
                    "type": "prestige",
                    "message": f"{name_fa} به رتبه {i} جدول رسید و {reward} پرستیژ دریافت کرد."
                })
                print(f"Added {reward} prestige to {name_fa}")


def main():
    print(f"Calculating daily rankings at {datetime.now().isoformat()}")
    
    state = load_game_state()
    if not state:
        print("Failed to load game state")
        return
    
    players = state.get("countries", {})
    rankings = []
    
    # محاسبه پتانسیل هر کشور
    for country_key, player in players.items():
        name_fa = player.get("name_fa", country_key)
        potential = calculate_potential(player)
        icons = get_status_icons(player)
        rankings.append((country_key, name_fa, potential, icons))
    
    # مرتب‌سازی بر اساس پتانسیل (نزولی)
    rankings.sort(key=lambda x: x[2], reverse=True)
    
    # توزیع پاداش پرستیژ
    distribute_prestige_rewards(rankings, state)
    
    # ساخت جدول
    game_day = state.get("game_day", 0)
    rankings_table = generate_rankings_table(rankings, game_day)
    
    # ارسال به GCC
    send_to_gcc(rankings_table)
    
    # ذخیره در state (برای لاگ و به‌روزرسانی)
    state["last_update"] = datetime.now().isoformat()
    save_game_state(state)
    
    print("Rankings calculated and sent successfully")


if __name__ == "__main__":
    main()
