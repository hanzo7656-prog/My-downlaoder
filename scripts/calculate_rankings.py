#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
محاسبه جدول پتانسیل روزانه و توزیع پاداش پرستیژ
هر روز ساعت 12 ظهر اجرا می‌شود (توسط GitHub Actions)

پتانسیل = (صنعت × 3) + (تجارت × 2.5) + (قدرت نظامی × 2) + (دیپلماسی × 1) + (ثبات × 1)
با اعمال اثرات سازه‌ها و زیرساخت‌ها
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

# ==================== قدرت پایه تجهیزات ====================

UNIT_POWERS = {
    "F22": 90, "رپتور": 90, "F35": 75, "لایتنینگ": 75,
    "SU57": 85, "فلون": 85, "جی۲۰": 70, "J20": 70,
    "تمپست": 95, "Tempest": 95, "تایفون": 65, "رافال": 65,
    "آر ماتا": 75, "T-14": 75, "آبرامز": 72, "Abrams X": 72,
    "لئوپارد": 70, "چلنجر": 64, "یاسن": 70, "اوهایو": 75,
    "فورد": 100, "نیمیتز": 85
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
        
        payload = {"message": f"[rankings] {datetime.now().isoformat()}", "content": encoded, "sha": current_sha}
        response = requests.put(GITHUB_API_URL, headers=headers, json=payload)
        return response.status_code == 200
    except:
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


def get_speed_multiplier(state: Dict[str, Any]) -> int:
    return state.get("admin", {}).get("game_speed", 1)


def get_structure_effects(state: Dict[str, Any], country_key: str) -> Dict[str, Any]:
    """دریافت اثرات سازه‌های یک کشور"""
    player = state["countries"].get(country_key, {})
    structures = player.get("structures", [])
    
    effects = {
        "air_capacity_bonus": 0,
        "naval_capacity_bonus": 0,
        "ground_capacity_bonus": 0,
        "income_bonus": 0,
        "research_discount": 0,
        "missile_defense_chance": 0,
        "industry_bonus": 0,
        "trade_bonus": 0
    }
    
    for structure in structures:
        if structure.get("status") != "active":
            continue
        
        struct_type = structure.get("type")
        level = structure.get("level", 1)
        
        if struct_type == "trade_center":
            effects["income_bonus"] = max(effects["income_bonus"], 0.30 * level)
            effects["trade_bonus"] = max(effects["trade_bonus"], 0.10 * level)
        elif struct_type == "laboratory":
            effects["research_discount"] = max(effects["research_discount"], 0.20 * level)
        elif struct_type == "airbase":
            effects["air_capacity_bonus"] = max(effects["air_capacity_bonus"], 0.50 * level)
        elif struct_type == "navalbase":
            effects["naval_capacity_bonus"] = max(effects["naval_capacity_bonus"], 0.50 * level)
        elif struct_type == "barracks":
            effects["ground_capacity_bonus"] = max(effects["ground_capacity_bonus"], 0.30 * level)
        elif struct_type == "shield":
            effects["missile_defense_chance"] = max(effects["missile_defense_chance"], 0.50 * (level / 2))
    
    return effects


def get_infrastructure_effects(state: Dict[str, Any], country_key: str) -> Dict[str, Any]:
    """دریافت اثرات زیرساخت‌های یک کشور"""
    player = state["countries"].get(country_key, {})
    infra = player.get("infrastructure", {})
    
    effects = {
        "ground_speed_bonus": infra.get("road", 0) * 0.10,
        "naval_speed_bonus": infra.get("port", 0) * 0.10,
        "air_speed_bonus": infra.get("airport", 0) * 0.10,
        "maintenance_discount": infra.get("power", 0) * 0.05,
        "mission_speed_bonus": infra.get("internet", 0) * 0.10
    }
    
    return effects


def calculate_military_power(player: Dict[str, Any]) -> int:
    """محاسبه قدرت نظامی بر اساس تجهیزات"""
    units = player.get("units", {})
    total_power = 0
    
    for category in ["air", "ground", "naval", "destroyer", "submarine", "carrier", "artillery", "air_defense"]:
        for unit in units.get(category, []):
            count = unit.get("count", 0)
            health = unit.get("health", 100)
            experience = unit.get("experience", 0)
            
            name = unit.get("name_fa", unit.get("name_en", ""))
            base_power = UNIT_POWERS.get(name, 50)
            
            power = base_power * (health / 100) * (1 + experience * 0.1)
            total_power += power * count
    
    return int(total_power)


def calculate_potential(player: Dict[str, Any], structure_effects: Dict, country_key: str = None) -> int:
    """محاسبه پتانسیل کامل یک کشور"""
    industry = player.get("industry", 0)
    trade = player.get("trade", 0)
    diplomacy = player.get("diplomacy", 0)
    stability = player.get("stability", 5)
    military_power = calculate_military_power(player) // 10
    
    # اعمال اثرات سازه‌ها
    industry_bonus = 1 + structure_effects.get("industry_bonus", 0)
    trade_bonus = 1 + structure_effects.get("trade_bonus", 0)
    
    # فرمول اصلی
    potential = (industry * 3 * industry_bonus) + \
                (int(trade * 2.5) * trade_bonus) + \
                (military_power * 2) + \
                (diplomacy * 1) + \
                (stability * 1)
    
    return potential


def get_country_flag(country_key: str) -> str:
    """دریافت ایموجی پرچم کشور"""
    flags = {
        "usa": "🇺🇸", "russia": "🇷🇺", "china": "🇨🇳",
        "germany": "🇩🇪", "france": "🇫🇷", "uk": "🇬🇧",
        "japan": "🇯🇵", "south_korea": "🇰🇷", "india": "🇮🇳",
        "iran": "🇮🇷", "turkey": "🇹🇷", "israel": "🇮🇱",
        "brazil": "🇧🇷", "canada": "🇨🇦", "australia": "🇦🇺"
    }
    return flags.get(country_key, "🏳️")


def get_status_icons(player: Dict[str, Any]) -> str:
    """دریافت آیکون‌های وضعیت کشور"""
    icons = []
    
    if player.get("active_wars") and len(player.get("active_wars", [])) > 0:
        icons.append("⚔️")
    else:
        icons.append("🕊️")
    
    treaties = player.get("treaties", [])
    for treaty in treaties:
        if treaty.get("type") == "fa":
            icons.append("🤝")
            break
    
    if player.get("sanctioned", False):
        icons.append("💰")
    
    if player.get("stability", 5) < 3:
        icons.append("⚠️")
    
    if player.get("used_nuclear", False):
        icons.append("🔥")
    
    return "".join(icons)


def generate_rankings_table(rankings: List[Tuple], game_day: int, speed: int) -> str:
    """ساخت جدول رتبه‌بندی"""
    table = f"🏆 *جدول پتانسیل روزانه - روز {game_day}*\n"
    table += "═══════════════════════════════════════\n\n"
    
    for i, (country_key, name_fa, potential, icons) in enumerate(rankings[:24], 1):
        blocks = max(0, int((potential - 100) / 50))
        blocks = min(blocks, 20)
        bar = "█" * blocks + "░" * (20 - blocks)
        
        flag = get_country_flag(country_key)
        line = f"*{i}. {flag} {name_fa}*" + " " * (18 - len(name_fa))
        line += f" {bar}  {potential}  {icons}\n"
        table += line
    
    table += "\n═══════════════════════════════════════\n"
    table += "📊 هر █ = ۵۰ امتیاز پتانسیل\n"
    table += "⚔️ جنگ | 🕊️ صلح | 🤝 متحد | 💰 تحریم | ⚠️ بحران | 🔥 هسته‌ای"
    
    if speed > 1:
        table += f"\n\n⚙️ سرعت بازی: {speed} برابر"
    
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
                
                if "logs" not in state:
                    state["logs"] = []
                state["logs"].append({
                    "timestamp": datetime.now().isoformat(),
                    "type": "prestige",
                    "message": f"{name_fa} به رتبه {i} جدول رسید و {reward} پرستیژ دریافت کرد."
                })


def main():
    print(f"Calculating daily rankings at {datetime.now().isoformat()}")
    
    state = load_game_state()
    if not state:
        print("Failed to load game state")
        return
    
    players = state.get("countries", {})
    rankings = []
    
    for country_key, player in players.items():
        if player.get("user_id") is None:
            continue
        
        name_fa = player.get("name_fa", country_key)
        
        # دریافت اثرات سازه‌ها
        structure_effects = get_structure_effects(state, country_key)
        
        # محاسبه پتانسیل کامل
        potential = calculate_potential(player, structure_effects, country_key)
        icons = get_status_icons(player)
        rankings.append((country_key, name_fa, potential, icons))
    
    # مرتب‌سازی بر اساس پتانسیل (نزولی)
    rankings.sort(key=lambda x: x[2], reverse=True)
    
    # توزیع پاداش پرستیژ
    distribute_prestige_rewards(rankings, state)
    
    # ساخت جدول
    game_day = state.get("game_day", 0)
    speed = get_speed_multiplier(state)
    rankings_table = generate_rankings_table(rankings, game_day, speed)
    
    # ارسال به GCC
    send_to_gcc(rankings_table)
    
    # ذخیره در state
    state["last_update"] = datetime.now().isoformat()
    save_game_state(state)
    
    print("Rankings calculated and sent successfully")


if __name__ == "__main__":
    main()
