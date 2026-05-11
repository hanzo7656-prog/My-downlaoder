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

سیستم تجربه:
- برنده نبرد: +1 ستاره (حداکثر 5)
- بازنده نبرد: +0.5 ستاره (حداکثر 3)
- مساوی: هر دو +0.5 ستاره
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

# ==================== قدرت پایه تجهیزات (برای محاسبه تلفات) ====================

UNIT_POWERS = {
    "F22": 90, "رپتور": 90,
    "F35": 75, "لایتنینگ": 75,
    "SU57": 85, "فلون": 85,
    "جی۲۰": 70, "J20": 70,
    "تمپست": 95, "Tempest": 95,
    "تایفون": 65, "Eurofighter Typhoon": 65,
    "رافال": 65, "Rafale": 65,
    "آر ماتا": 75, "T-14 Armata": 75,
    "آبرامز": 72, "Abrams X": 72,
    "لئوپارد": 70, "Leopard 2A7+": 70,
}


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


# ==================== سیستم تجربه ====================

def get_star_display(experience: int) -> str:
    """تبدیل تجربه به نمایش ستاره"""
    if experience >= 5:
        return "⭐⭐⭐⭐⭐"
    elif experience >= 4:
        return "⭐⭐⭐⭐"
    elif experience >= 3:
        return "⭐⭐⭐"
    elif experience >= 2:
        return "⭐⭐"
    elif experience >= 1:
        return "⭐"
    return "☆"


def update_all_units_experience(state: Dict[str, Any], country_key: str, is_winner: bool):
    """
    افزایش تجربه همه یگان‌های یک کشور پس از نبرد
    is_winner: True برای برنده (+1 ستاره، حداکثر 5)
               False برای بازنده (+0.5 ستاره، حداکثر 3)
    """
    player = state["countries"].get(country_key)
    if not player:
        return
    
    units = player.get("units", {})
    categories = ["air", "ground", "artillery", "destroyer", "submarine", "carrier", "air_defense"]
    
    total_updated = 0
    
    for category in categories:
        for unit in units.get(category, []):
            if unit.get("count", 0) > 0:
                current = unit.get("experience", 0)
                if is_winner:
                    # برنده: +1 تجربه (حداکثر 5)
                    new_exp = min(current + 1, 5)
                else:
                    # بازنده: +0.5 تجربه (حداکثر 3)
                    new_exp = min(current + 0.5, 3)
                
                if new_exp != current:
                    unit["experience"] = new_exp
                    total_updated += 1
    
    if total_updated > 0:
        print(f"Updated experience for {player.get('name_fa')}: {'winner' if is_winner else 'loser'} ({total_updated} units)")


# ==================== محاسبه قدرت و تلفات ====================

def calculate_unit_power(unit: Dict[str, Any]) -> int:
    """محاسبه قدرت یک یگان با احتساب تجربه و سلامت"""
    name_fa = unit.get("name_fa", "")
    name_en = unit.get("name_en", "")
    health = unit.get("health", 100)
    experience = unit.get("experience", 0)
    
    base_power = UNIT_POWERS.get(name_fa, UNIT_POWERS.get(name_en, 50))
    
    health_mult = health / 100
    exp_mult = 1 + (experience * 0.1)  # هر ستاره 10% قدرت بیشتر
    
    return int(base_power * health_mult * exp_mult)


def calculate_total_power(player: Dict[str, Any]) -> int:
    """محاسبه قدرت کل ارتش یک کشور"""
    units = player.get("units", {})
    total = 0
    
    for category in ["air", "ground", "artillery", "destroyer", "submarine", "carrier", "air_defense"]:
        for unit in units.get(category, []):
            count = unit.get("count", 0)
            if count > 0:
                power = calculate_unit_power(unit)
                total += power * count
    
    return total


