import os
import time
import threading
import requests
from flask import Flask
from openai import OpenAI

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
HF_TOKEN = os.environ["HF_TOKEN"]

API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)

MODEL = "openai/gpt-oss-120b:fastest"

app = Flask(__name__)

@app.route("/")
def home():
    return "🤖 Telegram AI Bot работает!"

def telegram_bot():

    print("🤖 TELEGRAM BOT STARTED")

    # Удаляем webhook, чтобы getUpdates точно работал
    try:
        r = requests.post(
            f"{API}/deleteWebhook",
            json={"drop_pending_updates": False},
            timeout=20
        )
        print("Webhook:", r.json())
    except Exception as e:
        print("Webhook error:", e)

    offset = 0

    while True:
        try:
            response = requests.get(
                f"{API}/getUpdates",
                params={
                    "offset": offset,
                    "timeout": 30,
                    "allowed_updates": ["message"]
                },
                timeout=35
            )

            data = response.json()

            if not data.get("ok"):
                print("TELEGRAM ERROR:", data)
                time.sleep(5)
                continue

            for update in data.get("result", []):

                offset = update["update_id"] + 1

                print("📩 UPDATE:", update)

                message = update.get("message")

                if not message:
                    continue

                text = message.get("text", "")
                chat_id = message["chat"]["id"]

                print("💬 MESSAGE:", text)

                if not text.startswith("/ai"):
                    continue

                question = text[3:].strip()

                if not question:
                    answer = "Напиши вопрос после /ai 🙂"

                else:
                    try:
                        print("🧠 Отправляю вопрос в нейросеть...")

                        result = client.chat.completions.create(
                            model=MODEL,
                            messages=[
                                {
                                    "role": "system",
                                    "content": (
                                        "Ты дружелюбный помощник в Telegram. "
                                        "Отвечай на русском языке. "
                                        "Отвечай понятно и по существу."
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

                        print("✅ Ответ получен")

                    except Exception as e:
                        print("❌ AI ERROR:", repr(e))
                        answer = "⚠️ Ошибка нейросети."

                result = requests.post(
                    f"{API}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": answer
                    },
                    timeout=20
                )

                print("📤 TELEGRAM RESPONSE:", result.text)

        except Exception as e:
            print("❌ BOT ERROR:", repr(e))
            time.sleep(5)


if __name__ == "__main__":

    bot_thread = threading.Thread(
        target=telegram_bot,
        daemon=True
    )

    bot_thread.start()
    print("🔥 ПОТОК TELEGRAM ЗАПУЩЕН")
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
                        )
