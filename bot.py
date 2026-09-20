import os
import html
import random
import time
import requests

from flask import Flask, request

import database
import ai
import games
import moderation
import image_ai


# =====================================================
# START
# =====================================================

database.init_db()


TOKEN = os.environ.get(
    "TELEGRAM_TOKEN"
)

BOT_USERNAME = "hren_67_bot"


API = (
    f"https://api.telegram.org/bot{TOKEN}"
)


app = Flask(__name__)


# =====================================================
# TELEGRAM
# =====================================================

def tg(
    method,
    data=None
):

    try:

        r = requests.post(
            f"{API}/{method}",
            json=data or {},
            timeout=40
        )

        print(
            "TG:",
            method,
            r.status_code
        )

        return r.json()

    except Exception as e:

        print(
            "TG ERROR:",
            e
        )

        return None


def send(
    chat_id,
    text,
    reply=None
):

    data = {

        "chat_id":
            chat_id,

        "text":
            text,

        "parse_mode":
            "HTML"
    }

    if reply:

        data[
            "reply_parameters"
        ] = {
            "message_id":
                reply
        }

    return tg(
        "sendMessage",
        data
    )


def photo(
    chat_id,
    filename,
    caption=""
):

    try:

        with open(
            filename,
            "rb"
        ) as f:

            r = requests.post(

                f"{API}/sendPhoto",

                data={
                    "chat_id":
                        chat_id,

                    "caption":
                        caption
                },

                files={
                    "photo":
                        f
                },

                timeout=120
            )

        return r.json()

    except Exception as e:

        print(
            "PHOTO ERROR:",
            e
        )

        return None


def download_telegram_file(
    file_id,
    filename
):

    try:

        result = tg(
            "getFile",
            {
                "file_id":
                    file_id
            }
        )

        path = (
            result
            ["result"]
            ["file_path"]
        )

        url = (
            f"https://api.telegram.org/file/"
            f"bot{TOKEN}/{path}"
        )

        r = requests.get(
            url,
            timeout=60
        )

        with open(
            filename,
            "wb"
        ) as f:

            f.write(
                r.content
            )

        return True

    except Exception as e:

        print(
            "DOWNLOAD ERROR:",
            e
        )

        return False


# =====================================================
# HELPERS
# =====================================================

def mention(user):

    name = html.escape(
        (
            user.get(
                "first_name",
                ""
            )
            + " "
            + user.get(
                "last_name",
                ""
            )
        ).strip()
        or "Участник"
    )

    return (
        f'<a href="tg://user?id={user["id"]}">'
        f'{name}'
        f'</a>'
    )


def random_user(
    chat_id
):

    users = database.get_users(
        chat_id
    )

    if not users:

        return None

    row = random.choice(
        users
    )

    return {
        "id":
            row["user_id"],

        "first_name":
            row["name"]
    }


# =====================================================
# COMMANDS
# =====================================================