def apply_damage_to_units(player: Dict[str, Any], damage_percent: float):
    """
    اعمال آسیب به یگان‌های یک کشور (بر اساس درصدی از قدرت کل)
    یگان‌های ضعیف‌تر اول آسیب می‌بینند
    """
    units = player.get("units", {})
    categories = ["air", "ground", "artillery", "destroyer", "submarine", "carrier", "air_defense"]
    
    # جمع‌آوری همه یگان‌ها با قدرت
    all_units = []
    for category in categories:
        for unit in units.get(category, []):
            count = unit.get("count", 0)
            if count > 0:
                power = calculate_unit_power(unit)
                all_units.append({
                    "category": category,
                    "unit": unit,
                    "count": count,
                    "power": power
                })
    
    # مرتب‌سازی بر اساس قدرت (ضعیف‌ترین اول)
    all_units.sort(key=lambda x: x["power"])
    
    # محاسبه تعداد یگان‌هایی که باید آسیب ببینند
    total_units = sum(u["count"] for u in all_units)
    units_to_damage = max(1, int(total_units * damage_percent))
    
    damaged = 0
    for unit_info in all_units:
        if damaged >= units_to_damage:
            break
        
        unit = unit_info["unit"]
        count = unit_info["count"]
        remaining = units_to_damage - damaged
        
        if count <= remaining:
            # کل یگان نابود می‌شود
            unit["count"] = 0
            unit["health"] = 0
            damaged += count
        else:
            # تعدادی از یگان‌ها آسیب می‌بینند
            unit["count"] = count - remaining
            # یگان‌های باقی‌مانده سلامت کمتری دارند
            if "health" in unit:
                unit["health"] = max(50, unit["health"] - 25)
            damaged += remaining


# ==================== منطق حل جنگ ====================

