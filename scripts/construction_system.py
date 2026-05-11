#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
سیستم ساخت و ساز و توسعه زیرساخت‌ها
انواع سازه: پایگاه هوایی، پایگاه دریایی، پادگان، کارخانه مهمات، پالایشگاه سوخت، آزمایشگاه، مرکز تجاری، سپر پدافندی
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

# ==================== تعریف سازه‌ها ====================

STRUCTURES = {
    "airbase": {
        "name_fa": "پایگاه هوایی",
        "name_en": "Airbase",
        "cost": 300,
        "build_time": 72,  # ساعت
        "slots": 2,
        "maintenance": 15,
        "max_level": 4,
        "effects": {
            "air_capacity_bonus": 0.50,      # +50% ظرفیت هوایی
            "air_repair_speed": 0.20,        # +20% سرعت تعمیر هواپیما
            "air_damage_bonus": 0.10,        # +10% آسیب هوایی
        },
        "level_effects": {
            2: {"air_capacity_bonus": 0.75, "air_repair_speed": 0.30},
            3: {"air_capacity_bonus": 1.00, "air_repair_speed": 0.40, "air_damage_bonus": 0.15},
            4: {"air_capacity_bonus": 1.50, "air_repair_speed": 0.60, "air_damage_bonus": 0.20, "extra_aircraft": 2}
        }
    },
    "navalbase": {
        "name_fa": "پایگاه دریایی",
        "name_en": "Naval Base",
        "cost": 400,
        "build_time": 96,
        "slots": 3,
        "maintenance": 20,
        "max_level": 4,
        "effects": {
            "naval_capacity_bonus": 0.50,    # +50% ظرفیت دریایی
            "naval_repair_speed": 0.20,      # +20% سرعت تعمیر ناوها
        },
        "level_effects": {
            2: {"naval_capacity_bonus": 0.75, "naval_repair_speed": 0.30},
            3: {"naval_capacity_bonus": 1.00, "naval_repair_speed": 0.40},
            4: {"naval_capacity_bonus": 1.50, "naval_repair_speed": 0.60, "extra_ships": 1}
        }
    },
    "barracks": {
        "name_fa": "پادگان نظامی",
        "name_en": "Military Barracks",
        "cost": 200,
        "build_time": 48,
        "slots": 2,
        "maintenance": 10,
        "max_level": 4,
        "effects": {
            "ground_capacity_bonus": 0.30,   # +30% ظرفیت زمینی
            "ground_defense_bonus": 0.10,    # +10% دفاع زمینی
        },
        "level_effects": {
            2: {"ground_capacity_bonus": 0.50, "ground_defense_bonus": 0.15},
            3: {"ground_capacity_bonus": 0.70, "ground_defense_bonus": 0.20},
            4: {"ground_capacity_bonus": 1.00, "ground_defense_bonus": 0.30, "ground_attack_bonus": 0.10}
        }
    },
    "ammo_factory": {
        "name_fa": "کارخانه مهمات‌سازی",
        "name_en": "Ammunition Factory",
        "cost": 250,
        "build_time": 72,
        "slots": 2,
        "maintenance": 12,
        "max_level": 4,
        "effects": {
            "ammo_production_bonus": 0.50,   # +50% تولید مهمات
        },
        "level_effects": {
            2: {"ammo_production_bonus": 0.75},
            3: {"ammo_production_bonus": 1.00},
            4: {"ammo_production_bonus": 1.50, "ammo_storage_bonus": 0.50}
        }
    },
    "refinery": {
        "name_fa": "پالایشگاه سوخت",
        "name_en": "Fuel Refinery",
        "cost": 250,
        "build_time": 72,
        "slots": 2,
        "maintenance": 12,
        "max_level": 4,
        "effects": {
            "fuel_production_bonus": 0.50,   # +50% تولید سوخت
        },
        "level_effects": {
            2: {"fuel_production_bonus": 0.75},
            3: {"fuel_production_bonus": 1.00},
            4: {"fuel_production_bonus": 1.50, "fuel_storage_bonus": 0.50}
        }
    },
    "laboratory": {
        "name_fa": "آزمایشگاه تحقیقاتی",
        "name_en": "Research Laboratory",
        "cost": 400,
        "build_time": 120,
        "slots": 3,
        "maintenance": 25,
        "max_level": 4,
        "effects": {
            "research_discount": 0.20,       # 20% تخفیف تحقیق
        },
        "level_effects": {
            2: {"research_discount": 0.30, "tech_share_bonus": 1},
            3: {"research_discount": 0.40, "tech_share_bonus": 2},
            4: {"research_discount": 0.50, "tech_share_bonus": 3, "unlimited_tech_share": True}
        }
    },
    "trade_center": {
        "name_fa": "مرکز تجاری",
        "name_en": "Trade Center",
        "cost": 350,
        "build_time": 96,
        "slots": 2,
        "maintenance": 20,
        "max_level": 4,
        "effects": {
            "income_bonus": 0.30,            # +30% درآمد
            "purchase_discount": 0.10,       # 10% تخفیف خرید
        },
        "level_effects": {
            2: {"income_bonus": 0.50, "purchase_discount": 0.15},
            3: {"income_bonus": 0.70, "purchase_discount": 0.20, "extra_trade_deal": 1},
            4: {"income_bonus": 1.00, "purchase_discount": 0.30, "extra_trade_deal": 2}
        }
    },
    "shield": {
        "name_fa": "سپر پدافندی",
        "name_en": "Defense Shield",
        "cost": 500,
        "build_time": 144,
        "slots": 4,
        "maintenance": 30,
        "max_level": 4,
        "effects": {
            "missile_defense_chance": 0.50,  # 50% شانس نابودی موشک
        },
        "level_effects": {
            2: {"missile_defense_chance": 0.60},
            3: {"missile_defense_chance": 0.70, "air_defense_bonus": 0.20},
            4: {"missile_defense_chance": 0.80, "air_defense_bonus": 0.30, "nuclear_defense": True}
        }
    }
}

