import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any

from src.config import DB_PATH


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                company TEXT,
                interest TEXT,
                message TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chat_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS automation_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                payload TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def insert_lead(
    name: str,
    email: str,
    phone: str = "",
    company: str = "",
    interest: str = "",
    message: str = "",
) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO leads (name, email, phone, company, interest, message, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name, email, phone, company, interest, message, _now()),
        )
        return int(cur.lastrowid)


def log_chat(session_id: str, role: str, content: str) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO chat_logs (session_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, role, content, _now()),
        )


def log_automation(event_type: str, payload: str, status: str) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO automation_events (event_type, payload, status, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (event_type, payload, status, _now()),
        )


def get_all_leads() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM leads ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_chat_logs(limit: int = 200) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_logs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_automation_events(limit: int = 100) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM automation_events ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_stats() -> dict[str, int]:
    with get_db() as conn:
        leads = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        chats = conn.execute("SELECT COUNT(*) FROM chat_logs").fetchone()[0]
        events = conn.execute("SELECT COUNT(*) FROM automation_events").fetchone()[0]
    return {"leads": leads, "chats": chats, "automation_events": events}
