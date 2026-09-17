import os
import time
import requests
from flask import Flask
from openai import OpenAI

# =========================
# НАСТРОЙКИ
# =========================

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
HF_TOKEN = os.environ["HF_TOKEN"]

API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# =========================
# НЕЙРОСЕТЬ
# =========================

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)

MODEL = "openai/gpt-oss-120b:fastest"

# =========================
# RENDER
# =========================

app = Flask(__name__)

@app.route("/")
def home():
    return "Telegram AI Bot работает!"

# =========================
# TELEGRAM
# =========================

def run_bot():

    print("BOT STARTED")

    # Удаляем webhook
    try:
        r = requests.post(
            f"{API}/deleteWebhook",
            timeout=20
        )
        print("WEBHOOK:", r.text)
    except Exception as e:
        print("WEBHOOK ERROR:", e)

    offset = 0

    while True:

        try:

            r = requests.get(
                f"{API}/getUpdates",
                params={
                    "offset": offset,
                    "timeout": 25
                },
                timeout=35
            )

            data = r.json()

            print("TELEGRAM:", data.get("ok"))

            if not data.get("ok"):
                print(data)
                time.sleep(5)
                continue

            for update in data["result"]:

                offset = update["update_id"] + 1

                message = update.get("message")

                if not message:
                    continue

                text = message.get("text", "")
                chat_id = message["chat"]["id"]

                print("MESSAGE:", text)

                if not text.startswith("/ai"):
                    continue

                question = text[3:].strip()

                if not question:
                    answer = "Напиши вопрос после /ai 🙂"

                else:

                    try:

                        print("ASK AI:", question)

                        result = client.chat.completions.create(
                            model=MODEL,
                            messages=[
                                {
                                    "role": "system",
                                    "content": (
                                        "Ты дружелюбный помощник "
                                        "в Telegram. Отвечай "
                                        "на русском языке."
                                    )
                                },
                                {
                                    "role": "user",
                                    "content": question
                                }
                            ],
                            max_tokens=500
                        )

                        answer = result.choices[0].message.content

                        print("AI ANSWER OK")

                    except Exception as e:

                        print("AI ERROR:", repr(e))

                        answer = "⚠️ Ошибка нейросети."

                send = requests.post(
                    f"{API}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": answer
                    },
                    timeout=20
                )

                print("SEND:", send.text)

        except Exception as e:

            print("BOT ERROR:", repr(e))

            time.sleep(5)


# =========================
# ЗАПУСК
# =========================

if __name__ == "__main__":

    import threading

    thread = threading.Thread(
        target=run_bot,
        daemon=True
    )

    thread.start()

    print("TELEGRAM THREAD STARTED")

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
                        )
