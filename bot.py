import os
import requests
from flask import Flask, request
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


def send_message(chat_id, text):
    requests.post(
        f"{API}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text
        },
        timeout=30
    )


@app.route("/")
def home():
    return "🤖 Telegram AI Bot работает!"


@app.route("/telegram", methods=["POST"])
def telegram():

    update = request.get_json(silent=True)

    if not update:
        return "OK"

    message = update.get("message")

    if not message:
        return "OK"

    text = message.get("text", "")
    chat_id = message["chat"]["id"]

    print("📩 Получено:", text)

    # Команды
    if text.startswith("/start"):
        send_message(
            chat_id,
            "Привет! 🤖 Я AI-бот. Просто напиши мне сообщение."
        )
        return "OK"

    # Обычные сообщения
    if not text:
        return "OK"

    try:

        print("🧠 Отправляю в нейросеть...")

        result = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты грубый и не вежливый AI-помощник в Telegram. "
                        "Отвечай на русском языке, понятно и по существу."
                    )
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            max_tokens=500
        )

        answer = result.choices[0].message.content

        print("✅ Ответ:", answer)

        send_message(chat_id, answer)

    except Exception as e:

        print("❌ Ошибка AI:", repr(e))

        send_message(
            chat_id,
            "⚠️ Нейросеть временно недоступна."
        )

    return "OK"


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
