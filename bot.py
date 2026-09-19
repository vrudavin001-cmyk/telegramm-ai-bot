import os
import requests
from flask import Flask, request
from openai import OpenAI

app = Flask(__name__)

# =========================
# НАСТРОЙКИ
# =========================

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
HF_TOKEN = os.environ["HF_TOKEN"]

BOT_USERNAME = "hren_67_bot"

MODEL = "openai/gpt-oss-120b:fastest"

# =========================
# HUGGING FACE
# =========================

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)

# =========================
# СТИЛИ
# =========================

STYLES = {
    "normal": (
        "Отвечай нормально, понятно и естественно."
    ),

    "friend": (
        "Общайся как близкий друг: тепло, неформально, "
        "просто и с юмором."
    ),

    "troll": (
        "Общайся дерзко, саркастично и с подколами. "
        "Можно использовать мат в шутливом контексте."
    ),

    "rude": (
        "Общайся максимально дерзко, грубо и нахально. "
        "Используй разговорный русский, мат, сарказм, "
        "жёсткие подколы и оскорбительные шутки в адрес "
        "собеседника, если это соответствует контексту. "
        "Не будь излишне вежливым. "
        "Не угрожай человеку и не призывай к насилию. "
        "Не оскорбляй людей по расе, национальности, "
        "религии, инвалидности, полу, сексуальной ориентации "
        "или другим защищённым признакам. "
        "Не превращай каждый ответ в бессмысленный мат — "
        "отвечай по существу."
    ),

    "serious": (
        "Отвечай серьёзно, спокойно и по делу."
    ),

    "expert": (
        "Отвечай как эксперт: подробно, логично, "
        "точно и структурированно."
    )
}

# Текущий стиль каждого чата
chat_styles = {}


# =========================
# ОТПРАВКА СООБЩЕНИЯ
# =========================

def send_message(chat_id, text, reply_to=None):

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}/sendMessage"
    )

    data = {
        "chat_id": chat_id,
        "text": text
    }

    # В группе отвечаем именно на сообщение пользователя
    if reply_to:
        data["reply_parameters"] = {
            "message_id": reply_to
        }

    try:
        response = requests.post(
            url,
            json=data,
            timeout=30
        )

        print(
            "SEND:",
            response.status_code,
            response.text
        )

    except Exception as e:
        print(
            "SEND ERROR:",
            repr(e)
        )


# =========================
# ЗАПРОС К НЕЙРОСЕТИ
# =========================

def ask_ai(chat_id, question):

    style_name = chat_styles.get(
        chat_id,
        "normal"
    )

    style = STYLES.get(
        style_name,
        STYLES["normal"]
    )

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

        answer = response.choices[0].message.content

        if not answer:
            return "Что-то нейросеть ничего не ответила 😐"

        return answer

    except Exception as e:

        print(
            "AI ERROR:",
            repr(e)
        )

        return (
            "Блин, нейросеть сейчас что-то заглючила 😕 "
            "Попробуй ещё раз."
        )


# =========================
# ГЛАВНАЯ СТРАНИЦА
# =========================

@app.route("/")
def home():

    return "BOT IS ALIVE"


# =========================
# TELEGRAM WEBHOOK
# =========================

@app.route(
    "/telegram",
    methods=["POST"]
)
def telegram():

    try:

        update = request.get_json()

        if not update:
            return "OK"

        message = update.get("message")

        if not message:
            return "OK"

        chat = message.get(
            "chat",
            {}
        )

        chat_id = chat.get("id")

        chat_type = chat.get("type")

        text = message.get(
            "text",
            ""
        )

        if not text:
            return "OK"

        print(
            "📩 Получено:",
            text
        )

        # =========================
        # КОМАНДА /STYLE
        # =========================

        if text.startswith("/style"):

            parts = text.split()

            # Если написали просто /style
            if len(parts) == 1:

                send_message(
                    chat_id,
                    "🎭 Доступные стили:\n\n"
                    "/style normal — обычный\n"
                    "/style friend — как друг\n"
                    "/style troll — тролль\n"
                    "/style rude — грубый 😈\n"
                    "/style serious — серьёзный\n"
                    "/style expert — эксперт"
                )

                return "OK"

            style_name = parts[1].lower()

            # Проверяем существование стиля
            if style_name in STYLES:

                chat_styles[chat_id] = style_name

                send_message(
                    chat_id,
                    f"😈 Стиль изменён на: {style_name}"
                )

            else:

                send_message(
                    chat_id,
                    "❌ Такого стиля нет.\n\n"
                    "Используй /style чтобы посмотреть список."
                )

            return "OK"

        # =========================
        # ЛИЧНЫЕ СООБЩЕНИЯ
        # =========================

        if chat_type == "private":

            answer = ask_ai(
                chat_id,
                text
            )

            send_message(
                chat_id,
                answer
            )

            return "OK"

        # =========================
        # ГРУППЫ
        # =========================

        if chat_type in [
            "group",
            "supergroup"
        ]:

            mentioned = False

            # Проверяем @hren_67_bot
            for entity in message.get(
                "entities",
                []
            ):

                if entity.get(
                    "type"
                ) == "mention":

                    offset = entity.get(
                        "offset",
                        0
                    )

                    length = entity.get(
                        "length",
                        0
                    )

                    mention = text[
                        offset:
                        offset + length
                    ]

                    if (
                        mention.lower()
                        ==
                        f"@{BOT_USERNAME}".lower()
                    ):

                        mentioned = True

                        break

            # =========================
            # ПРОВЕРКА ОТВЕТА БОТУ
            # =========================

            reply = message.get(
                "reply_to_message"
            )

            replied_to_bot = False

            if reply:

                reply_from = reply.get(
                    "from",
                    {}
                )

                if (
                    reply_from.get(
                        "is_bot"
                    ) is True
                    and
                    reply_from.get(
                        "username"
                    ) == BOT_USERNAME
                ):

                    replied_to_bot = True

            # Если бота не упомянули
            # и не ответили ему — ничего не делаем
            if not mentioned and not replied_to_bot:

                return "OK"

            # =========================
            # УБИРАЕМ УПОМИНАНИЕ
            # =========================

            question = text

            question = question.replace(
                f"@{BOT_USERNAME}",
                ""
            )

            question = question.strip()

            # Если написали только @бот
            if not question:

                question = "Привет!"

            # =========================
            # ОТПРАВЛЯЕМ В НЕЙРОСЕТЬ
            # =========================

            answer = ask_ai(
                chat_id,
                question
            )

            # =========================
            # ОТВЕЧАЕМ В ГРУППЕ
            # =========================

            send_message(
                chat_id,
                answer,
                message.get(
                    "message_id"
                )
            )

            return "OK"

        return "OK"

    except Exception as e:

        print(
            "WEBHOOK ERROR:",
            repr(e)
        )

        return "OK"


# =========================
# ЗАПУСК
# =========================

if __name__ == "__main__":

    print("BOT STARTED")

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
