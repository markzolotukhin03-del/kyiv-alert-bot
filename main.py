import os
import time
import threading
import requests
from flask import Flask

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

# Публичный API без ключа. Источник неофициальный.
ALERTS_URL = "https://ubilling.net.ua/aerialalerts/"

KYIV_KEYWORDS = [
    "м. Київ",
    "Київ",
    "Kyiv",
    "Kiev",
]

last_status = None

app = Flask(__name__)


@app.route("/")
def home():
    return "KYIV NEWS alert bot is running"


def send_message(text: str) -> None:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    response = requests.post(url, data=payload, timeout=20)
    response.raise_for_status()


def get_kyiv_alert_status() -> bool:
    response = requests.get(ALERTS_URL, timeout=20)
    response.raise_for_status()

    data = response.json()
    text = str(data)

    for keyword in KYIV_KEYWORDS:
        if keyword in text:
            return True

    return False


def alert_loop() -> None:
    global last_status

    print("KYIV NEWS alert monitor started")

    while True:
        try:
            current_status = get_kyiv_alert_status()

            if last_status is None:
                last_status = current_status
                print(f"Initial Kyiv alert status: {current_status}")

            elif current_status is True and last_status is False:
                send_message(
                    "🚨 <b>Повітряна тривога в Києві</b>\n\n"
                    "За даними моніторингових сервісів, у столиці оголошено повітряну тривогу.\n\n"
                    "Пройдіть в укриття та стежте за офіційними повідомленнями."
                )
                last_status = True
                print("Alert started message sent")

            elif current_status is False and last_status is True:
                send_message(
                    "🟢 <b>Відбій повітряної тривоги в Києві</b>\n\n"
                    "За даними моніторингових сервісів, у столиці оголошено відбій повітряної тривоги.\n\n"
                    "Бережіть себе та стежте за офіційними повідомленнями."
                )
                last_status = False
                print("Alert ended message sent")

            else:
                print(f"No change. Kyiv alert status: {current_status}")

        except Exception as error:
            print("Error:", error)

        time.sleep(60)


if __name__ == "__main__":
    threading.Thread(target=alert_loop, daemon=True).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
