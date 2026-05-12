#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بازی جنگ جهانی: رمز و فرماندهی
هندلر اصلی بات بله - نسخه کامل با همه سیستم‌ها
"""

import json
import os
import requests
import base64
import time
from datetime import datetime
from typing import Dict, Any, Optional

# ==================== import ماژول‌ها ====================
from admin_system import handle_admin_command, is_admin, admin_commands_list, get_speed_multiplier
from war_system import (
    declare_war, deploy_forces, get_war_status, propose_peace,
    get_war_details_for_admin, calculate_total_power_with_abilities
)
from economy_system import (
    buy_unit, sell_unit, upgrade_stat, research_tech,
    get_inventory, get_daily_income
)
from alliance_system import (
    propose_treaty, accept_treaty, reject_treaty, break_treaty,
    get_treaties_list, get_pending_treaties, share_technology,
    get_alliance_help
)
from sanction_system import (
    impose_sanction, remove_sanction, get_sanctions_list,
    get_imposed_sanctions, counter_sanction, get_sanctions_help
)
from map_system import (
    get_region_info, get_distance_to_country, get_world_overview, get_map_help
)
from construction_system import (
    build_structure, upgrade_structure, demolish_structure,
    get_available_structures, get_infrastructure_status,
    upgrade_infrastructure, get_construction_help
)
from disaster_system import (
    buy_insurance, evacuate_units, return_evacuated,
    get_warning, get_disaster_help
)
from market_system import (
    get_market_prices, place_buy_order, place_sell_order,
    cancel_order, get_auction, place_bid, get_market_help
)
from un_system import (
    propose_resolution, vote_on_resolution, get_resolutions,
    get_un_help
)

# ==================== تنظیمات ====================

BALE_TOKEN = os.environ.get("BALE_TOKEN", "")
GH_TOKEN = os.environ.get("GH_TOKEN", "")
REPO_OWNER = os.environ.get("REPO_OWNER", "")
REPO_NAME = os.environ.get("REPO_NAME", "")
GCC_CHAT_ID = os.environ.get("GCC_CHAT_ID", "")

GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/game_state.json"
BALE_API_URL = f"https://tapi.bale.ai/bot{BALE_TOKEN}"

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
        
        payload = {"message": f"[bot] {datetime.now().isoformat()}", "content": encoded, "sha": current_sha}
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


def get_user_data(state: Dict[str, Any], user_id: str) -> Optional[Dict[str, Any]]:
    for country_key, player in state.get("countries", {}).items():
        if player.get("user_id") == user_id:
            return player
    return None


def get_country_key_by_user(state: Dict[str, Any], user_id: str) -> Optional[str]:
    for country_key, player in state.get("countries", {}).items():
        if player.get("user_id") == user_id:
            return country_key
    return None


def get_star_display(experience: int) -> str:
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


# ==================== دستورات اصلی ====================

def handle_start(state: Dict[str, Any], user_id: str) -> str:
    existing = get_user_data(state, user_id)
    if existing:
        return f"❌ شما قبلاً به عنوان {existing.get('name_fa', '')} وارد شده‌اید.\nوضعیت: /status"
    
    for country_key, country_data in state.get("countries", {}).items():
        if country_data.get("user_id") is None:
            country_data["user_id"] = user_id
            country_data["last_login"] = datetime.now().isoformat()
            save_game_state(state)
            return f"""
✅ شما به عنوان {country_data['name_fa']} وارد بازی شدید!

📊 وضعیت اولیه:
• صنعت: {country_data['industry']}
• تجارت: {country_data['trade']}
• دیپلماسی: {country_data['diplomacy']}
• ثبات: {country_data['stability']}

💰 منابع اولیه:
• نفوذ: {country_data['resources']['influence']}
• فناوری: {country_data['resources']['tech_points']}
• مهمات: {country_data['resources']['ammo']}
• سوخت: {country_data['resources']['fuel']}

