#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
سیستم بلایای طبیعی
انواع بلا: زلزله، سیل، طوفان، آتش‌سوزی، خشکسالی، گردباد، آتشفشان، همه‌گیری، شهاب سنگ
هر 72 ساعت یک بلا به طور تصادفی رخ می‌دهد
"""

import json
import os
import requests
import base64
import random
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

# ==================== تعریف بلایا ====================

DISASTERS = {
    "earthquake": {
        "name_fa": "🌋 زلزله",
        "name_en": "Earthquake",
        "probability": 12,  # درصد (مجموع 100)
        "duration": 0,  # آنی
        "effects": {
            "industry_damage": 2,        # -2 صنعت
            "ground_units_damage": 0.30, # 30% تجهیزات زمینی آسیب
            "building_damage_chance": 0.30,
        },
        "counter_measures": {
            "early_warning": False,
            "cost": 200,
            "effect_reduction": 0.50
        }
    },
    "flood": {
        "name_fa": "🌊 سیل",
        "name_en": "Flood",
        "probability": 12,
        "duration": 3,  # روز
        "effects": {
            "ammo_production_penalty": 0.50,  # -50% تولید مهمات
            "ground_units_damage": 0.15,
        },
        "counter_measures": {
            "dam": True,
            "cost": 150,
            "effect_reduction": 0.70
        }
    },
    "storm": {
        "name_fa": "🌀 طوفان",
        "name_en": "Storm",
        "probability": 12,
        "duration": 7,
        "effects": {
            "naval_lockdown": True,        # ناوگان قفل می‌شوند
            "air_units_grounded": 0.50,    # 50% هواپیماها زمین‌گیر
        },
        "counter_measures": {
            "covered_dock": True,
            "cost": 250,
            "effect_reduction": 0.60
        }
    },
    "wildfire": {
        "name_fa": "🔥 آتش‌سوزی جنگل",
        "name_en": "Wildfire",
        "probability": 12,
        "duration": 5,
        "effects": {
            "fuel_production_penalty": 0.20,  # -20% تولید سوخت
            "industry_damage": 1,
        },
        "counter_measures": {
            "firefighting": True,
            "cost": 100,
            "effect_reduction": 0.80
        }
    },
    "drought": {
        "name_fa": "🏜️ خشکسالی",
        "name_en": "Drought",
        "probability": 12,
        "duration": 7,
        "effects": {
            "income_penalty": 0.30,        # -30% درآمد
            "approval_penalty": 2,          # -2 رضایت
        },
        "counter_measures": {
            "irrigation": True,
            "cost": 180,
            "effect_reduction": 0.60
        }
    },
    "tornado": {
        "name_fa": "🌪️ گردباد",
        "name_en": "Tornado",
        "probability": 10,
        "duration": 0,
        "effects": {
            "air_units_destroyed": 0.15,   # 15% تجهیزات هوایی نابود
            "building_damage_chance": 0.20,
        },
        "counter_measures": {
            "underground_shelter": True,
            "cost": 300,
            "effect_reduction": 0.70
        }
    },
    "volcano": {
        "name_fa": "🌋 آتشفشان",
        "name_en": "Volcano",
        "probability": 8,
        "duration": 4,
        "effects": {
            "trade_penalty": 1,            # -1 تجارت
            "flights_cancelled": 0.50,     # 50% پروازها لغو
            "air_quality_penalty": 0.20,
        },
        "counter_measures": {
            "temporary_relocation": True,
            "cost": 250,
            "effect_reduction": 0.50
        }
    },
    "pandemic": {
        "name_fa": "🦠 همه‌گیری",
        "name_en": "Pandemic",
        "probability": 10,
        "duration": 10,
        "effects": {
            "population_reduction": 0.20,   # -20% نیروی انسانی
            "production_penalty": 0.30,
            "approval_penalty": 3,
        },
        "counter_measures": {
            "quarantine": True,
            "cost": 120,
            "effect_reduction": 0.60
        }
    },
    "meteor": {
        "name_fa": "☄️ شهاب سنگ",
        "name_en": "Meteor Strike",
        "probability": 1,
        "duration": 0,
        "effects": {
            "industry_damage": 5,          # -5 صنعت
            "units_destroyed": 1.00,       # 100% تجهیزات در منطقه
            "building_destroyed": 1.00,
        },
        "counter_measures": {},
        "special": "unavoidable"
    }
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
        
        payload = {"message": f"[disaster] {datetime.now().isoformat()}", "content": encoded, "sha": current_sha}
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


def get_country_key_by_user(state: Dict[str, Any], user_id: str) -> Optional[str]:
    for country_key, player in state.get("countries", {}).items():
        if player.get("user_id") == user_id:
            return country_key
    return None


def get_country_name(state: Dict[str, Any], user_id: str) -> str:
    for country_key, player in state.get("countries", {}).items():
        if player.get("user_id") == user_id:
            return player.get("name_fa", country_key)
    return "نامشخص"


def get_active_disasters(state: Dict[str, Any], country_key: str) -> List[Dict[str, Any]]:
    """دریافت بلایای فعال یک کشور"""
    country = state["countries"].get(country_key, {})
    return country.get("active_disasters", [])


def get_disaster_effects(state: Dict[str, Any], country_key: str) -> Dict[str, Any]:
    """دریافت اثرات جمعی بلایای فعال یک کشور"""
    country = state["countries"].get(country_key, {})
    disasters = country.get("active_disasters", [])
    now = datetime.now()
    
    total_effects = {}
    
    for disaster in disasters:
        expires_at = disaster.get("expires_at")
        if expires_at:
            expires = datetime.fromisoformat(expires_at)
            if expires <= now:
                continue
        
        effects = disaster.get("effects", {})
        for key, value in effects.items():
            if key not in total_effects:
                total_effects[key] = value
            elif isinstance(value, (int, float)):
                total_effects[key] = max(total_effects[key], value)
            else:
                total_effects[key] = total_effects[key] or value
    
    return total_effects


def apply_disaster_effects(state: Dict[str, Any], country_key: str, disaster_type: str, with_counter: bool = False):
    """اعمال اثرات بلا روی کشور"""
    country = state["countries"].get(country_key)
    if not country:
        return
    
    disaster_info = DISASTERS.get(disaster_type, {})
    effects = disaster_info.get("effects", {}).copy()
    
    # کاهش اثرات در صورت مقابله
    if with_counter:
        reduction = disaster_info.get("counter_measures", {}).get("effect_reduction", 0)
        for key in effects:
            if isinstance(effects[key], (int, float)):
                effects[key] = effects[key] * (1 - reduction)
    
    # اعمال اثرات
    if "industry_damage" in effects:
        new_industry = max(0, country.get("industry", 0) - effects["industry_damage"])
        country["industry"] = new_industry
    
    if "trade_penalty" in effects:
        new_trade = max(0, country.get("trade", 0) - effects["trade_penalty"])
        country["trade"] = new_trade
    
    if "approval_penalty" in effects:
        new_approval = max(0, country.get("approval", 5) - effects["approval_penalty"])
        country["approval"] = new_approval
    
    if "ground_units_damage" in effects:
        damage_units(state, country_key, "ground", effects["ground_units_damage"])
    
    if "air_units_destroyed" in effects:
        damage_units(state, country_key, "air", effects["air_units_destroyed"])
    
    if "naval_lockdown" in effects:
        country["naval_lockdown_until"] = (datetime.now() + timedelta(days=disaster_info.get("duration", 0))).isoformat()
    
    if "income_penalty" in effects or "ammo_production_penalty" in effects or "fuel_production_penalty" in effects:
        # ذخیره اثرات برای مدت زمان بلا
        disaster_record = {
            "type": disaster_type,
            "name_fa": disaster_info.get("name_fa"),
            "started_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=disaster_info.get("duration", 0))).isoformat(),
            "effects": effects
        }
        
        if "active_disasters" not in country:
            country["active_disasters"] = []
        country["active_disasters"].append(disaster_record)


def damage_units(state: Dict[str, Any], country_key: str, category: str, damage_percent: float):
    """اعمال آسیب به یگان‌های یک دسته"""
    country = state["countries"].get(country_key)
    if not country:
        return
    
    units = country.get("units", {})
    for unit in units.get(category, []):
        count = unit.get("count", 0)
        if count > 0:
            destroyed = int(count * damage_percent)
            unit["count"] = max(0, count - destroyed)


def buy_insurance(state: Dict[str, Any], user_id: str) -> Tuple[bool, str]:
    """خرید بیمه بلایا (کاهش 50% خسارت)"""
    player = get_country_data(state, user_id)
    if not player:
        return False, "❌ شما کشوری انتخاب نکرده‌اید."
    
    influence = player.get("resources", {}).get("influence", 0)
    if influence < 100:
        return False, "❌ نفوذ کافی ندارید. نیاز: 100"
    
    player["resources"]["influence"] -= 100
    player["insurance_until"] = (datetime.now() + timedelta(days=7)).isoformat()
    
    save_game_state(state)
    
    return True, "✅ بیمه بلایا به مدت 7 روز فعال شد. در صورت وقوع بلا، 50% خسارت جبران می‌شود."


def has_insurance(state: Dict[str, Any], country_key: str) -> bool:
    """بررسی وجود بیمه فعال"""
    country = state["countries"].get(country_key, {})
    insurance_until = country.get("insurance_until")
    if insurance_until:
        try:
            expires = datetime.fromisoformat(insurance_until)
            return expires > datetime.now()
        except:
            pass
    return False


def get_random_disaster() -> Tuple[str, Dict[str, Any]]:
    """دریافت یک بلا به صورت تصادفی (بر اساس احتمال)"""
    disasters_list = []
    for disaster_id, info in DISASTERS.items():
        prob = info.get("probability", 0)
        if prob > 0:
            disasters_list.extend([disaster_id] * prob)
    
    if not disasters_list:
        return "earthquake", DISASTERS["earthquake"]
    
    selected = random.choice(disasters_list)
    return selected, DISASTERS[selected]


def check_and_trigger_disaster(state: Dict[str, Any]) -> Tuple[bool, str, str]:
    """
    بررسی و وقوع بلا (هر 72 ساعت)
    بازگشت: (آیا بلا رخ داد، کشور هدف، نوع بلا)
    """
    last_disaster = state.get("last_disaster_time")
    if last_disaster:
        try:
            last = datetime.fromisoformat(last_disaster)
            if datetime.now() - last < timedelta(hours=72):
                return False, "", ""
        except:
            pass
    
    # انتخاب کشور تصادفی
    countries = [k for k, v in state.get("countries", {}).items() if v.get("user_id") is not None]
    if not countries:
        return False, "", ""
    
    target_country = random.choice(countries)
    disaster_id, disaster_info = get_random_disaster()
    
    # اعمال اثرات
    apply_disaster_effects(state, target_country, disaster_id, False)
    
    # ذخیره زمان آخرین بلا
    state["last_disaster_time"] = datetime.now().isoformat()
    
    save_game_state(state)
    
    # اعلان به GCC
    country_name = state["countries"][target_country].get("name_fa", target_country)
    msg = f"⚠️ *بلا در {country_name}*\n{disaster_info['name_fa']} رخ داد!\n\n"
    
    effects = disaster_info.get("effects", {})
    if "industry_damage" in effects:
        msg += f"🏭 صنعت: -{effects['industry_damage']}\n"
    if "trade_penalty" in effects:
        msg += f"💰 تجارت: -{effects['trade_penalty']}\n"
    if "approval_penalty" in effects:
        msg += f"😊 رضایت: -{effects['approval_penalty']}\n"
    
    msg += f"\nکشورهای دیگر می‌توانند کمک بفرستند: `/aid {country_name}`"
    
    send_to_gcc(msg)
    
    return True, target_country, disaster_id


def get_warning(state: Dict[str, Any]) -> str:
    """دریافت هشدار بلایای در حال وقوع"""
    countries = state.get("countries", {})
    warnings = []
    
    for key, country in countries.items():
        disasters = get_active_disasters(state, key)
        if disasters:
            name = country.get("name_fa", key)
            for d in disasters:
                warnings.append(f"⚠️ {name}: {d.get('name_fa')}")
    
    if not warnings:
        return "✅ هیچ بلای فعالی در حال حاضر وجود ندارد."
    
    return "⚠️ *بلایای فعال در حال حاضر:*\n" + "\n".join(warnings)


def handle_evacuate(state: Dict[str, Any], user_id: str, unit_type: str, count: int) -> Tuple[bool, str]:
    """جابه‌جایی تجهیزات به منطقه امن (کاهش خسارت بلا)"""
    player = get_country_data(state, user_id)
    if not player:
        return False, "❌ شما کشوری انتخاب نکرده‌اید."
    
    country_key = get_country_key_by_user(state, user_id)
    if not country_key:
        return False, "❌ خطا در شناسایی کشور."
    
    # بررسی هزینه
    cost = 50
    influence = player.get("resources", {}).get("influence", 0)
    if influence < cost:
        return False, f"❌ نفوذ کافی ندارید. نیاز: {cost}"
    
    # پیدا کردن یگان
    units = player.get("units", {})
    category = None
    for cat in ["air", "ground", "naval", "destroyer", "submarine", "carrier"]:
        for unit in units.get(cat, []):
            if unit.get("name_fa") == unit_type or unit.get("name_en") == unit_type:
                if unit.get("count", 0) >= count:
                    category = cat
                    break
        if category:
            break
    
    if not category:
        return False, f"❌ {count} عدد {unit_type} در تجهیزات شما وجود ندارد."
    
    # جابه‌جایی (ذخیره در حالت تخلیه)
    player["resources"]["influence"] -= cost
    if "evacuated_units" not in player:
        player["evacuated_units"] = []
    
    player["evacuated_units"].append({
        "type": unit_type,
        "count": count,
        "category": category,
        "evacuated_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=2)).isoformat()
    })
    
    # کاهش از یگان‌های اصلی
    for unit in units.get(category, []):
        if unit.get("name_fa") == unit_type or unit.get("name_en") == unit_type:
            unit["count"] = unit.get("count", 0) - count
            break
    
    save_game_state(state)
    
    return True, f"✅ {count} عدد {unit_type} به منطقه امن منتقل شدند. هزینه: {cost} نفوذ"


def handle_return_evacuated(state: Dict[str, Any], user_id: str) -> Tuple[bool, str]:
    """بازگرداندن تجهیزات تخلیه شده"""
    player = get_country_data(state, user_id)
    if not player:
        return False, "❌ شما کشوری انتخاب نکرده‌اید."
    
    evacuated = player.get("evacuated_units", [])
    if not evacuated:
        return False, "❌ هیچ تجهیزات تخلیه شده‌ای ندارید."
    
    now = datetime.now()
    returned = 0
    
    for ev in evacuated[:]:
        expires_at = ev.get("expires_at")
        if expires_at:
            expires = datetime.fromisoformat(expires_at)
            if expires <= now:
                # بازگرداندن به یگان‌ها
                units = player.get("units", {})
                category = ev.get("category", "ground")
                unit_type = ev.get("type")
                count = ev.get("count", 0)
                
                found = False
                for unit in units.get(category, []):
                    if unit.get("name_fa") == unit_type or unit.get("name_en") == unit_type:
                        unit["count"] = unit.get("count", 0) + count
                        found = True
                        break
                
                if not found:
                    units[category].append({
                        "name_fa": unit_type,
                        "name_en": unit_type,
                        "count": count,
                        "health": 100,
                        "experience": 0
                    })
                
                evacuated.remove(ev)
                returned += 1
    
    if returned > 0:
        player["evacuated_units"] = evacuated
        save_game_state(state)
        return True, f"✅ {returned} نوع تجهیزات تخلیه شده بازگشت داده شدند."
    
    return False, "❌ هیچ تجهیزات تخلیه شده‌ای منقضی نشده است."


def get_disaster_help() -> str:
    """راهنمای بلایای طبیعی"""
    return """
