
import os
import json
import time
import hashlib
import requests

YAD2_URL = "https://www.yad2.co.il/realestate/rent?maxPrice=9000&minRooms=5&minFloor=2&minEntranceDate=1746057600&multiNeighborhood=991420%2C991421%2C470%2C793%2C20436%2C1674&zoom=12"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = "678043915"
CHECK_INTERVAL_SECONDS = 300

def get_yad2_ads():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(YAD2_URL, headers=headers)
        if "window.__PRELOADED_STATE__" in response.text:
            start = response.text.find("window.__PRELOADED_STATE__ =") + len("window.__PRELOADED_STATE__ =")
            end = response.text.find(";</script>", start)
            raw_json = response.text[start:end].strip()
            data = json.loads(raw_json)
            ads = data.get("feed", {}).get("realestate", {}).get("feed_items", [])
            return [ad for ad in ads if isinstance(ad, dict) and ad.get("id")]
    except Exception as e:
        print("Error fetching Yad2 ads:", e)
    return []

def get_hash(ad):
    return hashlib.md5((str(ad.get("id")) + ad.get("title", "")).encode()).hexdigest()

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        print("Sending to Telegram:", message)
        response = requests.post(url, json=payload)
        print("Telegram response:", response.status_code, response.text)
    except Exception as e:
        print("Telegram error:", e)

def notify(ad):
    title = ad.get("title", "No title")
    price = ad.get("price", "N/A")
    floor = ad.get("floor_from", "N/A")
    ad_id = ad.get("id")
    ad_url = f"https://www.yad2.co.il/item/{ad_id}"
    wa_link = f"https://wa.me/972549258977?text=Check%20this%20apartment:%20{ad_url}"
    message = f"""🏠 <b>New Yad2 Listing</b>

<b>{title}</b>
💰 Price: {price} ₪
🏢 Floor: {floor}
🔗 <a href='{ad_url}'>View Listing</a>
📲 <a href='{wa_link}'>Send on WhatsApp</a>"""
    print("Detected new ad:", title)
    send_telegram_message(message)

def run():
    print("Watcher started. Polling every 5 minutes...")
    while True:
        print("Checking for new listings on Yad2...")
        new_ads = get_yad2_ads()
        for ad in new_ads:
            notify(ad)
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    run()