برای مشاهده وضعیت کامل: /status
"""
    return "❌ همه کشورها پر شده‌اند. منتظر دور بعدی باشید."


def handle_status(state: Dict[str, Any], user_id: str) -> str:
    player = get_user_data(state, user_id)
    if not player:
        return "❌ شما کشوری انتخاب نکرده‌اید. /start"
    
    name = player.get("name_fa", "ناشناس")
    flag = player.get("flag", "")
    industry = player.get("industry", 0)
    trade = player.get("trade", 0)
    diplomacy = player.get("diplomacy", 0)
    stability = player.get("stability", 5)
    approval = player.get("approval", 5)
    corruption = player.get("corruption", 3)
    
    resources = player.get("resources", {})
    influence = resources.get("influence", 0)
    tech = resources.get("tech_points", 0)
    ammo = resources.get("ammo", 0)
    fuel = resources.get("fuel", 0)
    prestige = resources.get("prestige", 0)
    
    daily_income = get_daily_income(player)
    
    industry_bar = "█" * min(industry, 10) + "░" * (10 - min(industry, 10))
    trade_bar = "█" * min(trade, 10) + "░" * (10 - min(trade, 10))
    
    military_power, _, _ = calculate_total_power_with_abilities(player)
    
    return f"""
📊 *وضعیت {flag} {name}*

━━━━━━━━━━━━━━━━━━━━━
🏭 *صنعت:* {industry_bar} ({industry}/10)
💰 *تجارت:* {trade_bar} ({trade}/10)
🤝 *دیپلماسی:* {diplomacy}/10
📈 *ثبات:* {stability}/10 | 😊 رضایت: {approval}/10 | 💀 فساد: {corruption}/10

━━━━━━━━━━━━━━━━━━━━━
💰 *منابع:*
• نفوذ: {influence} (+{daily_income}/روز)
• فناوری: {tech}
• مهمات: {ammo} | سوخت: {fuel}
• پرستیژ: {prestige}

⚔️ *قدرت نظامی:* {military_power}

━━━━━━━━━━━━━━━━━━━━━
📝 *دستورات مفید:*
/buy - خرید تجهیزات
/upgrade - ارتقاء شاخص‌ها
/inventory - لیست تجهیزات
/attack [کشور] - اعلان جنگ
/ally - مدیریت اتحادها
/sanction - مدیریت تحریم‌ها
/market - بازار خرید و فروش
"""


def handle_help(user_id: str) -> str:
    help_text = """
📚 *راهنمای بازی جنگ جهانی: رمز و فرماندهی*

━━━━━━━━━━━━━━━━━━━━━
*دستورات پایه:*
/start - شروع بازی
/status - وضعیت کشور
/help - راهنما

━━━━━━━━━━━━━━━━━━━━━
*اقتصاد و ارتقاء:*
/upgrade [industry/trade/diplomacy] - ارتقاء
/buy [نام] [تعداد] - خرید تجهیزات
/sell [نام] [تعداد] - فروش تجهیزات
/inventory - لیست تجهیزات
/research [شاخه] [سطح] - تحقیق فناوری

━━━━━━━━━━━━━━━━━━━━━
*نظامی و جنگ:*
/attack [کشور] - اعلان جنگ
/deploy - استقرار نیرو
/war_status - وضعیت جنگ فعال
/peace [کشور] - پیشنهاد صلح

━━━━━━━━━━━━━━━━━━━━━
*اتحاد و دیپلماسی:*
/propose_treaty [کشور] [type] - پیشنهاد اتحاد
/accept_treaty [کشور] - پذیرش اتحاد
/reject_treaty [کشور] - رد اتحاد
/break_treaty [کشور] - لغو اتحاد
/my_treaties - قراردادهای من
/pending_treaties - پیشنهادهای دریافتی
/share_tech [کشور] [شاخه] [سطح] - اشتراک فناوری

