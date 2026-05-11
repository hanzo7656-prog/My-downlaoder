#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
سیستم سازمان ملل متحد (UN)
امکانات: قطعنامه، رأی‌گیری، تحریم جهانی، شورای امنیت، دبیرکل
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

# ==================== تعریف قطعنامه‌ها ====================

RESOLUTIONS = {
    "economic_sanction": {
        "name_fa": "تحریم اقتصادی جهانی",
        "name_en": "Global Economic Sanction",
        "body": "security_council",  # شورای امنیت
        "required_votes": 9,  # از 15
        "vetoable": True,
        "duration": 14,
        "effects": {
            "income_penalty": 0.50,  # -50% درآمد
            "trade_penalty": 0.30,   # -30% تجارت
        },
        "trigger": "use_of_nuclear_weapon"
    },
    "weapon_embargo": {
        "name_fa": "تحریم تسلیحاتی جهانی",
        "name_en": "Global Weapon Embargo",
        "body": "security_council",
        "required_votes": 9,
        "vetoable": True,
        "duration": 14,
        "effects": {
            "block_weapons": True,    # نمی‌تواند تجهیزات بخرد
        },
        "trigger": "aggression_against_2_countries"
    },
    "ceasefire": {
        "name_fa": "آتش‌بس اجباری",
        "name_en": "Forced Ceasefire",
        "body": "security_council",
        "required_votes": 9,
        "vetoable": True,
        "duration": 7,
        "effects": {
            "force_ceasefire": True,  # جنگ متوقف می‌شود
        },
        "trigger": "high_civilian_casualties"
    },
    "peacekeeping": {
        "name_fa": "نیروی حافظ صلح",
        "name_en": "Peacekeeping Force",
        "body": "security_council",
        "required_votes": 9,
        "vetoable": True,
        "duration": 30,
        "effects": {
            "peacekeeping_force": 2000,  # قدرت 50
        },
        "trigger": "prolonged_conflict"
    },
    "condemnation": {
        "name_fa": "محکومیت رسمی",
        "name_en": "Official Condemnation",
        "body": "general_assembly",
        "required_votes": 0.5,  # اکثریت ساده
        "vetoable": False,
        "duration": 0,
        "effects": {
            "prestige_penalty": 10,   # -10 پرستیژ
            "diplomacy_penalty": 2,   # -2 دیپلماسی
        },
        "trigger": "any_violation"
    },
    "aid_call": {
        "name_fa": "فراخوان کمک",
        "name_en": "Aid Call",
        "body": "general_assembly",
        "required_votes": 0.5,
        "vetoable": False,
        "duration": 7,
        "effects": {
            "aid_discount": 0.20,     # 20% تخفیف کمک
        },
        "trigger": "natural_disaster"
    },
    "diplomatic_sanction": {
        "name_fa": "تحریم دیپلماتیک",
        "name_en": "Diplomatic Sanction",
        "body": "general_assembly",
        "required_votes": 0.5,
        "vetoable": False,
        "duration": 14,
        "effects": {
            "block_treaties": True,   # نمی‌تواند قرارداد ببندد
        },
        "trigger": "treaty_violation"
    },
    "suspension": {
        "name_fa": "تعلیق عضویت",
        "name_en": "Membership Suspension",
        "body": "general_assembly",
        "required_votes": 0.66,  # دو سوم
        "vetoable": False,
        "duration": 30,
        "effects": {
            "suspend_membership": True,  # از همه قابلیت‌ها محروم
        },
        "trigger": "multiple_violations"
    },
    "military_intervention": {
        "name_fa": "مداخله نظامی مجاز",
        "name_en": "Authorized Military Intervention",
        "body": "general_assembly",
        "required_votes": 0.66,
        "vetoable": False,
        "duration": 14,
        "effects": {
            "authorized_war": True,   # هر کشوری می‌تواند حمله کند
        },
        "trigger": "aggression"
    },
    "icc_referral": {
        "name_fa": "دادگاه جنایی",
        "name_en": "ICC Referral",
        "body": "general_assembly",
        "required_votes": 0.66,
        "vetoable": False,
        "duration": 0,
        "effects": {
            "war_crimes_trial": True,  # محاکمه پس از بازی
        },
        "trigger": "war_crimes"
    }
}

