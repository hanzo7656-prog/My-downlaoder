#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
سیستم کامل اتحادها و دیپلماسی
انواع قراردادها: عدم تعرض، تجارت آزاد، اتحاد نظامی، اتحاد کامل
با تمام پاداش‌ها و محدودیت‌ها
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

# ==================== تعریف انواع قراردادها ====================

TREATY_TYPES = {
    "nap": {
        "name_fa": "پیمان عدم تعرض",
        "name_en": "Non-Aggression Pact",
        "duration": 30,
        "cost": 0,
        "min_diplomacy": 0,
        "benefits": {
            "share_tech_levels": [1, 2],
            "share_tech_per_week": 1,
            "share_tech_discount": 0,
            "auto_defense": False,
            "military_base": False,
            "veto_right": False,
            "stability_bonus": 0,
            "purchase_discount": 0,
            "income_bonus": 0,
            "extra_trade_deal": 0,
            "lend_units": False,
            "share_resources": False
        }
    },
    "fta": {
        "name_fa": "پیمان تجارت آزاد",
        "name_en": "Free Trade Agreement",
        "duration": 30,
        "cost": 100,
        "min_diplomacy": 3,
        "benefits": {
            "share_tech_levels": [1, 2, 3, 4],
            "share_tech_per_week": 2,
            "share_tech_discount": 0,
            "auto_defense": False,
            "military_base": False,
            "veto_right": False,
            "stability_bonus": 0,
            "purchase_discount": 0.10,
            "income_bonus": 0.10,
            "extra_trade_deal": 1,
            "lend_units": False,
            "share_resources": True
        }
    },
    "ma": {
        "name_fa": "اتحاد نظامی",
        "name_en": "Military Alliance",
        "duration": 30,
        "cost": 200,
        "min_diplomacy": 4,
        "benefits": {
            "share_tech_levels": [1, 2, 3, 4, 5, 6],
            "share_tech_per_week": 3,
            "share_tech_discount": 0,
            "auto_defense": True,
            "military_base": False,
            "veto_right": False,
            "stability_bonus": 0,
            "purchase_discount": 0.20,
            "income_bonus": 0,
            "extra_trade_deal": 0,
            "lend_units": False,
            "share_resources": True
        }
    },
    "fa": {
        "name_fa": "اتحاد کامل",
        "name_en": "Full Alliance",
        "duration": 0,
        "cost": 500,
        "min_diplomacy": 5,
        "requirements": "30 days acquaintance",
        "benefits": {
            "share_tech_levels": [1, 2, 3, 4, 5, 6],
            "share_tech_per_week": 5,
            "share_tech_discount": 0.50,
            "auto_defense": True,
            "military_base": True,
            "veto_right": True,
            "stability_bonus": 2,
            "purchase_discount": 0.40,
            "income_bonus": 0.15,
            "extra_trade_deal": 2,
            "lend_units": True,
            "share_resources": True
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
        
        payload = {"message": f"[alliance] {datetime.now().isoformat()}", "content": encoded, "sha": current_sha}
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


# ==================== مدیریت قراردادها ====================

def get_active_treaties(state: Dict[str, Any], user_id: str) -> List[Dict[str, Any]]:
    player = get_country_data(state, user_id)
    if not player:
        return []
    return player.get("treaties", [])


def get_treaty_with(state: Dict[str, Any], user_id: str, other_id: str) -> Optional[Dict[str, Any]]:
    treaties = get_active_treaties(state, user_id)
    for treaty in treaties:
        if treaty.get("with") == other_id:
            return treaty
    return None


def can_propose_treaty(state: Dict[str, Any], proposer_id: str, target_id: str, treaty_type: str) -> Tuple[bool, str]:
    if proposer_id == target_id:
        return False, "❌ نمی‌توانید با خودتان قرارداد ببندید."
    
    proposer = get_country_data(state, proposer_id)
    target = get_country_data(state, target_id)
    
    if not proposer or not target:
        return False, "❌ یکی از کشورها وجود ندارد."
    
    existing = get_treaty_with(state, proposer_id, target_id)
    if existing:
        return False, f"❌ شما قبلاً با این کشور قرارداد دارید."
    
    treaty_info = TREATY_TYPES.get(treaty_type)
    if not treaty_info:
        return False, "❌ نوع قرارداد نامعتبر."
    
    if proposer.get("diplomacy", 0) < treaty_info["min_diplomacy"]:
        return False, f"❌ دیپلماسی شما باید حداقل {treaty_info['min_diplomacy']} باشد."
    
    if target.get("diplomacy", 0) < treaty_info["min_diplomacy"]:
        return False, f"❌ دیپلماسی کشور هدف باید حداقل {treaty_info['min_diplomacy']} باشد."
    
    cost = treaty_info["cost"]
    influence = proposer.get("resources", {}).get("influence", 0)
    if influence < cost:
        return False, f"❌ نفوذ کافی ندارید. نیاز: {cost}"
    
    return True, ""


def propose_treaty(state: Dict[str, Any], proposer_id: str, target_name: str, treaty_type: str) -> Tuple[bool, str]:
    target_id = get_user_by_country(state, target_name)
    if not target_id:
        return False, f"❌ کشور '{target_name}' یافت نشد."
    
    success, msg = can_propose_treaty(state, proposer_id, target_id, treaty_type)
    if not success:
        return False, msg
    
    proposer = get_country_data(state, proposer_id)
    target = get_country_data(state, target_id)
    
    if "pending_treaties" not in state:
        state["pending_treaties"] = []
    
    pending = {
        "proposer_id": proposer_id,
        "proposer_name": proposer.get("name_fa"),
        "target_id": target_id,
        "target_name": target.get("name_fa"),
        "type": treaty_type,
        "proposed_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(hours=48)).isoformat()
    }
    state["pending_treaties"].append(pending)
    
    save_game_state(state)
    
    treaty_info = TREATY_TYPES[treaty_type]
    msg_target = f"🤝 *پیشنهاد {treaty_info['name_fa']}*\n{proposer.get('name_fa')} به شما پیشنهاد {treaty_info['name_fa']} داد.\n\nمهلت پاسخ: 48 ساعت\n\nبرای پذیرش: `/accept_treaty {proposer.get('name_fa')}`\nبرای رد: `/reject_treaty {proposer.get('name_fa')}`"
    send_message(target_id, msg_target)
    
    return True, f"✅ پیشنهاد {treaty_info['name_fa']} به {target.get('name_fa')} ارسال شد."


def accept_treaty(state: Dict[str, Any], user_id: str, proposer_name: str) -> Tuple[bool, str]:
    pending_treaties = state.get("pending_treaties", [])
    pending = None
    for p in pending_treaties:
        if p.get("target_id") == user_id and p.get("proposer_name") == proposer_name:
            pending = p
            break
    
    if not pending:
        return False, "❌ هیچ پیشنهاد فعالی از این کشور وجود ندارد."
    
    treaty_type = pending["type"]
    proposer_id = pending["proposer_id"]
    
    success, msg = can_propose_treaty(state, proposer_id, user_id, treaty_type)
    if not success:
        state["pending_treaties"] = [p for p in pending_treaties if p != pending]
        save_game_state(state)
        return False, msg
    
    proposer = get_country_data(state, proposer_id)
    target = get_country_data(state, user_id)
    treaty_info = TREATY_TYPES[treaty_type]
    
    proposer["resources"]["influence"] -= treaty_info["cost"]
    
    now = datetime.now()
    expires = now + timedelta(days=treaty_info["duration"]) if treaty_info["duration"] > 0 else None
    
    treaty_data = {
        "type": treaty_type,
        "with": user_id,
        "with_name": target.get("name_fa"),
        "started_at": now.isoformat(),
        "expires": expires.isoformat() if expires else None,
        "benefits": treaty_info["benefits"]
    }
    
    treaty_data_target = {
        "type": treaty_type,
        "with": proposer_id,
        "with_name": proposer.get("name_fa"),
        "started_at": now.isoformat(),
        "expires": expires.isoformat() if expires else None,
        "benefits": treaty_info["benefits"]
    }
    
    if "treaties" not in proposer:
        proposer["treaties"] = []
    if "treaties" not in target:
        target["treaties"] = []
    
    proposer["treaties"].append(treaty_data)
    target["treaties"].append(treaty_data_target)
    
    if treaty_type == "fa":
        proposer["stability"] = min(proposer.get("stability", 5) + 2, 10)
        target["stability"] = min(target.get("stability", 5) + 2, 10)
    
    state["pending_treaties"] = [p for p in pending_treaties if p != pending]
    
    save_game_state(state)
    
    send_to_gcc(f"🤝 *قرارداد جدید*\n{proposer.get('name_fa')} و {target.get('name_fa')} {treaty_info['name_fa']} امضا کردند.")
    
    return True, f"✅ شما {treaty_info['name_fa']} با {proposer.get('name_fa')} را پذیرفتید."


def reject_treaty(state: Dict[str, Any], user_id: str, proposer_name: str) -> Tuple[bool, str]:
    pending_treaties = state.get("pending_treaties", [])
    pending = None
    for p in pending_treaties:
        if p.get("target_id") == user_id and p.get("proposer_name") == proposer_name:
            pending = p
            break
    
    if not pending:
        return False, "❌ هیچ پیشنهاد فعالی از این کشور وجود ندارد."
    
    proposer = get_country_data(state, pending["proposer_id"])
    
    state["pending_treaties"] = [p for p in pending_treaties if p != pending]
    save_game_state(state)
    
    return True, f"❌ پیشنهاد {TREATY_TYPES[pending['type']]['name_fa']} از {proposer.get('name_fa')} رد شد."


def break_treaty(state: Dict[str, Any], user_id: str, target_name: str, mutual: bool = False) -> Tuple[bool, str]:
    target_id = get_user_by_country(state, target_name)
    if not target_id:
        return False, f"❌ کشور '{target_name}' یافت نشد."
    
    player = get_country_data(state, user_id)
    target = get_country_data(state, target_id)
    
    treaty = None
    for t in player.get("treaties", []):
        if t.get("with") == target_id:
            treaty = t
            break
    
    if not treaty:
        return False, "❌ شما هیچ قراردادی با این کشور ندارید."
    
    treaty_type = treaty["type"]
    treaty_info = TREATY_TYPES[treaty_type]
    
    if mutual:
        player["treaties"] = [t for t in player.get("treaties", []) if t.get("with") != target_id]
        target["treaties"] = [t for t in target.get("treaties", []) if t.get("with") != user_id]
        send_to_gcc(f"🤝 *لغو قرارداد*\n{player.get('name_fa')} و {target.get('name_fa')} {treaty_info['name_fa']} را با توافق دوطرفه لغو کردند.")
        save_game_state(state)
        return True, f"✅ {treaty_info['name_fa']} با {target_name} با توافق دوطرفه لغو شد."
    else:
        player["diplomacy"] = max(0, player.get("diplomacy", 0) - 2)
        penalty = treaty_info["cost"] // 2
        player["resources"]["influence"] = max(0, player.get("resources", {}).get("influence", 0) - penalty)
        player["treaties"] = [t for t in player.get("treaties", []) if t.get("with") != target_id]
        target["treaties"] = [t for t in target.get("treaties", []) if t.get("with") != user_id]
        
        if "treaty_ban_until" not in player:
            player["treaty_ban_until"] = {}
        player["treaty_ban_until"][target_id] = (datetime.now() + timedelta(days=14)).isoformat()
        
        send_to_gcc(f"⚠️ *لغو یکطرفه قرارداد*\n{player.get('name_fa')} {treaty_info['name_fa']} با {target.get('name_fa')} را یکطرفه لغو کرد و جریمه شد.")
        save_game_state(state)
        return True, f"⚠️ {treaty_info['name_fa']} با {target_name} یکطرفه لغو شد.\nجریمه: -{penalty} نفوذ، -2 دیپلماسی"


def get_treaties_list(state: Dict[str, Any], user_id: str) -> str:
    player = get_country_data(state, user_id)
    if not player:
        return "❌ شما کشوری انتخاب نکرده‌اید."
    
    treaties = player.get("treaties", [])
    if not treaties:
        return "📋 شما هیچ قرارداد فعالی ندارید."
    
    msg = "📋 *قراردادهای فعال شما*\n\n"
    for treaty in treaties:
        treaty_info = TREATY_TYPES[treaty["type"]]
        expires = treaty.get("expires")
        if expires:
            try:
                exp_date = datetime.fromisoformat(expires)
                days_left = (exp_date - datetime.now()).days
                expires_text = f" (انقضا: {days_left} روز)"
            except:
                expires_text = ""
        else:
            expires_text = " (نامحدود)"
        
        msg += f"• {treaty_info['name_fa']} با {treaty.get('with_name')}{expires_text}\n"
        benefits = treaty_info["benefits"]
        if benefits.get("auto_defense"):
            msg += f"  🛡️ دفاع مشترک خودکار\n"
        if benefits.get("share_tech_levels"):
            msg += f"  🔬 اشتراک فناوری (سطوح {benefits['share_tech_levels'][0]}-{benefits['share_tech_levels'][-1]})\n"
        if benefits.get("purchase_discount"):
            msg += f"  💰 تخفیف خرید: {int(benefits['purchase_discount']*100)}%\n"
        if benefits.get("income_bonus"):
            msg += f"  📈 افزایش درآمد: {int(benefits['income_bonus']*100)}%\n"
        msg += "\n"
    
    return msg


def get_pending_treaties(state: Dict[str, Any], user_id: str) -> str:
    pending_treaties = state.get("pending_treaties", [])
    pending = [p for p in pending_treaties if p.get("target_id") == user_id]
    
    if not pending:
        return "📭 هیچ پیشنهاد قرارداد فعالی ندارید."
    
    msg = "📭 *پیشنهادهای قرارداد دریافتی*\n\n"
    for p in pending:
        treaty_info = TREATY_TYPES[p["type"]]
        msg += f"• {treaty_info['name_fa']} از {p['proposer_name']}\n"
        msg += f"  برای پذیرش: `/accept_treaty {p['proposer_name']}`\n"
        msg += f"  برای رد: `/reject_treaty {p['proposer_name']}`\n\n"
    
    return msg


def get_alliance_benefits(state: Dict[str, Any], country_key: str) -> Dict[str, Any]:
    player = state["countries"].get(country_key, {})
    treaties = player.get("treaties", [])
    
    benefits = {
        "share_tech_levels": [],
        "share_tech_per_week": 0,
        "share_tech_discount": 0,
        "auto_defense": False,
        "military_base": False,
        "veto_right": False,
        "stability_bonus": 0,
        "purchase_discount": 0,
        "income_bonus": 0,
        "extra_trade_deal": 0,
        "lend_units": False,
        "share_resources": False
    }
    
    now = datetime.now()
    
    for treaty in treaties:
        expires = treaty.get("expires")
        if expires:
            try:
                if datetime.fromisoformat(expires) <= now:
                    continue
            except:
                pass
        
        treaty_type = treaty.get("type")
        treaty_info = TREATY_TYPES.get(treaty_type, {})
        treaty_benefits = treaty_info.get("benefits", {})
        
        if treaty_benefits.get("share_tech_levels"):
            benefits["share_tech_levels"] = treaty_benefits["share_tech_levels"]
        benefits["share_tech_per_week"] = max(benefits["share_tech_per_week"], treaty_benefits.get("share_tech_per_week", 0))
        benefits["share_tech_discount"] = max(benefits["share_tech_discount"], treaty_benefits.get("share_tech_discount", 0))
        benefits["auto_defense"] = benefits["auto_defense"] or treaty_benefits.get("auto_defense", False)
        benefits["military_base"] = benefits["military_base"] or treaty_benefits.get("military_base", False)
        benefits["veto_right"] = benefits["veto_right"] or treaty_benefits.get("veto_right", False)
        benefits["stability_bonus"] += treaty_benefits.get("stability_bonus", 0)
        benefits["purchase_discount"] = max(benefits["purchase_discount"], treaty_benefits.get("purchase_discount", 0))
        benefits["income_bonus"] += treaty_benefits.get("income_bonus", 0)
        benefits["extra_trade_deal"] += treaty_benefits.get("extra_trade_deal", 0)
        benefits["lend_units"] = benefits["lend_units"] or treaty_benefits.get("lend_units", False)
        benefits["share_resources"] = benefits["share_resources"] or treaty_benefits.get("share_resources", False)
    
    return benefits


def get_all_allies(state: Dict[str, Any], country_key: str) -> List[str]:
    player = state["countries"].get(country_key, {})
    treaties = player.get("treaties", [])
    allies = []
    
    for treaty in treaties:
        if treaty.get("type") == "fa":
            allies.append(treaty.get("with_name", ""))
    
    return allies


def check_auto_defense(state: Dict[str, Any], attacker_key: str, defender_key: str) -> List[str]:
    defender = state["countries"].get(defender_key, {})
    treaties = defender.get("treaties", [])
    
    allies_joining = []
    
    for treaty in treaties:
        if treaty.get("type") in ["ma", "fa"]:
            benefits = treaty.get("benefits", {})
            if benefits.get("auto_defense", False):
                ally_id = treaty.get("with")
                ally = state["countries"].get(ally_id, {})
                if ally:
                    allies_joining.append(ally.get("name_fa", "نامشخص"))
    
    return allies_joining


def apply_stability_bonus(state: Dict[str, Any], country_key: str):
    benefits = get_alliance_benefits(state, country_key)
    bonus = benefits.get("stability_bonus", 0)
    
    if bonus > 0:
        player = state["countries"].get(country_key, {})
        current = player.get("stability", 5)
        player["stability"] = min(10, current + bonus)


def share_technology(state: Dict[str, Any], from_key: str, to_key: str, branch: str, level: int) -> Tuple[bool, str]:
    from_player = state["countries"].get(from_key, {})
    treaties = from_player.get("treaties", [])
    
    has_alliance = False
    benefits = None
    
    for treaty in treaties:
        if treaty.get("with") == to_key:
            has_alliance = True
            benefits = treaty.get("benefits", {})
            break
    
    if not has_alliance:
        return False, "❌ شما با این کشور متحد نیستید."
    
    allowed_levels = benefits.get("share_tech_levels", [])
    if level not in allowed_levels:
        return False, f"❌ قرارداد شما فقط اجازه اشتراک سطوح {allowed_levels} را می‌دهد."
    
    tech_costs = [20, 40, 70, 110, 160, 220, 290, 370, 460]
    if level > len(tech_costs):
        return False, "❌ سطح نامعتبر."
    
    discount = benefits.get("share_tech_discount", 0)
    cost = int(tech_costs[level - 1] * (1 - discount))
    
    from_research = from_player.get("research", {})
    if from_research.get(branch, 0) < level:
        return False, "❌ شما این سطح فناوری را ندارید."
    
    to_player = state["countries"].get(to_key, {})
    to_tech = to_player.get("resources", {}).get("tech_points", 0)
    if to_tech < cost:
        return False, f"❌ کشور هدف فناوری کافی ندارد. نیاز: {cost}"
    
    to_player["resources"]["tech_points"] = to_tech - cost
    if "research" not in to_player:
        to_player["research"] = {}
    to_player["research"][branch] = max(to_player["research"].get(branch, 0), level)
    
    save_game_state(state)
    
    send_to_gcc(f"🔬 *اشتراک فناوری*\n{from_player.get('name_fa')} فناوری {branch} سطح {level} را با {to_player.get('name_fa')} به اشتراک گذاشت.")
    
    return True, f"✅ فناوری {branch} سطح {level} به اشتراک گذاشته شد. هزینه گیرنده: {cost} فناوری"


def get_alliance_help() -> str:
    return """
🤝 *سیستم اتحادها*

*انواع قراردادها:*

1. *پیمان عدم تعرض (nap)*
   - هزینه: رایگان | نیاز دیپلماسی: 0
   - اشتراک فناوری سطوح 1-2 (1 بار در هفته)

2. *پیمان تجارت آزاد (fta)*
   - هزینه: 100 نفوذ | نیاز دیپلماسی: 3
   - اشتراک فناوری سطوح 1-4 (2 بار در هفته)
   - تخفیف خرید 10% | افزایش درآمد 10%

3. *اتحاد نظامی (ma)*
   - هزینه: 200 نفوذ | نیاز دیپلماسی: 4
   - اشتراک فناوری سطوح 1-6 (3 بار در هفته)
   - دفاع مشترک خودکار | تخفیف خرید 20%

4. *اتحاد کامل (fa)*
   - هزینه: 500 نفوذ | نیاز دیپلماسی: 5
   - اشتراک فناوری سطوح 1-6 (5 بار در هفته، 50% تخفیف)
   - دفاع مشترک خودکار | پایگاه نظامی | حق وتو
   - +2 ثبات داخلی | تخفیف خرید 40% | افزایش درآمد 15%
   - قرض دادن تجهیزات | اشتراک منابع

*دستورات:*
/propose_treaty [کشور] [نوع] - پیشنهاد قرارداد
/accept_treaty [کشور] - پذیرش پیشنهاد
/reject_treaty [کشور] - رد پیشنهاد
/break_treaty [کشور] [mutual] - لغو قرارداد
/my_treaties - مشاهده قراردادهای فعال
/pending_treaties - مشاهده پیشنهادها
/share_tech [کشور] [شاخه] [سطح] - اشتراک فناوری
"""


if __name__ == "__main__":
    print("Alliance system module loaded (complete)")