━━━━━━━━━━━━━━━━━━━━━
*تحریم‌ها:*
/sanction [کشور] [type] - اعمال تحریم
/remove_sanction [کشور] [type] - لغو تحریم
/my_sanctions - تحریم‌های علیه من
/imposed_sanctions - تحریم‌های اعمال شده
/counter_sanction [کشور] - تحریم متقابل

━━━━━━━━━━━━━━━━━━━━━
*بازار و تجارت:*
/market - قیمت‌های بازار
/buy_from_market [نام] [تعداد] - خرید از بازار
/sell_to_market [نام] [تعداد] - فروش در بازار
/auction - حراج روزانه
/bid [id] [قیمت] - پیشنهاد در حراج

━━━━━━━━━━━━━━━━━━━━━
*ساخت و ساز:*
/build [نوع] [سطح] - ساخت سازه
/upgrade_structure [id] - ارتقاء سازه
/structures - سازه‌های من
/infrastructure - زیرساخت‌ها
/upgrade_infra [نوع] - ارتقاء زیرساخت

━━━━━━━━━━━━━━━━━━━━━
*پیشگیری و بلا:*
/buy_insurance - خرید بیمه
/evacuate [نوع] [تعداد] - تخلیه تجهیزات
/warning - هشدار بلایا

━━━━━━━━━━━━━━━━━━━━━
*سازمان ملل:*
/propose_resolution [کشور] [نوع] [دلیل] - طرح قطعنامه
/vote [id] [yes/no/abstain] - رأی‌گیری
/resolutions - قطعنامه‌های فعال

