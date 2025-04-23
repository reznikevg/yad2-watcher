
import os
import json
import time
import hashlib
import requests
import smtplib
from email.mime.text import MIMEText

# ----- CONFIGURATION -----
YAD2_URL = "https://www.yad2.co.il/realestate/rent?maxPrice=9000&minRooms=5&minFloor=2&minEntranceDate=1746057600&multiNeighborhood=991420%2C991421%2C470%2C793%2C20436&zoom=12"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = "678043915"
EMAIL_FROM = "reznikevg@gmail.com"
EMAIL_TO = "reznikevg@gmail.com"
EMAIL_SUBJECT = "🔔 מודעה חדשה ביד2"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "reznikevg@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
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
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen_ads(seen_ads):
    with open(STATE_FILE, "w") as f:
        json.dump(list(seen_ads), f)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Telegram send error:", e)

def send_email(subject, body):
    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    try:
        with smtpllib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())
    except Exception as e:
        print("Email send error:", e)

def notify(ad):
    title = ad.get("title", "No title")
    price = ad.get("price", "Unknown price")
    floor = ad.get("floor_from", "Unknown floor")
    ad_id = ad.get("id")
    ad_url = f"https://www.yad2.co.il/item/{ad_id}"
    wa_link = f"https://wa.me/972549258977?text=היי%2C%20מצאתי%20מודעה%20חדשה%20שיכולה%20לעניין%20אותך%20%3A%20{ad_url}"
    msg = f"📢 <b>מודעה חדשה ביד2</b>\n\n<b>{title}</b>\n💰 {price} ₪\n🏢 קומה: {floor}\n🔗 <a href='{ad_url}'>לצפייה במודעה</a>\n📱 <a href='{wa_link}'>שלח בווטסאפ</a>"
    send_telegram_message(msg)
    send_email(EMAIL_SUBJECT, msg)

def run():
    seen_ads = load_seen_ads()
    while True:
        new_ads = get_yad2_ads()
        for ad in new_ads:
            ad_hash = get_hash(ad)
            if ad_hash not in seen_ads:
                seen_ads.add(ad_hash)
                notify(ad)
        save_seen_ads(seen_ads)
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    run()
