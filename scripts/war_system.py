#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
سیستم کامل نبرد
امکانات: اعلان جنگ، استقرار نیرو، محاسبه قدرت، تصرف بخش، پیشنهاد صلح
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


# ==================== محاسبه قدرت رزمی ====================

def calculate_unit_power(unit: Dict[str, Any]) -> int:
    """محاسبه قدرت یک یگان با احتساب سلامت و تجربه"""
    name_fa = unit.get("name_fa", "")
    name_en = unit.get("name_en", "")
    health = unit.get("health", 100)
    experience = unit.get("experience", 0)
    
    base_power = UNIT_POWERS.get(name_fa, UNIT_POWERS.get(name_en, 30))
    
    # ضریب سلامت (یگان آسیب دیده ضعیف‌تر است)
    health_mult = health / 100
    
    # ضریب تجربه (هر ستاره ۱۰٪ قدرت بیشتر)
    exp_mult = 1 + (experience * 0.1)
    
    return int(base_power * health_mult * exp_mult)


def calculate_army_power(units: Dict[str, Any], category: str) -> int:
    """محاسبه قدرت کل یک دسته از یگان‌ها"""
    total = 0
    for unit in units.get(category, []):
        count = unit.get("count", 0)
        if count > 0:
            power = calculate_unit_power(unit)
            total += power * count
    return total


def calculate_total_power(player: Dict[str, Any]) -> int:
    """محاسبه قدرت کل ارتش یک کشور"""
    units = player.get("units", {})
    categories = ["air", "ground", "naval", "destroyer", "submarine", "carrier", "artillery", "air_defense"]
    
    total = 0
    for cat in categories:
        total += calculate_army_power(units, cat)
    
    return total


# ==================== مدیریت جنگ ====================

def declare_war(state: Dict[str, Any], attacker_id: str, target_name: str) -> Tuple[bool, str]:
    """اعلان جنگ"""
    # پیدا کردن هدف
    target_id = get_user_by_country(state, target_name)
    if not target_id:
        return False, f"❌ کشور '{target_name}' یافت نشد."
    
    if attacker_id == target_id:
        return False, "❌ نمی‌توانید به خودتان حمله کنید!"
    
    attacker = get_country_key(state, attacker_id)
    target = get_country_key(state, target_id)
    
    if not attacker or not target:
        return False, "❌ خطا در شناسایی کشورها."
    
    attacker_name = get_country_name(state, attacker_id)
    target_name = get_country_name(state, target_id)
    
    # بررسی جنگ فعال
    attacker_player = state["countries"][attacker]
    for war in attacker_player.get("active_wars", []):
        if war.get("with") == target_id and war.get("status") == "active":
            return False, "❌ شما در حال حاضر با این کشور در جنگ هستید!"
    
    # ایجاد جنگ جدید
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
        "captured_sectors": []
    }
    
    # اضافه کردن به مهاجم
    if "active_wars" not in attacker_player:
        attacker_player["active_wars"] = []
    attacker_player["active_wars"].append(new_war)
    
    # اضافه کردن به مدافع
    defender_player = state["countries"][target]
    defender_war = new_war.copy()
    defender_war["is_attacker"] = False
    if "active_wars" not in defender_player:
        defender_player["active_wars"] = []
    defender_player["active_wars"].append(defender_war)
    
    save_game_state(state)
    
    # اعلان به GCC
    gcc_msg = f"⚔️ *اعلان جنگ*\n{attacker_name} به {target_name} اعلام جنگ داد!"
    send_to_gcc(gcc_msg)
    
    # پیام به طرفین
    deadline = get_adjusted_deadline(8, state)
    attacker_msg = f"⚔️ شما به {target_name} اعلام جنگ کردید.\nمدافع {deadline:.0f} ساعت فرصت پاسخ دارد."
    target_msg = f"⚔️ {attacker_name} به شما اعلام جنگ کرد!\nشما {deadline:.0f} ساعت فرصت پاسخ دارید.\nبرای استقرار نیرو: `/deploy`"
    
    send_message(attacker_id, attacker_msg)
    send_message(target_id, target_msg)
    
    return True, f"✅ اعلان جنگ به {target_name} ارسال شد."


def deploy_forces(state: Dict[str, Any], user_id: str, units_str: str) -> Tuple[bool, str]:
    """استقرار نیرو در جنگ فعال"""
    player = None
    for country_key, p in state["countries"].items():
        if p.get("user_id") == user_id:
            player = p
            break
    
    if not player:
        return False, "❌ شما کشوری انتخاب نکرده‌اید."
    
    # پیدا کردن جنگ فعال
    active_war = None
    for war in player.get("active_wars", []):
        if war.get("status") == "active":
            active_war = war
            break
    
    if not active_war:
        return False, "❌ شما در هیچ جنگ فعالی نیستید."
    
    # محاسبه قدرت کل ارتش
    total_power = calculate_total_power(player)
    
    # به‌روزرسانی قدرت در جنگ
    is_attacker = active_war.get("is_attacker", True)
    if is_attacker:
        active_war["attacker_power"] = total_power
    else:
        active_war["defender_power"] = total_power
    
    active_war["current_phase"] = "attack"
    active_war["last_move"] = datetime.now().isoformat()
    
    save_game_state(state)
    
    return True, f"✅ نیروهای شما مستقر شدند! قدرت رزمی: {total_power}"


def get_war_status(state: Dict[str, Any], user_id: str) -> str:
    """دریافت وضعیت جنگ فعال"""
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
    last_move = active_war.get("last_move")
    
    phase_names = {
        "declaration": "⏳ منتظر پاسخ دشمن",
        "deploy": "📦 در حال استقرار نیروها",
        "attack": "⚔️ در حال نبرد",
        "retreat": "🏃 عقب‌نشینی",
        "peace": "🕊️ پیشنهاد صلح"
    }
    
    msg = f"⚔️ *وضعیت جنگ با {opponent_name}*\n\n"
    msg += f"📍 بخش {sector} از 3\n"
    msg += f"📊 قدرت شما: {my_power}\n"
    msg += f"📊 قدرت دشمن: {enemy_power}\n"
    msg += f"📌 وضعیت: {phase_names.get(phase, phase)}\n"
    
    if last_move:
        try:
            last = datetime.fromisoformat(last_move)
            now = datetime.now()
            elapsed = (now - last).total_seconds() / 3600
            msg += f"⏱️ آخرین فعالیت: {elapsed:.1f} ساعت قبل\n"
        except:
            pass
    
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


# ==================== توابع عمومی ====================

def get_active_wars_list(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """دریافت لیست تمام جنگ‌های فعال"""
    wars = []
    for country_key, player in state.get("countries", {}).items():
        for war in player.get("active_wars", []):
            if war.get("status") == "active":
                wars.append({
                    "attacker": country_key,
                    "attacker_name": player.get("name_fa"),
                    "defender_id": war.get("with"),
                    "sector": war.get("current_sector", 1)
                })
    return wars


if __name__ == "__main__":
    # تست
    print("War system module loaded")
