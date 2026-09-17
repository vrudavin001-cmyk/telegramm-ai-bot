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

# Стиль по умолчанию
chat_styles = {}

STYLES = {

    "normal": """
Общайся естественно и дружелюбно.
Пиши на русском языке.
Отвечай понятно и по существу.
Не будь слишком официальным.
""",

    "friend": """
Общайся как близкий приятель в Telegram.
Пиши естественно, свободно и непринуждённо.
Можно использовать разговорные выражения и лёгкий сленг.
Иногда шути и поддерживай собеседника.
Не будь занудным или слишком официальным.
""",

    "troll": """
Общайся весело и с юмором.
Можно слегка подкалывать собеседника и использовать иронию.
Не переходи в настоящие оскорбления или травлю.
Даже серьёзные вопросы объясняй понятно.
Пиши как весёлый участник компании.
""",

    "serious": """
Общайся спокойно, серьёзно и уверенно.
Отвечай чётко и без лишних шуток.
Если вопрос сложный — объясняй по пунктам.
Не используй лишний сленг.
""",

    "expert": """
Общайся как компетентный специалист.
Давай точные и хорошо структурированные ответы.
Объясняй сложные вещи простым языком.
При необходимости используй списки и примеры.
Не добавляй лишнюю информацию, которая не помогает ответить на вопрос.
"""
}


def send_message(chat_id, text, reply_to=None):

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if reply_to:
        data["reply_parameters"] = {
            "message_id": reply_to
        }

    try:
        requests.post(
            f"{API}/sendMessage",
            json=data,
            timeout=30
        )
    except Exception as e:
        print("SEND ERROR:", repr(e))


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

    # ==================================================
    # КОМАНДА /START
    # ==================================================

    if text.startswith("/start"):

        send_message(
            chat_id,
            "🤖 Привет!\n\n"
            "Просто напиши мне сообщение.\n\n"
            "Доступные стили:\n"
            "/style normal\n"
            "/style friend\n"
            "/style troll\n"
            "/style serious\n"
            "/style expert"
        )

        return "OK"

    # ==================================================
    # ПЕРЕКЛЮЧЕНИЕ СТИЛЯ
    # ==================================================

    if text.lower().startswith("/style"):

        parts = text.split()

        if len(parts) < 2:

            send_message(
                chat_id,
                "Выбери стиль:\n\n"
                "normal — обычный\n"
                "friend — приятель\n"
                "troll — юмор и подколы\n"
                "serious — серьёзный\n"
                "expert — профессиональный"
            )

            return "OK"

        style = parts[1].lower()

        if style not in STYLES:

            send_message(
                chat_id,
                "❌ Такого стиля нет.\n\n"
                "Доступно: normal, friend, troll, serious, expert"
            )

            return "OK"

        chat_styles[chat_id] = style

        send_message(
            chat_id,
            f"✅ Стиль изменён на: {style}"
        )

        return "OK"

    # ==================================================
    # ОПРЕДЕЛЯЕМ, НУЖНО ЛИ ОТВЕЧАТЬ
    # ==================================================

    # Личная переписка — отвечаем на всё
    if chat_type == "private":

        question = text

    # Группа — только упоминание или ответ боту
    elif chat_type in ["group", "supergroup"]:

        bot_username = "hren_67_bot"

        mentioned = False

        # Проверяем официальное Telegram-упоминание
        for entity in message.get("entities", []):

            if entity.get("type") == "mention":

                offset = entity["offset"]
                length = entity["length"]

                mention = text[offset:offset + length]

                if mention.lower() == f"@{bot_username}".lower():
                    mentioned = True
                    break

        # Проверяем ответ на сообщение бота
        reply = message.get("reply_to_message")

        replied_to_bot = (
            reply
            and reply.get("from")
            and reply["from"].get("is_bot") is True
            and reply["from"].get("username") == bot_username
        )

        if not mentioned and not replied_to_bot:
            return "OK"

        # Убираем упоминание
        question = text

        question = question.replace(
            f"@{bot_username}",
            ""
        ).strip()

        if not question:

            send_message(
                chat_id,
                "Да? 🙂 Напиши вопрос."
            )

            return "OK"

    else:
        return "OK"

    # ==================================================
    # ВЫБИРАЕМ СТИЛЬ
    # ==================================================

    style = chat_styles.get(chat_id, "normal")

    style_instruction = STYLES[style]

    # ==================================================
    # НЕЙРОСЕТЬ
    # ==================================================

    try:

        print("🧠 Стиль:", style)
        print("🧠 Вопрос:", question)

        result = client.chat.completions.create(

            model=MODEL,

            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты AI-помощник в Telegram.\n\n"
                        + style_instruction
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

        print("❌ AI ERROR:", repr(e))

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