🌍 *سیستم بلایای طبیعی*

هر 72 ساعت یک بلا به طور تصادفی در یک کشور رخ می‌دهد.

*انواع بلا:*

• 🌋 زلزله - آسیب به صنعت و تجهیزات زمینی
• 🌊 سیل - کاهش تولید مهمات
• 🌀 طوفان - قفل شدن ناوگان، زمین‌گیری هواپیماها
• 🔥 آتش‌سوزی - کاهش تولید سوخت
• 🏜️ خشکسالی - کاهش درآمد و رضایت
• 🌪️ گردباد - نابودی تجهیزات هوایی
• 🌋 آتشفشان - کاهش تجارت، لغو پروازها
• 🦠 همه‌گیری - کاهش نیروی انسانی و تولید
• ☄️ شهاب سنگ - نادر، تخریب گسترده

*راه‌های مقابله:*
/buy_insurance - خرید بیمه (100 نفوذ، 7 روز)
/evacuate [نوع] [تعداد] - جابه‌جایی تجهیزات (50 نفوذ)
/return_evacuated - بازگرداندن تجهیزات تخلیه شده
/warning - مشاهده بلایای فعال
"""


# برای رفع خطای undefined
def get_country_data(state: Dict[str, Any], user_id: str) -> Optional[Dict[str, Any]]:
    for country_key, player in state.get("countries", {}).items():
        if player.get("user_id") == user_id:
            return player
    return None


if __name__ == "__main__":
    print("Disaster system module loaded")