━━━━━━━━━━━━━━━━━━━━━
*سایر:*
/region - موقعیت جغرافیایی
/distance [کشور] - فاصله تا کشور
/rank - جدول رتبه‌بندی
/mission - مأموریت رمزنگاری
/solve [پاسخ] - حل مأموریت
"""
    if is_admin(user_id):
        help_text += admin_commands_list()
    
    return help_text


# ==================== پردازش اصلی ====================

def process_update(update: Dict[str, Any]) -> Optional[str]:
    message = update.get("message", {})
    if not message:
        return None
    
    chat_id = str(message.get("chat", {}).get("id", ""))
    text = message.get("text", "").strip()
    user_id = str(message.get("from", {}).get("id", ""))
    
    if not text:
        return None
    
    state = load_game_state()
    if not state:
        return "❌ خطا در بارگذاری بازی"
    
    # به‌روزرسانی آخرین ورود
    country_key = get_country_key_by_user(state, user_id)
    if country_key:
        state["countries"][country_key]["last_login"] = datetime.now().isoformat()
    
    response = None
    
    # ========== دستورات پایه ==========
    if text.startswith("/start"):
        response = handle_start(state, user_id)
    elif text.startswith("/status"):
        response = handle_status(state, user_id)
    elif text.startswith("/help"):
        response = handle_help(user_id)
    
    # ========== اقتصاد ==========
    elif text.startswith("/buy"):
        response = handle_buy(state, user_id, text[4:].strip())
    elif text.startswith("/sell"):
        response = handle_sell(state, user_id, text[5:].strip())
    elif text.startswith("/inventory"):
        response = handle_inventory(state, user_id)
    elif text.startswith("/upgrade"):
        response = handle_upgrade(state, user_id, text[8:].strip())
    elif text.startswith("/research"):
        response = handle_research(state, user_id, text[9:].strip())
    
    # ========== جنگ ==========
    elif text.startswith("/attack"):
        response = handle_attack(state, user_id, text[7:].strip())
    elif text.startswith("/deploy"):
        response = handle_deploy(state, user_id, text[7:].strip())
    elif text.startswith("/war_status"):
        response = handle_war_status(state, user_id)
    elif text.startswith("/peace"):
        response = handle_peace(state, user_id, text[6:].strip())
    
    # ========== اتحادها ==========
    elif text.startswith("/propose_treaty"):
        response = handle_propose_treaty(state, user_id, text[15:].strip())
    elif text.startswith("/accept_treaty"):
        response = handle_accept_treaty(state, user_id, text[14:].strip())
    elif text.startswith("/reject_treaty"):
        response = handle_reject_treaty(state, user_id, text[14:].strip())
    elif text.startswith("/break_treaty"):
        response = handle_break_treaty(state, user_id, text[13:].strip())
    elif text.startswith("/my_treaties"):
        response = handle_my_treaties(state, user_id)
    elif text.startswith("/pending_treaties"):
        response = handle_pending_treaties(state, user_id)
    elif text.startswith("/share_tech"):
        response = handle_share_tech(state, user_id, text[11:].strip())
    
    # ========== تحریم‌ها ==========
    elif text.startswith("/sanction"):
        response = handle_impose_sanction(state, user_id, text[9:].strip())
    elif text.startswith("/remove_sanction"):
        response = handle_remove_sanction(state, user_id, text[16:].strip())
    elif text.startswith("/my_sanctions"):
        response = handle_my_sanctions(state, user_id)
    elif text.startswith("/imposed_sanctions"):
        response = handle_imposed_sanctions(state, user_id)
    elif text.startswith("/counter_sanction"):
        response = handle_counter_sanction(state, user_id, text[17:].strip())
    
    # ========== بازار ==========
    elif text.startswith("/market"):
        response = handle_market(state, user_id)
    elif text.startswith("/buy_from_market"):
        response = handle_buy_from_market(state, user_id, text[17:].strip())
    elif text.startswith("/sell_to_market"):
        response = handle_sell_to_market(state, user_id, text[16:].strip())
    elif text.startswith("/cancel_order"):
        response = handle_cancel_order(state, user_id, text[14:].strip())
    elif text.startswith("/auction"):
        response = handle_auction(state, user_id)
    elif text.startswith("/bid"):
        response = handle_bid(state, user_id, text[4:].strip())
    
    # ========== ساخت و ساز ==========
    elif text.startswith("/build"):
        response = handle_build(state, user_id, text[6:].strip())
    elif text.startswith("/upgrade_structure"):
        response = handle_upgrade_structure(state, user_id, text[18:].strip())
    elif text.startswith("/demolish"):
        response = handle_demolish(state, user_id, text[9:].strip())
    elif text.startswith("/structures"):
        response = handle_structures(state, user_id)
    elif text.startswith("/infrastructure"):
        response = handle_infrastructure(state, user_id)
    elif text.startswith("/upgrade_infra"):
        response = handle_upgrade_infra(state, user_id, text[14:].strip())
    
    # ========== بلایا ==========
    elif text.startswith("/buy_insurance"):
        response = handle_buy_insurance(state, user_id)
    elif text.startswith("/evacuate"):
        response = handle_evacuate(state, user_id, text[9:].strip())
    elif text.startswith("/return_evacuated"):
        response = handle_return_evacuated(state, user_id)
    elif text.startswith("/warning"):
        response = handle_warning(state, user_id)
    
    # ========== نقشه ==========
    elif text.startswith("/region"):
        response = handle_region(state, user_id)
    elif text.startswith("/distance"):
        response = handle_distance(state, user_id, text[9:].strip())
    elif text.startswith("/world_map"):
        response = handle_world_map(state, user_id)
    
    # ========== سازمان ملل ==========
    elif text.startswith("/propose_resolution"):
        response = handle_propose_resolution(state, user_id, text[19:].strip())
    elif text.startswith("/vote"):
        response = handle_vote(state, user_id, text[5:].strip())
    elif text.startswith("/resolutions"):
        response = handle_resolutions(state, user_id)
    
    # ========== سایر ==========
    elif text.startswith("/rank"):
        response = handle_rank(state, user_id)
    elif text.startswith("/mission"):
        response = handle_mission(state, user_id)
    elif text.startswith("/solve"):
        response = handle_solve(state, user_id, text[6:].strip())
    
    # ========== دستورات ادمین ==========
    elif text.startswith("/set_speed"):
        handle_admin_command(user_id, "set_speed", text[10:].strip(), chat_id)
        return None
    elif text.startswith("/game_speed"):
        handle_admin_command(user_id, "game_speed", "", chat_id)
        return None
    elif text.startswith("/all_stats"):
        handle_admin_command(user_id, "all_stats", "", chat_id)
        return None
    elif text.startswith("/player_stats"):
        handle_admin_command(user_id, "player_stats", text[13:].strip(), chat_id)
        return None
    elif text.startswith("/add_influence"):
        handle_admin_command(user_id, "add_influence", text[14:].strip(), chat_id)
        return None
    elif text.startswith("/admin_help"):
        handle_admin_command(user_id, "admin_help", "", chat_id)
        return None
    elif text.startswith("/war_details"):
        if is_admin(user_id):
            response = get_war_details_for_admin(state)
        else:
            response = "❌ شما دسترسی ادمین ندارید."
    
    else:
        response = f"❌ دستور '{text}' شناسایی نشد.\n/help"
    
    save_game_state(state)
    return response


# ==================== توابع هندلر ساده ====================

def handle_buy(state, user_id, args):
    from economy_system import buy_unit
    parts = args.strip().split()
    if len(parts) < 2:
        return "❌ فرمت: `/buy [نام] [تعداد]`"
    try:
        count = int(parts[1])
    except:
        return "❌ تعداد باید عدد باشد."
    success, msg = buy_unit(state, user_id, parts[0], count)
    return msg if success else msg


def handle_sell(state, user_id, args):
    from economy_system import sell_unit
    parts = args.strip().split()
    if len(parts) < 2:
        return "❌ فرمت: `/sell [نام] [تعداد]`"
    try:
        count = int(parts[1])
    except:
        return "❌ تعداد باید عدد باشد."
    success, msg = sell_unit(state, user_id, parts[0], count)
    return msg if success else msg


def handle_inventory(state, user_id):
    from economy_system import get_inventory
    return get_inventory(state, user_id)


def handle_upgrade(state, user_id, args):
    from economy_system import upgrade_stat
    if not args.strip():
        return "❌ فرمت: `/upgrade [industry/trade/diplomacy]`"
    success, msg = upgrade_stat(state, user_id, args.strip())
    return msg if success else msg


def handle_research(state, user_id, args):
    from economy_system import research_tech
    parts = args.strip().split()
    if len(parts) < 2:
        return "❌ فرمت: `/research [شاخه] [سطح]`"
    try:
        level = int(parts[1])
    except:
        return "❌ سطح باید عدد باشد."
    success, msg = research_tech(state, user_id, parts[0], level)
    return msg if success else msg


def handle_attack(state, user_id, args):
    from war_system import declare_war
    if not args.strip():
        return "❌ فرمت: `/attack [کشور]`"
    success, msg = declare_war(state, user_id, args.strip())
    return msg if success else msg


def handle_deploy(state, user_id, args):
    from war_system import deploy_forces
    success, msg = deploy_forces(state, user_id, args)
    return msg if success else msg


def handle_war_status(state, user_id):
    from war_system import get_war_status
    return get_war_status(state, user_id)


def handle_peace(state, user_id, args):
    from war_system import propose_peace
    success, msg = propose_peace(state, user_id, args)
    return msg if success else msg


def handle_propose_treaty(state, user_id, args):
    from alliance_system import propose_treaty
    parts = args.strip().split()
    if len(parts) < 2:
        return get_alliance_help()
    success, msg = propose_treaty(state, user_id, parts[0], parts[1])
    return msg if success else msg


def handle_accept_treaty(state, user_id, args):
    from alliance_system import accept_treaty
    if not args.strip():
        return "❌ فرمت: `/accept_treaty [کشور]`"
    success, msg = accept_treaty(state, user_id, args.strip())
    return msg if success else msg


def handle_reject_treaty(state, user_id, args):
    from alliance_system import reject_treaty
    if not args.strip():
        return "❌ فرمت: `/reject_treaty [کشور]`"
    success, msg = reject_treaty(state, user_id, args.strip())
    return msg if success else msg


def handle_break_treaty(state, user_id, args):
    from alliance_system import break_treaty
    if not args.strip():
        return "❌ فرمت: `/break_treaty [کشور] [mutual]`"
    parts = args.strip().split()
    mutual = len(parts) > 1 and parts[1].lower() == "mutual"
    success, msg = break_treaty(state, user_id, parts[0], mutual)
    return msg if success else msg


def handle_my_treaties(state, user_id):
    from alliance_system import get_treaties_list
    return get_treaties_list(state, user_id)


def handle_pending_treaties(state, user_id):
    from alliance_system import get_pending_treaties
    return get_pending_treaties(state, user_id)


def handle_share_tech(state, user_id, args):
    from alliance_system import share_technology
    parts = args.strip().split()
    if len(parts) < 3:
        return "❌ فرمت: `/share_tech [کشور] [شاخه] [سطح]`"
    try:
        level = int(parts[2])
    except:
        return "❌ سطح باید عدد باشد."
    success, msg = share_technology(state, user_id, parts[0], parts[1], level)
    return msg if success else msg


def handle_impose_sanction(state, user_id, args):
    from sanction_system import impose_sanction
    parts = args.strip().split()
    if len(parts) < 2:
        return get_sanctions_help()
    success, msg = impose_sanction(state, user_id, parts[0], parts[1])
    return msg if success else msg


def handle_remove_sanction(state, user_id, args):
    from sanction_system import remove_sanction
    parts = args.strip().split()
    if len(parts) < 2:
        return "❌ فرمت: `/remove_sanction [کشور] [نوع]`"
    success, msg = remove_sanction(state, user_id, parts[0], parts[1])
    return msg if success else msg


def handle_my_sanctions(state, user_id):
    from sanction_system import get_sanctions_list
    return get_sanctions_list(state, user_id)


def handle_imposed_sanctions(state, user_id):
    from sanction_system import get_imposed_sanctions
    return get_imposed_sanctions(state, user_id)


def handle_counter_sanction(state, user_id, args):
    from sanction_system import counter_sanction
    if not args.strip():
        return "❌ فرمت: `/counter_sanction [کشور]`"
    success, msg = counter_sanction(state, user_id, args.strip())
    return msg if success else msg


def handle_market(state, user_id):
    from market_system import get_market_prices
    return get_market_prices(state, user_id)


def handle_buy_from_market(state, user_id, args):
    from market_system import place_buy_order
    parts = args.strip().split()
    if len(parts) < 2:
        return "❌ فرمت: `/buy_from_market [نام] [تعداد]`"
    try:
        count = int(parts[1])
    except:
        return "❌ تعداد باید عدد باشد."
    price = int(parts[2]) if len(parts) > 2 else None
    success, msg = place_buy_order(state, user_id, parts[0], count, price)
    return msg if success else msg


def handle_sell_to_market(state, user_id, args):
    from market_system import place_sell_order
    parts = args.strip().split()
    if len(parts) < 2:
        return "❌ فرمت: `/sell_to_market [نام] [تعداد]`"
    try:
        count = int(parts[1])
    except:
        return "❌ تعداد باید عدد باشد."
    price = int(parts[2]) if len(parts) > 2 else None
    success, msg = place_sell_order(state, user_id, parts[0], count, price)
    return msg if success else msg


def handle_cancel_order(state, user_id, args):
    from market_system import cancel_order
    if not args.strip():
        return "❌ فرمت: `/cancel_order [id]`"
    success, msg = cancel_order(state, user_id, args.strip())
    return msg if success else msg


def handle_auction(state, user_id):
    from market_system import get_auction
    return get_auction(state, user_id)


def handle_bid(state, user_id, args):
    from market_system import place_bid
    parts = args.strip().split()
    if len(parts) < 2:
        return "❌ فرمت: `/bid [id] [قیمت]`"
    try:
        price = int(parts[1])
    except:
        return "❌ قیمت باید عدد باشد."
    success, msg = place_bid(state, user_id, parts[0], price)
    return msg if success else msg


def handle_build(state, user_id, args):
    from construction_system import build_structure
    parts = args.strip().split()
    if len(parts) < 1:
        return get_construction_help()
    level = int(parts[1]) if len(parts) > 1 else 1
    success, msg = build_structure(state, user_id, parts[0], level)
    return msg if success else msg


def handle_upgrade_structure(state, user_id, args):
    from construction_system import upgrade_structure
    if not args.strip():
        return "❌ فرمت: `/upgrade_structure [id]`"
    success, msg = upgrade_structure(state, user_id, args.strip())
    return msg if success else msg


def handle_demolish(state, user_id, args):
    from construction_system import demolish_structure
    if not args.strip():
        return "❌ فرمت: `/demolish [id]`"
    success, msg = demolish_structure(state, user_id, args.strip())
    return msg if success else msg


def handle_structures(state, user_id):
    from construction_system import get_available_structures
    return get_available_structures(state, user_id)


def handle_infrastructure(state, user_id):
    from construction_system import get_infrastructure_status
    return get_infrastructure_status(state, user_id)


def handle_upgrade_infra(state, user_id, args):
    from construction_system import upgrade_infrastructure
    if not args.strip():
        return "❌ فرمت: `/upgrade_infra [نوع]`"
    success, msg = upgrade_infrastructure(state, user_id, args.strip())
    return msg if success else msg


def handle_buy_insurance(state, user_id):
    from disaster_system import buy_insurance
    success, msg = buy_insurance(state, user_id)
    return msg if success else msg


def handle_evacuate(state, user_id, args):
    from disaster_system import evacuate_units
    parts = args.strip().split()
    if len(parts) < 2:
        return "❌ فرمت: `/evacuate [نوع] [تعداد]`"
    try:
        count = int(parts[1])
    except:
        return "❌ تعداد باید عدد باشد."
    success, msg = evacuate_units(state, user_id, parts[0], count)
    return msg if success else msg


def handle_return_evacuated(state, user_id):
    from disaster_system import return_evacuated
    success, msg = return_evacuated(state, user_id)
    return msg if success else msg


def handle_warning(state, user_id):
    from disaster_system import get_warning
    return get_warning(state, user_id)


def handle_region(state, user_id):
    from map_system import get_region_info
    return get_region_info(state, user_id)


def handle_distance(state, user_id, args):
    from map_system import get_distance_to_country
    if not args.strip():
        return "❌ فرمت: `/distance [کشور]`"
    return get_distance_to_country(state, user_id, args.strip())


def handle_world_map(state, user_id):
    from map_system import get_world_overview
    return get_world_overview(state, user_id)


def handle_propose_resolution(state, user_id, args):
    from un_system import propose_resolution
    parts = args.strip().split(maxsplit=2)
    if len(parts) < 3:
        return get_un_help()
    target = get_user_by_country(state, parts[0])
    if not target:
        return f"❌ کشور '{parts[0]}' یافت نشد."
    success, msg = propose_resolution(state, user_id, target, parts[1], parts[2])
    return msg if success else msg


def handle_vote(state, user_id, args):
    from un_system import vote_on_resolution
    parts = args.strip().split()
    if len(parts) < 2:
        return "❌ فرمت: `/vote [id] [yes/no/abstain]`"
    success, msg = vote_on_resolution(state, user_id, parts[0], parts[1])
    return msg if success else msg


def handle_resolutions(state, user_id):
    from un_system import get_resolutions
    return get_resolutions(state, user_id)


def handle_rank(state, user_id):
    players = state.get("countries", {})
    rankings = []
    for country_key, player in players.items():
        if player.get("user_id") is None:
            continue
        name = player.get("name_fa", country_key)
        prestige = player.get("resources", {}).get("prestige", 0)
        rankings.append((name, prestige))
    rankings.sort(key=lambda x: x[1], reverse=True)
    
    msg = "🏆 *جدول پرستیژ*\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, (name, prestige) in enumerate(rankings[:10], 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        msg += f"{medal} {name}: {prestige} پرستیژ\n"
    return msg


def handle_mission(state, user_id):
    mission = state.get("daily_mission", {})
    if not mission.get("cipher"):
        return "❌ مأموریت امروز هنوز منتشر نشده است."
    return f"""
