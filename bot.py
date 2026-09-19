import os
import random
import html
import sqlite3
import time
import threading
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

DB_FILE = "bot.db"

if not TELEGRAM_TOKEN:
    raise RuntimeError("Не найден TELEGRAM_TOKEN")

if not HF_TOKEN:
    raise RuntimeError("Не найден HF_TOKEN")


# =========================================================
# TELEGRAM
# =========================================================

TELEGRAM_API = (
    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
)


# =========================================================
# AI
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
# SQLITE
# =========================================================

db_lock = threading.Lock()


def get_db():

    conn = sqlite3.connect(
        DB_FILE,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    with db_lock:

        conn = get_db()

        cur = conn.cursor()

        # Пользователи
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER,
                user_id INTEGER,
                name TEXT,
                username TEXT,
                messages INTEGER DEFAULT 0,
                joined_at INTEGER,
                PRIMARY KEY (chat_id, user_id)
            )
        """)

        # Настройки чатов
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_settings (
                chat_id INTEGER PRIMARY KEY,
                style TEXT DEFAULT 'normal'
            )
        """)

        # История
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_id INTEGER,
                name TEXT,
                text TEXT,
                created_at INTEGER
            )
        """)

        # Предупреждения
        cur.execute("""
            CREATE TABLE IF NOT EXISTS warnings (
                chat_id INTEGER,
                user_id INTEGER,
                warnings INTEGER DEFAULT 0,
                PRIMARY KEY (chat_id, user_id)
            )
        """)

        conn.commit()

        conn.close()


init_db()


# =========================================================
# ВРЕМЕННАЯ ПАМЯТЬ AI
# =========================================================

memory = defaultdict(
    lambda: deque(maxlen=10)
)


# =========================================================
# АНТИСПАМ
# =========================================================

spam_tracker = defaultdict(
    lambda: deque(maxlen=10)
)


# =========================================================
# ИГРЫ
# =========================================================

guess_number = {}

duels = {}

quiz_active = {}


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
""",

    "troll": """
Ты весёлый тролль.
Отвечай с юмором, подколами и сарказмом.
Не угрожай людям.
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
Не выдумывай факты.
""",

    "sigma": """
Ты говоришь уверенно, коротко и дерзко.
Стиль интернет-мемов и sigma-юмора.
Можно использовать «База», «Сигма момент» и подобные выражения.
"""
}


# =========================================================
# КОМАНДЫ
# =========================================================

BOT_COMMANDS = [

    {
        "command": "start",
        "description": "Запустить бота"
    },

    {
        "command": "style",
        "description": "Выбрать стиль AI"
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
        "command": "who",
        "description": "Выбрать случайного участника"
    },

    {
        "command": "pair",
        "description": "Случайная пара"
    },

    {
        "command": "duel",
        "description": "Устроить дуэль"
    },

    {
        "command": "8ball",
        "description": "Задать вопрос магическому шару"
    },

    {
        "command": "truth",
        "description": "Правда или действие"
    },

    {
        "command": "roulette",
        "description": "Случайное задание"
    },

    {
        "command": "nickname",
        "description": "Случайное прозвище"
    },

    {
        "command": "excuse",
        "description": "Сгенерировать оправдание"
    },

    {
        "command": "task",
        "description": "Получить задание"
    },

    {
        "command": "choose",
        "description": "Случайный выбор"
    },

    {
        "command": "stats",
        "description": "Статистика чата"
    },

    {
        "command": "top",
        "description": "Топ участников"
    },

    {
        "command": "summarize",
        "description": "Кратко пересказать чат"
    },

    {
        "command": "quiz",
        "description": "Запустить викторину"
    },

    {
        "command": "poll",
        "description": "Создать опрос"
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
        "description": "Угадай число"
    }
]


# =========================================================
# УСТАНОВКА КОМАНД
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
            "📋 Команды:",
            response.text
        )

    except Exception as e:

        print(
            "❌ Ошибка команд:",
            e
        )


# =========================================================
# TELEGRAM SEND
# =========================================================

