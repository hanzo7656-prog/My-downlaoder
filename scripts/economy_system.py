#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
سیستم کامل اقتصاد
امکانات: خرید تجهیزات، فروش تجهیزات، ارتقاء شاخص‌ها، مدیریت منابع، بازار
"""

import json
import os
import requests
import base64
import random
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

# ==================== تنظیمات ====================

GH_TOKEN = os.environ.get("GH_TOKEN", "")
REPO_OWNER = os.environ.get("REPO_OWNER", "")
REPO_NAME = os.environ.get("REPO_NAME", "")
BALE_TOKEN = os.environ.get("BALE_TOKEN", "")
GCC_CHAT_ID = os.environ.get("GCC_CHAT_ID", "")

GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/game_state.json"
BALE_API_URL = f"https://tapi.bale.ai/bot{BALE_TOKEN}"

# ==================== قیمت‌های پایه تجهیزات ====================

UNIT_PRICES = {
    # هواپیماها
    "تمپست": 350, "Tempest": 350,
    "F22": 300, "رپتور": 300,
    "SU57": 280, "فلون": 280,
    "F35": 250, "لایتنینگ": 250,
    "جی۲۰": 220, "J20": 220,
    "تایفون": 200, "Eurofighter Typhoon": 200,
    "رافال": 190, "Rafale": 190,
    "سوخو-۳۵": 170, "Su-35": 170,
    "سوپر هورنت": 150, "F/A-18": 150,
    "میگ-۲۹": 120, "MiG-29": 120,
    "فانتوم": 90, "F-4": 90,
    "جی-۱۵": 140, "J-15": 140,
    
    # تانک‌ها
    "آر ماتا": 250, "T-14 Armata": 250,
    "آبرامز": 230, "Abrams X": 230,
    "لئوپارد": 220, "Leopard 2A7+": 220,
    "پلنگ سیاه": 210, "K2 Black Panther": 210,
    "مِرکاوا": 200, "Merkava": 200,
    "چلنجر": 195, "Challenger 2": 195,
    "تایپ-۱۰": 185, "Type 10": 185,
    "لکلر": 190, "Leclerc": 190,
    "تایپ-۹۹": 180, "Type 99A": 180,
    "تی-۸۴": 170, "T-84": 170,
    "آبرامز ام۱": 120, "Abrams M1": 120,
    "تی-۹۰": 110, "T-90": 110,
    "لئوپارد ۲": 100, "Leopard 2": 100,
    "لئوپارد-۱": 60, "Leopard 1": 60,
    "تی-۵۵": 30, "T-55": 30,
    
    # توپخانه
    "کوالیتسیا": 140, "Koalitsiya-SV": 140,
    "پی‌زدهاچ-۲۰۰۰": 130, "PzH 2000": 130,
    "کی-۹": 120, "K9 Thunder": 120,
    "ام-۱۰۹": 110, "M109A7": 110,
    "پی‌ال‌زد-۵۲": 115, "PLZ-52": 115,
    "مستا-اس": 80, "Msta-S": 80,
    "ایاس-۹۰": 70, "AS90": 70,
    "ام-۱۰۹ قدیمی": 45, "M109": 45,
    
    # ناوشکن
    "زوموالت": 400, "Zumwalt": 400,
    "تایپ-۵۵": 350, "Type 55": 350,
    "سجونگ کبیر": 340, "Sejong the Great": 340,
    "آرلی بروک": 320, "Arleigh Burke": 320,
    "تایپ-۴۵": 300, "Type 45": 300,
    "مایا": 290, "Maya": 290,
    "هورایزن": 280, "Horizon": 280,
    "کلکته": 260, "Kolkata": 260,
    "تایپ-۵۲دی": 240, "Type 52D": 240,
    "کونگو": 200, "Kongo": 200,
    "هوبارت": 250, "Hobart": 250,
    "اسپرونس": 160, "Spruance": 160,
    
    # زیردریایی
    "اوهایو": 500, "Ohio": 500,
    "یاسن": 450, "Yasen": 450,
    "ونگارد": 480, "Vanguard": 480,
    "ویرجینیا": 400, "Virginia": 400,
    "سافرن": 380, "Suffren": 380,
    "تایپ-۰۹۳": 320, "Type 093": 320,
    "سی ولف": 310, "Seawolf": 310,
    "آریهانت": 300, "Arihant": 300,
    "سیرا": 250, "Sierra": 250,
    "تایپ-۰۹۱": 160, "Type 091": 160,
    
    # ناو هواپیمابر
    "فورد": 1200, "Ford": 1200,
    "نیمیتز": 1000, "Nimitz": 1000,
    "فوجیان": 950, "Fujian": 950,
    "ملکه الیزابت": 900, "Queen Elizabeth": 900,
    "شارل دوگل": 850, "Charles de Gaulle": 850,
    "شاندونگ": 800, "Shandong": 800,
    "لیائونینگ": 700, "Liaoning": 700,
    "کوزنتسف": 600, "Kuznetsov": 600,
    
    # پدافند
    "اس-۵۰۰": 350, "S-500": 350,
    "فلاخن داوود": 280, "David's Sling": 280,
    "اس-۴۰۰": 250, "S-400": 250,
    "تاد": 240, "THAAD": 240,
    "پاتریوت": 200, "Patriot": 200,
    "اچ‌کیو-۹بی": 180, "HQ-9B": 180,
    "اس-۳۰۰": 150, "S-300": 150,
}

# ==================== هزینه ارتقاء شاخص‌ها ====================

UPGRADE_COSTS = {
    "industry": [50, 80, 120, 170, 230, 300, 380, 470, 570, 680],
    "trade": [40, 60, 90, 130, 180, 240, 310, 390, 480, 580],
    "diplomacy": [30, 50, 80, 120, 170, 230, 300, 380, 470, 570]
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
        
        payload = {"message": f"[economy] {datetime.now().isoformat()}", "content": encoded, "sha": current_sha}
        response = requests.put(GITHUB_API_URL, headers=headers, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Error saving: {e}")
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


def get_user_data(state: Dict[str, Any], user_id: str) -> Optional[Dict[str, Any]]:
    for country_key, player in state.get("countries", {}).items():
        if player.get("user_id") == user_id:
            return player
    return None


def get_country_key(state: Dict[str, Any], user_id: str) -> Optional[str]:
    for country_key, player in state.get("countries", {}).items():
        if player.get("user_id") == user_id:
            return country_key
    return None


# ==================== خرید تجهیزات ====================

def buy_unit(state: Dict[str, Any], user_id: str, unit_name: str, count: int) -> Tuple[bool, str]:
    """خرید تجهیزات نظامی"""
    player = get_user_data(state, user_id)
    if not player:
        return False, "❌ شما کشوری انتخاب نکرده‌اید."
    
    if count <= 0 or count > 100:
        return False, "❌ تعداد باید بین 1 تا 100 باشد."
    
    # پیدا کردن قیمت
    price = UNIT_PRICES.get(unit_name, UNIT_PRICES.get(unit_name.lower(), 0))
    if price == 0:
        return False, f"❌ تجهیزات '{unit_name}' شناسایی نشد."
    
    total_cost = price * count
    influence = player.get("resources", {}).get("influence", 0)
    
    if influence < total_cost:
        return False, f"❌ نفوذ کافی ندارید. نیاز: {total_cost} (شما: {influence})"
    
    # تشخیص دسته تجهیزات و اضافه کردن
    air_units = ["F22", "رپتور", "F35", "لایتنینگ", "SU57", "فلون", "جی۲۰", "J20", "تایفون", "رافال", "تمپست", "سوخو-۳۵", "میگ-۲۹", "فانتوم", "سوپر هورنت", "جی-۱۵"]
    ground_units = ["آر ماتا", "آبرامز", "لئوپارد", "چلنجر", "پلنگ سیاه", "مِرکاوا", "تایپ-۱۰", "لکلر", "تایپ-۹۹", "تی-۸۴", "آبرامز ام۱", "تی-۹۰", "لئوپارد ۲", "لئوپارد-۱", "تی-۵۵"]
    artillery_units = ["کوالیتسیا", "پی‌زدهاچ-۲۰۰۰", "کی-۹", "ام-۱۰۹", "پی‌ال‌زد-۵۲", "مستا-اس", "ایاس-۹۰", "ام-۱۰۹ قدیمی"]
    naval_units = ["زوموالت", "تایپ-۵۵", "سجونگ کبیر", "آرلی بروک", "تایپ-۴۵", "مایا", "هورایزن", "کلکته", "تایپ-۵۲دی", "کونگو", "هوبارت", "اسپرونس"]
    sub_units = ["اوهایو", "یاسن", "ونگارد", "ویرجینیا", "سافرن", "تایپ-۰۹۳", "سی ولف", "آریهانت", "سیرا", "تایپ-۰۹۱"]
    carrier_units = ["فورد", "نیمیتز", "فوجیان", "ملکه الیزابت", "شارل دوگل", "شاندونگ", "لیائونینگ", "کوزنتسف"]
    defense_units = ["اس-۵۰۰", "فلاخن داوود", "اس-۴۰۰", "تاد", "پاتریوت", "اچ‌کیو-۹بی", "اس-۳۰۰"]
    
    units = player.get("units", {})
    
    # تعیین دسته
    if unit_name in air_units or any(u in unit_name for u in air_units):
        category = "air"
    elif unit_name in ground_units or any(u in unit_name for u in ground_units):
        category = "ground"
    elif unit_name in artillery_units or any(u in unit_name for u in artillery_units):
        category = "artillery"
    elif unit_name in naval_units or any(u in unit_name for u in naval_units):
        category = "destroyer"
    elif unit_name in sub_units or any(u in unit_name for u in sub_units):
        category = "submarine"
    elif unit_name in carrier_units or any(u in unit_name for u in carrier_units):
        category = "carrier"
    elif unit_name in defense_units or any(u in unit_name for u in defense_units):
        category = "air_defense"
    else:
        category = "ground"  # پیش‌فرض
    
    # اضافه کردن یگان
    if category not in units:
        units[category] = []
    
    found = False
    for unit in units[category]:
        if unit.get("name_fa") == unit_name or unit.get("name_en") == unit_name:
            unit["count"] = unit.get("count", 0) + count
            found = True
            break
    
    if not found:
        units[category].append({
            "name_fa": unit_name,
            "name_en": unit_name,
            "count": count,
            "health": 100,
            "experience": 0
        })
    
    # کسر هزینه
    player["resources"]["influence"] = influence - total_cost
    
    save_game_state(state)
    
    return True, f"✅ {count} عدد {unit_name} خریداری شد! هزینه: {total_cost} نفوذ"


def sell_unit(state: Dict[str, Any], user_id: str, unit_name: str, count: int) -> Tuple[bool, str]:
    """فروش تجهیزات نظامی (با 50% قیمت)"""
    player = get_user_data(state, user_id)
    if not player:
        return False, "❌ شما کشوری انتخاب نکرده‌اید."
    
    if count <= 0:
        return False, "❌ تعداد باید بیشتر از 0 باشد."
    
    # پیدا کردن یگان
    units = player.get("units", {})
    found = False
    for category, unit_list in units.items():
        for unit in unit_list:
            if unit.get("name_fa") == unit_name or unit.get("name_en") == unit_name:
                current = unit.get("count", 0)
                if current < count:
                    return False, f"❌ شما فقط {current} عدد {unit_name} دارید."
                
                price = UNIT_PRICES.get(unit_name, UNIT_PRICES.get(unit_name.lower(), 0))
                if price == 0:
                    return False, f"❌ قیمت {unit_name} مشخص نیست."
                
                sell_price = (price * count) // 2  # 50% قیمت
                unit["count"] = current - count
                
                if unit["count"] == 0:
                    unit_list.remove(unit)
                
                player["resources"]["influence"] = player.get("resources", {}).get("influence", 0) + sell_price
                found = True
                break
        if found:
            break
    
    if not found:
        return False, f"❌ شما {unit_name} ندارید."
    
    save_game_state(state)
    
    return True, f"💰 {count} عدد {unit_name} فروخته شد! دریافت: {sell_price} نفوذ"


# ==================== ارتقاء شاخص‌ها ====================

def upgrade_stat(state: Dict[str, Any], user_id: str, stat_name: str) -> Tuple[bool, str]:
    """ارتقاء شاخص (صنعت، تجارت، دیپلماسی)"""
    player = get_user_data(state, user_id)
    if not player:
        return False, "❌ شما کشوری انتخاب نکرده‌اید."
    
    if stat_name not in ["industry", "trade", "diplomacy"]:
        return False, "❌ شاخص نامعتبر. انتخاب‌ها: industry, trade, diplomacy"
    
    current = player.get(stat_name, 0)
    if current >= 10:
        return False, f"❌ سطح {stat_name} شما در حال حاضر حداکثر (۱۰) است."
    
    costs = UPGRADE_COSTS.get(stat_name, [])
    if current >= len(costs):
        return False, "❌ خطا در محاسبه هزینه."
    
    cost = costs[current]
    influence = player.get("resources", {}).get("influence", 0)
    
    if influence < cost:
        return False, f"❌ نفوذ کافی ندارید. نیاز: {cost} (شما: {influence})"
    
    player[stat_name] = current + 1
    player["resources"]["influence"] = influence - cost
    
    save_game_state(state)
    
    persian_names = {"industry": "صنعت", "trade": "تجارت", "diplomacy": "دیپلماسی"}
    return True, f"✅ {persian_names[stat_name]} شما به سطح {current + 1} ارتقاء یافت! هزینه: {cost} نفوذ"


# ==================== تحقیق فناوری ====================

def research_tech(state: Dict[str, Any], user_id: str, branch: str, level: int) -> Tuple[bool, str]:
    """تحقیق فناوری در شاخه مشخص"""
    player = get_user_data(state, user_id)
    if not player:
        return False, "❌ شما کشوری انتخاب نکرده‌اید."
    
    valid_branches = ["military", "industrial", "economic", "diplomacy", "nuclear"]
    if branch not in valid_branches:
        return False, f"❌ شاخه نامعتبر. انتخاب‌ها: {', '.join(valid_branches)}"
    
    research = player.get("research", {})
    current = research.get(branch, 0)
    
    if level <= current:
        return False, f"❌ شما قبلاً این سطح را تحقیق کرده‌اید."
    
    if level > current + 1:
        return False, f"❌ ابتدا باید سطح {current + 1} را تحقیق کنید."
    
    # هزینه‌های تقریبی
    costs = [20, 40, 70, 110, 160, 220, 290, 370, 460]
    if level > len(costs):
        return False, "❌ سطح نامعتبر."
    
    cost = costs[level - 1]
    tech_points = player.get("resources", {}).get("tech_points", 0)
    
    if tech_points < cost:
        return False, f"❌ فناوری کافی ندارید. نیاز: {cost} (شما: {tech_points})"
    
    research[branch] = level
    player["resources"]["tech_points"] = tech_points - cost
    
    save_game_state(state)
    
    branch_names = {
        "military": "نظامی", "industrial": "صنعتی",
        "economic": "اقتصادی", "diplomacy": "دیپلماسی", "nuclear": "هسته‌ای"
    }
    
    return True, f"✅ فناوری {branch_names[branch]} سطح {level} تحقیق شد! هزینه: {cost} فناوری"


# ==================== مدیریت منابع ====================

def get_daily_income(player: Dict[str, Any]) -> int:
    """محاسبه درآمد روزانه نفوذ"""
    industry = player.get("industry", 0)
    trade = player.get("trade", 0)
    stability = player.get("stability", 5)
    
    base = (trade * 15) + (industry * 5) + (stability * 2)
    
    if stability >= 8:
        base = int(base * 1.2)
    elif stability <= 2:
        base = int(base * 0.5)
    
    return base


def get_daily_tech(player: Dict[str, Any]) -> int:
    """محاسبه تولید روزانه فناوری"""
    base = 50
    trade = player.get("trade", 0)
    return base + (trade * 5)


def add_daily_resources(state: Dict[str, Any]) -> Dict[str, List[Tuple[str, int]]]:
    """اضافه کردن منابع روزانه به همه بازیکنان"""
    players = state.get("countries", {})
    results = {"influence": [], "tech": []}
    
    for country_key, player in players.items():
        if player.get("user_id") is None:
            continue
        
        name = player.get("name_fa", country_key)
        
        influence = get_daily_income(player)
        tech = get_daily_tech(player)
        
        if "resources" not in player:
            player["resources"] = {}
        
        player["resources"]["influence"] = player["resources"].get("influence", 0) + influence
        player["resources"]["tech_points"] = player["resources"].get("tech_points", 0) + tech
        
        results["influence"].append((name, influence))
        results["tech"].append((name, tech))
    
    return results


def get_inventory(state: Dict[str, Any], user_id: str) -> str:
    """دریافت لیست تجهیزات کشور"""
    player = get_user_data(state, user_id)
    if not player:
        return "❌ شما کشوری انتخاب نکرده‌اید."
    
    units = player.get("units", {})
    categories = [
        ("air", "✈️ هوایی"),
        ("ground", "🪖 زمینی (تانک)"),
        ("artillery", "💣 توپخانه"),
        ("destroyer", "🚢 ناوشکن"),
        ("submarine", "🛥️ زیردریایی"),
        ("carrier", "⚓ ناو هواپیمابر"),
        ("air_defense", "🛡️ پدافند")
    ]
    
    msg = f"📦 *تجهیزات نظامی {player.get('name_fa')}*\n\n"
    has_items = False
    
    for cat_key, cat_name in categories:
        items = units.get(cat_key, [])
        cat_items = []
        for item in items:
            count = item.get("count", 0)
            if count > 0:
                name = item.get("name_fa", item.get("name_en", "نامشخص"))
                health = item.get("health", 100)
                health_status = "🟢" if health == 100 else "🟡" if health >= 50 else "🔴"
                experience = item.get("experience", 0)
                stars = "⭐" * experience if experience > 0 else "☆"
                cat_items.append(f"  {health_status} {name}: {count} عدد (سلامت {health}%)")
        
        if cat_items:
            has_items = True
            msg += f"{cat_name}:\n"
            msg += "\n".join(cat_items) + "\n\n"
    
    if not has_items:
        msg += "❌ هیچ تجهیزاتی ندارید.\nبا /buy خرید کنید."
    
    return msg


# ==================== توابع عمومی ====================

def get_market_prices() -> Dict[str, int]:
    """دریافت قیمت‌های فعلی بازار (با نوسان تصادفی)"""
    prices = {}
    for name, base in UNIT_PRICES.items():
        # نوسان ±10%
        variation = random.uniform(0.9, 1.1)
        prices[name] = int(base * variation)
    return prices

def update_unit_experience(state: Dict[str, Any], country_key: str, category: str, unit_name: str, amount: float):
    """
    افزایش تجربه یک یگان خاص
    amount: مقدار تجربه اضافه شده (0.5 یا 1)
    """
    player = state["countries"].get(country_key)
    if not player:
        return
    
    units = player.get("units", {})
    for unit in units.get(category, []):
        if unit.get("name_fa") == unit_name or unit.get("name_en") == unit_name:
            current = unit.get("experience", 0)
            # حداکثر 5 ستاره
            new_exp = min(current + amount, 5)
            unit["experience"] = new_exp
            return

if __name__ == "__main__":
    print("Economy system module loaded")
