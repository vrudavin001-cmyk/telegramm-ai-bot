import os
import time
import threading
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
# WEB-СЕРВЕР ДЛЯ RENDER
# =========================

app = Flask(__name__)

@app.route("/")
def home():
    return "🤖 Telegram AI Bot работает!"

# =========================
# TELEGRAM-БОТ
# =========================

def telegram_bot():

    offset = 0

    print("🤖 Telegram бот запущен!")

    while True:
        try:

            response = requests.get(
                f"{API}/getUpdates",
                params={
                    "offset": offset,
                    "timeout": 30
                },
                timeout=35
            )

            data = response.json()

            if not data.get("ok"):
                print("Ошибка Telegram:", data)
                time.sleep(5)
                continue

            for update in data.get("result", []):

                offset = update["update_id"] + 1

                message = update.get("message")

                if not message:
                    continue

                text = message.get("text", "")

                # Отвечаем только на /ai
                if not text.startswith("/ai"):
                    continue

                question = text[3:].strip()

                chat_id = message["chat"]["id"]

                if not question:

                    answer = "Напиши вопрос после /ai 🙂"

                else:

                    try:

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

                    except Exception as e:

                        print("Ошибка нейросети:", e)

                        answer = "⚠️ Нейросеть временно недоступна."

                # Отправляем ответ в Telegram
                requests.post(
                    f"{API}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": answer
                    },
                    timeout=20
                )

        except Exception as e:

            print("Ошибка бота:", e)

            time.sleep(5)


# =========================
# ЗАПУСК
# =========================

if __name__ == "__main__":

    # Запускаем Telegram-бота отдельно
    bot_thread = threading.Thread(
        target=telegram_bot,
        daemon=True
    )

    bot_thread.start()

    # Render требует открытый порт
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
                                    )