def telegram_request(method, data=None):

    try:

        response = requests.post(
            f"{TELEGRAM_API}/{method}",
            json=data or {},
            timeout=30
        )

        if not response.ok:

            print(
                f"❌ Telegram {method}:",
                response.text
            )

            return None

        return response.json()

    except Exception as e:

        print(
            f"❌ Ошибка {method}:",
            e
        )

        return None


def send_message(
    chat_id,
    text,
    reply_to=None
):

    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    if reply_to:

        data["reply_parameters"] = {
            "message_id": reply_to
        }

    return telegram_request(
        "sendMessage",
        data
    )


# =========================================================
# БАЗА — ПОЛЬЗОВАТЕЛИ
# =========================================================

def save_user(
    chat_id,
    user
):

    if not user:
        return

    if user.get("is_bot"):
        return

    user_id = user.get("id")

    first_name = user.get(
        "first_name",
        "Участник"
    )

    last_name = user.get(
        "last_name",
        ""
    )

    name = (
        f"{first_name} {last_name}"
    ).strip()

    username = user.get(
        "username",
        ""
    )

    with db_lock:

        conn = get_db()

        conn.execute("""
            INSERT INTO users (
                chat_id,
                user_id,
                name,
                username,
                messages,
                joined_at
            )

            VALUES (?, ?, ?, ?, 0, ?)

            ON CONFLICT(chat_id, user_id)
            DO UPDATE SET
                name=excluded.name,
                username=excluded.username
        """, (
            chat_id,
            user_id,
            name,
            username,
            int(time.time())
        ))

        conn.commit()

        conn.close()


