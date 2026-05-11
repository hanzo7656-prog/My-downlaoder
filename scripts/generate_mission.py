#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تولید مأموریت رمزنگاری روزانه
هر روز ساعت 8 صبح اجرا می‌شود (توسط GitHub Actions)
"""

import json
import random
import os
import requests
import base64
from datetime import datetime

# ==================== تنظیمات ====================

GH_TOKEN = os.environ.get("GH_TOKEN", "")
REPO_OWNER = os.environ.get("REPO_OWNER", "")
REPO_NAME = os.environ.get("REPO_NAME", "")
BALE_TOKEN = os.environ.get("BALE_TOKEN", "")
GCC_CHAT_ID = os.environ.get("GCC_CHAT_ID", "")

GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/game_state.json"
BALE_API_URL = f"https://tapi.bale.ai/bot{BALE_TOKEN}"

# ==================== سطح‌های رمزنگاری ====================

# سطح 1: عدد به حرف (A=1, B=2, ...)
LEVEL_1_WORDS = [
    ("HELLO", "8-5-12-12-15"),
    ("WORLD", "23-15-18-12-4"),
    ("ATTACK", "1-20-20-1-3-11"),
    ("DEFEND", "4-5-6-5-14-4"),
    ("NUCLEAR", "14-21-3-12-5-1-18"),
    ("MISSILE", "13-9-19-19-9-12-5"),
    ("TANK", "20-1-14-11"),
    ("FIGHTER", "6-9-7-8-20-5-18"),
    ("BOMBER", "2-15-13-2-5-18"),
    ("NAVY", "14-1-22-25"),
    ("ARMY", "1-18-13-25"),
    ("STEALTH", "19-20-5-1-12-20-8"),
]

# سطح 2: معکوس (برعکس کردن کلمه)
LEVEL_2_WORDS = [
    ("HELLO", "OLLEH"),
    ("WORLD", "DLROW"),
    ("ATTACK", "KСАТТА"),
    ("DEFEND", "DNEFED"),
    ("NUCLEAR", "RAELCUN"),
    ("MISSILE", "ELISSIM"),
    ("TANK", "KNAT"),
    ("FIGHTER", "RETHGIF"),
    ("BOMBER", "REBMOB"),
    ("NAVY", "YVAN"),
    ("ARMY", "YMRA"),
    ("POWER", "REWOP"),
]

# سطح 3: سزار (حرف بعدی: A->B, B->C)
LEVEL_3_WORDS = [
    ("HELLO", "IFMMP"),
    ("WORLD", "XPSME"),
    ("ATTACK", "BUUBDL"),
    ("DEFEND", "EFGFOE"),
    ("NUCLEAR", "OVDMFBS"),
    ("MISSILE", "NJTTJMF"),
    ("TANK", "UBOL"),
    ("FIGHTER", "GJHIUFS"),
    ("BOMBER", "CPNCFS"),
    ("NAVY", "OBWZ"),
    ("ARMY", "BSNZ"),
    ("ALERT", "BMFSU"),
]


def load_game_state():
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
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def save_game_state(state):
    """ذخیره game_state.json در گیت‌هاب"""
    try:
        headers = {
            "Authorization": f"token {GH_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        # دریافت sha فعلی
        response = requests.get(GITHUB_API_URL, headers=headers)
        current_sha = response.json().get("sha", "")
        
        new_content = json.dumps(state, indent=2, ensure_ascii=False)
        encoded_content = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")
        
        payload = {
            "message": f"[auto] daily mission {datetime.now().strftime('%Y-%m-%d')}",
            "content": encoded_content,
            "sha": current_sha
        }
        
        response = requests.put(GITHUB_API_URL, headers=headers, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Error saving: {e}")
        return False


def send_to_gcc(message):
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


def generate_mission():
    """تولید مأموریت رمزنگاری با سطح تصادفی"""
    
    # توزیع سطوح: 60% سطح 1، 20% سطح 2، 20% سطح 3
    level = random.choices([1, 2, 3], weights=[60, 20, 20])[0]
    
    if level == 1:
        word, cipher = random.choice(LEVEL_1_WORDS)
        hint = "🔢 عدد به حرف (A=1, B=2, ...)"
        method = "number_to_letter"
    elif level == 2:
        word, cipher = random.choice(LEVEL_2_WORDS)
        hint = "🔄 کلمه برعکس شده است"
        method = "reverse"
    else:
        word, cipher = random.choice(LEVEL_3_WORDS)
        hint = "➕ هر حرف یک مرحله جلوتر است (A→B)"
        method = "caesar"
    
    return {
        "level": level,
        "cipher": cipher,
        "answer": word,
        "hint": hint,
        "method": method
    }


def main():
    print(f"Generating daily mission at {datetime.now().isoformat()}")
    
    # بارگذاری وضعیت بازی
    state = load_game_state()
    if not state:
        print("Failed to load game state")
        return
    
    # تولید مأموریت جدید
    mission = generate_mission()
    
    # ذخیره در state
    state["daily_mission"] = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "level": mission["level"],
        "cipher": mission["cipher"],
        "answer": mission["answer"],
        "hint": mission["hint"],
        "method": mission["method"],
        "solved_by": []
    }
    
    # به‌روزرسانی game_day
    state["game_day"] = state.get("game_day", 0) + 1
    state["last_update"] = datetime.now().isoformat()
    
    # ذخیره در گیت‌هاب
    if save_game_state(state):
        print("Mission saved successfully")
    else:
        print("Failed to save mission")
        return
    
    # ارسال پیام به GCC
    mission_text = f"""🕵️ *مأموریت رمزنگاری روز {state['game_day']}*

رمز: `{mission['cipher']}`

سطح: {mission['level']} 
راهنما: {mission['hint']}

پاسخ را با دستور `/solve [پاسخ]` ارسال کنید.

🏆 *جوایز:*
🥇 اول: ۳۰ نفوذ + ۸۰ فناوری
🥈 دوم: ۲۰ نفوذ + ۵۰ فناوری
🥉 سوم: ۱۰ نفوذ + ۳۰ فناوری

⏰ مهلت: تا فردا ساعت ۸ صبح
"""
    
    send_to_gcc(mission_text)
    print("Mission sent to GCC")


if __name__ == "__main__":
    main()
