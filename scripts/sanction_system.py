#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
سیستم کامل تحریم‌های اقتصادی
انواع تحریم: تحریم تجاری، تحریم تسلیحاتی، تحریم بانکی، تحریم فناوری، تحریم کامل
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

# ==================== تعریف انواع تحریم ====================

SANCTION_TYPES = {
    "trade": {  # تحریم تجاری
        "name_fa": "تحریم تجاری",
        "name_en": "Trade Sanction",
        "duration": 14,  # روز
        "cost": 300,
        "min_diplomacy": 4,
        "min_allies": 0,
        "effects": {
            "income_penalty": 0.30,      # -30% درآمد
            "trade_price_penalty": 0.20,  # +20% قیمت خرید
            "block_transfers": False,
            "block_tech": False,
            "block_weapons": False,
            "block_all_trade": False,
            "war_veto": False
        }
    },
    "weapon": {  # تحریم تسلیحاتی
        "name_fa": "تحریم تسلیحاتی",
        "name_en": "Weapon Embargo",
        "duration": 30,
        "cost": 400,
        "min_diplomacy": 5,
        "min_allies": 0,
        "effects": {
            "income_penalty": 0.0,
            "trade_price_penalty": 0.0,
            "block_transfers": False,
            "block_tech": False,
            "block_weapons": True,      # نمی‌تواند نسل 5+ بخرد
            "block_all_trade": False,
            "war_veto": False
        }
    },
    "banking": {  # تحریم بانکی
        "name_fa": "تحریم بانکی",
        "name_en": "Banking Sanction",
        "duration": 14,
        "cost": 300,
        "min_diplomacy": 4,
        "min_allies": 0,
        "effects": {
            "income_penalty": 0.0,
            "trade_price_penalty": 0.0,
            "block_transfers": True,     # نمی‌تواند نفوذ جابه‌جا کند
            "block_tech": False,
            "block_weapons": False,
            "block_all_trade": False,
            "war_veto": False
        }
    },
    "tech": {  # تحریم فناوری
        "name_fa": "تحریم فناوری",
        "name_en": "Technology Sanction",
        "duration": 14,
        "cost": 350,
        "min_diplomacy": 5,
        "min_allies": 0,
        "effects": {
            "income_penalty": 0.0,
            "trade_price_penalty": 0.0,
            "block_transfers": False,
            "block_tech": True,         # -50% فناوری از مأموریت‌ها
            "block_weapons": False,
            "block_all_trade": False,
            "war_veto": False
        }
    },
    "full": {  # تحریم کامل
        "name_fa": "تحریم کامل",
        "name_en": "Full Sanction",
        "duration": 14,
        "cost": 1000,
        "min_diplomacy": 6,
        "min_allies": 5,
        "effects": {
            "income_penalty": 0.50,      # -50% درآمد
            "trade_price_penalty": 0.50,  # +50% قیمت خرید
            "block_transfers": True,
            "block_tech": True,
            "block_weapons": True,
            "block_all_trade": True,     # قطع کامل تجارت
            "war_veto": True             # وتوی اعلان جنگ
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
        
        payload = {"message": f"[sanction] {datetime.now().isoformat()}", "content": encoded, "sha": current_sha}
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


def get_country_data(state: Dict[str, Any], user_id: str) -> Optional[Dict[str, Any]]:
    for country_key, player in state.get("countries", {}).items():
        if player.get("user_id") == user_id:
            return player
    return None


def get_active_sanctions(state: Dict[str, Any], user_id: str) -> List[Dict[str, Any]]:
    """دریافت لیست تحریم‌های فعال علیه یک کشور"""
    player = get_country_data(state, user_id)
    if not player:
        return []
    return player.get("sanctions", [])


def is_sanctioned(state: Dict[str, Any], user_id: str, sanction_type: str = None) -> bool:
    """بررسی اینکه آیا کشور تحت تحریم است"""
    sanctions = get_active_sanctions(state, user_id)
    if not sanctions:
        return False
    if sanction_type:
        for s in sanctions:
            if s.get("type") == sanction_type and s.get("active", True):
                return True
        return False
    return len(sanctions) > 0


def get_sanction_effects(state: Dict[str, Any], user_id: str) -> Dict[str, float]:
    """دریافت جمع اثرات همه تحریم‌های فعال علیه یک کشور"""
    sanctions = get_active_sanctions(state, user_id)
    effects = {
        "income_penalty": 0.0,
        "trade_price_penalty": 0.0,
        "block_transfers": False,
        "block_tech": False,
        "block_weapons": False,
        "block_all_trade": False,
        "war_veto": False
    }
    
    for sanction in sanctions:
        if not sanction.get("active", True):
            continue
        s_type = sanction.get("type")
        s_info = SANCTION_TYPES.get(s_type, {})
        s_effects = s_info.get("effects", {})
        
        effects["income_penalty"] = max(effects["income_penalty"], s_effects.get("income_penalty", 0))
        effects["trade_price_penalty"] = max(effects["trade_price_penalty"], s_effects.get("trade_price_penalty", 0))
        effects["block_transfers"] = effects["block_transfers"] or s_effects.get("block_transfers", False)
        effects["block_tech"] = effects["block_tech"] or s_effects.get("block_tech", False)
        effects["block_weapons"] = effects["block_weapons"] or s_effects.get("block_weapons", False)
        effects["block_all_trade"] = effects["block_all_trade"] or s_effects.get("block_all_trade", False)
        effects["war_veto"] = effects["war_veto"] or s_effects.get("war_veto", False)
    
    return effects


def get_allies_count(state: Dict[str, Any], user_id: str) -> int:
    """تعداد اتحادهای کامل یک کشور"""
    player = get_country_data(state, user_id)
    if not player:
        return 0
    
    treaties = player.get("treaties", [])
    allies = 0
    for treaty in treaties:
        if treaty.get("type") == "fa":
            # بررسی اینکه قرارداد هنوز فعال است
            expires = treaty.get("expires")
            if expires:
                try:
                    if datetime.fromisoformat(expires) > datetime.now():
                        allies += 1
                except:
                    allies += 1
            else:
                allies += 1
    return allies


def can_impose_sanction(state: Dict[str, Any], proposer_id: str, target_id: str, sanction_type: str) -> Tuple[bool, str]:
    """بررسی امکان اعمال تحریم"""
    if proposer_id == target_id:
        return False, "❌ نمی‌توانید به خودتان تحریم بزنید."
    
    proposer = get_country_data(state, proposer_id)
    target = get_country_data(state, target_id)
    
    if not proposer or not target:
        return False, "❌ یکی از کشورها وجود ندارد."
    
    sanction_info = SANCTION_TYPES.get(sanction_type)
    if not sanction_info:
        return False, "❌ نوع تحریم نامعتبر."
    
    # بررسی دیپلماسی
    if proposer.get("diplomacy", 0) < sanction_info["min_diplomacy"]:
        return False, f"❌ دیپلماسی شما باید حداقل {sanction_info['min_diplomacy']} باشد."
    
    # بررسی تعداد متحدان برای تحریم کامل
    if sanction_type == "full":
        allies = get_allies_count(state, proposer_id)
        if allies < sanction_info["min_allies"]:
            return False, f"❌ برای تحریم کامل نیاز به {sanction_info['min_allies']} متحد دارید."
    
    # بررسی تحریم فعال قبلی
    for s in target.get("sanctions", []):
        if s.get("type") == sanction_type and s.get("active", True):
            return False, f"❌ کشور هدف در حال حاضر تحت {sanction_info['name_fa']} است."
    
    # بررسی هزینه
    cost = sanction_info["cost"]
    influence = proposer.get("resources", {}).get("influence", 0)
    if influence < cost:
        return False, f"❌ نفوذ کافی ندارید. نیاز: {cost}"
    
    return True, ""


# ==================== مدیریت تحریم ====================

def impose_sanction(state: Dict[str, Any], proposer_id: str, target_name: str, sanction_type: str) -> Tuple[bool, str]:
    """اعمال تحریم علیه یک کشور"""
    target_id = get_user_by_country(state, target_name)
    if not target_id:
        return False, f"❌ کشور '{target_name}' یافت نشد."
    
    success, msg = can_impose_sanction(state, proposer_id, target_id, sanction_type)
    if not success:
        return False, msg
    
    proposer = get_country_data(state, proposer_id)
    target = get_country_data(state, target_id)
    sanction_info = SANCTION_TYPES[sanction_type]
    
    # کسر هزینه
    proposer["resources"]["influence"] -= sanction_info["cost"]
    
    # ایجاد تحریم
    now = datetime.now()
    expires = now + timedelta(days=sanction_info["duration"])
    
    sanction_data = {
        "type": sanction_type,
        "imposed_by": proposer_id,
        "imposed_by_name": proposer.get("name_fa"),
        "started_at": now.isoformat(),
        "expires_at": expires.isoformat(),
        "active": True,
        "effects": sanction_info["effects"]
    }
    
    if "sanctions" not in target:
        target["sanctions"] = []
    target["sanctions"].append(sanction_data)
    
    # کاهش دیپلماسی هدف (اختیاری)
    target["diplomacy"] = max(0, target.get("diplomacy", 0) - 1)
    
    save_game_state(state)
    
    # اعلان به GCC
    send_to_gcc(f"📜 *تحریم جدید*\n{proposer.get('name_fa')} علیه {target.get('name_fa')} {sanction_info['name_fa']} اعمال کرد.\nمدت: {sanction_info['duration']} روز")
    
    return True, f"✅ {sanction_info['name_fa']} علیه {target.get('name_fa')} اعمال شد.\nمدت: {sanction_info['duration']} روز\nهزینه: {sanction_info['cost']} نفوذ"


def remove_sanction(state: Dict[str, Any], remover_id: str, target_name: str, sanction_type: str) -> Tuple[bool, str]:
    """لغو تحریم (فقط توسط کشور اعمال‌کننده)"""
    target_id = get_user_by_country(state, target_name)
    if not target_id:
        return False, f"❌ کشور '{target_name}' یافت نشد."
    
    remover = get_country_data(state, remover_id)
    target = get_country_data(state, target_id)
    
    # پیدا کردن تحریم
    found = None
    for s in target.get("sanctions", []):
        if s.get("type") == sanction_type and s.get("imposed_by") == remover_id and s.get("active", True):
            found = s
            break
    
    if not found:
        return False, f"❌ شما هیچ {SANCTION_TYPES.get(sanction_type, {}).get('name_fa', 'تحریم')} فعالی علیه {target.get('name_fa')} ندارید."
    
    # لغو تحریم
    found["active"] = False
    found["removed_at"] = datetime.now().isoformat()
    
    save_game_state(state)
    
    send_to_gcc(f"✅ *لغو تحریم*\n{remover.get('name_fa')} {SANCTION_TYPES[sanction_type]['name_fa']} علیه {target.get('name_fa')} را لغو کرد.")
    
    return True, f"✅ {SANCTION_TYPES[sanction_type]['name_fa']} علیه {target.get('name_fa')} لغو شد."


def check_sanctions_expiry(state: Dict[str, Any]) -> int:
    """بررسی و حذف تحریم‌های منقضی شده"""
    players = state.get("countries", {})
    now = datetime.now()
    expired_count = 0
    
    for country_key, player in players.items():
        sanctions = player.get("sanctions", [])
        for s in sanctions:
            if not s.get("active", True):
                continue
            expires_at = s.get("expires_at")
            if expires_at:
                try:
                    expires = datetime.fromisoformat(expires_at)
                    if expires <= now:
                        s["active"] = False
                        expired_count += 1
                except:
                    pass
    
    if expired_count > 0:
        save_game_state(state)
    
    return expired_count


def get_sanctions_list(state: Dict[str, Any], user_id: str) -> str:
    """دریافت لیست تحریم‌های فعال علیه کشور کاربر"""
    player = get_country_data(state, user_id)
    if not player:
        return "❌ شما کشوری انتخاب نکرده‌اید."
    
    sanctions = player.get("sanctions", [])
    active = [s for s in sanctions if s.get("active", True)]
    
    if not active:
        return "📋 هیچ تحریم فعالی علیه شما وجود ندارد."
    
    msg = "📋 *تحریم‌های فعال علیه شما*\n\n"
    for s in active:
        sanction_info = SANCTION_TYPES.get(s["type"], {})
        expires_at = s.get("expires_at")
        if expires_at:
            try:
                expires = datetime.fromisoformat(expires_at)
                days_left = (expires - datetime.now()).days
                expires_text = f" ({days_left} روز باقی‌مانده)"
            except:
                expires_text = ""
        else:
            expires_text = ""
        
        msg += f"• {sanction_info.get('name_fa', s['type'])}{expires_text}\n"
        msg += f"  اعمال‌کننده: {s.get('imposed_by_name', 'نامشخص')}\n"
        
        # نمایش اثرات
        effects = s.get("effects", {})
        if effects.get("income_penalty"):
            msg += f"  📉 کاهش درآمد: {int(effects['income_penalty']*100)}%\n"
        if effects.get("trade_price_penalty"):
            msg += f"  💰 افزایش قیمت خرید: {int(effects['trade_price_penalty']*100)}%\n"
        if effects.get("block_weapons"):
            msg += f"  🔫 ممنوعیت خرید تسلیحات پیشرفته\n"
        if effects.get("block_transfers"):
            msg += f"  💸 ممنوعیت انتقال نفوذ\n"
        if effects.get("war_veto"):
            msg += f"  🛡️ وتوی اعلان جنگ\n"
        msg += "\n"
    
    return msg


def get_imposed_sanctions(state: Dict[str, Any], user_id: str) -> str:
    """دریافت لیست تحریم‌هایی که کشور کاربر اعمال کرده"""
    player = get_country_data(state, user_id)
    if not player:
        return "❌ شما کشوری انتخاب نکرده‌اید."
    
    # پیدا کردن تحریم‌های اعمال شده توسط این کشور
    imposed = []
    for country_key, other in state.get("countries", {}).items():
        for s in other.get("sanctions", []):
            if s.get("imposed_by") == user_id and s.get("active", True):
                imposed.append({
                    "target": other.get("name_fa"),
                    "type": s["type"],
                    "expires_at": s.get("expires_at")
                })
    
    if not imposed:
        return "📋 شما هیچ تحریم فعالی اعمال نکرده‌اید."
    
    msg = "📋 *تحریم‌های اعمال شده توسط شما*\n\n"
    for s in imposed:
        sanction_info = SANCTION_TYPES.get(s["type"], {})
        expires_at = s.get("expires_at")
        if expires_at:
            try:
                expires = datetime.fromisoformat(expires_at)
                days_left = (expires - datetime.now()).days
                expires_text = f" ({days_left} روز باقی‌مانده)"
            except:
                expires_text = ""
        else:
            expires_text = ""
        
        msg += f"• {sanction_info.get('name_fa', s['type'])} علیه {s['target']}{expires_text}\n"
        msg += f"  برای لغو: `/remove_sanction {s['target']} {s['type']}`\n\n"
    
    return msg


def apply_sanction_effects_on_income(income: int, state: Dict[str, Any], user_id: str) -> int:
    """اعمال اثر تحریم‌ها روی درآمد"""
    effects = get_sanction_effects(state, user_id)
    penalty = effects.get("income_penalty", 0)
    if penalty > 0:
        income = int(income * (1 - penalty))
    return income


def apply_sanction_effects_on_price(price: int, state: Dict[str, Any], user_id: str) -> int:
    """اعمال اثر تحریم‌ها روی قیمت خرید"""
    effects = get_sanction_effects(state, user_id)
    penalty = effects.get("trade_price_penalty", 0)
    if penalty > 0:
        price = int(price * (1 + penalty))
    return price


def can_transfer_influence(state: Dict[str, Any], user_id: str) -> bool:
    """بررسی امکان انتقال نفوذ (تحت تحریم بانکی)"""
    effects = get_sanction_effects(state, user_id)
    return not effects.get("block_transfers", False)


def can_buy_advanced_weapons(state: Dict[str, Any], user_id: str) -> bool:
    """بررسی امکان خرید تسلیحات پیشرفته (نسل 5+)"""
    effects = get_sanction_effects(state, user_id)
    return not effects.get("block_weapons", False)


def get_tech_mission_penalty(state: Dict[str, Any], user_id: str) -> float:
    """دریافت جریمه فناوری از مأموریت‌ها"""
    effects = get_sanction_effects(state, user_id)
    if effects.get("block_tech", False):
        return 0.5  # 50% کاهش
    return 1.0


# ==================== دستورات تحریم ====================

def handle_impose_sanction(state: Dict[str, Any], user_id: str, args: str) -> str:
    """دستور /sanction [کشور] [نوع]"""
    parts = args.strip().split()
    if len(parts) < 2:
        return """❌ فرمت صحیح: `/sanction [کشور] [نوع]`

انواع تحریم:
• trade - تحریم تجاری (-30% درآمد، +20% قیمت)
• weapon - تحریم تسلیحاتی (ممنوعیت خرید نسل 5+)
• banking - تحریم بانکی (ممنوعیت انتقال نفوذ)
• tech - تحریم فناوری (-50% فناوری از مأموریت‌ها)
• full - تحریم کامل (همه موارد + وتوی جنگ)

مثال: `/sanction آلمان trade`
"""
    
    target_name = parts[0]
    sanction_type = parts[1].lower()
    
    if sanction_type not in SANCTION_TYPES:
        return f"❌ نوع تحریم نامعتبر. انتخاب‌ها: trade, weapon, banking, tech, full"
    
    success, msg = impose_sanction(state, user_id, target_name, sanction_type)
    if success:
        save_game_state(state)
    return msg


def handle_remove_sanction(state: Dict[str, Any], user_id: str, args: str) -> str:
    """دستور /remove_sanction [کشور] [نوع]"""
    parts = args.strip().split()
    if len(parts) < 2:
        return "❌ فرمت صحیح: `/remove_sanction [کشور] [نوع]`\nمثال: `/remove_sanction آلمان trade`"
    
    target_name = parts[0]
    sanction_type = parts[1].lower()
    
    success, msg = remove_sanction(state, user_id, target_name, sanction_type)
    if success:
        save_game_state(state)
    return msg


def handle_my_sanctions(state: Dict[str, Any], user_id: str) -> str:
    """دستور /my_sanctions - نمایش تحریم‌های علیه خود"""
    return get_sanctions_list(state, user_id)


def handle_my_imposed_sanctions(state: Dict[str, Any], user_id: str) -> str:
    """دستور /imposed_sanctions - نمایش تحریم‌های اعمال شده"""
    return get_imposed_sanctions(state, user_id)


def handle_counter_sanction(state: Dict[str, Any], user_id: str, args: str) -> str:
    """دستور /counter_sanction [کشور] - تحریم متقابل"""
    if not args.strip():
        return "❌ لطفاً نام کشور را وارد کنید. مثال: `/counter_sanction آلمان`"
    
    target_name = args.strip()
    target_id = get_user_by_country(state, target_name)
    if not target_id:
        return f"❌ کشور '{target_name}' یافت نشد."
    
    # بررسی اینکه آیا کشور هدف به شما تحریم زده
    target = get_country_data(state, target_id)
    sanctions_against_me = []
    for s in target.get("sanctions", []):
        if s.get("imposed_by") == target_id and s.get("active", True):
            sanctions_against_me.append(s)
    
    if not sanctions_against_me:
        return f"❌ {target_name} هیچ تحریم فعالی علیه شما ندارد."
    
    # اعمال همان تحریم به صورت متقابل
    player = get_country_data(state, user_id)
    if player.get("diplomacy", 0) < 4:
        return "❌ دیپلماسی شما برای تحریم متقابل باید حداقل 4 باشد."
    
    imposed = []
    for s in sanctions_against_me:
        success, msg = impose_sanction(state, user_id, target_name, s["type"])
        if success:
            imposed.append(SANCTION_TYPES[s["type"]]["name_fa"])
    
    if imposed:
        save_game_state(state)
        return f"✅ تحریم متقابل اعمال شد: {', '.join(imposed)}"
    
    return "❌ خطا در اعمال تحریم متقابل."


def get_sanctions_help() -> str:
    """راهنمای سیستم تحریم"""
    return """
📜 *سیستم تحریم‌ها*

انواع تحریم:

1. *تحریم تجاری (trade)*
   - هزینه: 300 نفوذ
   - نیاز دیپلماسی: 4
   - مدت: 14 روز
   - اثرات: -30% درآمد هدف، +20% قیمت خرید

2. *تحریم تسلیحاتی (weapon)*
   - هزینه: 400 نفوذ
   - نیاز دیپلماسی: 5
   - مدت: 30 روز
   - اثرات: ممنوعیت خرید تجهیزات نسل 5+

3. *تحریم بانکی (banking)*
   - هزینه: 300 نفوذ
   - نیاز دیپلماسی: 4
   - مدت: 14 روز
   - اثرات: ممنوعیت انتقال نفوذ

4. *تحریم فناوری (tech)*
   - هزینه: 350 نفوذ
   - نیاز دیپلماسی: 5
   - مدت: 14 روز
   - اثرات: -50% فناوری از مأموریت‌ها

5. *تحریم کامل (full)*
   - هزینه: 1000 نفوذ
   - نیاز دیپلماسی: 6 + 5 متحد
   - مدت: 14 روز
   - اثرات: همه موارد بالا + وتوی اعلان جنگ

دستورات:
/sanction [کشور] [نوع] - اعمال تحریم
/remove_sanction [کشور] [نوع] - لغو تحریم
/my_sanctions - نمایش تحریم‌های علیه خود
/imposed_sanctions - نمایش تحریم‌های اعمال شده
/counter_sanction [کشور] - تحریم متقابل
"""


if __name__ == "__main__":
    print("Sanction system module loaded")