COMMANDS = [

    {
        "command":
            "start",

        "description":
            "Запустить бота"
    },

    {
        "command":
            "help",

        "description":
            "Все возможности"
    },

    {
        "command":
            "ask",

        "description":
            "Спросить AI"
    },

    {
        "command":
            "style",

        "description":
            "Стиль AI"
    },

    {
        "command":
            "img",

        "description":
            "Создать изображение"
    },

    {
        "command":
            "edit",

        "description":
            "Изменить фото"
    },

    {
        "command":
            "summarize",

        "description":
            "Сводка чата"
    },

    {
        "command":
            "profile",

        "description":
            "Профиль"
    },

    {
        "command":
            "top",

        "description":
            "Топ участников"
    },

    {
        "command":
            "balance",

        "description":
            "Баланс монет"
    },

    {
        "command":
            "daily",

        "description":
            "Ежедневная награда"
    },

    {
        "command":
            "pay",

        "description":
            "Передать монеты"
    },

    {
        "command":
            "who",

        "description":
            "Случайный участник"
    },

    {
        "command":
            "pair",

        "description":
            "Случайная пара"
    },

    {
        "command":
            "duel",

        "description":
            "Дуэль"
    },

    {
        "command":
            "8ball",

        "description":
            "Магический шар"
    },

    {
        "command":
            "truth",

        "description":
            "Правда или действие"
    },

    {
        "command":
            "task",

        "description":
            "Задание"
    },

    {
        "command":
            "nickname",

        "description":
            "Прозвище"
    },

    {
        "command":
            "choose",

        "description":
            "Выбрать вариант"
    },

    {
        "command":
            "coin",

        "description":
            "Монетка"
    },

    {
        "command":
            "dice",

        "description":
            "Кубик"
    },

    {
        "command":
            "guess",

        "description":
            "Угадай число"
    },

    {
        "command":
            "quiz",

        "description":
            "Викторина"
    },

    {
        "command":
            "poll",

        "description":
            "Опрос"
    },

    {
        "command":
            "stats",

        "description":
            "Статистика"
    },

    {
        "command":
            "warn",

        "description":
            "Предупредить"
    },

    {
        "command":
            "mute",

        "description":
            "Замутить"
    },

    {
        "command":
            "ban",

        "description":
            "Заблокировать"
    }
]


def install_commands():

    tg(
        "setMyCommands",
        {
            "commands":
                COMMANDS
        }
    )


# =====================================================
# HELP
# =====================================================

def help_text():

    return """
🤖 <b>МОИ ВОЗМОЖНОСТИ</b>

🧠 <b>AI</b>

/ask вопрос
/img описание картинки
/edit описание изменения фото
/summarize

🎮 <b>Игры</b>

/who
/pair
/duel
/8ball
/truth
/task
/nickname
/choose
/coin
/dice
/guess
/quiz

👤 <b>Профиль</b>

/profile
/top
/stats

💰 <b>Экономика</b>

/balance
/daily
/pay

🛡 <b>Модерация</b>

/warn
/mute
/ban

🎭 <b>AI-стили</b>

/style normal
/style friend
/style troll
/style rude
/style serious
/style expert
/style sigma

В группе можно просто написать:

<code>@hren_67_bot привет</code>
"""


# =====================================================
# PROFILE
# =====================================================

def profile(
    chat_id,
    user
):

    database.save_user(
        chat_id,
        user
    )

    row = database.get_user(
        chat_id,
        user["id"]
    )

    level = database.get_level(
        row["xp"]
    )

    achievements = database.get_achievements(
        chat_id,
        user["id"]
    )

    achievement_text = (
        " ".join(
            "🏅"
            for _ in achievements
        )
        or "Нет"
    )

    return f"""
👤 <b>ПРОФИЛЬ</b>

Имя: <b>{html.escape(row["name"])}</b>

🏆 Уровень: <b>{level}</b>
⭐ XP: <b>{row["xp"]}</b>
💬 Сообщений: <b>{row["messages"]}</b>
💰 Монеты: <b>{row["coins"]}</b>

⚠️ Предупреждений: <b>{row["warnings"]}</b>

🏅 Достижения:
{achievement_text}
"""


# =====================================================
# TOP
# =====================================================

def top(
    chat_id
):

    rows = database.get_top(
        chat_id
    )

    if not rows:

        return "Пока нет статистики."

    result = [
        "🏆 <b>ТОП ЧАТА</b>",
        ""
    ]

    medals = [
        "🥇",
        "🥈",
        "🥉"
    ]

    for i, row in enumerate(rows):

        prefix = (
            medals[i]
            if i < 3
            else f"{i + 1}."
        )

        level = database.get_level(
            row["xp"]
        )

        result.append(
            f"{prefix} "
            f"{html.escape(row['name'])} "
            f"— {row['xp']} XP "
            f"(LVL {level})"
        )

    return "\n".join(
        result
    )


# =====================================================
# DAILY
# =====================================================