def resolve_war(war: Dict[str, Any], attacker_key: str, defender_key: str, 
                attacker_name: str, defender_name: str, state: Dict[str, Any]) -> Tuple[bool, str]:
    """
    حل یک جنگ منفرد با اعمال خسارت و به‌روزرسانی تجربه
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
    
    attacker_player = state["countries"].get(attacker_key, {})
    defender_player = state["countries"].get(defender_key, {})
    
    # مهلت تمام شده - حل خودکار
    if phase == "declaration":
        # مدافع پاسخ نداد -> جنگ لغو می‌شود
        war["status"] = "cancelled"
        war["ended_at"] = now.isoformat()
        result = f"⚔️ *جنگ لغو شد*\n{attacker_name} → {defender_name}\nعلت: عدم پاسخ مدافع در مهلت {adjusted_deadline:.0f} ساعت"
        return True, result
    
    elif phase == "deploy":
        # استقرار نیرو تمام شد -> محاسبه خودکار قدرت
        attacker_power = calculate_total_power(attacker_player)
        defender_power = calculate_total_power(defender_player)
        
        war["attacker_power"] = attacker_power
        war["defender_power"] = defender_power
        war["current_phase"] = "attack"
        war["last_move"] = now.isoformat()
        
        result = f"⚔️ *مرحله استقرار پایان یافت*\n{attacker_name} vs {defender_name}\nقدرت مهاجم: {attacker_power} | قدرت مدافع: {defender_power}"
        return False, result
    
    elif phase == "attack":
        # نوبت حمله تمام شد -> نبرد حل می‌شود
        attacker_power = war.get("attacker_power", 0)
        defender_power = war.get("defender_power", 0)
        
        if attacker_power == 0 or defender_power == 0:
            # یک طرف نیرویی ندارد
            if attacker_power == 0 and defender_power == 0:
                war["status"] = "ended"
                result = f"🤝 *جنگ به بن‌بست خورد*\n{attacker_name} vs {defender_name}\nهر دو طرف نیرویی ندارند."
                return True, result
            elif attacker_power == 0:
                # مدافع خودکار برنده می‌شود
                update_all_units_experience(state, defender_key, True)
                update_all_units_experience(state, attacker_key, False)
                war["status"] = "ended"
                war["winner"] = defender_key
                result = f"🏆 *پیروزی خودکار*\n{defender_name} بدون جنگ پیروز شد (مهاجم نیرویی نداشت)."
                return True, result
            else:
                # مهاجم خودکار برنده می‌شود
                update_all_units_experience(state, attacker_key, True)
                update_all_units_experience(state, defender_key, False)
                war["status"] = "ended"
                war["winner"] = attacker_key
                result = f"🏆 *پیروزی خودکار*\n{attacker_name} بدون جنگ پیروز شد (مدافع نیرویی نداشت)."
                return True, result
        
        # نبرد واقعی
        if attacker_power > defender_power:
            # مهاجم برنده شد
            damage_percent = 0.15 if attacker_power > defender_power * 1.5 else 0.10
            apply_damage_to_units(defender_player, damage_percent)
            apply_damage_to_units(attacker_player, 0.05)
            
            update_all_units_experience(state, attacker_key, True)
            update_all_units_experience(state, defender_key, False)
            
            sector = war.get("current_sector", 1)
            war["captured_sectors"] = war.get("captured_sectors", []) + [sector]
            war["current_sector"] = sector + 1
            
            if war["current_sector"] > 3:
                war["status"] = "ended"
                war["winner"] = attacker_key
                result = f"🏆 *پیروزی کامل*\n{attacker_name} {defender_name} را به طور کامل شکست داد و تصرف کرد!\nتلفات سنگین به مدافع وارد شد."
                return True, result
            else:
                war["last_move"] = now.isoformat()
                result = f"⚔️ *بخش {sector} تصرف شد*\n{attacker_name} پیروز شد! {defender_name} بخش {sector} را از دست داد.\nمرحله بعد: بخش {war['current_sector']}"
                return False, result
        
        elif defender_power > attacker_power:
            # مدافع برنده شد
            damage_percent = 0.15 if defender_power > attacker_power * 1.5 else 0.10
            apply_damage_to_units(attacker_player, damage_percent)
            apply_damage_to_units(defender_player, 0.05)
            
            update_all_units_experience(state, defender_key, True)
            update_all_units_experience(state, attacker_key, False)
            
            war["status"] = "ended"
            war["winner"] = defender_key
            result = f"🛡️ *دفاع موفق*\n{defender_name} در برابر {attacker_name} مقاومت کرد و پیروز شد.\n{attacker_name} متحمل خسارت سنگین شد."
            return True, result
        
        else:
            # مساوی
            apply_damage_to_units(attacker_player, 0.10)
            apply_damage_to_units(defender_player, 0.10)
            
            update_all_units_experience(state, attacker_key, False)
            update_all_units_experience(state, defender_key, False)
            
            war["status"] = "ended"
            result = f"🤝 *نبرد مساوی*\n{attacker_name} vs {defender_name}\nهر دو طرف متحمل خسارت شدند و جنگ به پایان رسید."
            return True, result
    
    elif phase == "retreat":
        # عقب‌نشینی تمام شد -> مهاجم عقب‌نشینی کرده
        apply_damage_to_units(attacker_player, 0.20)  # جریمه عقب‌نشینی
        update_all_units_experience(state, defender_key, True)
        update_all_units_experience(state, attacker_key, False)
        
        war["status"] = "ended"
        result = f"🏃 *عقب‌نشینی*\n{attacker_name} از {defender_name} عقب‌نشینی کرد و جنگ تمام شد.\n{attacker_name} در حین عقب‌نشینی متحمل خسارت شد."
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
            
            # اگر یکی از طرفین وجود نداشت، جنگ را حذف کن
            if not attacker_key or not defender_key:
                remove_war_from_player(state, country_key, war)
                continue
            
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
            if war.get("status") == "active":
                opponent = get_player_name(state, war.get("with"))
                active_wars.append(f"{player.get('name_fa', country_key)} vs {opponent}")
    
    if not active_wars:
        return "هیچ جنگ فعالی وجود ندارد."
    
    return "⚔️ *جنگ‌های فعال:*\n" + "\n".join([f"• {w}" for w in set(active_wars)])


if __name__ == "__main__":
    resolve_timeout_wars()
