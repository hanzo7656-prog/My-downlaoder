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


def get_speed_multiplier(state: Dict[str, Any]) -> int:
    """دریافت ضریب سرعت بازی"""
    return state.get("admin", {}).get("game_speed", 1)


# ==================== محاسبه قدرت نظامی ====================

def calculate_military_power(player: Dict[str, Any]) -> int:
    """محاسبه قدرت نظامی بر اساس تجهیزات"""
    units = player.get("units", {})
    total_power = 0
    
    # قدرت پایه تجهیزات (نام فارسی و انگلیسی)
    unit_powers = {
        # هواپیماها
        "F22": 80, "رپتور": 80,
        "F35": 70, "لایتنینگ": 70,
        "SU57": 75, "فلون": 75,
        "جی۲۰": 65, "J20": 65,
        "تایفون": 58, "Eurofighter Typhoon": 58,
        "رافال": 57, "Rafale": 57,
        "تمپست": 85, "Tempest": 85,
        "سوخو-۳۵": 55, "Su-35": 55,
        "میگ-۲۹": 40, "MiG-29": 40,
        "فانتوم": 30, "F-4": 30,
        "سوپر هورنت": 50, "F/A-18": 50,
        
        # تانک‌ها
        "آبرامز": 65, "Abrams X": 65,
        "آر ماتا": 68, "T-14 Armata": 68,
        "لئوپارد": 62, "Leopard 2A7+": 62,
        "چلنجر": 58, "Challenger 2": 58,
        "پلنگ سیاه": 60, "K2 Black Panther": 60,
        "مِرکاوا": 59, "Merkava": 59,
        "تایپ-۱۰": 56, "Type 10": 56,
        "لکلر": 57, "Leclerc": 57,
        "تایپ-۹۹": 54, "Type 99A": 54,
        "تی-۸۴": 52, "T-84": 52,
        "آبرامز ام۱": 38, "Abrams M1": 38,
        "تی-۹۰": 37, "T-90": 37,
        "لئوپارد ۲": 35, "Leopard 2": 35,
        "لئوپارد-۱": 20, "Leopard 1": 20,
        "تی-۵۵": 10, "T-55": 10,
        
        # توپخانه
        "پی‌زدهاچ-۲۰۰۰": 42, "PzH 2000": 42,
        "کوالیتسیا": 45, "Koalitsiya-SV": 45,
        "ام-۱۰۹": 39, "M109A7": 39,
        "کی-۹": 40, "K9 Thunder": 40,
        "پی‌ال‌زد-۵۲": 38, "PLZ-52": 38,
        
        # ناوشکن‌ها
        "آرلی بروک": 45, "Arleigh Burke": 45,
        "زوموالت": 50, "Zumwalt": 50,
        "تایپ-۵۵": 48, "Type 55": 48,
        "مایا": 42, "Maya class": 42,
        "هورایزن": 40, "Horizon class": 40,
        "تایپ-۴۵": 43, "Type 45": 43,
        "سجونگ کبیر": 46, "Sejong the Great": 46,
        
        # زیردریایی‌ها
        "یاسن": 55, "Yasen class": 55,
        "اوهایو": 60, "Ohio class": 60,
        "تایپ-۰۹۳": 45, "Type 093": 45,
        "ویرجینیا": 50, "Virginia class": 50,
        
        # ناو هواپیمابر
        "نیمیتز": 70, "Nimitz": 70,
        "فورد": 85, "Ford": 85,
        "فوجیان": 65, "Fujian": 65,
        "شاندونگ": 55, "Shandong": 55,
        "لیائونینگ": 45, "Liaoning": 45,
        "شارل دوگل": 58, "Charles de Gaulle": 58,
        "ملکه الیزابت": 60, "Queen Elizabeth": 60,
        
        # پدافند
        "اس-۴۰۰": 60, "S-400": 60,
        "اس-۵۰۰": 85, "S-500": 85,
        "پاتریوت": 50, "Patriot": 50,
        "تاد": 55, "THAAD": 55,
        "فلاخن داوود": 65, "David's Sling": 65,
    }
    
    for category in ["air", "ground", "naval", "destroyer", "submarine", "carrier", "artillery", "air_defense"]:
        for unit in units.get(category, []):
            name_fa = unit.get("name_fa", "")
            name_en = unit.get("name_en", "")
            count = unit.get("count", 0)
            
            # جستجو در دیکشنری
            power = unit_powers.get(name_fa, unit_powers.get(name_en, 30))
            total_power += power * count * unit.get("health", 100) / 100  # ضریب سلامت
    
    # حداکثر 200 امتیاز نظامی برای جلوگیری از بینیازی
    return min(total_power // 10, 200)


# ==================== محاسبه پتانسیل ====================

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


# ==================== آیکون‌های وضعیت ====================

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
    
    # بحران داخلی (ثبات کمتر از 3)
    if player.get("stability", 5) < 3:
        icons.append("⚠️")
    
    # استفاده از سلاح هسته‌ای
    if player.get("used_nuclear", False):
        icons.append("🔥")
    
    # غیرفعال (5 روز آنلاین نبوده)
    last_login = player.get("last_login", "")
    if last_login:
        try:
            last = datetime.fromisoformat(last_login)
            if (datetime.now() - last).days >= 5:
                icons.append("❌")
        except:
            pass
    
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
        "brazil": "🇧🇷", "saudi": "🇸🇦", "south_africa": "🇿🇦",
        "austria": "🇦🇹", "belgium": "🇧🇪", "netherlands": "🇳🇱"
    }
    return flags.get(country_key, "🏳️")