def daily(
    chat_id,
    user
):

    database.save_user(
        chat_id,
        user
    )

    row = database.get_user(
        chat_id,
        user["id"]
    )

    now = int(
        time.time()
    )

    # SQLite
    import sqlite3

    conn = sqlite3.connect(
        database.DB_FILE
    )

    conn.row_factory = sqlite3.Row

    old = conn.execute("""
    SELECT last_claim
    FROM daily
    WHERE chat_id=?
    AND user_id=?
    """, (
        chat_id,
        user["id"]
    )).fetchone()

    if old:

        if now - old["last_claim"] < 86400:

            conn.close()

            return (
                "⏳ Ты уже получил "
                "ежедневную награду."
            )

        conn.execute("""
        UPDATE daily
        SET last_claim=?
        WHERE chat_id=?
        AND user_id=?
        """, (
            now,
            chat_id,
            user["id"]
        ))

    else:

        conn.execute("""
        INSERT INTO daily
        (chat_id,user_id,last_claim)
        VALUES(?,?,?)
        """, (
            chat_id,
            user["id"],
            now
        ))

    conn.commit()
    conn.close()

    reward = random.randint(
        50,
        150
    )

    database.add_coins(
        chat_id,
        user["id"],
        reward
    )

    return (
        f"🎁 Ежедневная награда: "
        f"<b>+{reward} 🪙</b>"
    )


# =====================================================
# BALANCE
# =====================================================

def balance(
    chat_id,
    user
):

    row = database.get_user(
        chat_id,
        user["id"]
    )

    if not row:

        database.save_user(
            chat_id,
            user
        )

        row = database.get_user(
            chat_id,
            user["id"]
        )

    return (
        f"💰 Твой баланс: "
        f"<b>{row['coins']} 🪙</b>"
    )


# =====================================================
# CHOOSE
# =====================================================

def choose(
    text
):

    data = text[
        len("/choose"):
    ].strip()

    if not data:

        return (
            "Пример:\n"
            "<code>/choose пицца | суши | бургер</code>"
        )

    options = [
        x.strip()
        for x in data.split("|")
        if x.strip()
    ]

    if len(options) < 2:

        return (
            "Нужно минимум "
            "2 варианта через |"
        )

    result = random.choice(
        options
    )

    return (
        "🎯 Выбираю...\n\n"
        f"<b>{html.escape(result)}</b>"
    )


# =====================================================
# IMAGE
# =====================================================

def make_image(
    chat_id,
    prompt
):

    filename = (
        f"/tmp/"
        f"image_{chat_id}_{int(time.time())}.png"
    )

    send(
        chat_id,
        "🎨 Генерирую изображение... ⏳"
    )

    ok = image_ai.generate_image(
        prompt,
        filename
    )

    if not ok:

        send(
            chat_id,
            "❌ Не получилось создать изображение."
        )

        return

    photo(
        chat_id,
        filename,
        "🎨 Готово!"
    )


# =====================================================
# EDIT PHOTO
# =====================================================

def edit_photo(
    chat_id,
    message,
    prompt
):

    if not prompt:

        send(
            chat_id,
            "Напиши, как изменить фото."
        )

        return

    photos = message.get(
        "photo"
    )

    if not photos:

        send(
            chat_id,
            "📸 Сначала отправь фотографию "
            "с командой /edit в подписи."
        )

        return

    largest = photos[-1]

    file_id = largest[
        "file_id"
    ]

    source = (
        f"/tmp/source_{chat_id}.jpg"
    )

    output = (
        f"/tmp/edit_{chat_id}.png"
    )

    if not download_telegram_file(
        file_id,
        source
    ):

        send(
            chat_id,
            "❌ Не удалось получить фото."
        )

        return

    send(
        chat_id,
        "🪄 Редактирую фото... ⏳"
    )

    try:

        with open(
            source,
            "rb"
        ) as f:

            image_bytes = f.read()

        ok = image_ai.edit_image(
            image_bytes,
            prompt,
            output
        )

        if not ok:

            send(
                chat_id,
                "❌ Не удалось изменить фото."
            )

            return

        photo(
            chat_id,
            output,
            "🪄 Готово!"
        )

    except Exception as e:

        print(
            "EDIT ERROR:",
            e
        )

        send(
            chat_id,
            "❌ Ошибка редактирования."
        )


