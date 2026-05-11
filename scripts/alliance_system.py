#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
سیستم کامل اتحادها و دیپلماسی
انواع قراردادها: عدم تعرض، تجارت آزاد، اتحاد نظامی، اتحاد کامل
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
    "nap": {  # Non-Aggression Pact - پیمان عدم تعرض
        "name_fa": "پیمان عدم تعرض",
        "name_en": "Non-Aggression Pact",
        "duration": 30,  # روز
        "cost": 0,
        "min_diplomacy": 0,
        "benefits": {
            "share_tech_levels": [1, 2],
            "share_tech_per_week": 1,
            "share_resources": False,
            "auto_defense": False,
            "military_base": False,
            "veto_right": False,
            "stability_bonus": 0,
            "purchase_discount": 0,
            "resource_sharing": False
        }
    },
    "fta": {  # Free Trade Agreement - پیمان تجارت آزاد
        "name_fa": "پیمان تجارت آزاد",
        "name_en": "Free Trade Agreement",
        "duration": 30,
        "cost": 100,
        "min_diplomacy": 3,
        "benefits": {
            "share_tech_levels": [1, 2, 3, 4],
            "share_tech_per_week": 2,
            "share_resources": True,
            "auto_defense": False,
            "military_base": False,
            "veto_right": False,
            "stability_bonus": 0,
            "purchase_discount": 0.10,  # 10% تخفیف برای نسل 1-3
            "resource_sharing": True
        }
    },
    "ma": {  # Military Alliance - اتحاد نظامی
        "name_fa": "اتحاد نظامی",
        "name_en": "Military Alliance",
        "duration": 30,
        "cost": 200,
        "min_diplomacy": 4,
        "benefits": {
            "share_tech_levels": [1, 2, 3, 4, 5, 6],
            "share_tech_per_week": 3,
            "share_resources": True,
            "auto_defense": True,
            "military_base": False,
            "veto_right": False,
            "stability_bonus": 0,
            "purchase_discount": 0.20,  # 20% تخفیف برای نسل 1-4
            "resource_sharing": True
        }
    },
    "fa": {  # Full Alliance - اتحاد کامل
        "name_fa": "اتحاد کامل",
        "name_en": "Full Alliance",
        "duration": 0,  # نامحدود
        "cost": 500,
        "min_diplomacy": 5,
        "requirements": "30 days acquaintance",
        "benefits": {
            "share_tech_levels": [1, 2, 3, 4, 5, 6],
            "share_tech_per_week": 5,
            "share_tech_discount": 0.50,  # 50% تخفیف اشتراک فناوری
            "share_resources": True,
            "auto_defense": True,
            "military_base": True,
            "veto_right": True,
            "stability_bonus": 2,  # +2 ثبات داخلی
            "purchase_discount": 0.40,  # 40% تخفیف برای نسل 1-3، 30% نسل 4-5، 20% نسل 6
            "resource_sharing": True,
            "lend_units": True  # قرض دادن تجهیزات
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


def get_country_data(state: Dict[str, Any], user_id: str) -> Optional[Dict[str, Any]]:
    for country_key, player in state.get("countries", {}).items():
        if player.get("user_id") == user_id:
            return player
    return None


# ==================== مدیریت قراردادها ====================

def get_active_treaties(state: Dict[str, Any], user_id: str) -> List[Dict[str, Any]]:
    """دریافت لیست قراردادهای فعال یک کشور"""
    player = get_country_data(state, user_id)
    if not player:
        return []
    return player.get("treaties", [])


def get_treaty_with(state: Dict[str, Any], user_id: str, other_id: str) -> Optional[Dict[str, Any]]:
    """دریافت قرارداد بین دو کشور"""
    treaties = get_active_treaties(state, user_id)
    for treaty in treaties:
        if treaty.get("with") == other_id:
            return treaty
    return None


def is_treaty_active(state: Dict[str, Any], user_id: str, other_id: str, treaty_type: str = None) -> bool:
    """بررسی وجود قرارداد فعال بین دو کشور"""
    treaty = get_treaty_with(state, user_id, other_id)
    if not treaty:
        return False
    if treaty_type and treaty.get("type") != treaty_type:
        return False
    if treaty.get("expires"):
        try:
            expires = datetime.fromisoformat(treaty["expires"])
            if expires < datetime.now():
                return False
        except:
            pass
    return True


def can_propose_treaty(state: Dict[str, Any], proposer_id: str, target_id: str, treaty_type: str) -> Tuple[bool, str]:
    """بررسی امکان پیشنهاد قرارداد"""
    if proposer_id == target_id:
        return False, "❌ نمی‌توانید با خودتان قرارداد ببندید."
    
    proposer = get_country_data(state, proposer_id)
    target = get_country_data(state, target_id)
    
    if not proposer or not target:
        return False, "❌ یکی از کشورها وجود ندارد."
    
    # بررسی قرارداد موجود
    existing = get_treaty_with(state, proposer_id, target_id)
    if existing:
        return False, f"❌ شما قبلاً با این کشور {TREATY_TYPES[existing['type']]['name_fa']} دارید."
    
    # بررسی دیپلماسی
    treaty_info = TREATY_TYPES.get(treaty_type)
    if not treaty_info:
        return False, "❌ نوع قرارداد نامعتبر."
    
    if proposer.get("diplomacy", 0) < treaty_info["min_diplomacy"]:
        return False, f"❌ دیپلماسی شما باید حداقل {treaty_info['min_diplomacy']} باشد."
    
    if target.get("diplomacy", 0) < treaty_info["min_diplomacy"]:
        return False, f"❌ دیپلماسی کشور هدف باید حداقل {treaty_info['min_diplomacy']} باشد."
    
    # بررسی هزینه
    cost = treaty_info["cost"]
    influence = proposer.get("resources", {}).get("influence", 0)
    if influence < cost:
        return False, f"❌ نفوذ کافی ندارید. نیاز: {cost}"
    
    return True, ""


def propose_treaty(state: Dict[str, Any], proposer_id: str, target_name: str, treaty_type: str) -> Tuple[bool, str]:
    """پیشنهاد قرارداد به کشور دیگر"""
    target_id = get_user_by_country(state, target_name)
    if not target_id:
        return False, f"❌ کشور '{target_name}' یافت نشد."
    
    success, msg = can_propose_treaty(state, proposer_id, target_id, treaty_type)
    if not success:
        return False, msg
    
    proposer = get_country_data(state, proposer_id)
    target = get_country_data(state, target_id)
    
    # ذخیره پیشنهاد
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
    
    # اعلان به طرف مقابل
    treaty_info = TREATY_TYPES[treaty_type]
    msg_target = f"🤝 *پیشنهاد {treaty_info['name_fa']}*\n{proposer.get('name_fa')} به شما پیشنهاد {treaty_info['name_fa']} داد.\n\nمهلت پاسخ: 48 ساعت\n\nبرای پذیرش: `/accept_treaty {proposer.get('name_fa')}`\nبرای رد: `/reject_treaty {proposer.get('name_fa')}`"
    send_message(target_id, msg_target)
    
    return True, f"✅ پیشنهاد {treaty_info['name_fa']} به {target.get('name_fa')} ارسال شد. 48 ساعت مهلت پاسخ."


def accept_treaty(state: Dict[str, Any], user_id: str, proposer_name: str) -> Tuple[bool, str]:
    """پذیرش پیشنهاد قرارداد"""
    # پیدا کردن پیشنهاد
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
    
    # بررسی مجدد شرایط
    success, msg = can_propose_treaty(state, proposer_id, user_id, treaty_type)
    if not success:
        # حذف پیشنهاد منقضی
        state["pending_treaties"] = [p for p in pending_treaties if p != pending]
        save_game_state(state)
        return False, msg
    
    # ایجاد قرارداد
    proposer = get_country_data(state, proposer_id)
    target = get_country_data(state, user_id)
    treaty_info = TREATY_TYPES[treaty_type]
    
    # کسر هزینه از پیشنهاد‌دهنده
    proposer["resources"]["influence"] -= treaty_info["cost"]
    
    # ایجاد قرارداد برای هر دو طرف
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
    
    # اعمال پاداش ثبات برای اتحاد کامل
    if treaty_type == "fa":
        proposer["stability"] = min(proposer.get("stability", 5) + 2, 10)
        target["stability"] = min(target.get("stability", 5) + 2, 10)
    
    # حذف پیشنهاد
    state["pending_treaties"] = [p for p in pending_treaties if p != pending]
    
    save_game_state(state)
    
    # اعلان به GCC
    send_to_gcc(f"🤝 *قرارداد جدید*\n{proposer.get('name_fa')} و {target.get('name_fa')} {treaty_info['name_fa']} امضا کردند.")
    
    return True, f"✅ شما {treaty_info['name_fa']} با {proposer.get('name_fa')} را پذیرفتید."


def reject_treaty(state: Dict[str, Any], user_id: str, proposer_name: str) -> Tuple[bool, str]:
    """رد پیشنهاد قرارداد"""
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
    """لغو قرارداد با کشور دیگر"""
    target_id = get_user_by_country(state, target_name)
    if not target_id:
        return False, f"❌ کشور '{target_name}' یافت نشد."
    
    player = get_country_data(state, user_id)
    target = get_country_data(state, target_id)
    
    # پیدا کردن قرارداد
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
        # لغو دوطرفه
        player["treaties"] = [t for t in player.get("treaties", []) if t.get("with") != target_id]
        target["treaties"] = [t for t in target.get("treaties", []) if t.get("with") != user_id]
        
        send_to_gcc(f"🤝 *لغو قرارداد*\n{player.get('name_fa')} و {target.get('name_fa')} {treaty_info['name_fa']} را با توافق دوطرفه لغو کردند.")
        
        save_game_state(state)
        return True, f"✅ {treaty_info['name_fa']} با {target_name} با توافق دوطرفه لغو شد."
    else:
        # لغو یکطرفه با جریمه
        player["diplomacy"] = max(0, player.get("diplomacy", 0) - 2)
        
        penalty = treaty_info["cost"] // 2
        player["resources"]["influence"] = max(0, player.get("resources", {}).get("influence", 0) - penalty)
        
        # حذف قرارداد
        player["treaties"] = [t for t in player.get("treaties", []) if t.get("with") != target_id]
        target["treaties"] = [t for t in target.get("treaties", []) if t.get("with") != user_id]
        
        # ممنوعیت قرارداد جدید به مدت 14 روز
        if "treaty_ban_until" not in player:
            player["treaty_ban_until"] = {}
        player["treaty_ban_until"][target_id] = (datetime.now() + timedelta(days=14)).isoformat()
        
        send_to_gcc(f"⚠️ *لغو یکطرفه قرارداد*\n{player.get('name_fa')} {treaty_info['name_fa']} با {target.get('name_fa')} را یکطرفه لغو کرد و جریمه شد.")
        
        save_game_state(state)
        return True, f"⚠️ {treaty_info['name_fa']} با {target_name} یکطرفه لغو شد.\nجریمه: -{penalty} نفوذ، -2 دیپلماسی"


def get_treaties_list(state: Dict[str, Any], user_id: str) -> str:
    """دریافت لیست قراردادهای فعال به صورت متن"""
    player = get_country_data(state, user_id)
    if not player:
        return "❌ شما کشوری انتخاب نکرده‌اید."
    
    treaties = player.get("treaties", [])
    if not treaties:
        return "📋 شما هیچ قرارداد فعالی ندارید.\nبرای پیشنهاد قرارداد: `/propose_treaty [کشور] [type]`\nانواع: nap, fta, ma, fa"
    
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
        
        # نمایش مزایا
        benefits = treaty_info["benefits"]
        if benefits.get("auto_defense"):
            msg += f"  🛡️ دفاع مشترک خودکار\n"
        if benefits.get("share_tech_levels"):
            msg += f"  🔬 اشتراک فناوری (سطوح {benefits['share_tech_levels'][0]}-{benefits['share_tech_levels'][-1]})\n"
        if benefits.get("purchase_discount"):
            msg += f"  💰 تخفیف خرید: {int(benefits['purchase_discount']*100)}%\n"
    
    return msg


def get_pending_treaties(state: Dict[str, Any], user_id: str) -> str:
    """دریافت لیست پیشنهادهای دریافتی"""
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


def share_technology(state: Dict[str, Any], user_id: str, target_name: str, branch: str, level: int) -> Tuple[bool, str]:
    """اشتراک فناوری با یک متحد"""
    target_id = get_user_by_country(state, target_name)
    if not target_id:
        return False, f"❌ کشور '{target_name}' یافت نشد."
    
    # بررسی وجود قرارداد
    treaty = get_treaty_with(state, user_id, target_id)
    if not treaty:
        return False, "❌ شما با این کشور قراردادی ندارید."
    
    treaty_info = TREATY_TYPES[treaty["type"]]
    allowed_levels = treaty_info["benefits"].get("share_tech_levels", [])
    
    if level not in allowed_levels:
        return False, f"❌ قرارداد شما فقط اجازه اشتراک سطوح {allowed_levels} را می‌دهد."
    
    # بررسی سابقه اشتراک در هفته
    # (در implementation واقعی نیاز به شمارش دارد)
    
    # هزینه اشتراک (75% قیمت اصلی)
    tech_costs = [20, 40, 70, 110, 160, 220, 290, 370, 460]
    if level > len(tech_costs):
        return False, "❌ سطح نامعتبر."
    
    cost = int(tech_costs[level - 1] * 0.75)
    
    sender = get_country_data(state, user_id)
    receiver = get_country_data(state, target_id)
    
    # بررسی فناوری فرستنده
    sender_research = sender.get("research", {})
    if sender_research.get(branch, 0) < level:
        return False, "❌ شما این سطح فناوری را ندارید."
    
    # بررسی منابع گیرنده
    receiver_tech = receiver.get("resources", {}).get("tech_points", 0)
    if receiver_tech < cost:
        return False, f"❌ کشور هدف فناوری کافی ندارد. نیاز: {cost}"
    
    # اعمال اشتراک
    if "research" not in receiver:
        receiver["research"] = {}
    receiver["research"][branch] = max(receiver["research"].get(branch, 0), level)
    receiver["resources"]["tech_points"] -= cost
    
    save_game_state(state)
    
    send_to_gcc(f"🔬 *اشتراک فناوری*\n{sender.get('name_fa')} فناوری {branch} سطح {level} را با {receiver.get('name_fa')} به اشتراک گذاشت.")
    
    return True, f"✅ فناوری {branch} سطح {level} با {target_name} به اشتراک گذاشته شد. هزینه گیرنده: {cost} فناوری"


# ==================== دستورات اتحاد ====================

def handle_propose_treaty(state: Dict[str, Any], user_id: str, args: str) -> str:
    """دستور /propose_treaty [کشور] [نوع]"""
    parts = args.strip().split()
    if len(parts) < 2:
        return """❌ فرمت صحیح: `/propose_treaty [کشور] [نوع]`

انواع قرارداد:
• nap - پیمان عدم تعرض
• fta - پیمان تجارت آزاد
• ma - اتحاد نظامی
• fa - اتحاد کامل

مثال: `/propose_treaty آلمان ma`
"""
    
    target_name = parts[0]
    treaty_type = parts[1].lower()
    
    if treaty_type not in TREATY_TYPES:
        return f"❌ نوع قرارداد نامعتبر. انتخاب‌ها: nap, fta, ma, fa"
    
    success, msg = propose_treaty(state, user_id, target_name, treaty_type)
    if success:
        save_game_state(state)
    return msg


def handle_accept_treaty(state: Dict[str, Any], user_id: str, args: str) -> str:
    """دستور /accept_treaty [کشور]"""
    if not args.strip():
        return "❌ لطفاً نام کشور پیشنهاد‌دهنده را وارد کنید. مثال: `/accept_treaty آلمان`"
    
    success, msg = accept_treaty(state, user_id, args.strip())
    if success:
        save_game_state(state)
    return msg


def handle_reject_treaty(state: Dict[str, Any], user_id: str, args: str) -> str:
    """دستور /reject_treaty [کشور]"""
    if not args.strip():
        return "❌ لطفاً نام کشور پیشنهاد‌دهنده را وارد کنید. مثال: `/reject_treaty آلمان`"
    
    success, msg = reject_treaty(state, user_id, args.strip())
    if success:
        save_game_state(state)
    return msg


def handle_break_treaty(state: Dict[str, Any], user_id: str, args: str) -> str:
    """دستور /break_treaty [کشور] [mutual]"""
    parts = args.strip().split()
    if len(parts) < 1:
        return "❌ لطفاً نام کشور را وارد کنید. مثال: `/break_treaty آلمان`\nبرای لغو دوطرفه: `/break_treaty آلمان mutual`"
    
    target_name = parts[0]
    mutual = len(parts) > 1 and parts[1].lower() == "mutual"
    
    success, msg = break_treaty(state, user_id, target_name, mutual)
    if success:
        save_game_state(state)
    return msg


def handle_my_treaties(state: Dict[str, Any], user_id: str) -> str:
    """دستور /my_treaties - نمایش قراردادهای فعال"""
    return get_treaties_list(state, user_id)


def handle_pending_treaties(state: Dict[str, Any], user_id: str) -> str:
    """دستور /pending_treaties - نمایش پیشنهادهای دریافتی"""
    return get_pending_treaties(state, user_id)


def handle_share_tech(state: Dict[str, Any], user_id: str, args: str) -> str:
    """دستور /share_tech [کشور] [شاخه] [سطح]"""
    parts = args.strip().split()
    if len(parts) < 3:
        return "❌ فرمت صحیح: `/share_tech [کشور] [شاخه] [سطح]`\nشاخه‌ها: military, industrial, economic, diplomacy, nuclear\nمثال: `/share_tech آلمان military 3`"
    
    target_name = parts[0]
    branch = parts[1].lower()
    try:
        level = int(parts[2])
    except:
        return "❌ سطح باید عدد باشد."
    
    valid_branches = ["military", "industrial", "economic", "diplomacy", "nuclear"]
    if branch not in valid_branches:
        return f"❌ شاخه نامعتبر. انتخاب‌ها: {', '.join(valid_branches)}"
    
    success, msg = share_technology(state, user_id, target_name, branch, level)
    if success:
        save_game_state(state)
    return msg


# ==================== توابع عمومی ====================

def get_alliance_help() -> str:
    """راهنمای سیستم اتحاد"""
    return """
🤝 *سیستم اتحادها*

انواع قراردادها:

1. *پیمان عدم تعرض (nap)*
   - هزینه: رایگان
   - نیاز دیپلماسی: 0
   - اشتراک فناوری سطوح 1-2 (1 بار در هفته)

2. *پیمان تجارت آزاد (fta)*
   - هزینه: 100 نفوذ
   - نیاز دیپلماسی: 3
   - اشتراک فناوری سطوح 1-4 (2 بار در هفته)
   - تخفیف خرید 10%

3. *اتحاد نظامی (ma)*
   - هزینه: 200 نفوذ
   - نیاز دیپلماسی: 4
   - اشتراک فناوری سطوح 1-6 (3 بار در هفته)
   - دفاع مشترک خودکار
   - تخفیف خرید 20%

4. *اتحاد کامل (fa)*
   - هزینه: 500 نفوذ
   - نیاز دیپلماسی: 5 + 30 روز آشنایی
   - اشتراک فناوری سطوح 1-6 (5 بار در هفته، 50% تخفیف)
   - دفاع مشترک خودکار
   - پایگاه نظامی در خاک متحد
   - حق وتو
   - +2 ثبات داخلی
   - تخفیف خرید 40%

دستورات:
/propose_treaty [کشور] [نوع] - پیشنهاد قرارداد
/accept_treaty [کشور] - پذیرش پیشنهاد
/reject_treaty [کشور] - رد پیشنهاد
/break_treaty [کشور] - لغو قرارداد
/my_treaties - مشاهده قراردادهای فعال
/pending_treaties - مشاهده پیشنهادها
/share_tech [کشور] [شاخه] [سطح] - اشتراک فناوری
"""


if __name__ == "__main__":
    print("Alliance system module loaded")
