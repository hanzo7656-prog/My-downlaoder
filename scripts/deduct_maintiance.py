#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
کسر هزینه نگهداری روزانه از بازیکنان
هر شب ساعت 12 اجرا می‌شود
"""

import json
import os
import requests
import base64
from datetime import datetime

from admin_system import get_speed_multiplier, load_game_state, save_game_state, send_to_gcc

# واحدهای پایه هزینه نگهداری
MAINTENANCE_COSTS = {
    "air": 8,
    "ground": 5,
    "naval": 12,
    "destroyer": 10,
    "submarine": 10,
    "carrier": 25,
    "artillery": 3,
    "air_defense": 6
}


def deduct_maintenance():
    state = load_game_state()
    if not state:
        print("Failed to load state")
        return
    
    speed = get_speed_multiplier(state)
    players = state.get("countries", {})
    notifications = []
    
    for key, player in players.items():
        total_cost = 0
        units = player.get("units", {})
        
        for category, cost in MAINTENANCE_COSTS.items():
            for unit in units.get(category, []):
                count = unit.get("count", 0)
                total_cost += cost * count
        
        # ضریب سرعت
        total_cost = int(total_cost * speed)
        
        influence = player.get("resources", {}).get("influence", 0)
        
        if influence >= total_cost:
            player["resources"]["influence"] -= total_cost
        else:
            # غیرفعال کردن یگان‌ها
            for category in units:
                for unit in units.get(category, []):
                    if influence <= 0:
                        unit["count"] = 0
                    else:
                        unit_cost = MAINTENANCE_COSTS.get(category, 5) * speed
                        if influence >= unit_cost:
                            influence -= unit_cost
                        else:
                            unit["count"] = 0
            player["resources"]["influence"] = max(0, influence)
            notifications.append(f"⚠️ {player.get('name_fa')}: هزینه نگهداری پرداخت نشد، برخی یگان‌ها غیرفعال شدند.")
    
    if notifications:
        for note in notifications[:5]:
            send_to_gcc(note)
    
    save_game_state(state)
    print(f"Maintenance deducted at {datetime.now().isoformat()}")


if __name__ == "__main__":
    deduct_maintenance()
