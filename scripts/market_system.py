#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
سیستم بازار مشترک و قیمت پویا
امکانات: خرید و فروش تجهیزات در بازار، قیمت‌گذاری پویا بر اساس عرضه و تقاضا، حراج روزانه
"""

import json
import os
import requests
import base64
import random
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

# ==================== قیمت‌های پایه تجهیزات ====================

BASE_PRICES = {
    # هواپیماها
    "F22": 300, "رپتور": 300,
    "F35": 250, "لایتنینگ": 250,
    "SU57": 280, "فلون": 280,
    "جی۲۰": 220, "J20": 220,
    "تمپست": 350, "Tempest": 350,
    "تایفون": 200, "Eurofighter Typhoon": 200,
    "رافال": 190, "Rafale": 190,
    "سوخو-۳۵": 170, "Su-35": 170,
    "سوپر هورنت": 150, "F/A-18": 150,
    "میگ-۲۹": 120, "MiG-29": 120,
    "فانتوم": 90, "F-4": 90,
    
    # تانک‌ها
    "آر ماتا": 250, "T-14 Armata": 250,
    "آبرامز": 230, "Abrams X": 230,
    "لئوپارد": 220, "Leopard 2A7+": 220,
    "پلنگ سیاه": 210, "K2 Black Panther": 210,
    "مِرکاوا": 200, "Merkava": 200,
    "چلنجر": 195, "Challenger 2": 195,
    "تایپ-۱۰": 185, "Type 10": 185,
    "تایپ-۹۹": 180, "Type 99A": 180,
    "آبرامز ام۱": 120, "Abrams M1": 120,
    "تی-۹۰": 110, "T-90": 110,
    "لئوپارد ۲": 100, "Leopard 2": 100,
    "تی-۵۵": 30, "T-55": 30,
    
    # ناوشکن
    "زوموالت": 400, "Zumwalt": 400,
    "تایپ-۵۵": 350, "Type 55": 350,
    "آرلی بروک": 320, "Arleigh Burke": 320,
    "تایپ-۴۵": 300, "Type 45": 300,
    "مایا": 290, "Maya": 290,
    
    # زیردریایی
    "اوهایو": 500, "Ohio": 500,
    "یاسن": 450, "Yasen": 450,
    "تایپ-۰۹۳": 320, "Type 093": 320,
    
    # ناو هواپیمابر
    "فورد": 1200, "Ford": 1200,
    "نیمیتز": 1000, "Nimitz": 1000,
    "فوجیان": 950, "Fujian": 950,
    
    # پدافند
    "اس-۵۰۰": 350, "S-500": 350,
    "اس-۴۰۰": 250, "S-400": 250,
    "تاد": 240, "THAAD": 240,
    "پاتریوت": 200, "Patriot": 200,
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
        
        payload = {"message": f"[market] {datetime.now().isoformat()}", "content": encoded, "sha": current_sha}
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


def send_message(chat_id: str, text: str):
    if not BALE_TOKEN:
        return
    url = f"{BALE_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
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


# ==================== قیمت‌گذاری پویا ====================

def update_market_prices(state: Dict[str, Any]):
    """
    به‌روزرسانی قیمت‌ها بر اساس عرضه و تقاضا
    هر 24 ساعت یکبار اجرا می‌شود
    """
    market = state.get("market", {})
    order_book = market.get("order_book", {})
    prices = market.get("prices", {})
    
    for item, base_price in BASE_PRICES.items():
        # محاسبه عرضه و تقاضا
        supply = 0
        demand = 0
        
        for order in order_book.get(item, {}).get("sell", []):
            if order.get("active", True):
                supply += order.get("count", 0)
        
        for order in order_book.get(item, {}).get("buy", []):
            if order.get("active", True):
                demand += order.get("count", 0)
        
        # تغییر قیمت بر اساس عرضه و تقاضا
        old_price = prices.get(item, base_price)
        
        if supply == 0 and demand == 0:
            new_price = base_price
        elif demand > supply:
            # افزایش قیمت (حداکثر 30%)
            increase = min(0.30, (demand - supply) / max(supply, 1) * 0.05)
            new_price = int(base_price * (1 + increase))
        elif supply > demand:
            # کاهش قیمت (حداکثر 25%)
            decrease = min(0.25, (supply - demand) / supply * 0.05)
            new_price = int(base_price * (1 - decrease))
        else:
            # گرایش به قیمت پایه
            new_price = int((old_price * 0.9 + base_price * 0.1))
        
        prices[item] = max(int(base_price * 0.5), min(int(base_price * 1.3), new_price))
    
    # به‌روزرسانی روند
    for item, price in prices.items():
        old = market.get("prices", {}).get(item, BASE_PRICES.get(item, 0))
        if price > old:
            trend = "up"
        elif price < old:
            trend = "down"
        else:
            trend = "stable"
        
        if "trends" not in market:
            market["trends"] = {}
        market["trends"][item] = trend
    
    state["market"] = market
    return prices


def get_market_price(state: Dict[str, Any], item: str) -> int:
    """دریافت قیمت فعلی یک تجهیزات در بازار"""
    market = state.get("market", {})
    prices = market.get("prices", {})
    return prices.get(item, BASE_PRICES.get(item, 100))


def get_trend_icon(item: str, state: Dict[str, Any]) -> str:
    """دریافت آیکون روند قیمت"""
    market = state.get("market", {})
    trends = market.get("trends", {})
    trend = trends.get(item, "stable")
    
    if trend == "up":
        return "📈"
    elif trend == "down":
        return "📉"
    return "➡️"


# ==================== سفارش‌های بازار ====================

def place_sell_order(state: Dict[str, Any], user_id: str, item: str, count: int, price: int = None) -> Tuple[bool, str]:
    """ثبت سفارش فروش در بازار"""
    player = get_country_data(state, user_id)
    if not player:
        return False, "❌ شما کشوری انتخاب نکرده‌اید."
    
    # بررسی داشتن تجهیزات
    units = player.get("units", {})
    found = False
    for category, unit_list in units.items():
        for unit in unit_list:
            if unit.get("name_fa") == item or unit.get("name_en") == item:
                if unit.get("count", 0) >= count:
                    found = True
                    unit["count"] = unit.get("count", 0) - count
                    break
        if found:
            break
    
    if not found:
        return False, f"❌ شما {count} عدد {item} ندارید."
    
    # قیمت پیشنهادی
    market_price = get_market_price(state, item)
    if price is None:
        price = market_price
    elif price < market_price * 0.5:
        return False, "❌ قیمت نمی‌تواند کمتر از 50% قیمت بازار باشد."
    elif price > market_price * 2:
        return False, "❌ قیمت نمی‌تواند بیشتر از 200% قیمت بازار باشد."
    
    # ثبت سفارش
    order = {
        "id": f"sell_{datetime.now().timestamp()}_{user_id}",
        "user_id": user_id,
        "country": player.get("name_fa"),
        "item": item,
        "count": count,
        "price": price,
        "placed_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=3)).isoformat(),
        "active": True
    }
    
    if "market" not in state:
        state["market"] = {}
    if "order_book" not in state["market"]:
        state["market"]["order_book"] = {}
    if item not in state["market"]["order_book"]:
        state["market"]["order_book"][item] = {"buy": [], "sell": []}
    
    state["market"]["order_book"][item]["sell"].append(order)
    
    # تلاش برای تطبیق خودکار با سفارش‌های خرید
    matched = match_orders(state, item)
    
    save_game_state(state)
    
    if matched:
        return True, f"✅ سفارش فروش {count} عدد {item} با قیمت {price} ثبت و بلافاصله تطبیق داده شد."
    return True, f"✅ سفارش فروش {count} عدد {item} با قیمت {price} در بازار ثبت شد."


def place_buy_order(state: Dict[str, Any], user_id: str, item: str, count: int, price: int = None) -> Tuple[bool, str]:
    """ثبت سفارش خرید در بازار"""
    player = get_country_data(state, user_id)
    if not player:
        return False, "❌ شما کشوری انتخاب نکرده‌اید."
    
    total_cost = 0
    market_price = get_market_price(state, item)
    
    if price is None:
        price = market_price
    
    total_cost = price * count
    influence = player.get("resources", {}).get("influence", 0)
    
    if influence < total_cost:
        return False, f"❌ نفوذ کافی ندارید. نیاز: {total_cost}"
    
    # قفل کردن مبلغ
    if "pending_orders" not in player:
        player["pending_orders"] = []
    
    # ثبت سفارش
    order = {
        "id": f"buy_{datetime.now().timestamp()}_{user_id}",
        "user_id": user_id,
        "country": player.get("name_fa"),
        "item": item,
        "count": count,
        "price": price,
        "total_cost": total_cost,
        "placed_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=3)).isoformat(),
        "active": True
    }
    
    if "market" not in state:
        state["market"] = {}
    if "order_book" not in state["market"]:
        state["market"]["order_book"] = {}
    if item not in state["market"]["order_book"]:
        state["market"]["order_book"][item] = {"buy": [], "sell": []}
    
    state["market"]["order_book"][item]["buy"].append(order)
    
    # تلاش برای تطبیق خودکار
    matched = match_orders(state, item)
    
    save_game_state(state)
    
    if matched:
        return True, f"✅ سفارش خرید {count} عدد {item} با قیمت {price} ثبت و بلافاصله تطبیق داده شد."
    return True, f"✅ سفارش خرید {count} عدد {item} با قیمت {price} در بازار ثبت شد. مبلغ {total_cost} نفوذ قفل شد."


def match_orders(state: Dict[str, Any], item: str) -> bool:
    """تطبیق سفارش‌های خرید و فروش"""
    order_book = state.get("market", {}).get("order_book", {}).get(item, {"buy": [], "sell": []})
    buy_orders = [o for o in order_book.get("buy", []) if o.get("active", True)]
    sell_orders = [o for o in order_book.get("sell", []) if o.get("active", True)]
    
    # مرتب‌سازی: خرید (قیمت بالا به پایین)، فروش (قیمت پایین به بالا)
    buy_orders.sort(key=lambda x: x.get("price", 0), reverse=True)
    sell_orders.sort(key=lambda x: x.get("price", 0))
    
    matched = False
    remaining_orders = []
    
    for buy in buy_orders[:]:
        for sell in sell_orders[:]:
            if buy.get("price", 0) >= sell.get("price", 0):
                # تطبیق
                trade_count = min(buy.get("count", 0), sell.get("count", 0))
                trade_price = (buy.get("price", 0) + sell.get("price", 0)) // 2
                
                # انجام معامله
                execute_trade(state, buy, sell, trade_count, trade_price, item)
                
                # به‌روزرسانی تعداد
                buy["count"] -= trade_count
                sell["count"] -= trade_count
                matched = True
                
                if buy["count"] == 0:
                    buy["active"] = False
                    break
                if sell["count"] == 0:
                    sell["active"] = False
        
        if buy["count"] > 0:
            remaining_orders.append(buy)
    
    # به‌روزرسانی سفارش‌ها
    order_book["buy"] = [o for o in order_book.get("buy", []) if o.get("active", True) and o.get("count", 0) > 0]
    order_book["sell"] = [o for o in order_book.get("sell", []) if o.get("active", True) and o.get("count", 0) > 0]
    
    return matched


def execute_trade(state: Dict[str, Any], buy_order: Dict[str, Any], sell_order: Dict[str, Any], 
                  count: int, price: int, item: str):
    """اجرای یک معامله"""
    # خریدار
    buyer = None
    for country_key, player in state.get("countries", {}).items():
        if player.get("user_id") == buy_order.get("user_id"):
            buyer = player
            break
    
    if buyer:
        # کسر نفوذ
        total = price * count
        if "pending_orders" in buyer:
            buyer["pending_orders"] = [o for o in buyer.get("pending_orders", []) if o.get("id") != buy_order.get("id")]
        buyer["resources"]["influence"] = buyer.get("resources", {}).get("influence", 0) - total
        
        # اضافه کردن تجهیزات
        units = buyer.get("units", {})
        added = False
        for category, unit_list in units.items():
            for unit in unit_list:
                if unit.get("name_fa") == item or unit.get("name_en") == item:
                    unit["count"] = unit.get("count", 0) + count
                    added = True
                    break
            if added:
                break
        
        if not added:
            if "ground" not in units:
                units["ground"] = []
            units["ground"].append({
                "name_fa": item,
                "name_en": item,
                "count": count,
                "health": 100,
                "experience": 0
            })
    
    # فروشنده
    seller = None
    for country_key, player in state.get("countries", {}).items():
        if player.get("user_id") == sell_order.get("user_id"):
            seller = player
            break
    
    if seller:
        # اضافه کردن نفوذ (97% بعد از مالیات)
        total = price * count
        tax = int(total * 0.05)
        seller["resources"]["influence"] = seller.get("resources", {}).get("influence", 0) + (total - tax)
    
    # اعلان به GCC
    buyer_name = buy_order.get("country", "نامشخص")
    seller_name = sell_order.get("country", "نامشخص")
    send_to_gcc(f"💰 *معامله در بازار*\n{seller_name} {count} عدد {item} را با قیمت {price} به {buyer_name} فروخت.")


def cancel_order(state: Dict[str, Any], user_id: str, order_id: str) -> Tuple[bool, str]:
    """لغو سفارش فعال"""
    player = get_country_data(state, user_id)
    if not player:
        return False, "❌ شما کشوری انتخاب نکرده‌اید."
    
    market = state.get("market", {})
    order_book = market.get("order_book", {})
    
    for item, orders in order_book.items():
        for order_type in ["buy", "sell"]:
            for order in orders.get(order_type, []):
                if order.get("id") == order_id and order.get("user_id") == user_id and order.get("active", True):
                    order["active"] = False
                    
                    if order_type == "buy":
                        # بازگرداندن نفوذ قفل شده
                        total = order.get("total_cost", order.get("price", 0) * order.get("count", 0))
                        player["resources"]["influence"] = player.get("resources", {}).get("influence", 0) + total
                        if "pending_orders" in player:
                            player["pending_orders"] = [o for o in player.get("pending_orders", []) if o.get("id") != order_id]
                    elif order_type == "sell":
                        # بازگرداندن تجهیزات
                        units = player.get("units", {})
                        item_name = order.get("item")
                        count = order.get("count", 0)
                        
                        added = False
                        for category, unit_list in units.items():
                            for unit in unit_list:
                                if unit.get("name_fa") == item_name or unit.get("name_en") == item_name:
                                    unit["count"] = unit.get("count", 0) + count
                                    added = True
                                    break
                            if added:
                                break
                    
                    save_game_state(state)
                    return True, f"✅ سفارش {order_id} لغو شد."
    
    return False, "❌ سفارش یافت نشد."


# ==================== حراج روزانه ====================

def generate_auction(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """تولید حراج روزانه (3 یگان تصادفی)"""
    all_items = list(BASE_PRICES.keys())
    auction_items = []
    
    for i in range(3):
        item = random.choice(all_items)
        count = random.randint(1, 5)
        base_price = BASE_PRICES.get(item, 100)
        starting_price = int(base_price * random.uniform(0.3, 0.7))
        
        auction_items.append({
            "id": f"auction_{datetime.now().timestamp()}_{i}",
            "item": item,
            "count": count,
            "starting_price": starting_price,
            "current_bid": starting_price,
            "current_bidder": None,
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
            "active": True
        })
    
    if "market" not in state:
        state["market"] = {}
    state["market"]["auction"] = auction_items
    
    return auction_items


def bid_on_auction(state: Dict[str, Any], user_id: str, auction_id: str, bid_amount: int) -> Tuple[bool, str]:
    """شرکت در حراج"""
    player = get_country_data(state, user_id)
    if not player:
        return False, "❌ شما کشوری انتخاب نکرده‌اید."
    
    auction = state.get("market", {}).get("auction", [])
    item = None
    for a in auction:
        if a.get("id") == auction_id and a.get("active", True):
            item = a
            break
    
    if not item:
        return False, "❌ حراج یافت نشد."
    
    if bid_amount <= item.get("current_bid", 0):
        return False, f"❌ قیمت پیشنهادی باید بالاتر از {item.get('current_bid')} باشد."
    
    influence = player.get("resources", {}).get("influence", 0)
    if influence < bid_amount:
        return False, f"❌ نفوذ کافی ندارید. نیاز: {bid_amount}"
    
    # قفل مبلغ
    if "pending_bids" not in player:
        player["pending_bids"] = []
    player["pending_bids"].append({
        "auction_id": auction_id,
        "amount": bid_amount,
        "bid_at": datetime.now().isoformat()
    })
    
    # به‌روزرسانی پیشنهاد
    item["current_bid"] = bid_amount
    item["current_bidder"] = user_id
    item["current_bidder_name"] = player.get("name_fa")
    
    save_game_state(state)
    
    return True, f"✅ پیشنهاد {bid_amount} نفوذ برای {item.get('item')} ثبت شد."


def resolve_auction(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """حل حراج‌های منقضی شده"""
    auction = state.get("market", {}).get("auction", [])
    now = datetime.now()
    resolved = []
    
    for item in auction:
        if not item.get("active", True):
            continue
        
        expires_at = item.get("expires_at")
        if expires_at:
            expires = datetime.fromisoformat(expires_at)
            if expires <= now:
                item["active"] = False
                
                if item.get("current_bidder"):
                    # برنده حراج
                    winner = None
                    for country_key, player in state.get("countries", {}).items():
                        if player.get("user_id") == item.get("current_bidder"):
                            winner = player
                            break
                    
                    if winner:
                        # کسر هزینه
                        winner["resources"]["influence"] = winner.get("resources", {}).get("influence", 0) - item.get("current_bid", 0)
                        
                        # اضافه کردن تجهیزات
                        units = winner.get("units", {})
                        item_name = item.get("item")
                        count = item.get("count", 1)
                        
                        added = False
                        for category, unit_list in units.items():
                            for unit in unit_list:
                                if unit.get("name_fa") == item_name or unit.get("name_en") == item_name:
                                    unit["count"] = unit.get("count", 0) + count
                                    added = True
                                    break
                            if added:
                                break
                        
                        if not added:
                            if "ground" not in units:
                                units["ground"] = []
                            units["ground"].append({
                                "name_fa": item_name,
                                "name_en": item_name,
                                "count": count,
                                "health": 100,
                                "experience": 0
                            })
                        
                        resolved.append({
                            "item": item_name,
                            "count": count,
                            "price": item.get("current_bid"),
                            "winner": winner.get("name_fa")
                        })
                        
                        send_to_gcc(f"🏆 *برنده حراج*\n{winner.get('name_fa')} {count} عدد {item_name} را با قیمت {item.get('current_bid')} نفوذ خریداری کرد.")
    
    # حذف حراج‌های منقضی
    state["market"]["auction"] = [a for a in auction if a.get("active", True)]
    
    return resolved


# ==================== دستورات بازار ====================

def handle_market_prices(state: Dict[str, Any], user_id: str) -> str:
    """دستور /market - نمایش قیمت‌های بازار"""
    market = state.get("market", {})
    prices = market.get("prices", {})
    
    msg = "💰 *قیمت‌های بازار*\n\n"
    
    for item, base_price in list(BASE_PRICES.items())[:20]:
        current_price = prices.get(item, base_price)
        trend = get_trend_icon(item, state)
        discount = int((1 - current_price / base_price) * 100)
        
        if discount > 0:
            msg += f"• {item}: {current_price} {trend} ({discount}% تخفیف)\n"
        elif discount < 0:
            msg += f"• {item}: {current_price} {trend} ({-discount}% افزایش)\n"
        else:
            msg += f"• {item}: {current_price} {trend}\n"
    
    msg += "\nبرای خرید: `/buy_from_market [نام] [تعداد] [قیمت]`"
    return msg


def handle_buy_from_market(state: Dict[str, Any], user_id: str, args: str) -> str:
    """دستور /buy_from_market [نام] [تعداد] [قیمت]"""
    parts = args.strip().split()
    if len(parts) < 2:
        return "❌ فرمت صحیح: `/buy_from_market [نام] [تعداد] [قیمت]`\nقیمت اختیاری است."
    
    item = parts[0]
    try:
        count = int(parts[1])
    except:
        return "❌ تعداد باید عدد باشد."
    
    price = None
    if len(parts) > 2:
        try:
            price = int(parts[2])
        except:
            return "❌ قیمت باید عدد باشد."
    
    success, msg = place_buy_order(state, user_id, item, count, price)
    if success:
        save_game_state(state)
    return msg


def handle_sell_to_market(state: Dict[str, Any], user_id: str, args: str) -> str:
    """دستور /sell_to_market [نام] [تعداد] [قیمت]"""
    parts = args.strip().split()
    if len(parts) < 2:
        return "❌ فرمت صحیح: `/sell_to_market [نام] [تعداد] [قیمت]`\nقیمت اختیاری است."
    
    item = parts[0]
    try:
        count = int(parts[1])
    except:
        return "❌ تعداد باید عدد باشد."
    
    price = None
    if len(parts) > 2:
        try:
            price = int(parts[2])
        except:
            return "❌ قیمت باید عدد باشد."
    
    success, msg = place_sell_order(state, user_id, item, count, price)
    if success:
        save_game_state(state)
    return msg


def handle_cancel_order(state: Dict[str, Any], user_id: str, args: str) -> str:
    """دستور /cancel_order [order_id]"""
    if not args.strip():
        return "❌ لطفاً ID سفارش را وارد کنید."
    
    success, msg = cancel_order(state, user_id, args.strip())
    if success:
        save_game_state(state)
    return msg


def handle_auction(state: Dict[str, Any], user_id: str) -> str:
    """دستور /auction - نمایش حراج روزانه"""
    auction = state.get("market", {}).get("auction", [])
    
    if not auction:
        return "🏷️ حراج جدیدی فعال نیست. بعداً تلاش کنید."
    
    msg = "🏷️ *حراج روزانه*\n\n"
    for item in auction:
        if item.get("active", True):
            expires = datetime.fromisoformat(item["expires_at"])
            hours_left = int((expires - datetime.now()).total_seconds() / 3600)
            msg += f"• {item['item']} x{item['count']}\n"
            msg += f"  قیمت پایه: {item['starting_price']}\n"
            msg += f"  آخرین پیشنهاد: {item.get('current_bid', item['starting_price'])}\n"
            msg += f"  مهلت: {hours_left} ساعت\n"
            msg += f"  برای پیشنهاد: `/bid {item['id']} [قیمت]`\n\n"
    
    return msg


def handle_bid(state: Dict[str, Any], user_id: str, args: str) -> str:
    """دستور /bid [auction_id] [price]"""
    parts = args.strip().split()
    if len(parts) < 2:
        return "❌ فرمت صحیح: `/bid [auction_id] [price]`"
    
    auction_id = parts[0]
    try:
        price = int(parts[1])
    except:
        return "❌ قیمت باید عدد باشد."
    
    success, msg = bid_on_auction(state, user_id, auction_id, price)
    if success:
        save_game_state(state)
    return msg


def get_market_help() -> str:
    """راهنمای بازار"""
    return """
💰 *سیستم بازار مشترک*

*قیمت‌گذاری پویا:*
قیمت تجهیزات بر اساس عرضه و تقاضا تغییر می‌کند (±30%)

*حراج روزانه:*
هر روز 3 تجهیزات با تخفیف 30-70% به حراج گذاشته می‌شود.

*دستورات:*
/market - نمایش قیمت‌های بازار
/buy_from_market [نام] [تعداد] [قیمت] - خرید از بازار
/sell_to_market [نام] [تعداد] [قیمت] - فروش در بازار
/cancel_order [id] - لغو سفارش
/auction - نمایش حراج روزانه
/bid [auction_id] [price] - پیشنهاد قیمت در حراج
"""


if __name__ == "__main__":
    print("Market system module loaded")