🕵️ *مأموریت رمزنگاری روز {state.get('game_day', 0)}*

رمز: `{mission.get('cipher', '')}`

سطح: {mission.get('level', 1)}
راهنما: {mission.get('hint', '')}

پاسخ را با `/solve [پاسخ]` ارسال کنید.

🏆 جوایز: اول: 30 نفوذ + 80 فناوری
⏰ مهلت: تا فردا ساعت 8 صبح
"""


def handle_solve(state, user_id, args):
    if not args.strip():
        return "❌ لطفاً پاسخ را وارد کنید."
    
    player = get_user_data(state, user_id)
    if not player:
        return "❌ شما کشوری انتخاب نکرده‌اید."
    
    mission = state.get("daily_mission", {})
    answer = mission.get("answer", "").upper()
    user_answer = args.strip().upper()
    
    if user_answer != answer:
        return "❌ پاسخ نادرست است."
    
    solved_by = mission.get("solved_by", [])
    for solver in solved_by:
        if solver.get("user_id") == user_id:
            return "❌ شما قبلاً این مأموریت را حل کرده‌اید."
    
    rank = len(solved_by) + 1
    if rank > 3:
        return "❌ سه نفر اول قبلاً پاسخ داده‌اند."
    
    rewards = {1: (30, 80), 2: (20, 50), 3: (10, 30)}
    influence_reward, tech_reward = rewards[rank]
    
    player["resources"]["influence"] = player["resources"].get("influence", 0) + influence_reward
    player["resources"]["tech_points"] = player["resources"].get("tech_points", 0) + tech_reward
    
    solved_by.append({"user_id": user_id, "name": player.get("name_fa"), "rank": rank})
    
    save_game_state(state)
    send_to_gcc(f"🎉 {player.get('name_fa')} رتبه {rank} مأموریت رمزنگاری را کسب کرد!")
    
    return f"✅ پاسخ صحیح! رتبه {rank} - پاداش: {influence_reward} نفوذ + {tech_reward} فناوری"


def get_user_by_country(state, country_name):
    for country_key, player in state.get("countries", {}).items():
        if player.get("name_fa") == country_name or player.get("name_en") == country_name:
            return player.get("user_id")
    return None


# ==================== اجرای اصلی ====================

def main():
    print("Bot started. Waiting for updates...")
    last_update_id = 0
    
    while True:
        try:
            params = {"timeout": 30, "offset": last_update_id + 1}
            response = requests.get(f"{BALE_API_URL}/getUpdates", params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok") and data.get("result"):
                    for update in data["result"]:
                        update_id = update.get("update_id", 0)
                        if update_id > last_update_id:
                            last_update_id = update_id
                            reply = process_update(update)
                            if reply:
                                chat_id = update.get("message", {}).get("chat", {}).get("id")
                                if chat_id:
                                    send_message(str(chat_id), reply)
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(1)


if __name__ == "__main__":
    main()
