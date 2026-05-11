#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
سیستم نقشه و فاصله (بدون نمایش گرافیکی)
منطقه‌بندی کشورها و محاسبه فاصله برای لجستیک جنگ
"""

import json
import os
import requests
import base64
from typing import Dict, Any, Tuple, Optional

# ==================== تنظیمات ====================

GH_TOKEN = os.environ.get("GH_TOKEN", "")
REPO_OWNER = os.environ.get("REPO_OWNER", "")
REPO_NAME = os.environ.get("REPO_NAME", "")

GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/game_state.json"

# ==================== منطقه‌بندی کشورها ====================

COUNTRY_ZONES = {
    # آمریکا و متحدان نزدیک
    "usa": "america",
    "canada": "america",
    "brazil": "america",
    "uk": "america",  # انگلیس متحد نزدیک آمریکا
    
    # ژاپن و شرق آسیا
    "japan": "japan",
    "china": "japan",
    "south_korea": "japan",
    "australia": "japan",
    
    # ایران و همسایگان + روسیه و هند
    "iran": "iran",
    "russia": "iran",
    "india": "iran",
    "pakistan": "iran",
    "turkey": "iran",
    "saudi": "iran",
    "egypt": "iran",
    "israel": "iran",
    
    # اروپا
    "germany": "europe",
    "france": "europe",
    "italy": "europe",
    "spain": "europe",
    "poland": "europe",
    "ukraine": "europe",
    "austria": "europe",
    "belgium": "europe",
    "netherlands": "europe",
    
    # آفریقا و دیگران (پیش‌فرض)
    "south_africa": "other",
    "indonesia": "other",
    "kazakhstan": "other",
}

# ==================== جدول فاصله بین مناطق ====================
# اعداد: 1=هممنطقه, 2=مجاور, 3=دور, 4=بسیار دور

DISTANCE_MATRIX = {
    ("america", "america"): 1,
    ("america", "japan"): 4,
    ("america", "iran"): 3,
    ("america", "europe"): 2,
    ("america", "other"): 3,
    
    ("japan", "america"): 4,
    ("japan", "japan"): 1,
    ("japan", "iran"): 3,
    ("japan", "europe"): 3,
    ("japan", "other"): 2,
    
    ("iran", "america"): 3,
    ("iran", "japan"): 3,
    ("iran", "iran"): 1,
    ("iran", "europe"): 2,
    ("iran", "other"): 2,
    
    ("europe", "america"): 2,
    ("europe", "japan"): 3,
    ("europe", "iran"): 2,
    ("europe", "europe"): 1,
    ("europe", "other"): 2,
    
    ("other", "america"): 3,
    ("other", "japan"): 2,
    ("other", "iran"): 2,
    ("other", "europe"): 2,
    ("other", "other"): 1,
}

# ==================== مصرف سوخت و قدرت ====================

FUEL_COST_PER_DISTANCE = 20  # هر واحد فاصله = 20 واحد سوخت
POWER_PENALTY_PER_DISTANCE = 0.10  # هر واحد فاصله = 10% کاهش قدرت (حداکثر 50%)

# ==================== توابع کمکی ====================

def load_game_state() -> Dict[str, Any]:
    try:
        headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        response = requests.get(GITHUB_API_URL, headers=headers)
        if response.status_code == 200:
            content = response.json()["content"]
            decoded = base64.b64decode(content).decode("utf-8")
            return json.loads(decoded)
        return {}
    except:
        return {}


def get_country_zone(country_key: str) -> str:
    """دریافت منطقه یک کشور"""
    return COUNTRY_ZONES.get(country_key, "other")


def get_distance_between_countries(country1_key: str, country2_key: str) -> int:
    """محاسبه فاصله بین دو کشور (1 تا 4)"""
    zone1 = get_country_zone(country1_key)
    zone2 = get_country_zone(country2_key)
    return DISTANCE_MATRIX.get((zone1, zone2), 3)


def get_distance_between_zones(zone1: str, zone2: str) -> int:
    """محاسبه فاصله بین دو منطقه"""
    return DISTANCE_MATRIX.get((zone1, zone2), 3)


def get_fuel_cost_for_war(distance: int, num_battles: int = 1) -> int:
    """
    محاسبه مصرف سوخت برای یک جنگ
    distance: فاصله بین دو کشور (1 تا 4)
    num_battles: تعداد نبردها (پیش‌فرض 1)
    """
    base_cost = distance * FUEL_COST_PER_DISTANCE
    return base_cost * num_battles


def get_power_penalty(distance: int) -> float:
    """
    محاسبه ضریب کاهش قدرت مهاجم بر اساس فاصله
    distance: 1 -> 1.0 (100%)
    distance: 2 -> 0.9 (90%)
    distance: 3 -> 0.8 (80%)
    distance: 4 -> 0.5 (50%)
    """
    penalty = 1 - (min(distance, 5) * POWER_PENALTY_PER_DISTANCE)
    return max(penalty, 0.5)  # حداقل 50% قدرت


def get_distance_description(distance: int) -> str:
    """دریافت توضیح متنی برای فاصله"""
    descriptions = {
        1: "همسایه (فاصله کم)",
        2: "منطقه مجاور (فاصله متوسط)",
        3: "دور (فاصله زیاد)",
        4: "بسیار دور (نیمکره دیگر)"
    }
    return descriptions.get(distance, "دور")


def get_region_description(country_key: str) -> str:
    """دریافت توضیح منطقه برای نمایش به کاربر"""
    zone = get_country_zone(country_key)
    region_names = {
        "america": "آمریکا و متحدان (آمریکای شمالی، برزیل، انگلیس)",
        "japan": "شرق آسیا (ژاپن، چین، کره جنوبی، استرالیا)",
        "iran": "خاورمیانه و جنوب آسیا (ایران، روسیه، هند، پاکستان، ترکیه)",
        "europe": "اروپا (آلمان، فرانسه، ایتالیا، لهستان)",
        "other": "سایر مناطق"
    }
    return region_names.get(zone, "سایر مناطق")


# ==================== توابع لاگستیک جنگ ====================

def can_attack(state: Dict[str, Any], attacker_key: str, defender_key: str) -> Tuple[bool, str]:
    """
    بررسی امکان حمله (بر اساس سوخت موجود)
    """
    distance = get_distance_between_countries(attacker_key, defender_key)
    fuel_cost = get_fuel_cost_for_war(distance, 1)
    
    attacker = state["countries"].get(attacker_key, {})
    fuel = attacker.get("resources", {}).get("fuel", 0)
    
    if fuel < fuel_cost:
        return False, f"❌ سوخت کافی ندارید! نیاز: {fuel_cost} واحد سوخت"
    
    return True, ""


def deduct_fuel_for_attack(state: Dict[str, Any], attacker_key: str, defender_key: str, num_battles: int = 1) -> bool:
    """
    کسر سوخت برای حمله
    """
    distance = get_distance_between_countries(attacker_key, defender_key)
    fuel_cost = get_fuel_cost_for_war(distance, num_battles)
    
    attacker = state["countries"].get(attacker_key, {})
    if "resources" not in attacker:
        attacker["resources"] = {}
    
    current_fuel = attacker["resources"].get("fuel", 0)
    if current_fuel < fuel_cost:
        return False
    
    attacker["resources"]["fuel"] = current_fuel - fuel_cost
    return True


def get_attacker_power_multiplier(attacker_key: str, defender_key: str) -> float:
    """
    دریافت ضریب قدرت مهاجم بر اساس فاصله
    """
    distance = get_distance_between_countries(attacker_key, defender_key)
    return get_power_penalty(distance)


# ==================== دستورات نمایشی ====================

def get_region_info(state: Dict[str, Any], user_id: str) -> str:
    """دریافت اطلاعات منطقه برای نمایش به کاربر"""
    # پیدا کردن کشور کاربر
    country_key = None
    for key, player in state.get("countries", {}).items():
        if player.get("user_id") == user_id:
            country_key = key
            break
    
    if not country_key:
        return "❌ شما کشوری انتخاب نکرده‌اید."
    
    player = state["countries"][country_key]
    zone = get_country_zone(country_key)
    
    # پیدا کردن همسایگان (کشورهای با فاصله 1)
    neighbors = []
    for other_key, other_player in state.get("countries", {}).items():
        if other_key == country_key:
            continue
        if other_player.get("user_id") is None:
            continue
        distance = get_distance_between_countries(country_key, other_key)
        if distance == 1:
            neighbors.append(other_player.get("name_fa", other_key))
    
    msg = f"""
