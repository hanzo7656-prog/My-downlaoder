#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
کسر هزینه نگهداری روزانه از بازیکنان
هر شب ساعت 12 اجرا می‌شود (توسط GitHub Actions)

هزینه نگهداری بر اساس:
- تعداد و نوع تجهیزات
- سطح فساد کشور (هرچه فساد بالاتر، هزینه بیشتر)
- سطح صنعت (تخفیف برای صنعت بالا)
- سرعت بازی (ضریب اعمال می‌شود)
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

# ==================== هزینه پایه هر تجهیزات (به ازای هر واحد) ====================

MAINTENANCE_BASE_COST = {
    # نیروی هوایی
    "F22": 12, "رپتور": 12,
    "F35": 10, "لایتنینگ": 10,
    "SU57": 11, "فلون": 11,
    "جی۲۰": 9, "J20": 9,
    "تایفون": 8, "Eurofighter Typhoon": 8,
    "رافال": 8, "Rafale": 8,
    "تمپست": 14, "Tempest": 14,
    "سوخو-۳۵": 7, "Su-35": 7,
    "میگ-۲۹": 5, "MiG-29": 5,
    "فانتوم": 4, "F-4": 4,
    "سوپر هورنت": 6, "F/A-18": 6,
    "جی-۱۵": 6, "J-15": 6,
    
    # نیروی زمینی - تانک
    "آبرامز": 9, "Abrams X": 9,
    "آر ماتا": 10, "T-14 Armata": 10,
    "لئوپارد": 8, "Leopard 2A7+": 8,
    "چلنجر": 7, "Challenger 2": 7,
    "پلنگ سیاه": 8, "K2 Black Panther": 8,
    "مِرکاوا": 8, "Merkava": 8,
    "تایپ-۱۰": 7, "Type 10": 7,
    "لکلر": 7, "Leclerc": 7,
    "تایپ-۹۹": 6, "Type 99A": 6,
    "تی-۸۴": 6, "T-84": 6,
    "آبرامز ام۱": 5, "Abrams M1": 5,
    "تی-۹۰": 5, "T-90": 5,
    "لئوپارد ۲": 5, "Leopard 2": 5,
    "لئوپارد-۱": 3, "Leopard 1": 3,
    "تی-۵۵": 2, "T-55": 2,
    
    # توپخانه
    "پی‌زدهاچ-۲۰۰۰": 6, "PzH 2000": 6,
    "کوالیتسیا": 7, "Koalitsiya-SV": 7,
    "ام-۱۰۹": 5, "M109A7": 5,
    "کی-۹": 6, "K9 Thunder": 6,
    "پی‌ال‌زد-۵۲": 5, "PLZ-52": 5,
    "ام-۱۰۹ قدیمی": 3, "M109": 3,
    "ایاس-۹۰": 4, "AS90": 4,
    "مستا-اس": 4, "Msta-S": 4,
    
    # ناوشکن
    "آرلی بروک": 15, "Arleigh Burke": 15,
    "زوموالت": 20, "Zumwalt": 20,
    "تایپ-۵۵": 18, "Type 55": 18,
    "مایا": 14, "Maya class": 14,
    "هورایزن": 13, "Horizon class": 13,
    "تایپ-۴۵": 14, "Type 45": 14,
    "سجونگ کبیر": 16, "Sejong the Great": 16,
    "اسپرونس": 8, "Spruance": 8,
    "تایپ-۵۲دی": 12, "Type 52D": 12,
    "کونگو": 10, "Kongo": 10,
    "کلکته": 11, "Kolkata": 11,
    "هوبارت": 10, "Hobart": 10,
    
    # زیردریایی
    "یاسن": 18, "Yasen": 18,
    "اوهایو": 25, "Ohio": 25,
    "تایپ-۰۹۳": 14, "Type 093": 14,
    "ویرجینیا": 16, "Virginia": 16,
    "سی ولف": 15, "Seawolf": 15,
    "سیرا": 12, "Sierra": 12,
    "تایپ-۰۹۱": 8, "Type 091": 8,
    "ونگارد": 22, "Vanguard": 22,
    "سافرن": 15, "Suffren": 15,
    "آریهانت": 14, "Arihant": 14,
    
    # ناو هواپیمابر
    "نیمیتز": 50, "Nimitz": 50,
    "فورد": 60, "Ford": 60,
    "فوجیان": 40, "Fujian": 40,
    "شاندونگ": 35, "Shandong": 35,
    "لیائونینگ": 30, "Liaoning": 30,
    "شارل دوگل": 38, "Charles de Gaulle": 38,
    "ملکه الیزابت": 40, "Queen Elizabeth": 40,
    "کوزنتسف": 28, "Kuznetsov": 28,
    
    # پدافند
    "اس-۴۰۰": 25, "S-400": 25,
    "اس-۵۰۰": 35, "S-500": 35,
    "پاتریوت": 20, "Patriot": 20,
    "تاد": 28, "THAAD": 28,
    "فلاخن داوود": 25, "David's Sling": 25,
    "اس-۳۰۰": 15, "S-300": 15,
    "اچ‌کیو-۹بی": 18, "HQ-9B": 18,
    
    # پدافند ساحلی
    "باستیون-پی": 12, "Bastion-P": 12,
    "ان‌اس‌ام": 10, "NSM": 10,
    "سیلک‌ورم": 8, "Silkworm": 8,
}

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
            "message": f"[auto] maintenance {datetime.now().strftime('%Y-%m-%d')}",
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