# =====================================================
# MAIN UPDATE
# =====================================================

@app.route(
    "/telegram",
    methods=["POST"]
)
def webhook():

    try:

        update = request.get_json()

        if not update:

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

        text = (
            message.get(
                "text",
                ""
            )
            or ""
        )

        caption = (
            message.get(
                "caption",
                ""
            )
            or ""
        )

        message_id = message.get(
            "message_id"
        )


        # =============================================
        # USER
        # =============================================

        database.save_user(
            chat_id,
            user
        )


        # =============================================
        # NEW MEMBERS
        # =============================================

        new_members = message.get(
            "new_chat_members"
        )

        if new_members:

            for member in new_members:

                database.save_user(
                    chat_id,
                    member
                )

                send(
                    chat_id,
                    "👋 Добро пожаловать, "
                    + mention(member)
                    + "!"
                )


        # =============================================
        # MESSAGE STATS
        # =============================================

        if text:

            database.add_message(
                chat_id,
                user,
                text
            )


        # =============================================
        # ANTI SPAM
        # =============================================

        if (
            chat_type in
            ["group", "supergroup"]
            and text
        ):

            if moderation.is_spam(
                chat_id,
                user["id"]
            ):

                send(
                    chat_id,
                    "🛑 Сбавь обороты 😄",
                    message_id
                )

                return "OK"


        # =============================================
        # /START
        # =============================================

        if text.startswith(
            "/start"
        ):

            send(
                chat_id,
                help_text(),
                message_id
            )

            return "OK"


        # =============================================
        # /HELP
        # =============================================

        if text.startswith(
            "/help"
        ):

            send(
                chat_id,
                help_text(),
                message_id
            )

            return "OK"


        # =============================================
        # /PROFILE
        # =============================================

        if text.startswith(
            "/profile"
        ):

            send(
                chat_id,
                profile(
                    chat_id,
                    user
                ),
                message_id
            )

            return "OK"


        # =============================================
        # /TOP
        # =============================================

        if text.startswith(
            "/top"
        ):

            send(
                chat_id,
                top(chat_id),
                message_id
            )

            return "OK"


        # =============================================
        # /BALANCE
        # =============================================

        if text.startswith(
            "/balance"
        ):

            send(
                chat_id,
                balance(
                    chat_id,
                    user
                ),
                message_id
            )

            return "OK"


        # =============================================
        # /DAILY
        # =============================================

        if text.startswith(
            "/daily"
        ):

            send(
                chat_id,
                daily(
                    chat_id,
                    user
                ),
                message_id
            )

            return "OK"


        # =============================================
        # /WHO
        # =============================================

        if text.startswith(
            "/who"
        ):

            target = random_user(
                chat_id
            )

            if target:

                send(
                    chat_id,
                    "🎯 Выпал:\n\n"
                    + mention(target),
                    message_id
                )

            else:

                send(
                    chat_id,
                    "Пока не знаю участников.",
                    message_id
                )

            return "OK"


        # =============================================
        # /PAIR
        # =============================================

        if text.startswith(
            "/pair"
        ):

            users = database.get_users(
                chat_id
            )

            if len(users) < 2:

                send(
                    chat_id,
                    "Нужно минимум 2 участника.",
                    message_id
                )

                return "OK"

            a, b = random.sample(
                users,
                2
            )

            send(
                chat_id,
                "💘 <b>СЛУЧАЙНАЯ ПАРА</b>\n\n"
                f"❤️ {html.escape(a['name'])}\n"
                f"❤️ {html.escape(b['name'])}\n\n"
                f"Совместимость: "
                f"<b>{random.randint(1,100)}%</b>",
                message_id
            )

            return "OK"


        # =============================================
        # /DUEL
        # =============================================

        if text.startswith(
            "/duel"
        ):

            users = database.get_users(
                chat_id
            )

            if len(users) >= 2:

                a, b = random.sample(
                    users,
                    2
                )

                winner = random.choice(
                    [a, b]
                )

                send(
                    chat_id,
                    "⚔️ <b>ДУЭЛЬ</b>\n\n"
                    f"🥊 {html.escape(a['name'])}\n"
                    f"🆚\n"
                    f"🥊 {html.escape(b['name'])}\n\n"
                    f"🏆 Победитель: "
                    f"<b>{html.escape(winner['name'])}</b>",
                    message_id
                )

            return "OK"


        # =============================================
        # /8BALL
        # =============================================

        if text.startswith(
            "/8ball"
        ):

            send(
                chat_id,
                games.ball(),
                message_id
            )

            return "OK"


        # =============================================
        # /TRUTH
        # =============================================

        if text.startswith(
            "/truth"
        ):

            result = (
                games.truth()
                if random.choice(
                    [True, False]
                )
                else games.dare()
            )

            send(
                chat_id,
                result,
                message_id
            )

            return "OK"


        # =============================================
        # /TASK
        # =============================================

        if text.startswith(
            "/task"
        ):

            send(
                chat_id,
                games.task(),
                message_id
            )

            return "OK"


        # =============================================
        # /NICKNAME
        # =============================================

        if text.startswith(
            "/nickname"
        ):

            send(
                chat_id,
                "🏷 Твоё новое имя:\n\n"
                f"<b>{games.nickname()}</b>",
                message_id
            )

            return "OK"


        # =============================================
        # /CHOOSE
        # =============================================

        if text.startswith(
            "/choose"
        ):

            send(
                chat_id,
                choose(text),
                message_id
            )

            return "OK"


        # =============================================
        # /COIN
        # =============================================

        if text.startswith(
            "/coin"
        ):

            send(
                chat_id,
                games.coin(),
                message_id
            )

            return "OK"


        # =============================================
        # /DICE
        # =============================================

        if text.startswith(
            "/dice"
        ):

            send(
                chat_id,
                f"🎲 Выпало: "
                f"<b>{games.dice()}</b>",
                message_id
            )

            return "OK"


        # =============================================
        # /IMG
        # =============================================

        if text.startswith(
            "/img"
        ):

            prompt = text[
                len("/img"):
            ].strip()

            if not prompt:

                send(
                    chat_id,
                    "🎨 Пример:\n\n"
                    "<code>/img "
                    "чёрная машина возле вулкана, "
                    "молнии, огонь, киношный стиль</code>",
                    message_id
                )

                return "OK"

            make_image(
                chat_id,
                prompt
            )

            return "OK"


        # =============================================
        # /EDIT
        # =============================================

        if (
            text.startswith("/edit")
            and message.get("photo")
        ):

            prompt = text[
                len("/edit"):
            ].strip()

            edit_photo(
                chat_id,
                message,
                prompt
            )

            return "OK"


        # =============================================
        # /ASK
        # =============================================

        if text.startswith(
            "/ask"
        ):

            prompt = text[
                len("/ask"):
            ].strip()

            if not prompt:

                send(
                    chat_id,
                    "Пример:\n"
                    "<code>/ask объясни квантовую физику</code>",
                    message_id
                )

                return "OK"

            answer = ai.ask(
                chat_id,
                prompt,
                database.get_style(
                    chat_id
                )
            )

            send(
                chat_id,
                html.escape(answer),
                message_id
            )

            return "OK"


        # =============================================
        # /STYLE
        # =============================================

        if text.startswith(
            "/style"
        ):

            parts = text.split()

            if len(parts) == 1:

                send(
                    chat_id,
                    "🎭 Стили:\n\n"
                    + "\n".join(
                        f"• <code>{x}</code>"
                        for x in ai.STYLES
                    ),
                    message_id
                )

                return "OK"

            style = parts[1].lower()

            if style not in ai.STYLES:

                send(
                    chat_id,
                    "❌ Такого стиля нет.",
                    message_id
                )

                return "OK"

            database.set_style(
                chat_id,
                style
            )

            send(
                chat_id,
                f"✅ Стиль: <b>{style}</b>",
                message_id
            )

            return "OK"


        # =============================================
        # /SUMMARIZE
        # =============================================

        if text.startswith(
            "/summarize"
        ):

            rows = database.get_history(
                chat_id,
                30
            )

            conversation = "\n".join(
                f"{r['name']}: {r['text']}"
                for r in rows
            )

            if not conversation:

                send(
                    chat_id,
                    "Пока нечего суммировать.",
                    message_id
                )

                return "OK"

            send(
                chat_id,
                "🧠 Анализирую последние сообщения...",
                message_id
            )

            result = ai.summarize(
                conversation
            )

            send(
                chat_id,
                html.escape(result)
            )

            return "OK"


        # =============================================
        # /STATS
        # =============================================

        if text.startswith(
            "/stats"
        ):

            users = database.get_users(
                chat_id
            )

            total_messages = sum(
                x["messages"]
                for x in users
            )

            send(
                chat_id,
                "📊 <b>СТАТИСТИКА</b>\n\n"
                f"👥 Участников: "
                f"<b>{len(users)}</b>\n"
                f"💬 Сообщений: "
                f"<b>{total_messages}</b>",
                message_id
            )

            return "OK"


        # =============================================
        # /QUIZ
        # =============================================

        if text.startswith(
            "/quiz"
        ):

            questions = [

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
                    "Самый большой океан?",
                    [
                        "Атлантический",
                        "Индийский",
                        "Тихий",
                        "Северный Ледовитый"
                    ],
                    2
                )
            ]

            q, options, correct = random.choice(
                questions
            )

            tg(
                "sendPoll",
                {
                    "chat_id":
                        chat_id,

                    "question":
                        "🧠 " + q,

                    "options":
                        [
                            {
                                "text":
                                    x
                            }
                            for x in options
                        ],

                    "type":
                        "quiz",

                    "correct_option_id":
                        correct,

                    "is_anonymous":
                        False
                }
            )

            return "OK"


        # =============================================
        # @BOT MENTION
        # =============================================

        should_ai = False

        if chat_type == "private":

            should_ai = bool(
                text
            )

        elif chat_type in [
            "group",
            "supergroup"
        ]:

            if (
                f"@{BOT_USERNAME.lower()}"
                in text.lower()
            ):

                should_ai = True

            reply = message.get(
                "reply_to_message"
            )

            if reply:

                sender = reply.get(
                    "from",
                    {}
                )

                if (
                    sender.get(
                        "username",
                        ""
                    ).lower()
                    ==
                    BOT_USERNAME.lower()
                ):

                    should_ai = True


        if should_ai:

            clean = text.replace(
                f"@{BOT_USERNAME}",
                ""
            ).strip()

            if not clean:

                clean = "Привет!"

            answer = ai.ask(
                chat_id,
                clean,
                database.get_style(
                    chat_id
                )
            )

            send(
                chat_id,
                html.escape(answer),
                message_id
            )

            return "OK"


        return "OK"


    except Exception as e:

        print(
            "WEBHOOK ERROR:",
            repr(e)
        )

        return "OK"


# =====================================================
# HOME
# =====================================================

@app.route(
    "/",
    methods=[
        "GET",
        "HEAD"
    ]
)
def home():

    return "Telegram AI Bot is running!"


# =====================================================
# START
# =====================================================

if __name__ == "__main__":

    print(
        "================================"
    )

    print(
        "🤖 MAX AI BOT STARTED"
    )

    print(
        "🗄 SQLite enabled"
    )

    print(
        "🎨 Image AI enabled"
    )

    print(
        "🎮 Games enabled"
    )

    print(
        "🏆 XP enabled"
    )

    print(
        "💰 Economy enabled"
    )

    install_commands()

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
