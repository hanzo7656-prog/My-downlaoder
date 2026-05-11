#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
حل خودکار جنگ‌های بی‌پاسخ بر اساس مهلت‌های تنظیم شده
هر 4 ساعت یکبار اجرا می‌شود
"""

import json
import os
import requests
import base64
from datetime import datetime, timedelta

from admin_system import get_adjusted_deadline, load_game_state, save_game_state, send_to_gcc

GH_TOKEN = os.environ.get("GH_TOKEN", "")
REPO_OWNER = os.environ.get("REPO_OWNER", "")
REPO_NAME = os.environ.get("REPO_NAME", "")

GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/game_state.json"


def resolve_timeout_wars():
    state = load_game_state()
    if not state:
        print("Failed to load state")
        return
    
    speed = state.get("admin", {}).get("game_speed", 1)
    deadline_hours = get_adjusted_deadline(12, state)  # 12 ساعت پایه
    
    players = state.get("countries", {})
    resolved_count = 0
    
    for key, player in players.items():
        wars = player.get("active_wars", [])
        for war in wars[:]:
            last_move = war.get("last_move")
            if last_move:
                last = datetime.fromisoformat(last_move)
                if datetime.now() - last > timedelta(hours=deadline_hours):
                    # حل خودکار به نفع مدافع
                    war["status"] = "auto_resolved"
                    war["result"] = "defender_wins"
                    wars.remove(war)
                    resolved_count += 1
                    
                    # ارسال اعلان
                    msg = f"⚔️ *جنگ خودکار حل شد*\n{player.get('name_fa')} در برابر {war.get('with')}\nنتیجه: دفاع کننده پیروز شد (مهلت تمام شد)"
                    send_to_gcc(msg)
    
    if resolved_count > 0:
        save_game_state(state)
        print(f"Resolved {resolved_count} wars")


if __name__ == "__main__":
    resolve_timeout_wars()