def get_corruption_multiplier(corruption: int) -> float:
    """دریافت ضریب فساد (فساد بیشتر = هزینه نگهداری بیشتر)"""
    if corruption <= 2:
        return 0.9  # 10% تخفیف
    elif corruption <= 4:
        return 1.0  # عادی
    elif corruption <= 7:
        return 1.25  # 25% جریمه
    else:
        return 1.5  # 50% جریمه


def get_industry_discount(industry: int) -> float:
    """دریافت تخفیف صنعت (صنعت بالاتر = هزینه کمتر)"""
    if industry >= 9:
        return 0.7  # 30% تخفیف
    elif industry >= 7:
        return 0.8  # 20% تخفیف
    elif industry >= 5:
        return 0.9  # 10% تخفیف
    else:
        return 1.0


# ==================== محاسبه هزینه یک کشور ====================

def calculate_maintenance_cost(player: Dict[str, Any], state: Dict[str, Any]) -> Tuple[int, List[str]]:
    """
    محاسبه هزینه نگهداری یک کشور
    بازگشت: (هزینه کل، لیست یگان‌های غیرفعال شده)
    """
    units = player.get("units", {})
    total_cost = 0
    disabled_units = []
    
    corruption = player.get("corruption", 3)
    industry = player.get("industry", 0)
    
    corruption_mult = get_corruption_multiplier(corruption)
    industry_discount = get_industry_discount(industry)
    speed_mult = get_speed_multiplier(state)
    
    for category, unit_list in units.items():
        for unit in unit_list:
            name_fa = unit.get("name_fa", "")
            name_en = unit.get("name_en", "")
            count = unit.get("count", 0)
            health = unit.get("health", 100)
            
            if count <= 0:
                continue
            
            # هزینه پایه
            base_cost = MAINTENANCE_BASE_COST.get(name_fa, MAINTENANCE_BASE_COST.get(name_en, 5))
            
            # هزینه هر واحد با احتساب سلامت (یگان آسیب دیده هزینه کمتری دارد)
            unit_cost = base_cost * (health / 100)
            
            # اعمال ضرایب
            final_cost = unit_cost * corruption_mult * industry_discount * speed_mult
            total_cost += final_cost * count
    
    return int(total_cost), disabled_units


def deduct_from_resources(player: Dict[str, Any], amount: int) -> bool:
    """کسر هزینه از منابع کشور، برگرداندن موفقیت یا شکست"""
    if "resources" not in player:
        player["resources"] = {}
    
    current = player["resources"].get("influence", 0)
    if current >= amount:
        player["resources"]["influence"] = current - amount
        return True
    else:
        player["resources"]["influence"] = 0
        return False


