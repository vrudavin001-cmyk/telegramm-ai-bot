import os
import requests
from flask import Flask, request
from openai import OpenAI

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
HF_TOKEN = os.environ["HF_TOKEN"]

BOT_USERNAME = "hren_67_bot"

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)

MODEL = "openai/gpt-oss-120b:fastest"

STYLES = {
    "normal": "Отвечай нормально, понятно и естественно.",
    "friend": "Общайся как близкий друг: просто, тепло, немного неформально.",
    "troll": "Общайся весело и дерзко, допускай лёгкий безобидный троллинг.",
    "serious": "Отвечай серьёзно, спокойно и по делу.",
    "expert": "Отвечай как эксперт: подробно, логично и точно."
}

chat_styles = {}


def send_message(chat_id, text, reply_to=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if reply_to:
        data["reply_parameters"] = {
            "message_id": reply_to
        }

    r = requests.post(url, json=data, timeout=30)
    print("SEND:", r.status_code, r.text)


def ask_ai(chat_id, question):
    style_name = chat_styles.get(chat_id, "normal")
    style = STYLES[style_name]

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": style
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            max_tokens=500
        )

        return response.choices[0].message.content

    except Exception as e:
        print("AI ERROR:", repr(e))
        return "Не смог получить ответ от нейросети 😕"


@app.route("/")
def home():
    return "BOT IS ALIVE"


@app.route("/telegram", methods=["POST"])
def telegram():
    try:
        update = request.get_json()

        if not update:
            return "OK"

        message = update.get("message")

        if not message:
            return "OK"

        chat = message.get("chat", {})
        chat_id = chat.get("id")
        chat_type = chat.get("type")
        text = message.get("text", "")

        if not text:
            return "OK"

        print("📩 Получено:", text)

        # Команда смены стиля
        if text.startswith("/style"):
            parts = text.split()

            if len(parts) == 1:
                send_message(
                    chat_id,
                    "Доступные стили:\n"
                    "/style normal\n"
                    "/style friend\n"
                    "/style troll\n"
                    "/style serious\n"
                    "/style expert"
                )
                return "OK"

            style = parts[1].lower()

            if style in STYLES:
                chat_styles[chat_id] = style

                send_message(
                    chat_id,
                    f"Стиль изменён на: {style}"
                )
            else:
                send_message(
                    chat_id,
                    "Такого стиля нет."
                )

            return "OK"

        # В личке отвечаем на обычные сообщения
        if chat_type == "private":
            answer = ask_ai(chat_id, text)
            send_message(chat_id, answer)
            return "OK"

        # В группах отвечаем только на упоминание
        if chat_type in ["group", "supergroup"]:

            mentioned = False

            for entity in message.get("entities", []):
                if entity.get("type") == "mention":
                    offset = entity["offset"]
                    length = entity["length"]

                    mention = text[offset:offset + length]

                    if mention.lower() == f"@{BOT_USERNAME}".lower():
                        mentioned = True
                        break

            # Или если пользователь отвечает на сообщение бота
            reply = message.get("reply_to_message")

            replied_to_bot = False

            if reply:
                reply_from = reply.get("from", {})

                if (
                    reply_from.get("is_bot") is True
                    and reply_from.get("username") == BOT_USERNAME
                ):
                    replied_to_bot = True

            if not mentioned and not replied_to_bot:
                return "OK"

            question = text

            question = question.replace(
                f"@{BOT_USERNAME}",
                ""
            ).strip()

            if not question:
                question = "Привет!"

            answer = ask_ai(chat_id, question)

            send_message(
                chat_id,
                answer,
                message.get("message_id")
            )

            return "OK"

        return "OK"

    except Exception as e:
        print("WEBHOOK ERROR:", repr(e))
        return "OK"


if __name__ == "__main__":
    print("BOT STARTED")

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
