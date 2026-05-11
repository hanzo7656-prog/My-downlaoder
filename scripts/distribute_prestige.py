#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
توزیع پاداش پرستیژ به بازیکنان برتر و رویدادهای خاص
هر روز ساعت 12 اجرا می‌شود (توسط GitHub Actions)

منابع پرستیژ:
- رتبه 1 جدول پتانسیل: +20
- رتبه 2 جدول: +10
- رتبه 3 جدول: +5
- پیروزی در جنگ: +10 تا +50 (بسته به تعداد بخش‌های تصرف شده)
- حل مأموریت رمزنگاری: +5 (اولین نفر)
- ساخت بمب هسته‌ای: +50
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
            "message": f"[auto] prestige {datetime.now().strftime('%Y-%m-%d')}",
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


def add_prestige(player: Dict[str, Any], amount: int, reason: str, state: Dict[str, Any]):
    """اضافه کردن پرستیژ به یک کشور و ثبت لاگ"""
    if "resources" not in player:
        player["resources"] = {}
    
    old = player["resources"].get("prestige", 0)
    player["resources"]["prestige"] = old + amount
    
    # ثبت لاگ
    if "logs" not in state:
        state["logs"] = []
    state["logs"].append({
        "timestamp": datetime.now().isoformat(),
        "type": "prestige",
        "message": f"{player.get('name_fa', 'نامشخص')}: +{amount} پرستیژ ({reason})"
    })
    
    print(f"Added {amount} prestige to {player.get('name_fa')} - {reason}")
    return player["resources"]["prestige"]


def calculate_military_power(player: Dict[str, Any]) -> int:
    """محاسبه قدرت نظامی بر اساس تجهیزات (ساده شده)"""
    units = player.get("units", {})
    total_power = 0
    
    unit_powers = {
        "air": 50, "ground": 30, "naval": 40,
        "destroyer": 35, "submarine": 45, "carrier": 70,
        "artillery": 20, "air_defense": 40
    }
    
    for category, power in unit_powers.items():
        for unit in units.get(category, []):
            total_power += power * unit.get("count", 0) * (unit.get("health", 100) / 100)
    
    return total_power


def calculate_potential(player: Dict[str, Any]) -> int:
    """محاسبه پتانسیل کلی کشور"""
    industry = player.get("industry", 0)
    trade = player.get("trade", 0)
    diplomacy = player.get("diplomacy", 0)
    stability = player.get("stability", 5)
    military_power = calculate_military_power(player) // 10
    
    return (industry * 3) + (int(trade * 2.5)) + (military_power * 2) + diplomacy + stability


# ==================== توزیع پاداش رتبه‌بندی ====================

def distribute_rankings_prestige(state: Dict[str, Any]) -> List[Tuple[str, int]]:
    """
    توزیع پاداش پرستیژ بر اساس رتبه‌بندی پتانسیل
    بازگشت: لیست (نام کشور، پاداش دریافتی)
    """
    players = state.get("countries", {})
    rankings = []
    
    # محاسبه پتانسیل همه
    for country_key, player in players.items():
        if player.get("user_id") is None:
            continue
        potential = calculate_potential(player)
        rankings.append((country_key, player.get("name_fa", country_key), potential))
    
    # مرتب‌سازی
    rankings.sort(key=lambda x: x[2], reverse=True)
    
    rewards = {0: 20, 1: 10, 2: 5}  # رتبه 1, 2, 3
    distributed = []
    
    for i, (country_key, name, potential) in enumerate(rankings[:3]):
        reward = rewards.get(i, 0)
        if reward > 0:
            player = players.get(country_key)
            if player:
                add_prestige(player, reward, f"رتبه {i+1} جدول پتانسیل", state)
                distributed.append((name, reward))
    
    return distributed


# ==================== توزیع پاداش پیروزی در جنگ ====================