🌍 *موقعیت جغرافیایی {player.get('name_fa')}*

📍 منطقه: {get_region_description(country_key)}

🤝 *کشورهای همسایه (فاصله کم):*
{', '.join(neighbors) if neighbors else 'هیچ'}

📊 *تأثیر فاصله در جنگ:*
• حمله به همسایه: ۱۰۰% قدرت
• حمله به منطقه مجاور: ۹۰% قدرت
• حمله به منطقه دور: ۸۰% قدرت
• حمله به نیمکره دیگر: ۵۰% قدرت

⛽ *مصرف سوخت در هر نبرد:*
• همسایه: ۲۰ واحد
• منطقه مجاور: ۴۰ واحد
• منطقه دور: ۶۰ واحد
• نیمکره دیگر: ۸۰ واحد
"""
    return msg


def get_distance_to_country(state: Dict[str, Any], user_id: str, target_name: str) -> str:
    """نمایش فاصله با کشور دیگر"""
    # پیدا کردن کشور کاربر
    country_key = None
    for key, player in state.get("countries", {}).items():
        if player.get("user_id") == user_id:
            country_key = key
            break
    
    if not country_key:
        return "❌ شما کشوری انتخاب نکرده‌اید."
    
    player = state["countries"][country_key]
    
    # پیدا کردن کشور هدف
    target_key = None
    target_player = None
    for key, p in state.get("countries", {}).items():
        if p.get("name_fa") == target_name or p.get("name_en") == target_name:
            target_key = key
            target_player = p
            break
    
    if not target_key:
        return f"❌ کشور '{target_name}' یافت نشد."
    
    distance = get_distance_between_countries(country_key, target_key)
    
    msg = f"""
