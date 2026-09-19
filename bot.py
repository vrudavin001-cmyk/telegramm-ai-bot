import os
import random
import requests
from collections import defaultdict, deque
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
# AI
# =========================

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)

# =========================
# СТИЛИ
# =========================

STYLES = {
    "normal": "Отвечай нормально, понятно и естественно.",

    "friend": (
        "Общайся как близкий друг: тепло, неформально "
        "и с юмором."
    ),

    "troll": (
        "Общайся дерзко, саркастично и с подколами. "
        "Можно использовать мат в шутливом контексте."
    ),

    "rude": (
        "Общайся грубо, дерзко и нахально. "
        "Используй разговорный русский, мат, сарказм "
        "и жёсткие подколы. Не угрожай человеку и "
        "не атакуй людей по защищённым признакам."
    ),

    "serious": (
        "Отвечай серьёзно, спокойно и по делу."
    ),

    "expert": (
        "Отвечай как эксперт: подробно, логично и точно."
    ),

    "sigma": (
        "Общайся уверенно, дерзко и с мемным "
        "сигма-вайбом. Используй современный сленг "
        "и юмор, но отвечай по существу."
    )
}

# Стиль каждого чата
chat_styles = {}

# Память последних 10 сообщений каждого чата
memory = defaultdict(lambda: deque(maxlen=10))


# =========================
# TELEGRAM
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
        print("SEND ERROR:", repr(e))


# =========================
# AI
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

    # Добавляем сообщение пользователя в память
    memory[chat_id].append({
        "role": "user",
        "content": question
    })

    messages = [
        {
            "role": "system",
            "content": (
                style +
                "\nТы Telegram-бот. "
                "Отвечай на русском языке, если пользователь "
                "не попросил другой язык."
            )
        }
    ]

    # Добавляем историю
    messages.extend(
        list(memory[chat_id])
    )

    try:

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=500
        )

        answer = response.choices[0].message.content

        if not answer:
            answer = "Я что-то завис 😐"

        # Сохраняем ответ
        memory[chat_id].append({
            "role": "assistant",
            "content": answer
        })

        return answer

    except Exception as e:

        print(
            "AI ERROR:",
            repr(e)
        )

        return (
            "Нейросеть сейчас заглючила 😕 "
            "Попробуй ещё раз."
        )


# =========================
# ГЛАВНАЯ
# =========================

@app.route("/")
def home():
    return "BOT IS ALIVE"


# =========================
# WEBHOOK
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

        print("📩 Получено:", text)

        # =========================
        # /STYLE
        # =========================

        if text.startswith("/style"):

            parts = text.split()

            if len(parts) == 1:

                send_message(
                    chat_id,
                    "🎭 Стили:\n\n"
                    "/style normal — обычный\n"
                    "/style friend — друг\n"
                    "/style troll — тролль\n"
                    "/style rude — грубый 😈\n"
                    "/style serious — серьёзный\n"
                    "/style expert — эксперт\n"
                    "/style sigma — сигма 😎"
                )

                return "OK"

            style = parts[1].lower()

            if style in STYLES:

                chat_styles[chat_id] = style

                send_message(
                    chat_id,
                    f"🎭 Стиль установлен: {style}"
                )

            else:

                send_message(
                    chat_id,
                    "❌ Такого стиля нет. "
                    "Напиши /style"
                )

            return "OK"

        # =========================
        # /COIN
        # =========================

        if text.startswith("/coin"):

            result = random.choice([
                "🪙 Орёл!",
                "🪙 Решка!"
            ])

            send_message(
                chat_id,
                result
            )

            return "OK"

        # =========================
        # /DICE
        # =========================

        if text.startswith("/dice"):

            number = random.randint(
                1,
                6
            )

            send_message(
                chat_id,
                f"🎲 Выпало: {number}"
            )

            return "OK"

        # =========================
        # /GUESS
        # =========================

        if text.startswith("/guess"):

            number = random.randint(
                1,
                10
            )

            send_message(
                chat_id,
                "🔢 Я загадал число от 1 до 10.\n"
                "Попробуй угадать его!"
            )

            # Запоминаем число
            memory[chat_id].append({
                "role": "system",
                "content": (
                    f"В игре угадай число загадано число "
                    f"{number}. Пользователь должен угадать."
                )
            })

            return "OK"

        # =========================
        # /JOKE
        # =========================

        if text.startswith("/joke"):

            answer = ask_ai(
                chat_id,
                "Придумай короткую смешную шутку."
            )

            send_message(
                chat_id,
                answer
            )

            return "OK"

        # =========================
        # /FACT
        # =========================

        if text.startswith("/fact"):

            answer = ask_ai(
                chat_id,
                "Расскажи один интересный и правдивый "
                "факт. Коротко."
            )

            send_message(
                chat_id,
                answer
            )

            return "OK"

        # =========================
        # /ROAST
        # =========================

        if text.startswith("/roast"):

            target = text[
                len("/roast"):
            ].strip()

            if not target:

                target = "меня"

            answer = ask_ai(
                chat_id,
                (
                    f"Сделай короткий шуточный roast "
                    f"для {target}. "
                    f"Это должна быть шутка, без угроз "
                    f"и атак на защищённые признаки."
                )
            )

            send_message(
                chat_id,
                answer
            )

            return "OK"

        # =========================
        # /ASK
        # =========================

        if text.startswith("/ask"):

            question = text[
                len("/ask"):
            ].strip()

            if not question:

                send_message(
                    chat_id,
                    "Напиши вопрос после /ask"
                )

                return "OK"

            answer = ask_ai(
                chat_id,
                question
            )

            send_message(
                chat_id,
                answer
            )

            return "OK"

        # =========================
        # ЛИЧКА
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

            # Проверяем упоминание
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

            # Проверяем ответ боту
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

            # Не обращались к боту
            if (
                not mentioned
                and
                not replied_to_bot
            ):

                return "OK"

            # Убираем @username
            question = text.replace(
                f"@{BOT_USERNAME}",
                ""
            ).strip()

            if not question:

                question = "Привет!"

            answer = ask_ai(
                chat_id,
                question
            )

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