def disable_units_by_priority(player: Dict[str, Any], deficit: int, speed_mult: int) -> List[str]:
    """
    غیرفعال کردن یگان‌ها به ترتیب اولویت (ارزان‌ترین اولویت)
    بازگشت: لیست یگان‌های غیرفعال شده
    """
    disabled = []
    units = player.get("units", {})
    
    # جمع‌آوری همه یگان‌ها با هزینه
    all_units = []
    for category, unit_list in units.items():
        for unit in unit_list:
            if unit.get("count", 0) <= 0:
                continue
            
            name = unit.get("name_fa", unit.get("name_en", "نامشخص"))
            count = unit.get("count", 0)
            base_cost = MAINTENANCE_BASE_COST.get(unit.get("name_fa", ""), 
                         MAINTENANCE_BASE_COST.get(unit.get("name_en", ""), 5))
            
            all_units.append({
                "category": category,
                "unit": unit,
                "name": name,
                "count": count,
                "cost": base_cost
            })
    
    # مرتب‌سازی بر اساس هزینه (ارزان‌ترین اولویت برای غیرفعال شدن)
    all_units.sort(key=lambda x: x["cost"])
    
    remaining_deficit = deficit
    for unit_info in all_units:
        if remaining_deficit <= 0:
            break
        
        unit = unit_info["unit"]
        count = unit_info["count"]
        cost = unit_info["cost"]
        name = unit_info["name"]
        
        # هزینه نگهداری این یگان برای یک روز
        daily_cost = cost * count
        
        if daily_cost <= remaining_deficit:
            # غیرفعال کردن کل یگان
            disabled.append(f"{name} x{count}")
            unit["count"] = 0
            remaining_deficit -= daily_cost
        else:
            # غیرفعال کردن تعدادی از یگان
            can_keep = remaining_deficit // cost
            to_disable = count - can_keep
            if to_disable > 0:
                disabled.append(f"{name} x{to_disable}")
                unit["count"] = can_keep
                remaining_deficit = 0
    
    return disabled


# ==================== تابع اصلی ====================

def main():
    print(f"Running maintenance deduction at {datetime.now().isoformat()}")
    
    state = load_game_state()
    if not state:
        print("Failed to load game state")
        return
    
    players = state.get("countries", {})
    speed = get_speed_multiplier(state)
    notifications = []
    total_deducted = 0
    total_players_with_deficit = 0
    
    for country_key, player in players.items():
        # رد شدن از کشورهای بدون بازیکن
        if player.get("user_id") is None:
            continue
        
        name = player.get("name_fa", country_key)
        cost, _ = calculate_maintenance_cost(player, state)
        
        if cost <= 0:
            continue
        
        total_deducted += cost
        
        # کسر از منابع
        success = deduct_from_resources(player, cost)
        
        if not success:
            # هزینه کامل پرداخت نشد، یگان‌ها را غیرفعال کن
            deficit = cost - player["resources"].get("influence", 0)
            player["resources"]["influence"] = 0
            
            disabled = disable_units_by_priority(player, deficit, speed)
            if disabled:
                notifications.append(f"⚠️ *{name}*: {', '.join(disabled[:5])} غیرفعال شدند (کمبود {deficit} نفوذ)")
                total_players_with_deficit += 1
        
        # اضافه کردن لاگ
        if "logs" not in state:
            state["logs"] = []
        state["logs"].append({
            "timestamp": datetime.now().isoformat(),
            "type": "maintenance",
            "message": f"{name}: {cost} نفوذ کسر شد"
        })
    
    # ارسال اعلان‌ها به GCC
    if notifications:
        for note in notifications[:10]:  # حداکثر 10 اعلان در یک پیام
            send_to_gcc(note)
        if len(notifications) > 10:
            send_to_gcc(f"... و {len(notifications)-10} کشور دیگر دچار کمبود نفوذ شدند.")
    
    # ارسال خلاصه به GCC
    summary = f"💰 *خلاصه هزینه نگهداری روز {state.get('game_day', 0)}*\n"
    summary += f"• کل نفوذ کسر شده: {total_deducted}\n"
    summary += f"• کشورهای دارای کسری: {total_players_with_deficit}\n"
    if speed > 1:
        summary += f"• سرعت بازی: {speed} برابر (هزینه‌ها ضرب شد)"
    send_to_gcc(summary)
    
    # ذخیره وضعیت
    state["last_update"] = datetime.now().isoformat()
    save_game_state(state)
    
    print(f"Maintenance completed. Total deducted: {total_deducted}")


if __name__ == "__main__":
    main()
