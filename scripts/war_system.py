#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
سیستم کامل نبرد با همه ضرایب و ویژگی‌ها
- اعلان جنگ و مدیریت جنگ
- سه مرحله نبرد تفکیک شده (هوایی، دریایی، زمینی)
- ضرایب: ائتلاف، لجستیک، دفاع از خاک، فرسایش، صنعت دشمن، تحریم
- ویژگی‌های منحصر به فرد تجهیزات (رادارگریز، زره سنگین، سرعت بالا، ...)
- سیستم تجربه و سلامت یگان‌ها
- محاسبه مصرف سوخت و مهمات
"""

import json
import os
import requests
import base64
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional

# ==================== تنظیمات ====================

GH_TOKEN = os.environ.get("GH_TOKEN", "")
REPO_OWNER = os.environ.get("REPO_OWNER", "")
REPO_NAME = os.environ.get("REPO_NAME", "")
BALE_TOKEN = os.environ.get("BALE_TOKEN", "")
GCC_CHAT_ID = os.environ.get("GCC_CHAT_ID", "")

GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/game_state.json"
BALE_API_URL = f"https://tapi.bale.ai/bot{BALE_TOKEN}"

# ==================== قدرت پایه تجهیزات ====================

UNIT_POWERS = {
    # هواپیماها
    "F22": 90, "رپتور": 90, "F35": 75, "لایتنینگ": 75,
    "SU57": 85, "فلون": 85, "جی۲۰": 70, "J20": 70,
    "تمپست": 95, "Tempest": 95, "تایفون": 65, "رافال": 65,
    "سوخو-۳۵": 60, "Su-35": 60, "سوپر هورنت": 55, "میگ-۲۹": 45,
    
    # تانک‌ها
    "آر ماتا": 75, "T-14": 75, "آبرامز": 72, "Abrams X": 72,
    "لئوپارد": 70, "پلنگ سیاه": 68, "چلنجر": 64, "مرکاوا": 65,
    "تایپ-۱۰": 62, "لکلر": 63, "تایپ-۹۹": 60, "تی-۸۴": 58,
    
    # ناوشکن و زیردریایی
    "زوموالت": 65, "تایپ-۵۵": 60, "آرلی بروک": 55, "یاسن": 70,
    "اوهایو": 75, "تایپ-۰۹۳": 45, "سیرا": 48,
    
    # ناو هواپیمابر
    "فورد": 100, "نیمیتز": 85, "فوجیان": 80, "شارل دوگل": 70,
    
    # پدافند
    "اس-۵۰۰": 90, "اس-۴۰۰": 70, "تاد": 65, "پاتریوت": 55
}

# ==================== ویژگی‌های منحصر به فرد تجهیزات ====================

UNIT_ABILITIES = {
    "F22": {"stealth": 0.20, "name_fa": "رادارگریز"},
    "رپتور": {"stealth": 0.20, "name_fa": "رادارگریز"},
    "F35": {"stealth": 0.15, "name_fa": "رادارگریز"},
    "لایتنینگ": {"stealth": 0.15, "name_fa": "رادارگریز"},
    "SU57": {"stealth": 0.10, "name_fa": "رادارگریز"},
    "فلون": {"stealth": 0.10, "name_fa": "رادارگریز"},
    "جی۲۰": {"stealth": 0.15, "name_fa": "رادارگریز"},
    "تمپست": {"long_range": 0.10, "ai_assisted": 0.15, "name_fa": "هوش مصنوعی+برد بلند"},
    "چلنجر": {"heavy_armor": 0.25, "name_fa": "زره سنگین"},
    "آر ماتا": {"heavy_armor": 0.15, "name_fa": "زره سنگین"},
    "آبرامز": {"heavy_armor": 0.20, "name_fa": "زره سنگین"},
    "تایپ-۱۰": {"fast": 0.15, "name_fa": "سرعت بالا"},
    "لئوپارد": {"fast": 0.10, "name_fa": "سرعت بالا"},
    "یاسن": {"long_range": 0.10, "name_fa": "برد بلند"},
    "اوهایو": {"long_range": 0.15, "name_fa": "برد بلند"},
    "اس-۵۰۰": {"air_defense": 0.40, "name_fa": "دفاع هوایی پیشرفته"},
    "اس-۴۰۰": {"air_defense": 0.30, "name_fa": "دفاع هوایی"},
    "تاد": {"air_defense": 0.35, "name_fa": "دفاع هوایی"},
    "تایپ-۵۵": {"anti_sub": 0.25, "name_fa": "ضد زیردریایی"},
    "آرلی بروک": {"anti_sub": 0.30, "name_fa": "ضد زیردریایی"},
    "تایپ-۹۹": {"mass_production": -0.10, "name_fa": "تولید انبوه"},
    "زوموالت": {"stealth": 0.25, "name_fa": "رادارگریز"}
}

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


def save_game_state(state: Dict[str, Any]) -> bool:
    try:
        headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        response = requests.get(GITHUB_API_URL, headers=headers)
        current_sha = response.json().get("sha", "")
        
        new_content = json.dumps(state, indent=2, ensure_ascii=False)
        encoded = base64.b64encode(new_content.encode()).decode()
        
        payload = {"message": f"[war] {datetime.now().isoformat()}", "content": encoded, "sha": current_sha}
        response = requests.put(GITHUB_API_URL, headers=headers, json=payload)
        return response.status_code == 200
    except:
        return False


def send_message(chat_id: str, text: str):
    if not BALE_TOKEN:
        return
    url = f"{BALE_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except:
        pass


def send_to_gcc(text: str):
    if GCC_CHAT_ID:
        send_message(GCC_CHAT_ID, text)


def get_country_data(state: Dict[str, Any], user_id: str) -> Optional[Dict[str, Any]]:
    for country_key, player in state.get("countries", {}).items():
        if player.get("user_id") == user_id:
            return player
    return None


def get_country_key_by_user(state: Dict[str, Any], user_id: str) -> Optional[str]:
    for country_key, player in state.get("countries", {}).items():
        if player.get("user_id") == user_id:
            return country_key
    return None


def get_user_by_country(state: Dict[str, Any], country_name: str) -> Optional[str]:
    for country_key, player in state.get("countries", {}).items():
        if player.get("name_fa") == country_name or player.get("name_en") == country_name:
            return player.get("user_id")
    return None


def get_country_name(state: Dict[str, Any], user_id: str) -> str:
    for country_key, player in state.get("countries", {}).items():
        if player.get("user_id") == user_id:
            return player.get("name_fa", country_key)
    return "نامشخص"


def get_speed_multiplier(state: Dict[str, Any]) -> int:
    return state.get("admin", {}).get("game_speed", 1)


def get_adjusted_deadline(base_hours: int, state: Dict[str, Any]) -> float:
    speed = get_speed_multiplier(state)
    adjusted = base_hours / speed
    return max(adjusted, 2)


# ==================== ضرایب نبرد ====================

def get_region_zone(country_key: str) -> str:
    """دریافت منطقه برای محاسبه فاصله"""
    zones = {
        "usa": "america", "canada": "america", "brazil": "america",
        "uk": "america", "germany": "europe", "france": "europe",
        "italy": "europe", "russia": "europe", "poland": "europe",
        "china": "asia", "japan": "asia", "south_korea": "asia",
        "india": "asia", "iran": "middle_east", "turkey": "middle_east",
        "israel": "middle_east", "saudi": "middle_east"
    }
    return zones.get(country_key, "other")


def get_distance_between_countries(country1_key: str, country2_key: str) -> int:
    """محاسبه فاصله بین دو کشور (1 تا 4)"""
    zone1 = get_region_zone(country1_key)
    zone2 = get_region_zone(country2_key)
    
    distance_matrix = {
        ("america", "america"): 1, ("america", "europe"): 2,
        ("america", "asia"): 4, ("america", "middle_east"): 3,
        ("europe", "europe"): 1, ("europe", "asia"): 3,
        ("europe", "middle_east"): 2, ("asia", "asia"): 1,
        ("asia", "middle_east"): 3, ("middle_east", "middle_east"): 1,
    }
    return distance_matrix.get((zone1, zone2), distance_matrix.get((zone2, zone1), 3))


def get_fuel_cost_for_war(distance: int, num_battles: int = 1) -> int:
    """محاسبه مصرف سوخت برای یک جنگ"""
    return distance * 20 * num_battles


def get_attacker_power_penalty(distance: int) -> float:
    """ضریب کاهش قدرت مهاجم بر اساس فاصله"""
    penalties = {1: 1.0, 2: 0.9, 3: 0.8, 4: 0.5}
    return penalties.get(distance, 0.8)


def get_alliance_bonus(state: Dict[str, Any], country_key: str) -> float:
    """محاسبه ضریب ائتلاف"""
    player = state["countries"].get(country_key, {})
    treaties = player.get("treaties", [])
    
    allies_count = 0
    for treaty in treaties:
        if treaty.get("type") in ["ma", "fa"]:
            allies_count += 1
    
    if allies_count == 0:
        return 1.0
    return 1 + min(0.1 * allies_count, 0.5)


def get_home_defense_bonus(is_defender: bool) -> float:
    """ضریب دفاع از خاک"""
    return 1.25 if is_defender else 1.0


def get_attrition_multiplier(war_days: int) -> float:
    """ضریب فرسایش (جنگ طولانی)"""
    if war_days <= 3:
        return 1.0
    elif war_days <= 7:
        return 0.95
    elif war_days <= 14:
        return 0.90
    else:
        return 0.85


def get_industry_penalty(industry: int) -> float:
    """ضریب صنعت دشمن"""
    if industry >= 8:
        return 1.0
    elif industry >= 5:
        return 0.95
    elif industry >= 3:
        return 0.90
    else:
        return 0.85


def get_sanction_penalty(state: Dict[str, Any], country_key: str) -> float:
    """ضریب تحریم"""
    player = state["countries"].get(country_key, {})
    if player.get("sanctioned", False):
        return 0.70
    return 1.0


# ==================== محاسبه قدرت یگان با ویژگی‌ها ====================

def calculate_unit_power_with_abilities(unit: Dict[str, Any], is_against_air: bool = False, is_against_sub: bool = False) -> Tuple[int, float, float]:
    """محاسبه قدرت یگان با احتساب ویژگی‌ها و تجربه و سلامت"""
    name_fa = unit.get("name_fa", "")
    name_en = unit.get("name_en", "")
    health = unit.get("health", 100)
    experience = unit.get("experience", 0)
    
    base_power = UNIT_POWERS.get(name_fa, UNIT_POWERS.get(name_en, 50))
    health_mult = health / 100
    exp_mult = 1 + (experience * 0.1)
    
    power = int(base_power * health_mult * exp_mult)
    
    ability = UNIT_ABILITIES.get(name_fa, UNIT_ABILITIES.get(name_en, {}))
    stealth = ability.get("stealth", 0)
    heavy_armor = ability.get("heavy_armor", 0)
    
    if ability.get("fast", 0):
        power = int(power * (1 + ability["fast"]))
    if is_against_air and ability.get("air_defense", 0):
        power = int(power * (1 + ability["air_defense"]))
    if is_against_sub and ability.get("anti_sub", 0):
        power = int(power * (1 + ability["anti_sub"]))
    if ability.get("ai_assisted", 0):
        power = int(power * (1 + ability["ai_assisted"]))
    if ability.get("long_range", 0):
        power = int(power * (1 + ability["long_range"]))
    if ability.get("mass_production", 0):
        power = int(power * (1 + ability["mass_production"]))
    
    return power, stealth, heavy_armor


def calculate_army_power_with_abilities(units: Dict[str, Any], category: str) -> Tuple[int, float, float]:
    """محاسبه قدرت کل یک دسته یگان با احتساب ویژگی‌ها"""
    total_power = 0
    total_stealth = 0
    total_heavy_armor = 0
    unit_count = 0
    
    is_against_air = category == "air_defense"
    is_against_sub = category == "destroyer"
    
    for unit in units.get(category, []):
        count = unit.get("count", 0)
        if count <= 0:
            continue
        
        unit_power, stealth, heavy_armor = calculate_unit_power_with_abilities(unit, is_against_air, is_against_sub)
        total_power += unit_power * count
        total_stealth += stealth * count
        total_heavy_armor += heavy_armor * count
        unit_count += count
    
    avg_stealth = total_stealth / unit_count if unit_count > 0 else 0
    avg_heavy_armor = total_heavy_armor / unit_count if unit_count > 0 else 0
    return total_power, avg_stealth, avg_heavy_armor


def calculate_total_power_with_abilities(player: Dict[str, Any]) -> Tuple[int, float, float]:
    """محاسبه قدرت کل ارتش با احتساب ویژگی‌ها"""
    units = player.get("units", {})
    total_power = 0
    total_stealth = 0
    total_heavy_armor = 0
    categories_count = 0
    
    categories = ["air", "ground", "artillery", "destroyer", "submarine", "carrier", "air_defense"]
    
    for category in categories:
        power, stealth, heavy_armor = calculate_army_power_with_abilities(units, category)
        total_power += power
        if power > 0:
            total_stealth += stealth * (power / 100)
            total_heavy_armor += heavy_armor * (power / 100)
            categories_count += 1
    
    avg_stealth = total_stealth / categories_count if categories_count > 0 else 0
    avg_heavy_armor = total_heavy_armor / categories_count if categories_count > 0 else 0
    return total_power, avg_stealth, avg_heavy_armor


def calculate_battle_power_with_all_coefficients(
    state: Dict[str, Any], country_key: str, is_attacker: bool, distance: int, war_days: int
) -> Tuple[int, float, float, Dict]:
    """محاسبه قدرت نهایی با همه ضرایب"""
    player = state["countries"].get(country_key, {})
    
    raw_power, stealth, heavy_armor = calculate_total_power_with_abilities(player)
    
    alliance_bonus = get_alliance_bonus(state, country_key)
    logistics_mult = get_attacker_power_penalty(distance) if is_attacker else 1.0
    home_defense = get_home_defense_bonus(not is_attacker)
    attrition = get_attrition_multiplier(war_days)
    industry_penalty = get_industry_penalty(player.get("industry", 5))
    sanction_penalty = get_sanction_penalty(state, country_key)
    
    final_power = int(raw_power * alliance_bonus * logistics_mult * home_defense * attrition * industry_penalty * sanction_penalty)
    
    details = {
        "raw_power": raw_power,
        "alliance_bonus": alliance_bonus,
        "logistics_mult": logistics_mult,
        "home_defense": home_defense,
        "attrition": attrition,
        "industry_penalty": industry_penalty,
        "sanction_penalty": sanction_penalty,
        "final_power": final_power
    }
    
    return final_power, stealth, heavy_armor, details


# ==================== نبرد تفکیک شده ====================

def calculate_separated_battle(
    attacker_units: Dict, defender_units: Dict,
    attacker_stealth: float, defender_stealth: float
) -> Dict[str, Any]:
    """محاسبه نبرد در سه مرحله با اعمال رادارگریز"""
    
    results = {
        "air": {"attacker": 0, "defender": 0, "winner": None},
        "naval": {"attacker": 0, "defender": 0, "winner": None},
        "ground": {"attacker": 0, "defender": 0, "winner": None}
    }
    
    # مرحله 1: نبرد هوایی
    attacker_air = calculate_army_power_with_abilities(attacker_units, "air")[0]
    defender_air = calculate_army_power_with_abilities(defender_units, "air")[0]
    results["air"]["attacker"] = int(attacker_air * (1 - defender_stealth))
    results["air"]["defender"] = int(defender_air * (1 - attacker_stealth))
    results["air"]["winner"] = "attacker" if results["air"]["attacker"] > results["air"]["defender"] else "defender" if results["air"]["defender"] > results["air"]["attacker"] else "draw"
    
    # مرحله 2: نبرد دریایی
    if results["air"]["winner"] != "defender":
        attacker_naval = calculate_army_power_with_abilities(attacker_units, "naval")[0] + \
                         calculate_army_power_with_abilities(attacker_units, "destroyer")[0] + \
                         calculate_army_power_with_abilities(attacker_units, "submarine")[0] + \
                         calculate_army_power_with_abilities(attacker_units, "carrier")[0]
        defender_naval = calculate_army_power_with_abilities(defender_units, "naval")[0] + \
                         calculate_army_power_with_abilities(defender_units, "destroyer")[0] + \
                         calculate_army_power_with_abilities(defender_units, "submarine")[0] + \
                         calculate_army_power_with_abilities(defender_units, "carrier")[0]
        results["naval"]["attacker"] = attacker_naval
        results["naval"]["defender"] = defender_naval
        results["naval"]["winner"] = "attacker" if attacker_naval > defender_naval else "defender" if defender_naval > attacker_naval else "draw"
    else:
        results["naval"]["winner"] = "defender"
    
    # مرحله 3: نبرد زمینی با پشتیبانی
    ground_mult = 1.0
    if results["air"]["winner"] == "attacker":
        ground_mult += 0.20
    if results["naval"]["winner"] == "attacker":
        ground_mult += 0.15
    
    defender_ground_mult = 1.10 if results["air"]["winner"] == "defender" else 1.0
    
    attacker_ground = calculate_army_power_with_abilities(attacker_units, "ground")[0] * ground_mult
    defender_ground = calculate_army_power_with_abilities(defender_units, "ground")[0] * defender_ground_mult
    results["ground"]["attacker"] = int(attacker_ground)
    results["ground"]["defender"] = int(defender_ground)
    results["ground"]["winner"] = "attacker" if attacker_ground > defender_ground else "defender" if defender_ground > attacker_ground else "draw"
    
    return results


def get_battle_result_message(results: Dict[str, Any], attacker_name: str, defender_name: str) -> str:
    """گرفتن متن نتیجه نبرد"""
    msg = f"⚔️ *نتیجه نبرد: {attacker_name} vs {defender_name}*\n\n"
    
    # مرحله هوایی
    air_result = "✅ مهاجم" if results["air"]["winner"] == "attacker" else "🛡️ مدافع" if results["air"]["winner"] == "defender" else "🤝 مساوی"
    msg += f"✈️ *نبرد هوایی:* {air_result}\n"
    msg += f"   قدرت مهاجم: {results['air']['attacker']} | مدافع: {results['air']['defender']}\n"
    
    # مرحله دریایی
    naval_result = "✅ مهاجم" if results["naval"]["winner"] == "attacker" else "🛡️ مدافع" if results["naval"]["winner"] == "defender" else "🤝 مساوی"
    msg += f"🚢 *نبرد دریایی:* {naval_result}\n"
    msg += f"   قدرت مهاجم: {results['naval']['attacker']} | مدافع: {results['naval']['defender']}\n"
    
    # مرحله زمینی
    ground_result = "✅ مهاجم" if results["ground"]["winner"] == "attacker" else "🛡️ مدافع" if results["ground"]["winner"] == "defender" else "🤝 مساوی"
    msg += f"🪖 *نبرد زمینی:* {ground_result}\n"
    msg += f"   قدرت مهاجم: {results['ground']['attacker']} | مدافع: {results['ground']['defender']}\n"
    
    # نتیجه نهایی
    if results["ground"]["winner"] == "attacker":
        msg += f"\n🏆 *پیروزی {attacker_name}*"
    elif results["ground"]["winner"] == "defender":
        msg += f"\n🏆 *پیروزی {defender_name}*"
    else:
        msg += "\n🤝 *نبرد مساوی*"
    
    return msg


# ==================== اعلان جنگ و مدیریت ====================

def declare_war(state: Dict[str, Any], attacker_id: str, target_name: str) -> Tuple[bool, str]:
    """اعلان جنگ با محاسبه فاصله و هزینه سوخت"""
    target_id = get_user_by_country(state, target_name)
    if not target_id:
        return False, f"❌ کشور '{target_name}' یافت نشد."
    
    if attacker_id == target_id:
        return False, "❌ نمی‌توانید به خودتان حمله کنید!"
    
    attacker_key = get_country_key_by_user(state, attacker_id)
    target_key = get_country_key_by_user(state, target_id)
    
    if not attacker_key or not target_key:
        return False, "❌ خطا در شناسایی کشورها."
    
    attacker_name = get_country_name(state, attacker_id)
    target_name = get_country_name(state, target_id)
    
    # بررسی جنگ فعال
    attacker_player = state["countries"][attacker_key]
    for war in attacker_player.get("active_wars", []):
        if war.get("with") == target_id and war.get("status") == "active":
            return False, "❌ شما در حال حاضر با این کشور در جنگ هستید!"
    
    # محاسبه فاصله و مصرف سوخت
    distance = get_distance_between_countries(attacker_key, target_key)
    fuel_cost = get_fuel_cost_for_war(distance, 1)
    fuel = attacker_player.get("resources", {}).get("fuel", 0)
    
    if fuel < fuel_cost:
        return False, f"❌ سوخت کافی ندارید! فاصله: {distance} واحد | نیاز: {fuel_cost} سوخت"
    
    # کسر سوخت
    attacker_player["resources"]["fuel"] = fuel - fuel_cost
    
    # ایجاد جنگ جدید
    now = datetime.now().isoformat()
    new_war = {
        "with": target_id,
        "with_name": target_name,
        "started_at": now,
        "status": "active",
        "current_sector": 1,
        "current_phase": "declaration",
        "last_move": now,
        "is_attacker": True,
        "distance": distance,
        "war_days": 0,
        "attacker_power": 0,
        "defender_power": 0,
        "captured_sectors": []
    }
    
    if "active_wars" not in attacker_player:
        attacker_player["active_wars"] = []
    attacker_player["active_wars"].append(new_war)
    
    # اضافه کردن به مدافع
    defender_player = state["countries"][target_key]
    defender_war = new_war.copy()
    defender_war["is_attacker"] = False
    if "active_wars" not in defender_player:
        defender_player["active_wars"] = []
    defender_player["active_wars"].append(defender_war)
    
    save_game_state(state)
    
    # اعلان به GCC
    send_to_gcc(f"⚔️ *اعلان جنگ*\n{attacker_name} به {target_name} اعلام جنگ داد!\nفاصله: {distance} واحد | مصرف سوخت: {fuel_cost}")
    
    deadline = get_adjusted_deadline(8, state)
    attacker_msg = f"⚔️ شما به {target_name} اعلام جنگ کردید.\nفاصله: {distance} واحد\nمدافع {deadline:.0f} ساعت فرصت پاسخ دارد."
    target_msg = f"⚔️ {attacker_name} به شما اعلام جنگ کرد!\nفاصله: {distance} واحد\nشما {deadline:.0f} ساعت فرصت پاسخ دارید.\nبرای استقرار نیرو: `/deploy`"
    
    send_message(attacker_id, attacker_msg)
    send_message(target_id, target_msg)
    
    return True, f"✅ اعلان جنگ به {target_name} ارسال شد. {fuel_cost} سوخت مصرف شد."


def deploy_forces(state: Dict[str, Any], user_id: str, units_str: str = "") -> Tuple[bool, str]:
    """استقرار نیرو در جنگ فعال با محاسبه کامل قدرت"""
    player = get_country_data(state, user_id)
    if not player:
        return False, "❌ شما کشوری انتخاب نکرده‌اید."
    
    active_war = None
    for war in player.get("active_wars", []):
        if war.get("status") == "active":
            active_war = war
            break
    
    if not active_war:
        return False, "❌ شما در هیچ جنگ فعالی نیستید."
    
    opponent_id = active_war.get("with")
    opponent_key = get_country_key_by_user(state, opponent_id)
    is_attacker = active_war.get("is_attacker", True)
    distance = active_war.get("distance", 3)
    war_days = active_war.get("war_days", 0)
    
    # محاسبه قدرت نهایی با همه ضرایب
    final_power, stealth, heavy_armor, details = calculate_battle_power_with_all_coefficients(
        state, get_country_key_by_user(state, user_id), is_attacker, distance, war_days
    )
    
    if is_attacker:
        active_war["attacker_power"] = final_power
        active_war["attacker_stealth"] = stealth
    else:
        active_war["defender_power"] = final_power
        active_war["defender_stealth"] = stealth
    
    active_war["current_phase"] = "attack"
    active_war["last_move"] = datetime.now().isoformat()
    
    save_game_state(state)
    
    power_msg = f"قدرت خام: {details['raw_power']} | "
    power_msg += f"ائتلاف: {details['alliance_bonus']:.1f}x | "
    power_msg += f"لجستیک: {details['logistics_mult']:.1f}x | "
    power_msg += f"دفاع از خاک: {details['home_defense']:.1f}x"
    
    return True, f"✅ نیروهای شما مستقر شدند!\nقدرت نهایی: {final_power}\n{power_msg}"


def resolve_battle(state: Dict[str, Any], war: Dict[str, Any], attacker_key: str, defender_key: str) -> Tuple[bool, str, Dict]:
    """حل یک نبرد با محاسبه مراحل تفکیک شده"""
    attacker_power = war.get("attacker_power", 0)
    defender_power = war.get("defender_power", 0)
    attacker_stealth = war.get("attacker_stealth", 0)
    defender_stealth = war.get("defender_stealth", 0)
    
    if attacker_power == 0 or defender_power == 0:
        return False, "⚠️ یکی از طرفین نیرویی مستقر نکرده است.", {}
    
    attacker_units = state["countries"][attacker_key].get("units", {})
    defender_units = state["countries"][defender_key].get("units", {})
    
    # محاسبه نبرد تفکیک شده
    battle_results = calculate_separated_battle(attacker_units, defender_units, attacker_stealth, defender_stealth)
    
    attacker_name = state["countries"][attacker_key].get("name_fa", attacker_key)
    defender_name = state["countries"][defender_key].get("name_fa", defender_key)
    result_text = get_battle_result_message(battle_results, attacker_name, defender_name)
    
    # تعیین برنده
    if battle_results["ground"]["winner"] == "attacker":
        war["winner"] = attacker_key
        return True, result_text, battle_results
    elif battle_results["ground"]["winner"] == "defender":
        war["winner"] = defender_key
        return True, result_text, battle_results
    else:
        return False, result_text, battle_results


def get_war_status(state: Dict[str, Any], user_id: str) -> str:
    """دریافت وضعیت جنگ فعال"""
    player = get_country_data(state, user_id)
    if not player:
        return "❌ شما کشوری انتخاب نکرده‌اید."
    
    active_war = None
    for war in player.get("active_wars", []):
        if war.get("status") == "active":
            active_war = war
            break
    
    if not active_war:
        return "❌ شما در هیچ جنگ فعالی نیستید."
    
    opponent_id = active_war.get("with")
    opponent_name = get_country_name(state, opponent_id)
    is_attacker = active_war.get("is_attacker", True)
    my_power = active_war.get("attacker_power" if is_attacker else "defender_power", 0)
    enemy_power = active_war.get("defender_power" if is_attacker else "attacker_power", 0)
    sector = active_war.get("current_sector", 1)
    phase = active_war.get("current_phase", "declaration")
    war_days = active_war.get("war_days", 0)
    distance = active_war.get("distance", 3)
    
    phase_names = {
        "declaration": "⏳ منتظر پاسخ دشمن",
        "deploy": "📦 در حال استقرار نیروها",
        "attack": "⚔️ در حال نبرد",
        "retreat": "🏃 عقب‌نشینی",
        "peace": "🕊️ پیشنهاد صلح"
    }
    
    msg = f"⚔️ *وضعیت جنگ با {opponent_name}*\n\n"
    msg += f"📍 بخش {sector} از 3\n"
    msg += f"📆 روز {war_days} جنگ\n"
    msg += f"📏 فاصله: {distance} واحد\n"
    msg += f"📊 قدرت شما: {my_power}\n"
    msg += f"📊 قدرت دشمن: {enemy_power}\n"
    msg += f"📌 وضعیت: {phase_names.get(phase, phase)}\n"
    
    if my_power > 0 and enemy_power > 0:
        ratio = my_power / enemy_power if enemy_power > 0 else 99
        if ratio > 1.5:
            msg += "\n🔮 پیش‌بینی: پیروزی محتمل"
        elif ratio > 0.8:
            msg += "\n🔮 پیش‌بینی: نبرد نزدیک"
        else:
            msg += "\n🔮 پیش‌بینی: شکست محتمل"
    
    return msg


def propose_peace(state: Dict[str, Any], user_id: str, terms: str = "") -> Tuple[bool, str]:
    """پیشنهاد صلح"""
    player = get_country_data(state, user_id)
    if not player:
        return False, "❌ شما کشوری انتخاب نکرده‌اید."
    
    active_war = None
    for war in player.get("active_wars", []):
        if war.get("status") == "active":
            active_war = war
            break
    
    if not active_war:
        return False, "❌ شما در هیچ جنگ فعالی نیستید."
    
    opponent_id = active_war.get("with")
    opponent_name = get_country_name(state, opponent_id)
    
    active_war["current_phase"] = "peace"
    active_war["last_move"] = datetime.now().isoformat()
    
    save_game_state(state)
    
    deadline = get_adjusted_deadline(12, state)
    
    msg = f"🕊️ *پیشنهاد صلح*\n{player.get('name_fa')} به {opponent_name} پیشنهاد صلح داد.\nشرایط: {terms or 'بدون شرایط'}\nمهلت پاسخ: {deadline:.0f} ساعت"
    send_to_gcc(msg)
    
    return True, f"✅ پیشنهاد صلح به {opponent_name} ارسال شد."


def get_war_details_for_admin(state: Dict[str, Any]) -> str:
    """گزارش کامل جنگ‌های فعال برای ادمین"""
    wars = []
    for country_key, player in state.get("countries", {}).items():
        for war in player.get("active_wars", []):
            if war.get("status") == "active" and war.get("is_attacker", True):
                opponent_id = war.get("with")
                opponent_name = get_country_name(state, opponent_id)
                wars.append({
                    "attacker": player.get("name_fa"),
                    "defender": opponent_name,
                    "sector": war.get("current_sector", 1),
                    "attacker_power": war.get("attacker_power", 0),
                    "defender_power": war.get("defender_power", 0),
                    "war_days": war.get("war_days", 0),
                    "distance": war.get("distance", 3)
                })
    
    if not wars:
        return "هیچ جنگ فعالی وجود ندارد."
    
    msg = "⚔️ *گزارش جنگ‌های فعال*\n\n"
    for war in wars:
        msg += f"• {war['attacker']} vs {war['defender']}\n"
        msg += f"  بخش: {war['sector']}/3 | روز: {war['war_days']} | فاصله: {war['distance']}\n"
        msg += f"  قدرت: {war['attacker_power']} vs {war['defender_power']}\n\n"
    
    return msg


if __name__ == "__main__":
    print("War system module loaded (complete with all coefficients)")