📏 *فاصله {player.get('name_fa')} تا {target_player.get('name_fa')}*

فاصله: {get_distance_description(distance)}

⚔️ *تأثیر در جنگ:*
• قدرت مهاجم: {int(get_power_penalty(distance) * 100)}%
• مصرف سوخت هر نبرد: {distance * FUEL_COST_PER_DISTANCE} واحد
"""
    return msg


def get_world_overview(state: Dict[str, Any]) -> str:
    """نمای کلی جهان (منطقه‌بندی شده)"""
    regions = {
        "america": [],
        "japan": [],
        "iran": [],
        "europe": [],
        "other": []
    }
    
    for country_key, player in state.get("countries", {}).items():
        if player.get("user_id") is None:
            continue
        zone = get_country_zone(country_key)
        regions[zone].append(player.get("name_fa", country_key))
    
    msg = """
🌎 *نمای کلی جهان*

━━━━━━━━━━━━━━━━━━━━━

🇺🇸 *منطقه آمریکا:*"
"""
    if regions["america"]:
        msg += "   " + ", ".join(regions["america"]) + "\n"
    else:
        msg += "   (بدون بازیکن فعال)\n"
    
    msg += """
🇯🇵 *منطقه شرق آسیا:*
"""
    if regions["japan"]:
        msg += "   " + ", ".join(regions["japan"]) + "\n"
    else:
        msg += "   (بدون بازیکن فعال)\n"
    
    msg += """
🇮🇷 *منطقه خاورمیانه و جنوب آسیا:*
"""
    if regions["iran"]:
        msg += "   " + ", ".join(regions["iran"]) + "\n"
    else:
        msg += "   (بدون بازیکن فعال)\n"
    
    msg += """
🇪🇺 *منطقه اروپا:*
"""
    if regions["europe"]:
        msg += "   " + ", ".join(regions["europe"]) + "\n"
    else:
        msg += "   (بدون بازیکن فعال)\n"
    
    if regions["other"]:
        msg += """
🌍 *سایر مناطق:*
"""
        msg += "   " + ", ".join(regions["other"]) + "\n"
    
    msg += """
━━━━━━━━━━━━━━━━━━━━━
📌 برای مشاهده منطقه خود: /region
📏 برای مشاهده فاصله با یک کشور: /distance [کشور]
"""
    return msg


def get_map_help() -> str:
    """راهنمای سیستم نقشه"""
    return """
🗺️ *سیستم نقشه و فاصله*

بدون نقشه گرافیکی، فاصله بین کشورها به صورت منطقه‌ای محاسبه می‌شود.

*مناطق:*
• آمریکا و متحدان: آمریکا، کانادا، برزیل، انگلیس
• شرق آسیا: ژاپن، چین، کره جنوبی، استرالیا
• خاورمیانه و جنوب آسیا: ایران، روسیه، هند، پاکستان، ترکیه
• اروپا: آلمان، فرانسه، ایتالیا، لهستان

*تأثیر فاصله در جنگ:*
• همسایه (فاصله 1): 100% قدرت، 20 سوخت
• منطقه مجاور (فاصله 2): 90% قدرت، 40 سوخت
• منطقه دور (فاصله 3): 80% قدرت، 60 سوخت
• نیمکره دیگر (فاصله 4): 50% قدرت، 80 سوخت

*دستورات:*
/region - نمایش موقعیت منطقه خود
/distance [کشور] - نمایش فاصله با یک کشور
/world_map - نمایش نمای کلی جهان
"""


if __name__ == "__main__":
    print("Map system module loaded")