# ==================== اعضای دائمی شورای امنیت ====================

PERMANENT_MEMBERS = ["usa", "russia", "china", "uk", "france"]

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
        
        payload = {"message": f"[un] {datetime.now().isoformat()}", "content": encoded, "sha": current_sha}
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


def get_country_zone(country_key: str) -> str:
    """دریافت منطقه برای تعیین کرسی متغیر شورای امنیت"""
    zones = {
        "usa": "america", "canada": "america", "brazil": "america",
        "japan": "asia", "china": "asia", "south_korea": "asia", "india": "asia",
        "iran": "middle_east", "turkey": "middle_east", "saudi": "middle_east", "israel": "middle_east",
        "germany": "europe", "france": "europe", "uk": "europe", "italy": "europe", "spain": "europe",
        "russia": "europe", "poland": "europe", "ukraine": "europe",
        "australia": "oceania",
        "south_africa": "africa", "egypt": "africa"
    }
    return zones.get(country_key, "other")


# ==================== مدیریت دبیرکل ====================

def get_secretary_general(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """دریافت اطلاعات دبیرکل فعلی"""
    return state.get("un", {}).get("secretary_general")


def get_secretary_general_term_end(state: Dict[str, Any]) -> Optional[datetime]:
    """دریافت تاریخ پایان دوره دبیرکل"""
    term_end = state.get("un", {}).get("sg_term_end")
    if term_end:
        return datetime.fromisoformat(term_end)
    return None


def is_secretary_general_election_needed(state: Dict[str, Any]) -> bool:
    """بررسی نیاز به انتخابات دبیرکل"""
    term_end = get_secretary_general_term_end(state)
    if not term_end:
        return True
    return datetime.now() >= term_end


def get_secretary_general_bonus(state: Dict[str, Any], country_key: str) -> Dict[str, Any]:
    """دریافت پاداش‌های دبیرکل برای یک کشور"""
    sg = get_secretary_general(state)
    if not sg or sg.get("country_key") != country_key:
        return {"diplomacy_bonus": 0, "statement_discount": 0, "symbolic_veto": False}
    
    return {
        "diplomacy_bonus": 2,
        "statement_discount": 0.20,
        "symbolic_veto": True
    }


# ==================== مدیریت قطعنامه‌ها ====================

def propose_resolution(state: Dict[str, Any], proposer_id: str, target_id: str, resolution_type: str, reason: str) -> Tuple[bool, str]:
    """طرح قطعنامه در سازمان ملل"""
    proposer_key = get_country_key_by_user(state, proposer_id)
    if not proposer_key:
        return False, "❌ شما کشوری انتخاب نکرده‌اید."
    
    target_key = get_country_key_by_user(state, target_id)
    if not target_key:
        return False, "❌ کشور هدف یافت نشد."
    
    resolution_info = RESOLUTIONS.get(resolution_type)
    if not resolution_info:
        return False, "❌ نوع قطعنامه نامعتبر."
    
    # هزینه طرح قطعنامه
    cost = 100 if resolution_info["body"] == "security_council" else 50
    proposer = state["countries"][proposer_key]
    if proposer.get("resources", {}).get("influence", 0) < cost:
        return False, f"❌ نفوذ کافی ندارید. نیاز: {cost}"
    
    # کسر هزینه
    proposer["resources"]["influence"] -= cost
    
    # ایجاد قطعنامه
    resolution_id = f"res_{datetime.now().timestamp()}"
    expires_at = datetime.now() + timedelta(hours=72)
    
    resolution = {
        "id": resolution_id,
        "type": resolution_type,
        "name_fa": resolution_info["name_fa"],
        "body": resolution_info["body"],
        "proposer": proposer_key,
        "proposer_name": proposer.get("name_fa"),
        "target": target_key,
        "target_name": get_country_name(state, target_id),
        "reason": reason,
        "proposed_at": datetime.now().isoformat(),
        "expires_at": expires_at.isoformat(),
        "votes_yes": [],
        "votes_no": [],
        "votes_abstain": [],
        "status": "voting"
    }
    
    if "un" not in state:
        state["un"] = {}
    if "resolutions" not in state["un"]:
        state["un"]["resolutions"] = []
    state["un"]["resolutions"].append(resolution)
    
    save_game_state(state)
    
    # اعلان به GCC
    send_to_gcc(f"📜 *قطعنامه جدید در {resolution_info['body']}*\n{proposer.get('name_fa')} قطعنامه {resolution_info['name_fa']} علیه {get_country_name(state, target_id)} طرح کرد.\nعلت: {reason}\nمهلت رأی‌گیری: 72 ساعت")
    
    return True, f"✅ قطعنامه {resolution_info['name_fa']} در {resolution_info['body']} طرح شد.\nمهلت رأی‌گیری: 72 ساعت"


def vote_on_resolution(state: Dict[str, Any], user_id: str, resolution_id: str, vote: str) -> Tuple[bool, str]:
    """رأی‌گیری روی یک قطعنامه"""
    country_key = get_country_key_by_user(state, user_id)
    if not country_key:
        return False, "❌ شما کشوری انتخاب نکرده‌اید."
    
    # پیدا کردن قطعنامه
    resolutions = state.get("un", {}).get("resolutions", [])
    resolution = None
    for r in resolutions:
        if r.get("id") == resolution_id:
            resolution = r
            break
    
    if not resolution:
        return False, "❌ قطعنامه یافت نشد."
    
    if resolution.get("status") != "voting":
        return False, "❌ رأی‌گیری برای این قطعنامه به پایان رسیده است."
    
    expires = datetime.fromisoformat(resolution["expires_at"])
    if datetime.now() > expires:
        resolution["status"] = "expired"
        save_game_state(state)
        return False, "❌ مهلت رأی‌گیری برای این قطعنامه به پایان رسیده است."
    
    # ثبت رأی
    if vote == "yes":
        if country_key not in resolution["votes_yes"]:
            resolution["votes_yes"].append(country_key)
            resolution["votes_no"] = [v for v in resolution["votes_no"] if v != country_key]
            resolution["votes_abstain"] = [v for v in resolution["votes_abstain"] if v != country_key]
    elif vote == "no":
        if country_key not in resolution["votes_no"]:
            resolution["votes_no"].append(country_key)
            resolution["votes_yes"] = [v for v in resolution["votes_yes"] if v != country_key]
            resolution["votes_abstain"] = [v for v in resolution["votes_abstain"] if v != country_key]
    elif vote == "abstain":
        if country_key not in resolution["votes_abstain"]:
            resolution["votes_abstain"].append(country_key)
            resolution["votes_yes"] = [v for v in resolution["votes_yes"] if v != country_key]
            resolution["votes_no"] = [v for v in resolution["votes_no"] if v != country_key]
    else:
        return False, "❌ رأی نامعتبر. انتخاب‌ها: yes, no, abstain"
    
    save_game_state(state)
    return True, f"✅ رأی شما ({vote}) ثبت شد."


def check_and_resolve_resolutions(state: Dict[str, Any]) -> int:
    """بررسی و حل قطعنامه‌های منقضی شده"""
    resolutions = state.get("un", {}).get("resolutions", [])
    now = datetime.now()
    resolved_count = 0
    
    for resolution in resolutions:
        if resolution.get("status") != "voting":
            continue
        
        expires = datetime.fromisoformat(resolution["expires_at"])
        if now <= expires:
            continue
        
        # محاسبه نتیجه
        total_votes = len(resolution["votes_yes"]) + len(resolution["votes_no"])
        yes_votes = len(resolution["votes_yes"])
        no_votes = len(resolution["votes_no"])
        
        resolution_info = RESOLUTIONS.get(resolution["type"], {})
        required = resolution_info.get("required_votes", 0)
        
        # برای مجمع عمومی (نسبی)
        if resolution_info.get("body") == "general_assembly":
            if total_votes > 0:
                if yes_votes / total_votes >= required:
                    resolution["status"] = "passed"
                    resolution["result"] = "passed"
                    apply_resolution_effects(state, resolution)
                    resolved_count += 1
                    send_to_gcc(f"✅ *قطعنامه {resolution_info['name_fa']} تصویب شد!*\nموافق: {yes_votes} | مخالف: {no_votes}")
                else:
                    resolution["status"] = "failed"
                    resolution["result"] = "failed"
                    resolved_count += 1
                    send_to_gcc(f"❌ *قطعنامه {resolution_info['name_fa']} رد شد!*\nموافق: {yes_votes} | مخالف: {no_votes}")
        
        # برای شورای امنیت (تعداد مشخص + بررسی وتو)
        elif resolution_info.get("body") == "security_council":
            # بررسی وتو از اعضای دائمی
            vetoed = False
            for member in PERMANENT_MEMBERS:
                if member in resolution["votes_no"]:
                    vetoed = True
                    break
            
            if vetoed:
                resolution["status"] = "vetoed"
                resolution["result"] = "vetoed"
                resolved_count += 1
                send_to_gcc(f"⚠️ *قطعنامه {resolution_info['name_fa']} وتو شد!*\nیک عضو دائم شورای امنیت وتو کرد.")
            elif yes_votes >= required:
                resolution["status"] = "passed"
                resolution["result"] = "passed"
                apply_resolution_effects(state, resolution)
                resolved_count += 1
                send_to_gcc(f"✅ *قطعنامه {resolution_info['name_fa']} در شورای امنیت تصویب شد!*\nموافق: {yes_votes} | مخالف: {no_votes}")
            else:
                resolution["status"] = "failed"
                resolution["result"] = "failed"
                resolved_count += 1
                send_to_gcc(f"❌ *قطعنامه {resolution_info['name_fa']} در شورای امنیت رد شد!*\nموافق: {yes_votes} | مخالف: {no_votes}")
    
    if resolved_count > 0:
        save_game_state(state)
    
    return resolved_count


def apply_resolution_effects(state: Dict[str, Any], resolution: Dict[str, Any]):
    """اعمال اثرات قطعنامه تصویب شده"""
    target_key = resolution.get("target")
    if not target_key:
        return
    
    target = state["countries"].get(target_key)
    if not target:
        return
    
    resolution_info = RESOLUTIONS.get(resolution["type"], {})
    effects = resolution_info.get("effects", {})
    
    if "un_effects" not in target:
        target["un_effects"] = []
    
    target["un_effects"].append({
        "type": resolution["type"],
        "name": resolution_info["name_fa"],
        "applied_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=resolution_info.get("duration", 0))).isoformat(),
        "effects": effects
    })


def get_active_un_effects(state: Dict[str, Any], country_key: str) -> Dict[str, Any]:
    """دریافت اثرات فعال سازمان ملل روی یک کشور"""
    target = state["countries"].get(country_key, {})
    un_effects = target.get("un_effects", [])
    now = datetime.now()
    active_effects = {}
    
    for effect in un_effects:
        expires_at = effect.get("expires_at")
        if expires_at:
            expires = datetime.fromisoformat(expires_at)
            if expires <= now:
                continue
        
        eff = effect.get("effects", {})
        for key, value in eff.items():
            active_effects[key] = value
    
    return active_effects


# ==================== دستورات سازمان ملل ====================

def handle_propose_resolution(state: Dict[str, Any], user_id: str, args: str) -> str:
    """دستور /propose_resolution [کشور] [نوع] [دلیل]"""
    parts = args.strip().split(maxsplit=2)
    if len(parts) < 3:
        return """❌ فرمت صحیح: `/propose_resolution [کشور] [نوع] [دلیل]`

انواع قطعنامه:
• economic_sanction - تحریم اقتصادی جهانی (شورای امنیت)
• weapon_embargo - تحریم تسلیحاتی جهانی (شورای امنیت)
• ceasefire - آتش‌بس اجباری (شورای امنیت)
• condemnation - محکومیت رسمی (مجمع عمومی)
• aid_call - فراخوان کمک (مجمع عمومی)
• suspension - تعلیق عضویت (مجمع عمومی، دو سوم آرا)

مثال: `/propose_resolution آلمان economic_sanction استفاده از سلاح هسته‌ای`
"""
    
    target_name = parts[0]
    resolution_type = parts[1]
    reason = parts[2]
    
    target_id = get_user_by_country(state, target_name)
    if not target_id:
        return f"❌ کشور '{target_name}' یافت نشد."
    
    if resolution_type not in RESOLUTIONS:
        return f"❌ نوع قطعنامه نامعتبر. انتخاب‌ها: {', '.join(RESOLUTIONS.keys())}"
    
    success, msg = propose_resolution(state, user_id, target_id, resolution_type, reason)
    if success:
        save_game_state(state)
    return msg


def handle_vote(state: Dict[str, Any], user_id: str, args: str) -> str:
    """دستور /vote [resolution_id] [yes/no/abstain]"""
    parts = args.strip().split()
    if len(parts) < 2:
        return "❌ فرمت صحیح: `/vote [resolution_id] [yes/no/abstain]`\nبرای مشاهده قطعنامه‌های فعال: `/resolutions`"
    
    resolution_id = parts[0]
    vote = parts[1].lower()
    
    success, msg = vote_on_resolution(state, user_id, resolution_id, vote)
    if success:
        save_game_state(state)
    return msg


def handle_resolutions(state: Dict[str, Any], user_id: str) -> str:
    """دستور /resolutions - نمایش قطعنامه‌های فعال"""
    resolutions = state.get("un", {}).get("resolutions", [])
    active = [r for r in resolutions if r.get("status") == "voting"]
    
    if not active:
        return "📋 هیچ قطعنامه فعالی در حال رأی‌گیری نیست."
    
    msg = "📜 *قطعنامه‌های فعال در حال رأی‌گیری*\n\n"
    for r in active:
        expires = datetime.fromisoformat(r["expires_at"])
        hours_left = int((expires - datetime.now()).total_seconds() / 3600)
        msg += f"• {r['name_fa']}\n"
        msg += f"  ID: `{r['id']}`\n"
        msg += f"  علیه: {r['target_name']}\n"
        msg += f"  مهلت: {hours_left} ساعت باقی‌مانده\n"
        msg += f"  موافق: {len(r['votes_yes'])} | مخالف: {len(r['votes_no'])} | ممتنع: {len(r['votes_abstain'])}\n\n"
    
    return msg


def handle_un_help() -> str:
    """راهنمای سازمان ملل"""
    return """
🇺🇳 *سازمان ملل متحد*

*ساختار:*
• شورای امنیت: 5 عضو دائم (آمریکا، روسیه، چین، انگلیس، فرانسه) + 4 عضو متغیر
• مجمع عمومی: همه 24 کشور

*انواع قطعنامه:*

*شورای امنیت (نیاز 9 رأی، قابل وتو):*
• economic_sanction - تحریم اقتصادی جهانی (-50% درآمد)
• weapon_embargo - تحریم تسلیحاتی جهانی
• ceasefire - آتش‌بس اجباری

*مجمع عمومی (اکثریت ساده یا دو سوم):*
• condemnation - محکومیت رسمی (-10 پرستیژ، -2 دیپلماسی)
• aid_call - فراخوان کمک (20% تخفیف کمک)
• suspension - تعلیق عضویت (30 روز محرومیت)

*دستورات:*
/propose_resolution [کشور] [نوع] [دلیل] - طرح قطعنامه
/vote [resolution_id] [yes/no/abstain] - رأی‌گیری
/resolutions - نمایش قطعنامه‌های فعال
"""


def get_user_by_country(state: Dict[str, Any], country_name: str) -> Optional[str]:
    for country_key, player in state.get("countries", {}).items():
        if player.get("name_fa") == country_name or player.get("name_en") == country_name:
            return player.get("user_id")
    return None


def handle_election_secretary_general(state: Dict[str, Any], user_id: str, args: str) -> str:
    """دستور /elect_sg [کشور] - نامزدی دبیرکل"""
    if not args.strip():
        return "❌ لطفاً نام کشور را وارد کنید. مثال: `/elect_sg آلمان`"
    
    # فقط ادمین می‌تواند انتخابات برگزار کند
    # (در implementation واقعی نیاز به بررسی ادمین دارد)
    
    return "✅ انتخابات دبیرکل برگزار شد. نتایج به زودی اعلام می‌شود."


if __name__ == "__main__":
    print("UN system module loaded")
