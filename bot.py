import os
import random
import html
import requests

from flask import Flask, request
from collections import defaultdict, deque
from openai import OpenAI


# =========================================================
# НАСТРОЙКИ
# =========================================================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")

BOT_USERNAME = "hren_67_bot"
MODEL = "openai/gpt-oss-120b:fastest"

if not TELEGRAM_TOKEN:
    raise RuntimeError("Не найден TELEGRAM_TOKEN")

if not HF_TOKEN:
    raise RuntimeError("Не найден HF_TOKEN")


# =========================================================
# TELEGRAM API
# =========================================================

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


# =========================================================
# HUGGING FACE
# =========================================================

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)


# =========================================================
# FLASK
# =========================================================

app = Flask(__name__)


# =========================================================
# ПАМЯТЬ
# =========================================================

memory = defaultdict(lambda: deque(maxlen=10))

chat_styles = {}

chat_users = defaultdict(dict)

guess_number = {}


# =========================================================
# СТИЛИ
# =========================================================

STYLES = {

    "normal": """
Ты дружелюбный и адекватный AI-помощник.
Отвечай понятно и по делу.
""",

    "friend": """
Ты общаешься как близкий друг.
Пиши естественно, просто и иногда используй юмор.
Не будь слишком официальным.
""",

    "troll": """
Ты весёлый тролль.
Отвечай с юмором, подколами и сарказмом.
Не переходи в угрозы или дискриминацию.
""",

    "rude": """
Ты дерзкий собеседник.
Можешь использовать грубоватый разговорный стиль,
сарказм, подколы и умеренный мат.
Не угрожай людям и не оскорбляй людей по защищаемым признакам.
""",

    "serious": """
Ты серьёзный и спокойный собеседник.
Отвечай кратко, логично и без лишнего юмора.
""",

    "expert": """
Ты эксперт.
Давай точные, структурированные и полезные ответы.
Если чего-то не знаешь — не выдумывай.
""",

    "sigma": """
Ты говоришь уверенно, коротко и дерзко.
Стиль интернет-мемов и sigma-юмора.
Иногда используй фразы:
«База», «Сильный ход», «Сигма момент».
Но ответ должен оставаться понятным.
"""
}


# =========================================================
# КОМАНДЫ TELEGRAM
# =========================================================

BOT_COMMANDS = [
    {
        "command": "start",
        "description": "Запустить бота"
    },
    {
        "command": "style",
        "description": "Выбрать стиль общения"
    },
    {
        "command": "ask",
        "description": "Задать вопрос AI"
    },
    {
        "command": "roast",
        "description": "Подколоть человека"
    },
    {
        "command": "joke",
        "description": "Рассказать шутку"
    },
    {
        "command": "fact",
        "description": "Интересный факт"
    },
    {
        "command": "coin",
        "description": "Подбросить монетку"
    },
    {
        "command": "dice",
        "description": "Бросить кубик"
    },
    {
        "command": "guess",
        "description": "Игра: угадай число"
    }
]


# =========================================================
# РЕГИСТРАЦИЯ КОМАНД
# =========================================================

def set_bot_commands():

    try:

        response = requests.post(
            f"{TELEGRAM_API}/setMyCommands",
            json={
                "commands": BOT_COMMANDS
            },
            timeout=15
        )

        print(
            "📋 Команды Telegram:",
            response.text
        )

    except Exception as e:

        print(
            "❌ Ошибка установки команд:",
            e
        )


# =========================================================
# ОТПРАВКА СООБЩЕНИЯ
# =========================================================

def send_message(chat_id, text, reply_to=None):

    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    if reply_to:

        data["reply_parameters"] = {
            "message_id": reply_to
        }

    try:

        response = requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json=data,
            timeout=30
        )

        if not response.ok:

            print(
                "❌ Ошибка Telegram:",
                response.text
            )

    except Exception as e:

        print(
            "❌ Ошибка send_message:",
            e
        )


# =========================================================
# AI
# =========================================================

def ask_ai(chat_id, user_text):

    style_name = chat_styles.get(
        chat_id,
        "normal"
    )

    style = STYLES.get(
        style_name,
        STYLES["normal"]
    )

    memory[chat_id].append({
        "role": "user",
        "content": user_text
    })

    messages = [

        {
            "role": "system",
            "content": f"""
{style}

Ты находишься в Telegram-чате.

Текущий стиль: {style_name}

Не выдумывай факты.
Отвечай на языке пользователя.
Не будь чрезмерно официальным.
"""
        }

    ]

    messages.extend(
        list(memory[chat_id])
    )

    try:

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=500,
            temperature=0.8
        )

        answer = response.choices[0].message.content

        if not answer:

            answer = "Я не придумал, что ответить 😐"

        memory[chat_id].append({
            "role": "assistant",
            "content": answer
        })

        return answer

    except Exception as e:

        print(
            "❌ Ошибка AI:",
            e
        )

        return (
            "⚠️ Не смог получить ответ "
            "от нейросети. Попробуй ещё раз."
        )