# ==================== تعریف زیرساخت‌ها ====================

INFRASTRUCTURE = {
    "road": {
        "name_fa": "جاده/راه‌آهن",
        "name_en": "Road/Railway",
        "cost_per_level": 150,
        "max_level": 5,
        "effects": {
            "ground_speed_bonus": 0.10,      # +10% سرعت جابه‌جایی زمینی
        }
    },
    "port": {
        "name_fa": "بندر",
        "name_en": "Port",
        "cost_per_level": 200,
        "max_level": 5,
        "effects": {
            "naval_speed_bonus": 0.10,       # +10% سرعت جابه‌جایی دریایی
        }
    },
    "airport": {
        "name_fa": "فرودگاه",
        "name_en": "Airport",
        "cost_per_level": 180,
        "max_level": 5,
        "effects": {
            "air_speed_bonus": 0.10,         # +10% سرعت جابه‌جایی هوایی
        }
    },
    "power": {
        "name_fa": "شبکه برق",
        "name_en": "Power Grid",
        "cost_per_level": 120,
        "max_level": 5,
        "effects": {
            "maintenance_discount": 0.05,    # -5% هزینه نگهداری
        }
    },
    "internet": {
        "name_fa": "مخابرات/اینترنت",
        "name_en": "Telecom/Internet",
        "cost_per_level": 100,
        "max_level": 5,
        "effects": {
            "mission_time_bonus": 0.10,      # 10% سریع‌تر حل مأموریت
        }
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
        
        payload = {"message": f"[construct] {datetime.now().isoformat()}", "content": encoded, "sha": current_sha}
        response = requests.put(GITHUB_API_URL, headers=headers, json=payload)
        return response.status_code == 200
    except:
        return False


def send_to_gcc(text: str):
    if not BALE_TOKEN or not GCC_CHAT_ID:
        return
    url = f"{BALE_API_URL}/sendMessage"
    payload = {"chat_id": GCC_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except:
        pass


def get_country_data(state: Dict[str, Any], user_id: str) -> Optional[Dict[str, Any]]:
    for country_key, player in state.get("countries", {}).items():
        if player.get("user_id") == user_id:
            return player
    return None


def get_country_key(state: Dict[str, Any], user_id: str) -> Optional[str]:
    for country_key, player in state.get("countries", {}).items():
        if player.get("user_id") == user_id:
            return country_key
    return None


def get_construction_slots(state: Dict[str, Any], country_key: str) -> int:
    """محاسبه ظرفیت ساخت بر اساس صنعت"""
    player = state["countries"].get(country_key, {})
    industry = player.get("industry", 0)
    
    if industry >= 9:
        return 22
    elif industry >= 7:
        return 15
    elif industry >= 5:
        return 10
    elif industry >= 3:
        return 6
    else:
        return 3


# ==================== مدیریت سازه‌ها ====================

def build_structure(state: Dict[str, Any], user_id: str, structure_type: str, level: int = 1) -> Tuple[bool, str]:
    """ساخت یک سازه جدید"""
    player = get_country_data(state, user_id)
    if not player:
        return False, "❌ شما کشوری انتخاب نکرده‌اید."
    
    country_key = get_country_key(state, user_id)
    
    structure_info = STRUCTURES.get(structure_type)
    if not structure_info:
        return False, f"❌ نوع سازه نامعتبر. انتخاب‌ها: {', '.join(STRUCTURES.keys())}"
    
    if level < 1 or level > structure_info["max_level"]:
        return False, f"❌ سطح باید بین 1 تا {structure_info['max_level']} باشد."
    
    # بررسی ظرفیت ساخت
    structures = player.get("structures", [])
    current_slots = sum(s.get("slots", 0) for s in structures)
    max_slots = get_construction_slots(state, country_key)
    
    new_slots = structure_info["slots"] * level
    if current_slots + new_slots > max_slots:
        return False, f"❌ ظرفیت ساخت کافی ندارید. نیاز: {new_slots} اسلات (حداکثر: {max_slots})"
    
    # بررسی هزینه
    total_cost = structure_info["cost"] * level
    influence = player.get("resources", {}).get("influence", 0)
    
    if influence < total_cost:
        return False, f"❌ نفوذ کافی ندارید. نیاز: {total_cost}"
    
    # کسر هزینه
    player["resources"]["influence"] -= total_cost
    
    # ایجاد سازه
    new_structure = {
        "id": f"{structure_type}_{datetime.now().timestamp()}",
        "type": structure_type,
        "name_fa": structure_info["name_fa"],
        "level": level,
        "slots": structure_info["slots"],
        "maintenance": structure_info["maintenance"] * level,
        "built_at": datetime.now().isoformat(),
        "ready_at": (datetime.now() + timedelta(hours=structure_info["build_time"])).isoformat(),
        "status": "building"
    }
    
    if "structures" not in player:
        player["structures"] = []
    player["structures"].append(new_structure)
    
    save_game_state(state)
    
    # اعلان به GCC
    send_to_gcc(f"🏗️ *ساخت سازه جدید*\n{player.get('name_fa')} در حال ساخت {structure_info['name_fa']} سطح {level} است.\nزمان تکمیل: {structure_info['build_time']} ساعت")
    
    return True, f"✅ ساخت {structure_info['name_fa']} سطح {level} آغاز شد.\nزمان تکمیل: {structure_info['build_time']} ساعت"


def upgrade_structure(state: Dict[str, Any], user_id: str, structure_id: str) -> Tuple[bool, str]:
    """ارتقاء یک سازه موجود"""
    player = get_country_data(state, user_id)
    if not player:
        return False, "❌ شما کشوری انتخاب نکرده‌اید."
    
    # پیدا کردن سازه
    structure = None
    for s in player.get("structures", []):
        if s.get("id") == structure_id:
            structure = s
            break
    
    if not structure:
        return False, "❌ سازه یافت نشد."
    
    if structure.get("status") == "building":
        return False, "❌ این سازه هنوز در حال ساخت است."
    
    structure_type = structure["type"]
    structure_info = STRUCTURES.get(structure_type, {})
    current_level = structure.get("level", 1)
    
    if current_level >= structure_info.get("max_level", 4):
        return False, "❌ این سازه به حداکثر سطح خود رسیده است."
    
    new_level = current_level + 1
    upgrade_cost = structure_info["cost"] * new_level
    build_time = structure_info["build_time"]
    
    influence = player.get("resources", {}).get("influence", 0)
    if influence < upgrade_cost:
        return False, f"❌ نفوذ کافی ندارید. نیاز: {upgrade_cost}"
    
    # کسر هزینه
    player["resources"]["influence"] -= upgrade_cost
    
    # به‌روزرسانی سازه
    structure["level"] = new_level
    structure["maintenance"] = structure_info["maintenance"] * new_level
    structure["status"] = "building"
    structure["ready_at"] = (datetime.now() + timedelta(hours=build_time)).isoformat()
    
    save_game_state(state)
    
    return True, f"✅ ارتقاء {structure_info['name_fa']} به سطح {new_level} آغاز شد.\nزمان تکمیل: {build_time} ساعت"


def demolish_structure(state: Dict[str, Any], user_id: str, structure_id: str) -> Tuple[bool, str]:
    """تخریب یک سازه (بازگشت 50% هزینه)"""
    player = get_country_data(state, user_id)
    if not player:
        return False, "❌ شما کشوری انتخاب نکرده‌اید."
    
    # پیدا کردن سازه
    structure = None
    for s in player.get("structures", []):
        if s.get("id") == structure_id:
            structure = s
            break
    
    if not structure:
        return False, "❌ سازه یافت نشد."
    
    structure_info = STRUCTURES.get(structure["type"], {})
    total_cost = structure_info["cost"] * structure.get("level", 1)
    refund = total_cost // 2
    
    # حذف سازه
    player["structures"] = [s for s in player.get("structures", []) if s.get("id") != structure_id]
    player["resources"]["influence"] = player["resources"].get("influence", 0) + refund
    
    save_game_state(state)
    
    return True, f"✅ {structure_info['name_fa']} تخریب شد. {refund} نفوذ بازگشت داده شد."


def check_construction_completion(state: Dict[str, Any]) -> int:
    """بررسی و تکمیل ساخت‌وسازهای در حال انجام"""
    players = state.get("countries", {})
    now = datetime.now()
    completed_count = 0
    
    for country_key, player in players.items():
        for structure in player.get("structures", []):
            if structure.get("status") != "building":
                continue
            
            ready_at = structure.get("ready_at")
            if ready_at:
                ready = datetime.fromisoformat(ready_at)
                if ready <= now:
                    structure["status"] = "active"
                    completed_count += 1
                    
                    # اعلان به GCC
                    send_to_gcc(f"✅ *سازه تکمیل شد*\n{player.get('name_fa')}: {structure.get('name_fa')} سطح {structure.get('level')} تکمیل شد.")
    
    if completed_count > 0:
        save_game_state(state)
    
    return completed_count


def get_structure_effects(state: Dict[str, Any], country_key: str) -> Dict[str, Any]:
    """دریافت اثرات جمعی همه سازه‌های یک کشور"""
    player = state["countries"].get(country_key, {})
    structures = player.get("structures", [])
    
    total_effects = {}
    
    for structure in structures:
        if structure.get("status") != "active":
            continue
        
        structure_type = structure["type"]
        structure_info = STRUCTURES.get(structure_type, {})
        level = structure.get("level", 1)
        
        # اثرات پایه
        effects = structure_info.get("effects", {}).copy()
        
        # اثرات سطح
        level_effects = structure_info.get("level_effects", {}).get(level, {})
        for key, value in level_effects.items():
            effects[key] = value
        
        # جمع اثرات
        for key, value in effects.items():
            if key in total_effects:
                # برای مقادیر درصدی، جمع نمی‌شوند بلکه ترکیب می‌شوند
                if isinstance(value, float):
                    total_effects[key] = max(total_effects[key], value)
                else:
                    total_effects[key] = total_effects[key] + value
            else:
                total_effects[key] = value
    
    return total_effects


def get_available_structures(state: Dict[str, Any], user_id: str) -> str:
    """دریافت لیست سازه‌های فعال کشور"""
    player = get_country_data(state, user_id)
    if not player:
        return "❌ شما کشوری انتخاب نکرده‌اید."
    
    structures = player.get("structures", [])
    if not structures:
        return "🏗️ شما هیچ سازه‌ای ندارید.\nبا `/build [نوع]` سازه بسازید."
    
    msg = "🏗️ *سازه‌های شما*\n\n"
    for s in structures:
        status = "✅ فعال" if s.get("status") == "active" else "🚧 در حال ساخت"
        msg += f"• {s.get('name_fa')} سطح {s.get('level')} - {status}\n"
        msg += f"  ID: `{s.get('id')}`\n"
        msg += f"  هزینه نگهداری: {s.get('maintenance')} نفوذ/روز\n\n"
    
    return msg


# ==================== مدیریت زیرساخت‌ها ====================

def upgrade_infrastructure(state: Dict[str, Any], user_id: str, infra_type: str) -> Tuple[bool, str]:
    """ارتقاء زیرساخت"""
    player = get_country_data(state, user_id)
    if not player:
        return False, "❌ شما کشوری انتخاب نکرده‌اید."
    
    infra_info = INFRASTRUCTURE.get(infra_type)
    if not infra_info:
        return False, f"❌ نوع زیرساخت نامعتبر. انتخاب‌ها: {', '.join(INFRASTRUCTURE.keys())}"
    
    if "infrastructure" not in player:
        player["infrastructure"] = {}
    
    current_level = player["infrastructure"].get(infra_type, 0)
    if current_level >= infra_info["max_level"]:
        return False, f"❌ زیرساخت {infra_info['name_fa']} به حداکثر سطح خود رسیده است."
    
    cost = infra_info["cost_per_level"]
    influence = player.get("resources", {}).get("influence", 0)
    
    if influence < cost:
        return False, f"❌ نفوذ کافی ندارید. نیاز: {cost}"
    
    player["resources"]["influence"] -= cost
    player["infrastructure"][infra_type] = current_level + 1
    
    save_game_state(state)
    
    return True, f"✅ {infra_info['name_fa']} به سطح {current_level + 1} ارتقاء یافت!"


def get_infrastructure_effects(state: Dict[str, Any], country_key: str) -> Dict[str, Any]:
    """دریافت اثرات جمعی زیرساخت‌های یک کشور"""
    player = state["countries"].get(country_key, {})
    infrastructure = player.get("infrastructure", {})
    
    total_effects = {}
    
    for infra_type, level in infrastructure.items():
        infra_info = INFRASTRUCTURE.get(infra_type, {})
        effects = infra_info.get("effects", {})
        
        for key, value in effects.items():
            total_effects[key] = total_effects.get(key, 0) + (value * level)
    
    return total_effects


def get_infrastructure_status(state: Dict[str, Any], user_id: str) -> str:
    """دریافت وضعیت زیرساخت‌های کشور"""
    player = get_country_data(state, user_id)
    if not player:
        return "❌ شما کشوری انتخاب نکرده‌اید."
    
    infrastructure = player.get("infrastructure", {})
    
    msg = "🏗️ *وضعیت زیرساخت‌ها*\n\n"
    
    for infra_type, info in INFRASTRUCTURE.items():
        current = infrastructure.get(infra_type, 0)
        max_level = info["max_level"]
        bar = "█" * current + "░" * (max_level - current)
        msg += f"• {info['name_fa']}: {bar} ({current}/{max_level})\n"
        msg += f"  هزینه ارتقاء بعدی: {info['cost_per_level']} نفوذ\n\n"
    
    return msg


# ==================== محاسبه نگهداری ====================

def get_total_maintenance(state: Dict[str, Any], country_key: str) -> int:
    """محاسبه کل هزینه نگهداری سازه‌ها"""
    player = state["countries"].get(country_key, {})
    structures = player.get("structures", [])
    
    total = 0
    for structure in structures:
        if structure.get("status") == "active":
            total += structure.get("maintenance", 0)
    
    return total


# ==================== دستورات ====================

def handle_build(state: Dict[str, Any], user_id: str, args: str) -> str:
    """دستور /build [نوع] [level]"""
    parts = args.strip().split()
    if len(parts) < 1:
        return """❌ فرمت صحیح: `/build [نوع] [سطح]`

انواع سازه:
• airbase - پایگاه هوایی
• navalbase - پایگاه دریایی
• barracks - پادگان نظامی
• ammo_factory - کارخانه مهمات‌سازی
• refinery - پالایشگاه سوخت
• laboratory - آزمایشگاه تحقیقاتی
• trade_center - مرکز تجاری
• shield - سپر پدافندی

مثال: `/build airbase 2`
"""
    
    structure_type = parts[0]
    level = 1
    if len(parts) > 1:
        try:
            level = int(parts[1])
        except:
            return "❌ سطح باید عدد باشد."
    
    success, msg = build_structure(state, user_id, structure_type, level)
    if success:
        save_game_state(state)
    return msg


def handle_upgrade_structure(state: Dict[str, Any], user_id: str, args: str) -> str:
    """دستور /upgrade_structure [structure_id]"""
    if not args.strip():
        return "❌ لطفاً ID سازه را وارد کنید. از `/structures` برای دیدن IDها استفاده کنید."
    
    success, msg = upgrade_structure(state, user_id, args.strip())
    if success:
        save_game_state(state)
    return msg


def handle_demolish(state: Dict[str, Any], user_id: str, args: str) -> str:
    """دستور /demolish [structure_id]"""
    if not args.strip():
        return "❌ لطفاً ID سازه را وارد کنید."
    
    success, msg = demolish_structure(state, user_id, args.strip())
    if success:
        save_game_state(state)
    return msg


def handle_structures(state: Dict[str, Any], user_id: str) -> str:
    """دستور /structures - نمایش سازه‌های فعال"""
    return get_available_structures(state, user_id)


def handle_infrastructure(state: Dict[str, Any], user_id: str) -> str:
    """دستور /infrastructure - نمایش وضعیت زیرساخت‌ها"""
    return get_infrastructure_status(state, user_id)


def handle_upgrade_infra(state: Dict[str, Any], user_id: str, args: str) -> str:
    """دستور /upgrade_infra [type] - ارتقاء زیرساخت"""
    if not args.strip():
        return "❌ نوع زیرساخت را وارد کنید. انتخاب‌ها: road, port, airport, power, internet"
    
    success, msg = upgrade_infrastructure(state, user_id, args.strip())
    if success:
        save_game_state(state)
    return msg


def get_construction_help() -> str:
    """راهنمای ساخت و ساز"""
    return """
🏗️ *سیستم ساخت و ساز*

*انواع سازه‌ها:*

1. *پایگاه هوایی (airbase)*
   - هزینه: 300 | نگهداری: 15/روز
   - +50% ظرفیت هوایی، +20% سرعت تعمیر

2. *پایگاه دریایی (navalbase)*
   - هزینه: 400 | نگهداری: 20/روز
   - +50% ظرفیت دریایی، +20% سرعت تعمیر

3. *پادگان نظامی (barracks)*
   - هزینه: 200 | نگهداری: 10/روز
   - +30% ظرفیت زمینی، +10% دفاع

4. *کارخانه مهمات‌سازی (ammo_factory)*
   - هزینه: 250 | نگهداری: 12/روز
   - +50% تولید مهمات

5. *پالایشگاه سوخت (refinery)*
   - هزینه: 250 | نگهداری: 12/روز
   - +50% تولید سوخت

6. *آزمایشگاه تحقیقاتی (laboratory)*
   - هزینه: 400 | نگهداری: 25/روز
   - 20% تخفیف تحقیق

7. *مرکز تجاری (trade_center)*
   - هزینه: 350 | نگهداری: 20/روز
   - +30% درآمد، 10% تخفیف خرید

8. *سپر پدافندی (shield)*
   - هزینه: 500 | نگهداری: 30/روز
   - 50% شانس نابودی موشک‌ها

*دستورات:*
/build [نوع] [سطح] - ساخت سازه جدید
/upgrade_structure [id] - ارتقاء سازه
/demolish [id] - تخریب سازه
/structures - مشاهده سازه‌ها
/infrastructure - مشاهده زیرساخت‌ها
/upgrade_infra [نوع] - ارتقاء زیرساخت
"""


if __name__ == "__main__":
    print("Construction system module loaded")
