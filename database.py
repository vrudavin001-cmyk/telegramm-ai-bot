import sqlite3
import threading
import time


DB_FILE = "bot.db"

lock = threading.Lock()


def db():
    conn = sqlite3.connect(
        DB_FILE,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    with lock:

        conn = db()

        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER,
            user_id INTEGER,
            username TEXT DEFAULT '',
            name TEXT DEFAULT '',
            messages INTEGER DEFAULT 0,
            xp INTEGER DEFAULT 0,
            coins INTEGER DEFAULT 100,
            warnings INTEGER DEFAULT 0,
            joined INTEGER,
            PRIMARY KEY(chat_id, user_id)
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            chat_id INTEGER PRIMARY KEY,
            style TEXT DEFAULT 'normal',
            antispam INTEGER DEFAULT 1
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            user_id INTEGER,
            name TEXT,
            text TEXT,
            created INTEGER
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            chat_id INTEGER,
            user_id INTEGER,
            achievement TEXT,
            created INTEGER,
            UNIQUE(chat_id, user_id, achievement)
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS daily (
            chat_id INTEGER,
            user_id INTEGER,
            last_claim INTEGER,
            PRIMARY KEY(chat_id, user_id)
        )
        """)

        conn.commit()
        conn.close()


def save_user(chat_id, user):

    if not user or user.get("is_bot"):
        return

    user_id = user["id"]

    name = (
        user.get("first_name", "")
        + " "
        + user.get("last_name", "")
    ).strip()

    username = user.get(
        "username",
        ""
    )

    with lock:

        conn = db()

        conn.execute("""
        INSERT INTO users
        (chat_id,user_id,username,name,joined)
        VALUES(?,?,?,?,?)
        ON CONFLICT(chat_id,user_id)
        DO UPDATE SET
            username=excluded.username,
            name=excluded.name
        """, (
            chat_id,
            user_id,
            username,
            name,
            int(time.time())
        ))

        conn.commit()
        conn.close()


def add_message(
    chat_id,
    user,
    text
):

    save_user(
        chat_id,
        user
    )

    user_id = user["id"]

    name = user.get(
        "first_name",
        "User"
    )

    with lock:

        conn = db()

        conn.execute("""
        UPDATE users
        SET
            messages=messages+1,
            xp=xp+5
        WHERE chat_id=?
        AND user_id=?
        """, (
            chat_id,
            user_id
        ))

        conn.execute("""
        INSERT INTO history
        (chat_id,user_id,name,text,created)
        VALUES(?,?,?,?,?)
        """, (
            chat_id,
            user_id,
            name,
            text[:1500],
            int(time.time())
        ))

        # Оставляем последние 100 сообщений
        conn.execute("""
        DELETE FROM history
        WHERE chat_id=?
        AND id NOT IN (
            SELECT id
            FROM history
            WHERE chat_id=?
            ORDER BY id DESC
            LIMIT 100
        )
        """, (
            chat_id,
            chat_id
        ))

        conn.commit()
        conn.close()


def get_user(
    chat_id,
    user_id
):

    conn = db()

    row = conn.execute("""
    SELECT *
    FROM users
    WHERE chat_id=?
    AND user_id=?
    """, (
        chat_id,
        user_id
    )).fetchone()

    conn.close()

    return row


def get_users(chat_id):

    conn = db()

    rows = conn.execute("""
    SELECT *
    FROM users
    WHERE chat_id=?
    AND messages > 0
    ORDER BY messages DESC
    """, (
        chat_id,
    )).fetchall()

    conn.close()

    return rows


def get_top(chat_id, limit=10):

    conn = db()

    rows = conn.execute("""
    SELECT *
    FROM users
    WHERE chat_id=?
    ORDER BY xp DESC
    LIMIT ?
    """, (
        chat_id,
        limit
    )).fetchall()

    conn.close()

    return rows


def get_history(
    chat_id,
    limit=30
):

    conn = db()

    rows = conn.execute("""
    SELECT *
    FROM history
    WHERE chat_id=?
    ORDER BY id DESC
    LIMIT ?
    """, (
        chat_id,
        limit
    )).fetchall()

    conn.close()

    return list(
        reversed(rows)
    )


def add_coins(
    chat_id,
    user_id,
    amount
):

    with lock:

        conn = db()

        conn.execute("""
        UPDATE users
        SET coins=coins+?
        WHERE chat_id=?
        AND user_id=?
        """, (
            amount,
            chat_id,
            user_id
        ))

        conn.commit()
        conn.close()


def add_warning(
    chat_id,
    user_id
):

    with lock:

        conn = db()

        conn.execute("""
        UPDATE users
        SET warnings=warnings+1
        WHERE chat_id=?
        AND user_id=?
        """, (
            chat_id,
            user_id
        ))

        conn.commit()

        row = conn.execute("""
        SELECT warnings
        FROM users
        WHERE chat_id=?
        AND user_id=?
        """, (
            chat_id,
            user_id
        )).fetchone()

        conn.close()

    return row["warnings"]


def set_style(
    chat_id,
    style
):

    with lock:

        conn = db()

        conn.execute("""
        INSERT INTO settings(chat_id,style)
        VALUES(?,?)
        ON CONFLICT(chat_id)
        DO UPDATE SET style=excluded.style
        """, (
            chat_id,
            style
        ))

        conn.commit()
        conn.close()


def get_style(chat_id):

    conn = db()

    row = conn.execute("""
    SELECT style
    FROM settings
    WHERE chat_id=?
    """, (
        chat_id,
    )).fetchone()

    conn.close()

    if row:
        return row["style"]

    return "normal"


def get_level(xp):

    return (
        xp // 100
    ) + 1


def add_achievement(
    chat_id,
    user_id,
    achievement
):

    with lock:

        conn = db()

        try:

            conn.execute("""
            INSERT INTO achievements
            (chat_id,user_id,achievement,created)
            VALUES(?,?,?,?)
            """, (
                chat_id,
                user_id,
                achievement,
                int(time.time())
            ))

            conn.commit()

            result = True

        except sqlite3.IntegrityError:

            result = False

        conn.close()

    return result


def get_achievements(
    chat_id,
    user_id
):

    conn = db()

    rows = conn.execute("""
    SELECT achievement
    FROM achievements
    WHERE chat_id=?
    AND user_id=?
    """, (
        chat_id,
        user_id
    )).fetchall()

    conn.close()

    return rows