# =========================================================
# СТИЛИ
# =========================================================

def style_command(chat_id, text):

    parts = text.strip().split()

    if len(parts) == 1:

        current = chat_styles.get(
            chat_id,
            "normal"
        )

        available = "\n".join(
            f"• <code>{name}</code>"
            for name in STYLES
        )

        return (
            f"🎭 Текущий стиль: "
            f"<b>{current}</b>\n\n"
            f"Доступные стили:\n"
            f"{available}\n\n"
            f"Например:\n"
            f"<code>/style troll</code>"
        )

    style_name = parts[1].lower()

    if style_name not in STYLES:

        return (
            "❌ Такого стиля нет.\n\n"
            "Доступны:\n"
            +
            "\n".join(
                f"• <code>{name}</code>"
                for name in STYLES
            )
        )

    chat_styles[chat_id] = style_name

    return (
        f"✅ Стиль изменён на: "
        f"<b>{style_name}</b>"
    )


# =========================================================
# СЛУЧАЙНЫЙ ЧЕЛОВЕК
# =========================================================

def choose_random_user(chat_id):

    users = list(
        chat_users.get(
            chat_id,
            {}
        ).values()
    )

    if not users:

        return None

    return random.choice(users)


# =========================================================
# WEBHOOK
# =========================================================

