#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
سیستم کامل نبرد
امکانات: اعلان جنگ، استقرار نیرو، محاسبه قدرت با احتساب:
- ویژگی‌های منحصر به فرد تجهیزات (رادارگریز، زره سنگین، سرعت بالا، ...)
- ضرایب ائتلاف (Alliance Bonus)
- ضریب لجستیک (فاصله از پایگاه)
- ضریب دفاع از خاک (Home Defense)
- ضریب فرسایش (Attrition)
- ضریب صنعت دشمن
- ضریب تحریم (Sanction)
- ضریب تجربه نیروها
- ضریب سلامت تجهیزات
"""

import json
import os
import requests
import base64
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
    "F22": 90, "رپتور": 90,
    "F35": 75, "لایتنینگ": 75,
    "SU57": 85, "فلون": 85,
    "جی۲۰": 70, "J20": 70,
    "تمپست": 95, "Tempest": 95,
    "تایفون": 65, "Eurofighter Typhoon": 65,
    "رافال": 65, "Rafale": 65,
    "سوخو-۳۵": 60, "Su-35": 60,
    "سوپر هورنت": 55, "F/A-18": 55,
    "میگ-۲۹": 45, "MiG-29": 45,
    "فانتوم": 35, "F-4": 35,
    "جی-۱۵": 50, "J-15": 50,
    
    # تانک‌ها
    "آر ماتا": 75, "T-14 Armata": 75,
    "آبرامز": 72, "Abrams X": 72,
    "لئوپارد": 70, "Leopard 2A7+": 70,
    "پلنگ سیاه": 68, "K2 Black Panther": 68,
    "مِرکاوا": 65, "Merkava": 65,
    "چلنجر": 64, "Challenger 2": 64,
    "تایپ-۱۰": 62, "Type 10": 62,
    "لکلر": 63, "Leclerc": 63,
    "تایپ-۹۹": 60, "Type 99A": 60,
    "تی-۸۴": 58, "T-84": 58,
    "آبرامز ام۱": 45, "Abrams M1": 45,
    "تی-۹۰": 42, "T-90": 42,
    "لئوپارد ۲": 40, "Leopard 2": 40,
    "لئوپارد-۱": 25, "Leopard 1": 25,
    "تی-۵۵": 15, "T-55": 15,
    
    # توپخانه
    "کوالیتسیا": 50, "Koalitsiya-SV": 50,
    "پی‌زدهاچ-۲۰۰۰": 48, "PzH 2000": 48,
    "کی-۹": 46, "K9 Thunder": 46,
    "ام-۱۰۹": 44, "M109A7": 44,
    "پی‌ال‌زد-۵۲": 43, "PLZ-52": 43,
    "مستا-اس": 35, "Msta-S": 35,
    "ایاس-۹۰": 32, "AS90": 32,
    "ام-۱۰۹ قدیمی": 22, "M109": 22,
    
    # ناوشکن
    "زوموالت": 65, "Zumwalt": 65,
    "تایپ-۵۵": 60, "Type 55": 60,
    "سجونگ کبیر": 58, "Sejong the Great": 58,
    "آرلی بروک": 55, "Arleigh Burke": 55,
    "تایپ-۴۵": 52, "Type 45": 52,
    "مایا": 50, "Maya": 50,
    "هورایزن": 48, "Horizon": 48,
    "کلکته": 45, "Kolkata": 45,
    "تایپ-۵۲دی": 42, "Type 52D": 42,
    "کونگو": 38, "Kongo": 38,
    "اسپرونس": 32, "Spruance": 32,
    "هوبارت": 42, "Hobart": 42,
    
    # زیردریایی
    "یاسن": 70, "Yasen": 70,
    "اوهایو": 75, "Ohio": 75,
    "ویرجینیا": 65, "Virginia": 65,
    "ونگارد": 68, "Vanguard": 68,
    "تایپ-۰۹۳": 55, "Type 093": 55,
    "سی ولف": 58, "Seawolf": 58,
    "سافرن": 60, "Suffren": 60,
    "آریهانت": 52, "Arihant": 52,
    "سیرا": 48, "Sierra": 48,
    "تایپ-۰۹۱": 35, "Type 091": 35,
    
    # ناو هواپیمابر
    "فورد": 100, "Ford": 100,
    "نیمیتز": 85, "Nimitz": 85,
    "فوجیان": 80, "Fujian": 80,
    "ملکه الیزابت": 78, "Queen Elizabeth": 78,
    "شارل دوگل": 70, "Charles de Gaulle": 70,
    "شاندونگ": 68, "Shandong": 68,
    "لیائونینگ": 60, "Liaoning": 60,
    "کوزنتسف": 55, "Kuznetsov": 55,
    
    # پدافند
    "اس-۵۰۰": 90, "S-500": 90,
    "فلاخن داوود": 75, "David's Sling": 75,
    "اس-۴۰۰": 70, "S-400": 70,
    "تاد": 65, "THAAD": 65,
    "پاتریوت": 55, "Patriot": 55,
    "اچ‌کیو-۹بی": 50, "HQ-9B": 50,
    "اس-۳۰۰": 45, "S-300": 45,
}

# ==================== ویژگی‌های منحصر به فرد تجهیزات ====================

UNIT_ABILITIES = {
    # رادارگریز (Stealth) - قدرت دشمن کاهش می‌یابد
    "F22": {"stealth": 0.20, "name_fa": "رادارگریز"},
    "رپتور": {"stealth": 0.20, "name_fa": "رادارگریز"},
    "F35": {"stealth": 0.15, "name_fa": "رادارگریز"},
    "لایتنینگ": {"stealth": 0.15, "name_fa": "رادارگریز"},
    "جی۲۰": {"stealth": 0.15, "name_fa": "رادارگریز"},
    "J20": {"stealth": 0.15, "name_fa": "رادارگریز"},
    "SU57": {"stealth": 0.10, "name_fa": "رادارگریز"},
    "فلون": {"stealth": 0.10, "name_fa": "رادارگریز"},
    "Zumwalt": {"stealth": 0.25, "name_fa": "رادارگریز"},
    "زوموالت": {"stealth": 0.25, "name_fa": "رادارگریز"},
    
    # زره سنگین (Heavy Armor) - آسیب دریافتی کمتر
    "Challenger 2": {"heavy_armor": 0.25, "name_fa": "زره سنگین"},
    "چلنجر": {"heavy_armor": 0.25, "name_fa": "زره سنگین"},
    "Abrams X": {"heavy_armor": 0.20, "name_fa": "زره سنگین"},
    "آبرامز": {"heavy_armor": 0.20, "name_fa": "زره سنگین"},
    "T-14 Armata": {"heavy_armor": 0.15, "name_fa": "زره سنگین"},
    "آر ماتا": {"heavy_armor": 0.15, "name_fa": "زره سنگین"},
    "Merkava": {"heavy_armor": 0.15, "name_fa": "زره سنگین"},
    "مِرکاوا": {"heavy_armor": 0.15, "name_fa": "زره سنگین"},
    
    # سرعت بالا (Fast) - اول شلیک می‌کند و قدرت بیشتری دارد
    "Type 10": {"fast": 0.15, "name_fa": "سرعت بالا"},
    "تایپ-۱۰": {"fast": 0.15, "name_fa": "سرعت بالا"},
    "Leopard 1": {"fast": 0.10, "name_fa": "سرعت بالا"},
    "لئوپارد-۱": {"fast": 0.10, "name_fa": "سرعت بالا"},
    "Leopard 2A7+": {"fast": 0.10, "name_fa": "سرعت بالا"},
    "لئوپارد": {"fast": 0.10, "name_fa": "سرعت بالا"},
    "K2 Black Panther": {"fast": 0.10, "name_fa": "سرعت بالا"},
    "پلنگ سیاه": {"fast": 0.10, "name_fa": "سرعت بالا"},
    
    # برد بلند (Long Range) - ضربه اول را می‌زند
    "Koalitsiya-SV": {"long_range": 0.10, "name_fa": "برد بلند"},
    "کوالیتسیا": {"long_range": 0.10, "name_fa": "برد بلند"},
    "Yasen": {"long_range": 0.10, "name_fa": "برد بلند"},
    "یاسن": {"long_range": 0.10, "name_fa": "برد بلند"},
    "Ohio": {"long_range": 0.15, "name_fa": "برد بلند"},
    "اوهایو": {"long_range": 0.15, "name_fa": "برد بلند"},
    "Tempest": {"long_range": 0.10, "name_fa": "برد بلند"},
    "تمپست": {"long_range": 0.10, "name_fa": "برد بلند"},
    
    # تولید انبوه (Mass Production) - قدرت کمتر ولی قیمت کمتر
    "Type 99A": {"mass_production": -0.10, "name_fa": "تولید انبوه"},
    "تایپ-۹۹": {"mass_production": -0.10, "name_fa": "تولید انبوه"},
    "T-55": {"mass_production": -0.15, "name_fa": "تولید انبوه"},
    "تی-۵۵": {"mass_production": -0.15, "name_fa": "تولید انبوه"},
    
    # دفاع هوایی پیشرفته (Air Defense) - علیه هواپیماها
    "S-500": {"air_defense": 0.40, "name_fa": "دفاع هوایی پیشرفته"},
    "اس-۵۰۰": {"air_defense": 0.40, "name_fa": "دفاع هوایی پیشرفته"},
    "THAAD": {"air_defense": 0.35, "name_fa": "دفاع هوایی"},
    "تاد": {"air_defense": 0.35, "name_fa": "دفاع هوایی"},
    "S-400": {"air_defense": 0.30, "name_fa": "دفاع هوایی"},
    "اس-۴۰۰": {"air_defense": 0.30, "name_fa": "دفاع هوایی"},
    "David's Sling": {"air_defense": 0.30, "name_fa": "دفاع هوایی"},
    "فلاخن داوود": {"air_defense": 0.30, "name_fa": "دفاع هوایی"},
    
    # ضد زیردریایی (Anti-Sub) - علیه زیردریایی‌ها
    "Arleigh Burke": {"anti_sub": 0.30, "name_fa": "ضد زیردریایی"},
    "آرلی بروک": {"anti_sub": 0.30, "name_fa": "ضد زیردریایی"},
    "Type 55": {"anti_sub": 0.25, "name_fa": "ضد زیردریایی"},
    "تایپ-۵۵": {"anti_sub": 0.25, "name_fa": "ضد زیردریایی"},
    
    # هوش مصنوعی (AI-Assisted) - دقت بالا
    "Tempest": {"ai_assisted": 0.15, "name_fa": "هوش مصنوعی"},
    "تمپست": {"ai_assisted": 0.15, "name_fa": "هوش مصنوعی"},
    "Abrams X": {"ai_assisted": 0.10, "name_fa": "هوش مصنوعی"},
    "آبرامز": {"ai_assisted": 0.10, "name_fa": "هوش مصنوعی"},
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
    except Exception as e:
        print(f"Error loading: {e}")
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
    except Exception as e:
        print(f"Error saving: {e}")
        return False


def send_to_gcc(message: str):
    if not BALE_TOKEN or not GCC_CHAT_ID:
        return
    url = f"{BALE_API_URL}/sendMessage"
    payload = {"chat_id": GCC_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except:
        pass


def send_message(chat_id: str, text: str):
    if not BALE_TOKEN:
        return
    url = f"{BALE_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except:
        pass


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


def get_country_key(state: Dict[str, Any], user_id: str) -> Optional[str]:
    for country_key, player in state.get("countries", {}).items():
        if player.get("user_id") == user_id:
            return country_key
    return None


def get_speed_multiplier(state: Dict[str, Any]) -> int:
    return state.get("admin", {}).get("game_speed", 1)


def get_adjusted_deadline(base_hours: int, state: Dict[str, Any]) -> float:
    speed = get_speed_multiplier(state)
    adjusted = base_hours / speed
    return max(adjusted, 2)


def get_distance_between_countries(country1_key: str, country2_key: str, state: Dict[str, Any]) -> int:
    """محاسبه فاصله تقریبی بین دو کشور (بر اساس مختصات)"""
    coords1 = state["countries"].get(country1_key, {}).get("coordinates", {"x": "E", "y": 4})
    coords2 = state["countries"].get(country2_key, {}).get("coordinates", {"x": "E", "y": 4})
    
    x1 = ord(coords1.get("x", "E")) - ord('A')
    y1 = coords1.get("y", 4)
    x2 = ord(coords2.get("x", "E")) - ord('A')
    y2 = coords2.get("y", 4)
    
    distance = abs(x1 - x2) + abs(y1 - y2)
    return max(distance, 1)


# ==================== محاسبه قدرت با احتساب ویژگی‌ها ====================

def calculate_unit_power_with_abilities(unit: Dict[str, Any], is_against_air: bool = False, is_against_sub: bool = False) -> Tuple[int, float, float]:
    """
    محاسبه قدرت یک یگان با احتساب ویژگی‌های ویژه
    بازگشت: (قدرت واحد, ضریب رادارگریز, ضریب زره سنگین)
    """
    name_fa = unit.get("name_fa", "")
    name_en = unit.get("name_en", "")
    health = unit.get("health", 100)
    experience = unit.get("experience", 0)
    
    base_power = UNIT_POWERS.get(name_fa, UNIT_POWERS.get(name_en, 30))
    
    health_mult = health / 100
    exp_mult = 1 + (experience * 0.1)
    
    power = int(base_power * health_mult * exp_mult)
    
    ability = UNIT_ABILITIES.get(name_fa, UNIT_ABILITIES.get(name_en, {}))
    
    stealth = ability.get("stealth", 0)
    heavy_armor = ability.get("heavy_armor", 0)
    
    fast = ability.get("fast", 0)
    if fast:
        power = int(power * (1 + fast))
    
    air_defense = ability.get("air_defense", 0)
    if is_against_air and air_defense:
        power = int(power * (1 + air_defense))
    
    anti_sub = ability.get("anti_sub", 0)
    if is_against_sub and anti_sub:
        power = int(power * (1 + anti_sub))
    
    ai_assisted = ability.get("ai_assisted", 0)
    if ai_assisted:
        power = int(power * (1 + ai_assisted))
    
    mass_production = ability.get("mass_production", 0)
    if mass_production:
        power = int(power * (1 + mass_production))
    
    long_range = ability.get("long_range", 0)
    if long_range:
        power = int(power * (1 + long_range))
    
    return power, stealth, heavy_armor


def calculate_army_power_with_abilities(units: Dict[str, Any], category: str) -> Tuple[int, float, float]:
    """محاسبه قدرت کل یک دسته از یگان‌ها"""
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
    """محاسبه قدرت کل ارتش یک کشور با احتساب ویژگی‌ها"""
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


# ==================== ضرایب نبرد ====================

def get_alliance_bonus(state: Dict[str, Any], country_key: str, is_attacker: bool) -> float:
    """محاسبه ضریب ائتلاف"""
    player = state["countries"].get(country_key, {})
    treaties = player.get("treaties", [])
    
    allies_count = 0
    for treaty in treaties:
        if treaty.get("type") == "full_alliance":
            allies_count += 1
    
    if allies_count == 0:
        return 1.0
    
    # هر متحد ۱۰٪ قدرت بیشتر (حداکثر ۵۰٪)
    bonus = 1 + min(0.1 * allies_count, 0.5)
    return bonus


def get_logistics_multiplier(distance: int, is_defender: bool) -> float:
    """محاسبه ضریب لجستیک (فاصله از پایگاه)"""
    if is_defender:
        return 1.0  # مدافع در خاک خودش
    
    # هر ۵ واحد فاصله، ۱۰٪ کاهش قدرت (حداقل ۵۰٪)
    multiplier = 1 - (distance / 50)
    return max(multiplier, 0.5)


def get_home_defense_bonus(is_defender: bool) -> float:
    """ضریب دفاع از خاک"""
    return 1.25 if is_defender else 1.0


def get_attrition_multiplier(war_days: int) -> float:
    """ضریب فرسایش (هرچه جنگ طولانی‌تر، ضعیف‌تر)"""
    if war_days <= 3:
        return 1.0
    elif war_days <= 7:
        return 0.95
    elif war_days <= 14:
        return 0.90
    else:
        return 0.85


def get_industry_penalty(industry: int, is_attacker: bool) -> float:
    """ضریب صنعت دشمن (اگر صنعت پایین باشد، قدرت کمتری دارد)"""
    if industry >= 8:
        return 1.0
    elif industry >= 5:
        return 0.95
    elif industry >= 3:
        return 0.90
    else:
        return 0.85


def get_sanction_penalty(player: Dict[str, Any]) -> float:
    """ضریب تحریم"""
    if player.get("sanctioned", False):
        return 0.70
    return 1.0


def calculate_final_power(
    raw_power: int,
    alliance_bonus: float,
    logistics_mult: float,
    home_defense_bonus: float,
    attrition_mult: float,
    industry_penalty: float,
    sanction_penalty: float,
    stealth: float,
    heavy_armor: float,
    is_attacker: bool
) -> Tuple[int, float]:
    """
    محاسبه قدرت نهایی با همه ضرایب
    بازگشت: (قدرت نهایی, ضریب رادارگریز برای کاهش قدرت دشمن)
    """
    # اعمال ضرایب
    final = raw_power
    final = final * alliance_bonus
    final = final * logistics_mult
    final = final * home_defense_bonus
    final = final * attrition_mult
    final = final * industry_penalty
    final = final * sanction_penalty
    
    # ضریب رادارگریز برای کاهش قدرت دشمن
    stealth_effect = stealth
    
    return int(final), stealth_effect


# ==================== نتیجه نبرد ====================

def calculate_battle_result(
    attacker_power: int, defender_power: int,
    attacker_stealth: float, defender_stealth: float,
    attacker_heavy: float, defender_heavy: float
) -> Tuple[str, int, int, str]:
    """
    محاسبه نتیجه نبرد
    بازگشت: (نتیجه, تلفات مهاجم, تلفات مدافع, شرح نتیجه)
    """
    # اعمال ضریب رادارگریز (قدرت دشمن کاهش می‌یابد)
    effective_attacker_power = int(attacker_power * (1 - defender_stealth))
    effective_defender_power = int(defender_power * (1 - attacker_stealth))
    
    # اعمال ضریب زره سنگین (کاهش آسیب دریافتی)
    attacker_loss_mult = 1 - attacker_heavy
    defender_loss_mult = 1 - defender_heavy
    
    total_power = effective_attacker_power + effective_defender_power
    
    if total_power == 0:
        return "draw", 0, 0, "🤝 نبرد مساوی شد! هیچکدام نتوانستند پیروز شوند."
    
    if effective_attacker_power > effective_defender_power + 100:
        # پیروزی قاطع مهاجم
        defender_loss = int(defender_power * 0.35 * defender_loss_mult)
        attacker_loss = int(attacker_power * 0.05 * attacker_loss_mult)
        return "attacker_crushing", attacker_loss, defender_loss, "🏆 پیروزی قاطع مهاجم! دشمن به شدت شکست خورد."
    
    elif effective_attacker_power > effective_defender_power:
        # پیروزی معمولی مهاجم
        defender_loss = int(defender_power * 0.20 * defender_loss_mult)
        attacker_loss = int(attacker_power * 0.10 * attacker_loss_mult)
        return "attacker_win", attacker_loss, defender_loss, "✅ مهاجم پیروز شد! دشمن عقب‌نشینی کرد."
    
    elif effective_defender_power > effective_attacker_power + 100:
        # پیروزی قاطع مدافع
        attacker_loss = int(attacker_power * 0.35 * attacker_loss_mult)
        defender_loss = int(defender_power * 0.05 * defender_loss_mult)
        return "defender_crushing", attacker_loss, defender_loss, "🛡️ پیروزی قاطع مدافع! مهاجم متوقف شد."
    
    elif effective_defender_power > effective_attacker_power:
        # پیروزی معمولی مدافع
        attacker_loss = int(attacker_power * 0.20 * attacker_loss_mult)
        defender_loss = int(defender_power * 0.10 * defender_loss_mult)
        return "defender_win", attacker_loss, defender_loss, "✅ مدافع پیروز شد! مهاجم عقب‌نشینی کرد."
    
    else:
        # مساوی
        attacker_loss = int(attacker_power * 0.10 * attacker_loss_mult)
        defender_loss = int(defender_power * 0.10 * defender_loss_mult)
        return "draw", attacker_loss, defender_loss, "🤝 نبرد مساوی شد! هر دو طرف متحمل خسارت شدند."


# ==================== محاسبه کامل قدرت یک کشور در جنگ ====================

def calculate_country_battle_power(state: Dict[str, Any], country_key: str, is_attacker: bool, distance: int, war_days: int) -> Tuple[int, float, float, Dict[str, Any]]:
    """محاسبه کامل قدرت یک کشور در جنگ با همه ضرایب"""
    player = state["countries"].get(country_key, {})
    
    raw_power, stealth, heavy_armor = calculate_total_power_with_abilities(player)
    
    alliance_bonus = get_alliance_bonus(state, country_key, is_attacker)
    logistics_mult = get_logistics_multiplier(distance, not is_attacker)
    home_defense_bonus = get_home_defense_bonus(not is_attacker)
    attrition_mult = get_attrition_multiplier(war_days)
    industry_penalty = get_industry_penalty(player.get("industry", 5), is_attacker)
    sanction_penalty = get_sanction_penalty(player)
    
    final_power, final_stealth = calculate_final_power(
        raw_power, alliance_bonus, logistics_mult, home_defense_bonus,
        attrition_mult, industry_penalty, sanction_penalty, stealth, heavy_armor, is_attacker
    )
    
    details = {
        "raw_power": raw_power,
        "alliance_bonus": alliance_bonus,
        "logistics_mult": logistics_mult,
        "home_defense_bonus": home_defense_bonus,
        "attrition_mult": attrition_mult,
        "industry_penalty": industry_penalty,
        "sanction_penalty": sanction_penalty,
        "stealth": stealth,
        "heavy_armor": heavy_armor,
        "final_power": final_power
    }
    
    return final_power, final_stealth, heavy_armor, details


# ==================== مدیریت جنگ ====================

def declare_war(state: Dict[str, Any], attacker_id: str, target_name: str) -> Tuple[bool, str]:
    """اعلان جنگ"""
    target_id = get_user_by_country(state, target_name)
    if not target_id:
        return False, f"❌ کشور '{target_name}' یافت نشد."
    
    if attacker_id == target_id:
        return False, "❌ نمی‌توانید به خودتان حمله کنید!"
    
    attacker_key = get_country_key(state, attacker_id)
    target_key = get_country_key(state, target_id)
    
    if not attacker_key or not target_key:
        return False, "❌ خطا در شناسایی کشورها."
    
    attacker_name = get_country_name(state, attacker_id)
    target_name = get_country_name(state, target_id)
    
    attacker_player = state["countries"][attacker_key]
    for war in attacker_player.get("active_wars", []):
        if war.get("with") == target_id and war.get("status") == "active":
            return False, "❌ شما در حال حاضر با این کشور در جنگ هستید!"
    
    distance = get_distance_between_countries(attacker_key, target_key, state)
    
    now = datetime.now().isoformat()
    new_war = {
        "with": target_id,
        "started_at": now,
        "status": "active",
        "current_sector": 1,
        "current_phase": "declaration",
        "last_move": now,
        "is_attacker": True,
        "attacker_power": 0,
        "defender_power": 0,
        "captured_sectors": [],
        "war_days": 0,
        "distance": distance
    }
    
    if "active_wars" not in attacker_player:
        attacker_player["active_wars"] = []
    attacker_player["active_wars"].append(new_war)
    
    defender_player = state["countries"][target_key]
    defender_war = new_war.copy()
    defender_war["is_attacker"] = False
    if "active_wars" not in defender_player:
        defender_player["active_wars"] = []
    defender_player["active_wars"].append(defender_war)
    
    save_game_state(state)
    
    gcc_msg = f"⚔️ *اعلان جنگ*\n{attacker_name} به {target_name} اعلام جنگ داد!\nفاصله: {distance} واحد"
    send_to_gcc(gcc_msg)
    
    deadline = get_adjusted_deadline(8, state)
    attacker_msg = f"⚔️ شما به {target_name} اعلام جنگ کردید.\nفاصله: {distance} واحد\nمدافع {deadline:.0f} ساعت فرصت پاسخ دارد."
    target_msg = f"⚔️ {attacker_name} به شما اعلام جنگ کرد!\nفاصله: {distance} واحد\nشما {deadline:.0f} ساعت فرصت پاسخ دارید.\nبرای استقرار نیرو: `/deploy`"
    
    send_message(attacker_id, attacker_msg)
    send_message(target_id, target_msg)
    
    return True, f"✅ اعلان جنگ به {target_name} ارسال شد."


def deploy_forces(state: Dict[str, Any], user_id: str, units_str: str = "") -> Tuple[bool, str]:
    """استقرار نیرو در جنگ فعال با محاسبه کامل قدرت"""
    player = None
    for country_key, p in state["countries"].items():
        if p.get("user_id") == user_id:
            player = p
            player_key = country_key
            break
    
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
    opponent_key = get_country_key(state, opponent_id)
    is_attacker = active_war.get("is_attacker", True)
    distance = active_war.get("distance", 5)
    war_days = active_war.get("war_days", 0)
    
    final_power, stealth, heavy_armor, details = calculate_country_battle_power(
        state, player_key, is_attacker, distance, war_days
    )
    
    if is_attacker:
        active_war["attacker_power"] = final_power
        active_war["attacker_stealth"] = stealth
        active_war["attacker_heavy"] = heavy_armor
    else:
        active_war["defender_power"] = final_power
        active_war["defender_stealth"] = stealth
        active_war["defender_heavy"] = heavy_armor
    
    active_war["current_phase"] = "attack"
    active_war["last_move"] = datetime.now().isoformat()
    
    save_game_state(state)
    
    power_msg = f"قدرت خام: {details['raw_power']} | "
    power_msg += f"ائتلاف: {details['alliance_bonus']:.1f}x | "
    power_msg += f"لجستیک: {details['logistics_mult']:.1f}x | "
    power_msg += f"دفاع از خاک: {details['home_defense_bonus']:.1f}x | "
    power_msg += f"فرسایش: {details['attrition_mult']:.1f}x"
    
    return True, f"✅ نیروهای شما مستقر شدند!\nقدرت نهایی: {final_power}\n{power_msg}"


def resolve_battle(state: Dict[str, Any], war: Dict[str, Any], attacker_key: str, defender_key: str) -> Tuple[bool, str]:
    """حل یک نبرد بین دو طرف"""
    attacker_power = war.get("attacker_power", 0)
    defender_power = war.get("defender_power", 0)
    attacker_stealth = war.get("attacker_stealth", 0)
    defender_stealth = war.get("defender_stealth", 0)
    attacker_heavy = war.get("attacker_heavy", 0)
    defender_heavy = war.get("defender_heavy", 0)
    
    if attacker_power == 0 or defender_power == 0:
        return False, "⚠️ یکی از طرفین نیرویی مستقر نکرده است."
    
    result, attacker_loss, defender_loss, description = calculate_battle_result(
        attacker_power, defender_power,
        attacker_stealth, defender_stealth,
        attacker_heavy, defender_heavy
    )
    
    # به‌روزرسانی جنگ
    if "attacker_crushing" in result or "attacker_win" in result:
        sector = war.get("current_sector", 1)
        war["captured_sectors"] = war.get("captured_sectors", []) + [sector]
        war["current_sector"] = sector + 1
        
        if war["current_sector"] > 3:
            war["status"] = "ended"
            war["ended_at"] = datetime.now().isoformat()
            return True, f"🏆 {description}\nبخش {sector} تصرف شد! پیروزی کامل."
        else:
            war["last_move"] = datetime.now().isoformat()
            return False, f"{description}\nبخش {sector} تصرف شد! نوبت بعدی: بخش {war['current_sector']}"
    
    elif "defender_crushing" in result or "defender_win" in result:
        war["status"] = "ended"
        war["ended_at"] = datetime.now().isoformat()
        return True, f"{description}\nمهاجم عقب‌نشینی کرد و جنگ تمام شد."
    
    else:
        war["war_days"] = war.get("war_days", 0) + 1
        war["last_move"] = datetime.now().isoformat()
        return False, f"{description}\nجنگ ادامه دارد. روز {war['war_days']}"


def get_war_status(state: Dict[str, Any], user_id: str) -> str:
    """دریافت وضعیت جنگ فعال با جزئیات کامل"""
    player = None
    for country_key, p in state["countries"].items():
        if p.get("user_id") == user_id:
            player = p
            break
    
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
    msg += f"📊 قدرت شما: {my_power}\n"
    msg += f"📊 قدرت دشمن: {enemy_power}\n"
    msg += f"📌 وضعیت: {phase_names.get(phase, phase)}\n"
    
    if my_power > 0 and enemy_power > 0:
        ratio = my_power / enemy_power if enemy_power > 0 else 99
        if ratio > 1.5:
            msg += "🔮 پیش‌بینی: پیروزی محتمل\n"
        elif ratio > 0.8:
            msg += "🔮 پیش‌بینی: نبرد نزدیک\n"
        else:
            msg += "🔮 پیش‌بینی: شکست محتمل\n"
    
    return msg


def propose_peace(state: Dict[str, Any], user_id: str, terms: str = "") -> Tuple[bool, str]:
    """پیشنهاد صلح"""
    player = None
    for country_key, p in state["countries"].items():
        if p.get("user_id") == user_id:
            player = p
            break
    
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
                    "war_days": war.get("war_days", 0)
                })
    
    if not wars:
        return "هیچ جنگ فعالی وجود ندارد."
    
    msg = "⚔️ *گزارش جنگ‌های فعال*\n\n"
    for war in wars:
        msg += f"• {war['attacker']} vs {war['defender']}\n"
        msg += f"  بخش: {war['sector']}/3 | روز: {war['war_days']}\n"
        msg += f"  قدرت: {war['attacker_power']} vs {war['defender_power']}\n\n"
    
    return msg


if __name__ == "__main__":
    print("War system module loaded with all coefficients")
