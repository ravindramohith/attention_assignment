# backend/database.py
import sqlite3
from datetime import datetime


def get_connection():
    conn = sqlite3.connect("travel_planner.db")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        title TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (username) REFERENCES users(username)
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        user_input TEXT NOT NULL,
        bot_response TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
    )
    """
    )

    conn.commit()
    conn.close()


def register_user(username: str, password: str) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)", (username, password)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def authenticate_user(username: str, password: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return row is not None and row[0] == password


def save_chat(username: str, title: str, user_input: str, bot_response: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO chats (username, title) VALUES (?, ?)", (username, title)
    )
    chat_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO chat_messages (chat_id, user_input, bot_response) VALUES (?, ?, ?)",
        (chat_id, user_input, bot_response),
    )

    conn.commit()
    conn.close()
    return chat_id


def add_message_to_chat(chat_id: int, user_input: str, bot_response: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_messages (chat_id, user_input, bot_response) VALUES (?, ?, ?)",
        (chat_id, user_input, bot_response),
    )
    conn.commit()
    conn.close()


def get_user_chats(username: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT c.id, c.title, c.created_at,
               json_group_array(
                   json_object(
                       'user_input', cm.user_input,
                       'bot_response', cm.bot_response,
                       'timestamp', cm.created_at
                   )
               ) as messages
        FROM chats c
        LEFT JOIN chat_messages cm ON c.id = cm.chat_id
        WHERE c.username = ?
        GROUP BY c.id
        ORDER BY c.created_at ASC
    """,
        (username,),
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {"id": row[0], "title": row[1], "created_at": row[2], "messages": row[3]}
        for row in rows
    ]
