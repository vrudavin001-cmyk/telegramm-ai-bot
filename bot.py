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


def send_message(chat_id, text, reply_to=None):
    data = {
        "chat_id": chat_id,
        "text": text
    }

    if reply_to:
        data["reply_parameters"] = {
            "message_id": reply_to
        }

    requests.post(
        f"{API}/sendMessage",
        json=data,
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
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    chat_type = chat.get("type")
    message_id = message.get("message_id")

    if not text or not chat_id:
        return "OK"

    print("📩 Получено:", text)
    print("💬 Тип чата:", chat_type)

    # =========================
    # ЛИЧНЫЙ ЧАТ
    # =========================

    if chat_type == "private":

        if text.startswith("/start"):
            send_message(
                chat_id,
                "Привет! 🤖 Просто напиши мне сообщение."
            )
            return "OK"

        question = text

    # =========================
    # ГРУППА
    # =========================

    elif chat_type in ["group", "supergroup"]:

        # Имя бота
        bot_username = "hren_67_bot"

        # 1. Проверяем, ответил ли пользователь на сообщение бота
        reply = message.get("reply_to_message")

        replied_to_bot = (
            reply
            and reply.get("from")
            and reply["from"].get("is_bot") is True
            and reply["from"].get("username") == bot_username
        )

        # 2. Проверяем упоминание бота
mentioned = False

for entity in message.get("entities", []):
    if entity.get("type") == "mention":
        offset = entity["offset"]
        length = entity["length"]

        mention = text[offset:offset + length]

        if mention.lower() == f"@{bot_username}".lower():
            mentioned = True
            break

# Если ни упоминания, ни ответа на бота — молчим
if not mentioned and not replied_to_bot:
    return "OK"
            return "OK"

        # Убираем @hren_67_bot из вопроса
        question = text.replace(
            f"@{bot_username}",
            ""
        ).strip()

        if not question:
            send_message(
                chat_id,
                "Да? 🙂 Напиши свой вопрос."
            )
            return "OK"

    else:
        return "OK"

    # =========================
    # НЕЙРОСЕТЬ
    # =========================

    try:

        print("🧠 Отправляю в нейросеть:", question)

        result = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты дружелюбный AI-помощник в Telegram. "
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

        # В группе отвечаем прямо на сообщение пользователя
        if chat_type in ["group", "supergroup"]:
            send_message(
                chat_id,
                answer,
                reply_to=message_id
            )
        else:
            send_message(
                chat_id,
                answer
            )

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