@app.route(
    "/telegram",
    methods=["POST"]
)
def telegram_webhook():

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

        user = message.get(
            "from",
            {}
        )

        text = message.get(
            "text",
            ""
        ) or ""

        message_id = message.get(
            "message_id"
        )


        # =================================================
        # ЗАПОМИНАЕМ УЧАСТНИКА
        # =================================================

        if chat_type in [
            "group",
            "supergroup"
        ]:

            if (
                user
                and not user.get("is_bot")
            ):

                user_id = user.get("id")

                first_name = user.get(
                    "first_name",
                    "Участник"
                )

                last_name = user.get(
                    "last_name",
                    ""
                )

                full_name = (
                    f"{first_name} {last_name}"
                ).strip()

                chat_users[
                    chat_id
                ][user_id] = {

                    "id": user_id,

                    "name": full_name
                }

                print(
                    f"👤 Запомнил: "
                    f"{full_name}"
                )


        print(
            "📩 Получено:",
            text
        )


        # =================================================
        # КТО В ЧАТЕ
        # =================================================

        if (
            chat_type in [
                "group",
                "supergroup"
            ]
            and text.lower().startswith(
                "кто в чате"
            )
        ):

            chosen = choose_random_user(
                chat_id
            )

            if not chosen:

                send_message(
                    chat_id,
                    "🤷 Я пока никого не запомнил."
                )

                return "OK"

            user_id = chosen["id"]

            name = chosen["name"]

            safe_name = html.escape(
                name
            )

            mention = (
                f'<a href="tg://user?id={user_id}">'
                f'{safe_name}'
                f'</a>'
            )

            send_message(
                chat_id,
                "🎯 Случайный человек из чата:\n\n"
                f"👉 {mention}"
            )

            return "OK"


        # =================================================
        # /START
        # =================================================

        if text.startswith("/start"):

            send_message(
                chat_id,
                """
🤖 <b>Привет!</b>

Я AI-бот для Telegram.

В группе я отвечаю, когда меня упоминают
или когда отвечают на моё сообщение.

🎭 Стили:

<code>/style</code>
<code>/style friend</code>
<code>/style troll</code>
<code>/style rude</code>
<code>/style serious</code>
<code>/style expert</code>
<code>/style sigma</code>

🎮 Игры:

<code>/coin</code>
<code>/dice</code>
<code>/guess</code>

👤 А ещё попробуй:

<code>Кто в чате самый крутой?</code>
""",
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /STYLE
        # =================================================

        if text.startswith("/style"):

            answer = style_command(
                chat_id,
                text
            )

            send_message(
                chat_id,
                answer,
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /COIN
        # =================================================

        if text.startswith("/coin"):

            result = random.choice(
                [
                    "🪙 Орёл",
                    "🪙 Решка"
                ]
            )

            send_message(
                chat_id,
                result,
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /DICE
        # =================================================

        if text.startswith("/dice"):

            number = random.randint(
                1,
                6
            )

            send_message(
                chat_id,
                f"🎲 Выпало: <b>{number}</b>",
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /JOKE
        # =================================================

        if text.startswith("/joke"):

            jokes = [

                "Почему программист не ходит в лес? Потому что там слишком много багов 🐛",

                "Я хотел пошутить про Wi-Fi, но связь оборвалась.",

                "Мой код работает. Не спрашивай почему.",

                "Хотел написать идеальный код... но дедлайн написал его раньше.",

                "Самая страшная ошибка программиста: «работало вчера»."

            ]

            send_message(
                chat_id,
                random.choice(jokes),
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /FACT
        # =================================================

        if text.startswith("/fact"):

            facts = [

                "🐙 У осьминога три сердца.",

                "🦈 Акулы существовали раньше деревьев.",

                "🌍 Земля не является идеальным шаром.",

                "🐝 Пчёлы могут распознавать человеческие лица.",

                "🚀 В космосе звук не распространяется как на Земле."

            ]

            send_message(
                chat_id,
                random.choice(facts),
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /ROAST
        # =================================================

        if text.startswith("/roast"):

            target = text[
                6:
            ].strip()

            if not target:

                target = "тебя"

            roasts = [

                f"{target}, ты настолько медленный, что даже черепаха тебя обгоняет 🐢",

                f"{target}, у тебя уверенности больше, чем аргументов 😂",

                f"{target}, твой IQ сейчас пытается подключиться к Wi-Fi.",

                f"{target}, даже бот иногда не понимает, что ты пишешь 💀",

                f"{target}, это был сильный заход. Жаль, что мимо."

            ]

            send_message(
                chat_id,
                random.choice(roasts),
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /ASK
        # =================================================

        if text.startswith("/ask"):

            question = text[
                4:
            ].strip()

            if not question:

                send_message(
                    chat_id,
                    "❓ Напиши вопрос после /ask",
                    reply_to=message_id
                )

                return "OK"

            answer = ask_ai(
                chat_id,
                question
            )

            send_message(
                chat_id,
                html.escape(answer),
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /GUESS
        # =================================================

        if text.startswith("/guess"):

            number = random.randint(
                1,
                10
            )

            guess_number[
                chat_id
            ] = number

            send_message(
                chat_id,
                "🎯 Я загадал число от "
                "<b>1 до 10</b>.\n"
                "Пиши свой вариант.",
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # ПРОВЕРКА GUESS
        # =================================================

        if (
            chat_id in guess_number
            and text.strip().isdigit()
        ):

            user_guess = int(
                text.strip()
            )

            if 1 <= user_guess <= 10:

                number = guess_number[
                    chat_id
                ]

                if user_guess == number:

                    send_message(
                        chat_id,
                        f"🎉 Правильно! "
                        f"Я загадал <b>{number}</b>!",
                        reply_to=message_id
                    )

                    del guess_number[
                        chat_id
                    ]

                    return "OK"

                elif user_guess < number:

                    send_message(
                        chat_id,
                        "⬆️ Моё число больше.",
                        reply_to=message_id
                    )

                    return "OK"

                else:

                    send_message(
                        chat_id,
                        "⬇️ Моё число меньше.",
                        reply_to=message_id
                    )

                    return "OK"


        # =================================================
        # НУЖНО ЛИ ОТВЕЧАТЬ
        # =================================================

        should_answer = False

        # Личные сообщения
        if chat_type == "private":

            should_answer = True


        # Группы
        elif chat_type in [
            "group",
            "supergroup"
        ]:

            # Упоминание бота
            if (
                f"@{BOT_USERNAME.lower()}"
                in text.lower()
            ):

                should_answer = True


            # Ответ на сообщение бота
            reply_to_message = message.get(
                "reply_to_message"
            )

            if reply_to_message:

                replied_from = (
                    reply_to_message.get(
                        "from",
                        {}
                    )
                )

                replied_username = (
                    replied_from.get(
                        "username",
                        ""
                    ).lower()
                )

                if (
                    replied_username
                    == BOT_USERNAME.lower()
                ):

                    should_answer = True


        # =================================================
        # НЕ ОТВЕЧАЕМ
        # =================================================

        if not should_answer:

            return "OK"


        # =================================================
        # УБИРАЕМ @БОТА
        # =================================================

        clean_text = text.replace(
            f"@{BOT_USERNAME}",
            ""
        ).strip()

        if not clean_text:

            clean_text = "Привет"


        # =================================================
        # AI
        # =================================================

        answer = ask_ai(
            chat_id,
            clean_text
        )


        # =================================================
        # ОТВЕТ
        # =================================================

        send_message(
            chat_id,
            html.escape(answer),
            reply_to=message_id
        )

        return "OK"


    except Exception as e:

        print(
            "❌ ОШИБКА WEBHOOK:",
            e
        )

        return "OK"


# =========================================================
# ГЛАВНАЯ
# =========================================================

@app.route(
    "/",
    methods=["GET", "HEAD"]
)
def home():

    return "Telegram AI Bot is running!"


# =========================================================
# ЗАПУСК
# =========================================================

if __name__ == "__main__":

    print("BOT STARTED")

    # Устанавливаем подсказки команд
    set_bot_commands()

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
