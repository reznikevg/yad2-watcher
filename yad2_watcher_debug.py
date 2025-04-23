
import os
import json
import time
import hashlib
import requests

# ----- CONFIGURATION -----
YAD2_URL = "https://www.yad2.co.il/realestate/rent?maxPrice=9000&minRooms=5&minFloor=2&minEntranceDate=1746057600&multiNeighborhood=991420%2C991421%2C470%2C793%2C20436&zoom=12"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = "678043915"
STATE_FILE = "yad2_seen_ads.json"
CHECK_INTERVAL_SECONDS = 300
# --------------------------

def get_yad2_ads():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(YAD2_URL, headers=headers)
        if "window.__PRELOADED_STATE__" in response.text:
            state_start = response.text.find("window.__PRELOADED_STATE__ =") + len("window.__PRELOADED_STATE__ =")
            state_end = response.text.find(";</script>", state_start)
            state_json = response.text[state_start:state_end].strip()
            data = json.loads(state_json)
            ads = data.get("feed", {}).get("realestate", {}).get("feed_items", [])
            filtered_ads = [ad for ad in ads if isinstance(ad, dict) and ad.get("id")]
            return filtered_ads
    except Exception as e:
        print("Error fetching ads:", e)
    return []

def get_hash(ad):
    return hashlib.md5((str(ad.get("id")) + ad.get("title", "")).encode()).hexdigest()

def load_seen_ads():
    return set()

def save_seen_ads(seen_ads):
    pass

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        print('📤 שולח לטלגרם:', message); response = requests.post(url, json=payload); print('✅ תגובת טלגרם:', response.status_code, response.text)
    except Exception as e:
        print("Telegram error:", e)

def print('✨ מודעה חדשה נמצאה:', ad.get('title')); notify(ad):
    title = ad.get("title", "No title")
    price = ad.get("price", "Unknown")
    floor = ad.get("floor_from", "Unknown")
    ad_id = ad.get("id")
    ad_url = f"https://www.yad2.co.il/item/{ad_id}"
    wa_link = f"https://wa.me/972549258977?text=היי%2C%20מצאתי%20מודעה%20חדשה%20שיכולה%20לעניין%20אותך%20%3A%20{ad_url}"
    msg = f"📢 <b>מודעה חדשה ביד2</b>\n\n<b>{title}</b>\n💰 {price} ₪\n🏢 קומה: {floor}\n🔗 <a href='{ad_url}'>לצפייה</a>\n📱 <a href='{wa_link}'>שלח בווטסאפ</a>"
    send_telegram_message(msg)

def run():
    seen_ads = load_seen_ads()
    while True:
        print("🔄 בודק מודעות חדשות ביד2...")
        new_ads = get_yad2_ads()
        for ad in new_ads:
            ad_hash = get_hash(ad)
            if ad_hash not in seen_ads:
                seen_ads.add(ad_hash)
                print('✨ מודעה חדשה נמצאה:', ad.get('title')); notify(ad)
        save_seen_ads(seen_ads)
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    run()