def distribute_war_prestige(state: Dict[str, Any]) -> List[Tuple[str, int]]:
    """
    توزیع پاداش پرستیژ برای پیروزی در جنگ‌های اخیر (۲۴ ساعت گذشته)
    بازگشت: لیست (نام کشور، پاداش دریافتی)
    """
    players = state.get("countries", {})
    now = datetime.now()
    cutoff = now - timedelta(hours=24)
    distributed = []
    
    for country_key, player in players.items():
        wars = player.get("active_wars", [])
        for war in wars:
            ended_at = war.get("ended_at")
            if not ended_at:
                continue
            
            try:
                ended = datetime.fromisoformat(ended_at)
                if ended < cutoff:
                    continue
            except:
                continue
            
            winner = war.get("winner")
            if winner != country_key:
                continue
            
            # محاسبه پاداش بر اساس تعداد بخش‌های تصرف شده
            captured = len(war.get("captured_sectors", []))
            if captured >= 3:
                reward = 50  # پیروزی کامل
            elif captured >= 2:
                reward = 25
            elif captured >= 1:
                reward = 10
            else:
                reward = 5
            
            if reward > 0:
                add_prestige(player, reward, f"پیروزی در جنگ (تصرف {captured} بخش)", state)
                distributed.append((player.get("name_fa", country_key), reward))
    
    return distributed


# ==================== توزیع پاداش مأموریت رمزنگاری ====================

def distribute_mission_prestige(state: Dict[str, Any]) -> List[Tuple[str, int]]:
    """
    توزیع پاداش پرستیژ برای حل مأموریت رمزنگاری (فقط نفر اول)
    بازگشت: لیست (نام کشور، پاداش دریافتی)
    """
    mission = state.get("daily_mission", {})
    solved = mission.get("solved_by", [])
    distributed = []
    
    if solved and len(solved) > 0:
        first_solver = solved[0]
        user_id = first_solver.get("user_id")
        name = first_solver.get("name", "نامشخص")
        
        for country_key, player in state.get("countries", {}).items():
            if player.get("user_id") == user_id:
                add_prestige(player, 10, "اولین حل کننده مأموریت رمزنگاری", state)
                distributed.append((name, 10))
                break
    
    # پاک کردن solved_by بعد از توزیع پاداش
    mission["solved_by"] = []
    return distributed


# ==================== تابع اصلی ====================

def main():
    """توزیع تمام پاداش‌های پرستیژ"""
    print(f"Distributing prestige rewards at {datetime.now().isoformat()}")
    
    state = load_game_state()
    if not state:
        print("Failed to load game state")
        return
    
    all_rewards = []
    
    # 1. پاداش رتبه‌بندی
    rank_rewards = distribute_rankings_prestige(state)
    all_rewards.extend(rank_rewards)
    
    # 2. پاداش پیروزی در جنگ
    war_rewards = distribute_war_prestige(state)
    all_rewards.extend(war_rewards)
    
    # 3. پاداش مأموریت رمزنگاری
    mission_rewards = distribute_mission_prestige(state)
    all_rewards.extend(mission_rewards)
    
    # ذخیره تغییرات
    if all_rewards:
        save_game_state(state)
        
        # ارسال خلاصه به GCC
        summary = "🏆 *پاداش‌های پرستیژ امروز*\n\n"
        for name, amount in all_rewards[:10]:
            summary += f"• {name}: +{amount}\n"
        
        total = sum(amount for _, amount in all_rewards)
        summary += f"\n📊 جمع پاداش توزیع شده: {total} پرستیژ"
        
        send_to_gcc(summary)
        print(f"Distributed {len(all_rewards)} prestige rewards, total: {total}")
    else:
        print("No prestige rewards distributed")


def get_leaderboard(state: Dict[str, Any], limit: int = 10) -> List[Tuple[str, int]]:
    """
    دریافت جدول رهبران بر اساس پرستیژ
    بازگشت: لیست (نام کشور، پرستیژ)
    """
    players = state.get("countries", {})
    leaderboard = []
    
    for country_key, player in players.items():
        if player.get("user_id") is None:
            continue
        name = player.get("name_fa", country_key)
        prestige = player.get("resources", {}).get("prestige", 0)
        leaderboard.append((name, prestige))
    
    leaderboard.sort(key=lambda x: x[1], reverse=True)
    return leaderboard[:limit]


def get_top_commanders(state: Dict[str, Any]) -> str:
    """
    دریافت متن جدول فرماندهان برتر برای نمایش در GCC
    """
    leaderboard = get_leaderboard(state, 10)
    if not leaderboard:
        return "📊 هنوز هیچ پرستیژی توزیع نشده است."
    
    text = "🏆 *جدول فرماندهان برتر* 🏆\n\n"
    medals = ["🥇", "🥈", "🥉"]
    
    for i, (name, prestige) in enumerate(leaderboard):
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} {name}: {prestige} پرستیژ\n"
    
    return text


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--leaderboard":
        state = load_game_state()
        if state:
            print(get_top_commanders(state))
    else:
        main()
