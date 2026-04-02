"""
Couche base de données SQLite.
Gère : comptes utilisateurs, historique des conversations, messages.
"""

import sqlite3
import hashlib
import os
import json
from datetime import datetime
from contextlib import contextmanager
from core.config import DB_PATH


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


@contextmanager
def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialise le schéma de la base de données."""
    with _get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT UNIQUE NOT NULL,
                password    TEXT NOT NULL,
                salt        TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                settings    TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                title       TEXT NOT NULL DEFAULT 'Nouvelle conversation',
                model_id    TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS messages (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role            TEXT NOT NULL,
                content         TEXT NOT NULL,
                reasoning       TEXT,
                model_id        TEXT,
                created_at      TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );
        """)


# ─── Users ───────────────────────────────────────────────────────────────────

def create_user(username: str, password: str) -> dict | None:
    """Crée un utilisateur. Retourne le user ou None si username déjà pris."""
    salt = os.urandom(16).hex()
    hashed = _hash_password(password, salt)
    now = datetime.now().isoformat()
    try:
        with _get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO users (username, password, salt, created_at) VALUES (?,?,?,?)",
                (username, hashed, salt, now)
            )
            return {"id": cursor.lastrowid, "username": username}
    except sqlite3.IntegrityError:
        return None


def authenticate_user(username: str, password: str) -> dict | None:
    """Authentifie un utilisateur. Retourne le user ou None."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT id, username, password, salt, settings FROM users WHERE username=?",
            (username,)
        ).fetchone()
    if not row:
        return None
    if _hash_password(password, row["salt"]) != row["password"]:
        return None
    return {"id": row["id"], "username": row["username"], "settings": json.loads(row["settings"])}


def get_user_settings(user_id: int) -> dict:
    with _get_conn() as conn:
        row = conn.execute("SELECT settings FROM users WHERE id=?", (user_id,)).fetchone()
    return json.loads(row["settings"]) if row else {}


def save_user_settings(user_id: int, settings: dict):
    with _get_conn() as conn:
        conn.execute("UPDATE users SET settings=? WHERE id=?", (json.dumps(settings), user_id))


def update_username(user_id: int, new_username: str) -> bool:
    """Change le nom d'utilisateur. Retourne False si déjà pris."""
    try:
        with _get_conn() as conn:
            conn.execute("UPDATE users SET username=? WHERE id=?", (new_username, user_id))
        return True
    except sqlite3.IntegrityError:
        return False


def update_password(user_id: int, old_password: str, new_password: str) -> bool:
    """Change le mot de passe. Vérifie l'ancien mot de passe."""
    with _get_conn() as conn:
        row = conn.execute("SELECT password, salt FROM users WHERE id=?", (user_id,)).fetchone()
    if not row:
        return False
    if _hash_password(old_password, row["salt"]) != row["password"]:
        return False
    new_salt = os.urandom(16).hex()
    new_hashed = _hash_password(new_password, new_salt)
    with _get_conn() as conn:
        conn.execute("UPDATE users SET password=?, salt=? WHERE id=?",
                     (new_hashed, new_salt, user_id))
    return True


# ─── Conversations ────────────────────────────────────────────────────────────

def create_conversation(user_id: int, model_id: str, title: str = "Nouvelle conversation") -> int:
    now = datetime.now().isoformat()
    with _get_conn() as conn:
        cursor = conn.execute(
            "INSERT INTO conversations (user_id, title, model_id, created_at, updated_at) VALUES (?,?,?,?,?)",
            (user_id, title, model_id, now, now)
        )
        return cursor.lastrowid


def get_conversations(user_id: int) -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT id, title, model_id, created_at, updated_at FROM conversations "
            "WHERE user_id=? ORDER BY updated_at DESC",
            (user_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def rename_conversation(conv_id: int, title: str):
    now = datetime.now().isoformat()
    with _get_conn() as conn:
        conn.execute("UPDATE conversations SET title=?, updated_at=? WHERE id=?", (title, now, conv_id))


def delete_conversation(conv_id: int):
    with _get_conn() as conn:
        conn.execute("DELETE FROM conversations WHERE id=?", (conv_id,))


def touch_conversation(conv_id: int):
    now = datetime.now().isoformat()
    with _get_conn() as conn:
        conn.execute("UPDATE conversations SET updated_at=? WHERE id=?", (now, conv_id))


# ─── Messages ─────────────────────────────────────────────────────────────────

def add_message(conv_id: int, role: str, content: str, reasoning: str = None, model_id: str = None) -> int:
    now = datetime.now().isoformat()
    with _get_conn() as conn:
        cursor = conn.execute(
            "INSERT INTO messages (conversation_id, role, content, reasoning, model_id, created_at) VALUES (?,?,?,?,?,?)",
            (conv_id, role, content, reasoning, model_id, now)
        )
    touch_conversation(conv_id)
    return cursor.lastrowid


def get_messages(conv_id: int) -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT id, role, content, reasoning, model_id, created_at "
            "FROM messages WHERE conversation_id=? ORDER BY created_at ASC",
            (conv_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_conversation_context(conv_id: int) -> list[dict]:
    """Retourne l'historique formaté pour l'API OpenAI."""
    msgs = get_messages(conv_id)
    return [{"role": m["role"], "content": m["content"]} for m in msgs]