# ==================== ساخت جدول ====================

def generate_rankings_table(rankings: List[Tuple], game_day: int) -> str:
    """ساخت جدول رتبه‌بندی با نوار پیشرفت"""
    table = f"🏆 *جدول پتانسیل روزانه - روز {game_day}*\n"
    table += "═══════════════════════════════════════\n\n"
    
    for i, (country_key, name_fa, potential, icons) in enumerate(rankings[:24], 1):
        # محاسبه نوار (هر ۵۰ امتیاز = ۱ بلوک، حداکثر ۲۰ بلوک)
        blocks = max(0, int((potential - 100) / 50))
        blocks = min(blocks, 20)
        bar = "█" * blocks + "░" * (20 - blocks)
        
        flag = get_country_flag(country_key)
        # ردیف جدول
        line = f"*{i}. {flag} {name_fa}*" + " " * (18 - len(name_fa))
        line += f" {bar}  {potential}  {icons}\n"
        table += line
    
    table += "\n═══════════════════════════════════════\n"
    table += "📊 هر █ = ۵۰ امتیاز پتانسیل\n"
    table += "⚔️ جنگ | 🕊️ صلح | 🤝 متحد | 💰 تحریم | ⚠️ بحران | 🔥 هسته‌ای | ❌ غیرفعال"
    
    return table


# ==================== توزیع پاداش پرستیژ ====================

def distribute_prestige_rewards(rankings: List[Tuple], state: Dict[str, Any]):
    """توزیع پاداش پرستیژ به 3 کشور اول جدول"""
    rewards = {1: 20, 2: 10, 3: 5}
    
    for i, (country_key, name_fa, potential, icons) in enumerate(rankings[:3], 1):
        reward = rewards.get(i, 0)
        if reward > 0:
            player = state["countries"].get(country_key)
            if player:
                # افزایش پرستیژ
                if "resources" not in player:
                    player["resources"] = {}
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


# ==================== تابع اصلی ====================

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
    
    # نمایش سرعت بازی در صورت بیشتر از 1
    speed = get_speed_multiplier(state)
    if speed > 1:
        rankings_table += f"\n\n⚙️ *سرعت بازی:* {speed} برابر (مهلت‌ها کوتاه‌تر)"
    
    # ارسال به GCC
    send_to_gcc(rankings_table)
    
    # ذخیره در state
    state["last_update"] = datetime.now().isoformat()
    save_game_state(state)
    
    print("Rankings calculated and sent successfully")


if __name__ == "__main__":
    main()