def add_message_stat(
    chat_id,
    user_id,
    name,
    text
):

    save_user(
        chat_id,
        {
            "id": user_id,
            "first_name": name
        }
    )

    with db_lock:

        conn = get_db()

        conn.execute("""
            UPDATE users
            SET messages = messages + 1
            WHERE chat_id = ?
            AND user_id = ?
        """, (
            chat_id,
            user_id
        ))

        conn.execute("""
            INSERT INTO chat_history (
                chat_id,
                user_id,
                name,
                text,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            chat_id,
            user_id,
            name,
            text[:1000],
            int(time.time())
        ))

        conn.commit()

        conn.close()


# =========================================================
# ПОЛУЧИТЬ УЧАСТНИКОВ
# =========================================================

def get_users(chat_id):

    with db_lock:

        conn = get_db()

        rows = conn.execute("""
            SELECT *
            FROM users
            WHERE chat_id = ?
            AND messages > 0
        """, (
            chat_id,
        )).fetchall()

        conn.close()

    return rows


def get_random_user(chat_id):

    users = get_users(chat_id)

    if not users:
        return None

    return random.choice(users)


def mention_user(user):

    name = html.escape(
        user["name"] or "Участник"
    )

    return (
        f'<a href="tg://user?id={user["user_id"]}">'
        f'{name}'
        f'</a>'
    )


# =========================================================
# СТИЛЬ
# =========================================================

def get_style(chat_id):

    with db_lock:

        conn = get_db()

        row = conn.execute("""
            SELECT style
            FROM chat_settings
            WHERE chat_id = ?
        """, (
            chat_id,
        )).fetchone()

        conn.close()

    if row:
        return row["style"]

    return "normal"


def set_style(
    chat_id,
    style
):

    with db_lock:

        conn = get_db()

        conn.execute("""
            INSERT INTO chat_settings (
                chat_id,
                style
            )

            VALUES (?, ?)

            ON CONFLICT(chat_id)
            DO UPDATE SET style=excluded.style
        """, (
            chat_id,
            style
        ))

        conn.commit()

        conn.close()


def style_command(
    chat_id,
    text
):

    parts = text.split()

    if len(parts) == 1:

        current = get_style(
            chat_id
        )

        styles = "\n".join(
            f"• <code>{x}</code>"
            for x in STYLES
        )

        return (
            f"🎭 Сейчас: <b>{current}</b>\n\n"
            f"{styles}\n\n"
            f"Пример:\n"
            f"<code>/style troll</code>"
        )

    style = parts[1].lower()

    if style not in STYLES:

        return (
            "❌ Такого стиля нет.\n\n"
            +
            "\n".join(
                f"• <code>{x}</code>"
                for x in STYLES
            )
        )

    set_style(
        chat_id,
        style
    )

    return (
        f"✅ Стиль установлен: "
        f"<b>{style}</b>"
    )


# =========================================================
# AI
# =========================================================

def ask_ai(
    chat_id,
    user_text
):

    style_name = get_style(
        chat_id
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

Ты AI-бот в Telegram.

Отвечай на языке пользователя.
Не выдумывай факты.
Не будь слишком официальным.

Текущий стиль: {style_name}
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
            max_tokens=600,
            temperature=0.8
        )

        answer = response.choices[0].message.content

        if not answer:

            answer = "Не знаю, что ответить 😐"

        memory[chat_id].append({
            "role": "assistant",
            "content": answer
        })

        return answer

    except Exception as e:

        print(
            "❌ AI ERROR:",
            e
        )

        return (
            "⚠️ Нейросеть сейчас "
            "не отвечает. Попробуй ещё раз."
        )


# =========================================================
# КТО В ЧАТЕ
# =========================================================

def command_who(chat_id):

    user = get_random_user(
        chat_id
    )

    if not user:

        return (
            "🤷 Я пока не знаю "
            "участников этого чата."
        )

    return (
        "🎯 Случайный участник:\n\n"
        f"👉 {mention_user(user)}"
    )


# =========================================================
# ПАРА
# =========================================================

def command_pair(chat_id):

    users = get_users(chat_id)

    if len(users) < 2:

        return (
            "😐 Мне нужно хотя бы "
            "2 участника."
        )

    a, b = random.sample(
        users,
        2
    )

    percent = random.randint(
        1,
        100
    )

    return (
        "💘 Случайная пара:\n\n"
        f"❤️ {mention_user(a)}\n"
        f"❤️ {mention_user(b)}\n\n"
        f"Совместимость: <b>{percent}%</b>"
    )


# =========================================================
# ДУЭЛЬ
# =========================================================

def command_duel(
    chat_id,
    message
):

    users = get_users(
        chat_id
    )

    if len(users) < 2:

        return "😐 Нужно минимум 2 участника."

    reply = message.get(
        "reply_to_message"
    )

    if reply:

        target = reply.get(
            "from"
        )

        if target and not target.get(
            "is_bot"
        ):

            save_user(
                chat_id,
                target
            )

            target_id = target.get(
                "id"
            )

            others = [
                x for x in users
                if x["user_id"] != target_id
            ]

            if others:

                a = random.choice(
                    others
                )

                b = target

                return (
                    "⚔️ <b>ДУЭЛЬ!</b>\n\n"
                    f"🥊 {mention_user(a)}\n"
                    f"🆚\n"
                    f"🥊 {mention_user(b)}\n\n"
                    f"🏆 Победитель: "
                    f"{mention_user(random.choice([a, b]))}"
                )

    a, b = random.sample(
        users,
        2
    )

    winner = random.choice(
        [a, b]
    )

    return (
        "⚔️ <b>ДУЭЛЬ!</b>\n\n"
        f"🥊 {mention_user(a)}\n"
        f"🆚\n"
        f"🥊 {mention_user(b)}\n\n"
        f"🏆 Победитель:\n"
        f"{mention_user(winner)}"
    )


# =========================================================
# 8 BALL
# =========================================================

def command_8ball():

    answers = [

        "🎱 Да.",
        "🎱 Нет.",
        "🎱 Скорее всего.",
        "🎱 Определённо.",
        "🎱 Сомнительно.",
        "🎱 Даже не думай.",
        "🎱 Возможно.",
        "🎱 Судьба решит.",
        "🎱 База.",
        "🎱 Сейчас лучше не надо."
    ]

    return random.choice(
        answers
    )


# =========================================================
# ПРАВДА ИЛИ ДЕЙСТВИЕ
# =========================================================

def command_truth():

    truths = [

        "Кто тебе нравится в этом чате?",
        "Какой самый кринжовый поступок ты совершал?",
        "Кому из чата ты доверяешь больше всего?",
        "Какой твой самый странный секрет?",
        "Кого бы ты взял с собой на необитаемый остров?"
    ]

    actions = [

        "Напиши последнему человеку в личке «Привет 😎».",
        "Поставь себе смешной статус на 10 минут.",
        "Отправь в чат случайный смайлик.",
        "Напиши сообщение только капсом.",
        "Сделай комплимент любому участнику."
    ]

    if random.choice(
        [True, False]
    ):

        return (
            "🎭 <b>ПРАВДА</b>\n\n"
            + random.choice(truths)
        )

    return (
        "🔥 <b>ДЕЙСТВИЕ</b>\n\n"
        + random.choice(actions)
    )


# =========================================================
# РУЛЕТКА
# =========================================================

def command_roulette():

    tasks = [

        "😂 Напиши сообщение только эмодзи.",
        "😎 Назови себя главным человеком чата.",
        "🐔 Напиши последнее сообщение с добавлением «кукареку».",
        "🤔 Напиши первое слово, которое пришло в голову.",
        "🔥 Сделай комплимент случайному участнику.",
        "💀 Отправь самый странный смайлик.",
        "🎤 Напиши строчку из любой песни.",
        "🗿 Напиши «Я легенда»."
    ]

    return (
        "🎰 <b>РУЛЕТКА</b>\n\n"
        + random.choice(tasks)
    )


# =========================================================
# ПРОЗВИЩЕ
# =========================================================

def command_nickname():

    first = [

        "Супер",
        "Легендарный",
        "Космический",
        "Безумный",
        "Главный",
        "Таинственный",
        "Могучий",
        "Сигма",
        "Кринжовый",
        "Босс"
    ]

    second = [

        "Гусь",
        "Кабан",
        "Кот",
        "Пельмень",
        "Ниндзя",
        "Терминатор",
        "Бобёр",
        "Мозг",
        "Миллионер",
        "Дракон"
    ]

    return (
        "🏷 Твоё новое прозвище:\n\n"
        f"<b>{random.choice(first)} "
        f"{random.choice(second)}</b>"
    )


# =========================================================
# ОПРАВДАНИЕ
# =========================================================

def command_excuse():

    excuses = [

        "Я не опоздал, это время пришло слишком рано.",
        "Телефон разрядился именно в самый важный момент.",
        "Я собирался это сделать, но судьба решила иначе.",
        "У меня был план. План был плохой.",
        "Я думал, что сегодня уже завтра.",
        "Виноват интернет.",
        "Меня отвлёк очень важный голубь.",
        "Я просто проверял, заметите ли вы моё отсутствие."
    ]

    return (
        "📝 <b>Оправдание:</b>\n\n"
        + random.choice(excuses)
    )


# =========================================================
# ЗАДАНИЕ
# =========================================================

def command_task():

    tasks = [

        "Напиши в чат комплимент.",
        "Отправь три случайных эмодзи.",
        "Назови любимую игру.",
        "Расскажи самый странный факт о себе.",
        "Напиши сообщение без буквы «а».",
        "Придумай новое слово.",
        "Назови фильм, который готов пересматривать.",
        "Сделай кому-нибудь смешное прозвище."
    ]

    return (
        "🎯 <b>Твоё задание:</b>\n\n"
        + random.choice(tasks)
    )


# =========================================================
# CHOOSE
# =========================================================

def command_choose(text):

    parts = text.split(
        maxsplit=1
    )

    if len(parts) < 2:

        return (
            "❓ Пример:\n"
            "<code>/choose пицца или суши или бургер</code>"
        )

    options = [

        x.strip()

        for x in parts[1].split(
            " или "
        )

        if x.strip()
    ]

    if len(options) < 2:

        return (
            "❓ Напиши минимум "
            "2 варианта через «или»."
        )

    return (
        "🎯 Я выбираю:\n\n"
        f"<b>{html.escape(random.choice(options))}</b>"
    )


# =========================================================
# СТАТИСТИКА
# =========================================================

def command_stats(chat_id):

    with db_lock:

        conn = get_db()

        total = conn.execute("""
            SELECT SUM(messages) AS total
            FROM users
            WHERE chat_id = ?
        """, (
            chat_id,
        )).fetchone()

        users = conn.execute("""
            SELECT COUNT(*) AS count
            FROM users
            WHERE chat_id = ?
        """, (
            chat_id,
        )).fetchone()

        conn.close()

    total_messages = (
        total["total"] or 0
    )

    return (
        "📊 <b>Статистика чата</b>\n\n"
        f"👥 Участников: <b>{users['count']}</b>\n"
        f"💬 Сообщений: <b>{total_messages}</b>"
    )


# =========================================================
# TOP
# =========================================================

def command_top(chat_id):

    with db_lock:

        conn = get_db()

        rows = conn.execute("""
            SELECT *
            FROM users
            WHERE chat_id = ?
            ORDER BY messages DESC
            LIMIT 10
        """, (
            chat_id,
        )).fetchall()

        conn.close()

    if not rows:

        return "📊 Пока нет статистики."

    result = [
        "🏆 <b>ТОП АКТИВНЫХ</b>",
        ""
    ]

    medals = [
        "🥇",
        "🥈",
        "🥉"
    ]

    for i, row in enumerate(rows):

        medal = (
            medals[i]
            if i < 3
            else f"{i + 1}."
        )

        result.append(
            f"{medal} "
            f"{html.escape(row['name'])} — "
            f"<b>{row['messages']}</b>"
        )

    return "\n".join(
        result
    )


# =========================================================
# SUMMARIZE
# =========================================================

def command_summarize(chat_id):

    with db_lock:

        conn = get_db()

        rows = conn.execute("""
            SELECT name, text
            FROM chat_history
            WHERE chat_id = ?
            ORDER BY id DESC
            LIMIT 30
        """, (
            chat_id,
        )).fetchall()

        conn.close()

    if not rows:

        return (
            "🤷 Пока нет сообщений "
            "для анализа."
        )

    rows = list(
        reversed(rows)
    )

    conversation = "\n".join(
        f"{row['name']}: {row['text']}"
        for row in rows
    )

    prompt = f"""
Кратко перескажи эту переписку Telegram.

Выдели:
1. Главные темы.
2. Что обсуждали.
3. Важные решения.
4. Самые заметные моменты.

Не выдумывай информацию.

Переписка:

{conversation}
"""

    try:

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=700,
            temperature=0.4
        )

        answer = response.choices[0].message.content

        return (
            "📝 <b>Краткая сводка:</b>\n\n"
            + html.escape(answer)
        )

    except Exception as e:

        print(
            "SUMMARIZE ERROR:",
            e
        )

        return (
            "⚠️ Не получилось "
            "сделать сводку."
        )


# =========================================================
# QUIZ
# =========================================================

QUIZ_QUESTIONS = [

    (
        "Столица Франции?",
        [
            "Париж",
            "Лондон",
            "Берлин",
            "Рим"
        ],
        0
    ),

    (
        "Сколько планет в Солнечной системе?",
        [
            "7",
            "8",
            "9",
            "10"
        ],
        1
    ),

    (
        "Какой океан самый большой?",
        [
            "Атлантический",
            "Индийский",
            "Тихий",
            "Северный Ледовитый"
        ],
        2
    ),

    (
        "Сколько сторон у треугольника?",
        [
            "2",
            "3",
            "4",
            "5"
        ],
        1
    )
]


def command_quiz(chat_id):

    question, options, correct = random.choice(
        QUIZ_QUESTIONS
    )

    result = telegram_request(
        "sendPoll",
        {
            "chat_id": chat_id,
            "question": "🧠 " + question,
            "options": [
                {"text": x}
                for x in options
            ],
            "type": "quiz",
            "correct_option_id": correct,
            "is_anonymous": False
        }
    )

    if result:

        return None

    return (
        "❌ Не удалось запустить викторину."
    )


# =========================================================
# ОПРОС
# =========================================================

def command_poll(
    chat_id,
    text
):

    parts = text.split(
        maxsplit=1
    )

    if len(parts) < 2:

        return (
            "❓ Пример:\n\n"
            "<code>/poll Пицца или суши</code>"
        )

    options = [
        x.strip()
        for x in parts[1].split(
            " или "
        )
        if x.strip()
    ]

    if len(options) < 2:

        return (
            "❌ Нужно минимум "
            "2 варианта через «или»."
        )

    if len(options) > 10:

        return (
            "❌ Максимум 10 вариантов."
        )

    result = telegram_request(
        "sendPoll",
        {
            "chat_id": chat_id,
            "question": "📊 Опрос",
            "options": [
                {"text": x}
                for x in options
            ],
            "is_anonymous": False
        }
    )

    if result:

        return None

    return "❌ Не удалось создать опрос."


# =========================================================
# GUESS
# =========================================================

def start_guess(chat_id):

    number = random.randint(
        1,
        10
    )

    guess_number[
        chat_id
    ] = number

    return (
        "🎯 Я загадал число от "
        "<b>1 до 10</b>.\n\n"
        "Пиши свой вариант."
    )


def check_guess(
    chat_id,
    text
):

    if chat_id not in guess_number:
        return None

    if not text.isdigit():
        return None

    number = guess_number[
        chat_id
    ]

    guess = int(text)

    if guess < 1 or guess > 10:

        return (
            "Число должно быть "
            "от 1 до 10."
        )

    if guess == number:

        del guess_number[
            chat_id
        ]

        return (
            f"🎉 Правильно!\n"
            f"Я загадал <b>{number}</b>."
        )

    if guess < number:

        return "⬆️ Моё число больше."

    return "⬇️ Моё число меньше."


# =========================================================
# АНТИСПАМ
# =========================================================

def is_spam(
    chat_id,
    user_id
):

    now = time.time()

    key = (
        chat_id,
        user_id
    )

    timestamps = spam_tracker[
        key
    ]

    timestamps.append(
        now
    )

    recent = [
        x for x in timestamps
        if now - x < 5
    ]

    spam_tracker[
        key
    ] = deque(
        recent,
        maxlen=10
    )

    return len(recent) >= 7


# =========================================================
# ПРИВЕТСТВИЕ
# =========================================================

def welcome_new_members(
    chat_id,
    members
):

    for user in members:

        save_user(
            chat_id,
            user
        )

        mention = mention_user(
            {
                "user_id": user["id"],
                "name":
                    (
                        user.get(
                            "first_name",
                            "участник"
                        )
                        + " "
                        + user.get(
                            "last_name",
                            ""
                        )
                    ).strip()
            }
        )

        send_message(
            chat_id,
            f"👋 Добро пожаловать, "
            f"{mention}!\n\n"
            f"Осваивайся 😎"
        )


# =========================================================
# ВЫХОД
# =========================================================

def goodbye_member(
    chat_id,
    user
):

    if not user:
        return

    name = html.escape(
        user.get(
            "first_name",
            "Участник"
        )
    )

    send_message(
        chat_id,
        f"👋 {name} покинул чат."
    )


# =========================================================
# ОБРАБОТКА
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


        # =================================================
        # НОВЫЕ УЧАСТНИКИ
        # =================================================

        if "message" in update:

            message = update[
                "message"
            ]

            chat = message.get(
                "chat",
                {}
            )

            chat_id = chat.get(
                "id"
            )

            chat_type = chat.get(
                "type"
            )


            new_members = message.get(
                "new_chat_members"
            )

            if new_members:

                welcome_new_members(
                    chat_id,
                    new_members
                )


            left_member = message.get(
                "left_chat_member"
            )

            if left_member:

                goodbye_member(
                    chat_id,
                    left_member
                )


        # =================================================
        # CALLBACK / POLL
        # =================================================

        if "poll_answer" in update:

            return "OK"


        message = update.get(
            "message"
        )

        if not message:

            return "OK"


        chat = message.get(
            "chat",
            {}
        )

        chat_id = chat.get(
            "id"
        )

        chat_type = chat.get(
            "type"
        )

        user = message.get(
            "from",
            {}
        )

        user_id = user.get(
            "id"
        )

        first_name = user.get(
            "first_name",
            "Участник"
        )

        text = message.get(
            "text",
            ""
        ) or ""

        message_id = message.get(
            "message_id"
        )


        # =================================================
        # СОХРАНЯЕМ ПОЛЬЗОВАТЕЛЯ
        # =================================================

        save_user(
            chat_id,
            user
        )


        # =================================================
        # СТАТИСТИКА
        # =================================================

        if text:

            add_message_stat(
                chat_id,
                user_id,
                first_name,
                text
            )


        print(
            "📩",
            chat_id,
            first_name,
            ":",
            text
        )


        # =================================================
        # АНТИСПАМ
        # =================================================

        if (
            chat_type in [
                "group",
                "supergroup"
            ]
            and user_id
            and text
        ):

            if is_spam(
                chat_id,
                user_id
            ):

                send_message(
                    chat_id,
                    "🛑 Эй, полегче 😄 "
                    "Слишком много сообщений подряд."
                )

                return "OK"


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

            send_message(
                chat_id,
                command_who(
                    chat_id
                )
            )

            return "OK"


        # =================================================
        # /START
        # =================================================

        if text.startswith(
            "/start"
        ):

            send_message(
                chat_id,
                """
🤖 <b>Привет!</b>

Я AI-бот для вашего чата.

Просто напиши мне сообщение
или упомяни меня в группе.

🎮 Введите <code>/</code>,
чтобы увидеть все команды.

👤 Также можно написать:

<code>Кто в чате самый смешной?</code>
""",
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /STYLE
        # =================================================

        if text.startswith(
            "/style"
        ):

            send_message(
                chat_id,
                style_command(
                    chat_id,
                    text
                ),
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /WHO
        # =================================================

        if text.startswith(
            "/who"
        ):

            send_message(
                chat_id,
                command_who(
                    chat_id
                ),
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /PAIR
        # =================================================

        if text.startswith(
            "/pair"
        ):

            send_message(
                chat_id,
                command_pair(
                    chat_id
                ),
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /DUEL
        # =================================================

        if text.startswith(
            "/duel"
        ):

            send_message(
                chat_id,
                command_duel(
                    chat_id,
                    message
                ),
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /8BALL
        # =================================================

        if text.startswith(
            "/8ball"
        ):

            send_message(
                chat_id,
                command_8ball(),
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /TRUTH
        # =================================================

        if text.startswith(
            "/truth"
        ):

            send_message(
                chat_id,
                command_truth(),
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /ROULETTE
        # =================================================

        if text.startswith(
            "/roulette"
        ):

            send_message(
                chat_id,
                command_roulette(),
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /NICKNAME
        # =================================================

        if text.startswith(
            "/nickname"
        ):

            send_message(
                chat_id,
                command_nickname(),
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /EXCUSE
        # =================================================

        if text.startswith(
            "/excuse"
        ):

            send_message(
                chat_id,
                command_excuse(),
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /TASK
        # =================================================

        if text.startswith(
            "/task"
        ):

            send_message(
                chat_id,
                command_task(),
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /CHOOSE
        # =================================================

        if text.startswith(
            "/choose"
        ):

            send_message(
                chat_id,
                command_choose(
                    text
                ),
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /STATS
        # =================================================

        if text.startswith(
            "/stats"
        ):

            send_message(
                chat_id,
                command_stats(
                    chat_id
                ),
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /TOP
        # =================================================

        if text.startswith(
            "/top"
        ):

            send_message(
                chat_id,
                command_top(
                    chat_id
                ),
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /SUMMARIZE
        # =================================================

        if text.startswith(
            "/summarize"
        ):

            send_message(
                chat_id,
                command_summarize(
                    chat_id
                ),
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /QUIZ
        # =================================================

        if text.startswith(
            "/quiz"
        ):

            result = command_quiz(
                chat_id
            )

            if result:

                send_message(
                    chat_id,
                    result,
                    reply_to=message_id
                )

            return "OK"


        # =================================================
        # /POLL
        # =================================================

        if text.startswith(
            "/poll"
        ):

            result = command_poll(
                chat_id,
                text
            )

            if result:

                send_message(
                    chat_id,
                    result,
                    reply_to=message_id
                )

            return "OK"


        # =================================================
        # /COIN
        # =================================================

        if text.startswith(
            "/coin"
        ):

            send_message(
                chat_id,
                random.choice(
                    [
                        "🪙 Орёл",
                        "🪙 Решка"
                    ]
                ),
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /DICE
        # =================================================

        if text.startswith(
            "/dice"
        ):

            send_message(
                chat_id,
                f"🎲 Выпало: "
                f"<b>{random.randint(1, 6)}</b>",
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # /JOKE
        # =================================================

        if text.startswith(
            "/joke"
        ):

            jokes = [

                "🐛 Почему программист не ходит в лес? Там слишком много багов.",

                "📱 Хотел пошутить про Wi-Fi, но связь оборвалась.",

                "💻 Мой код работает. Почему — не спрашивай.",

                "😂 Дедлайн — лучший программист."

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

        if text.startswith(
            "/fact"
        ):

            facts = [

                "🐙 У осьминога три сердца.",

                "🦈 Акулы существовали раньше деревьев.",

                "🐝 Пчёлы могут различать человеческие лица.",

                "🌍 Земля немного сплюснута у полюсов.",

                "🚀 В космосе нет обычного распространения звука."

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

        if text.startswith(
            "/roast"
        ):

            target = text[
                6:
            ].strip()

            if not target:

                target = "тебя"

            roasts = [

                f"😂 {target}, у тебя уверенности больше, чем аргументов.",

                f"💀 {target}, даже бот иногда не понимает, что ты пишешь.",

                f"🐢 {target}, тебя даже черепаха обгоняет.",

                f"🗿 {target}, сильный заход. Жаль, что мимо.",

                f"📡 {target}, попробуй сначала подключить мозг к Wi-Fi."

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

        if text.startswith(
            "/ask"
        ):

            question = text[
                4:
            ].strip()

            if not question:

                send_message(
                    chat_id,
                    "❓ Пример: "
                    "<code>/ask сколько будет 2+2?</code>",
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

        if text.startswith(
            "/guess"
        ):

            send_message(
                chat_id,
                start_guess(
                    chat_id
                ),
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # ПРОВЕРКА GUESS
        # =================================================

        guess_result = check_guess(
            chat_id,
            text.strip()
        )

        if guess_result:

            send_message(
                chat_id,
                guess_result,
                reply_to=message_id
            )

            return "OK"


        # =================================================
        # АВТООТВЕТЫ
        # =================================================

        lower = text.lower().strip()

        auto_answers = {

            "привет": [
                "👋 Привет!",
                "😎 Здарова!",
                "🤖 На связи!"
            ],

            "доброе утро": [
                "☀️ Доброе утро!",
                "🌅 Всем доброго утра!"
            ],

            "спокойной ночи": [
                "🌙 Спокойной ночи!",
                "😴 Выключай телефон и спать!"
            ],

            "кто тут": [
                "🤖 Я тут.",
                "👀 Наблюдаю за вами."
            ]
        }

        if lower in auto_answers:

            send_message(
                chat_id,
                random.choice(
                    auto_answers[lower]
                )
            )

            return "OK"


        # =================================================
        # НУЖНО ЛИ AI ОТВЕЧАТЬ
        # =================================================

        should_answer = False

        if chat_type == "private":

            should_answer = True

        elif chat_type in [
            "group",
            "supergroup"
        ]:

            if (
                f"@{BOT_USERNAME.lower()}"
                in text.lower()
            ):

                should_answer = True

            reply = message.get(
                "reply_to_message"
            )

            if reply:

                reply_from = reply.get(
                    "from",
                    {}
                )

                username = (
                    reply_from.get(
                        "username",
                        ""
                    ).lower()
                )

                if username == BOT_USERNAME.lower():

                    should_answer = True


        if not should_answer:

            return "OK"


        # =================================================
        # ОЧИЩАЕМ ТЕКСТ
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


        send_message(
            chat_id,
            html.escape(answer),
            reply_to=message_id
        )

        return "OK"


    except Exception as e:

        print(
            "❌ WEBHOOK ERROR:",
            e
        )

        return "OK"


# =========================================================
# ГЛАВНАЯ
# =========================================================

@app.route(
    "/",
    methods=[
        "GET",
        "HEAD"
    ]
)
def home():

    return (
        "Telegram AI Bot is running!"
    )


# =========================================================
# ЗАПУСК
# =========================================================

if __name__ == "__main__":

    print(
        "================================"
    )

    print(
        "🤖 BOT STARTED"
    )

    print(
        "🗄 SQLite database enabled"
    )

    print(
        "📋 Installing Telegram commands..."
    )

    set_bot_commands()

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    print(
        f"🌐 Starting on port {port}"
    )

    print(
        "================================"
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
