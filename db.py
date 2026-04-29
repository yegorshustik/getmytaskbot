"""
db.py — SQLite data layer for Get My Task bot.

All functions here are pure database operations.
No Telegram, no Google, no UI logic.
"""
from __future__ import annotations
import sqlite3
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


# ─── Schema ───────────────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            lang TEXT DEFAULT 'ru',
            calendar_token TEXT,
            first_task_done INTEGER DEFAULT 0,
            calendar_connected INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS sent_reminders (
            chat_id INTEGER,
            event_id TEXT,
            remind_at TEXT,
            PRIMARY KEY (chat_id, event_id, remind_at)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            event_type TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at)")
    c.execute("""
        CREATE TABLE IF NOT EXISTS oauth_states (
            state TEXT PRIMARY KEY,
            chat_id INTEGER,
            code_verifier TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            title TEXT,
            quadrant TEXT,
            suggested_date TEXT,
            suggested_time TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    for col, definition in [
        ("timezone", "TEXT DEFAULT 'Europe/Moscow'"),
        ("reminder_time", "TEXT DEFAULT '08:00'"),
        ("reminder_enabled", "INTEGER DEFAULT 1"),
        ("reminder_before", "INTEGER DEFAULT 30"),
        ("reminder_minutes", "INTEGER DEFAULT 30"),
        ("pending_task_json", "TEXT DEFAULT NULL"),
        ("last_active", "TEXT DEFAULT NULL"),
        ("ical_token", "TEXT DEFAULT NULL"),
        ("last_reengagement", "TEXT DEFAULT NULL"),
        ("reengagement_count", "INTEGER DEFAULT 0"),
        ("first_name", "TEXT DEFAULT NULL"),
        ("username", "TEXT DEFAULT NULL"),
        ("registered_at", "TEXT DEFAULT NULL"),
    ]:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
        except sqlite3.OperationalError:
            pass
    for col, definition in [
        ("description", "TEXT DEFAULT ''"),
        ("quadrant_name", "TEXT DEFAULT ''"),
        ("done", "INTEGER DEFAULT 0"),
        ("synced_to_calendar", "INTEGER DEFAULT 0"),
        ("google_event_id", "TEXT DEFAULT NULL"),
        ("task_url", "TEXT DEFAULT NULL"),
        ("goal_id", "INTEGER DEFAULT NULL"),
    ]:
        try:
            c.execute(f"ALTER TABLE tasks ADD COLUMN {col} {definition}")
        except sqlite3.OperationalError:
            pass
    c.execute("CREATE INDEX IF NOT EXISTS idx_tasks_event_id ON tasks(google_event_id)")
    # Remove duplicate tasks
    c.execute("""
        DELETE FROM tasks
        WHERE google_event_id IS NULL
          AND (chat_id || '|' || title || '|' || suggested_date || '|' || COALESCE(suggested_time,'')) IN (
              SELECT chat_id || '|' || title || '|' || suggested_date || '|' || COALESCE(suggested_time,'')
              FROM tasks WHERE google_event_id IS NOT NULL
          )
    """)
    c.execute("""
        DELETE FROM tasks WHERE id NOT IN (
            SELECT MAX(id) FROM tasks
            GROUP BY chat_id, title, suggested_date, COALESCE(suggested_time, '')
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            title TEXT,
            criteria TEXT,
            deadline TEXT,
            quadrant TEXT DEFAULT 'Q2',
            quadrant_name TEXT DEFAULT '',
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS recurring_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            title TEXT,
            google_event_id TEXT,
            rrule TEXT,
            suggested_time TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    try:
        c.execute("ALTER TABLE oauth_states ADD COLUMN code_verifier TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()


# ─── Users ────────────────────────────────────────────────────────────────────

def log_event(chat_id, event_type):
    conn = sqlite3.connect("users.db")
    conn.execute("INSERT INTO events (chat_id, event_type) VALUES (?, ?)", (chat_id, event_type))
    conn.execute("UPDATE users SET last_active=datetime('now') WHERE chat_id=?", (chat_id,))
    conn.commit()
    conn.close()


def get_user(chat_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "chat_id": row[0], "lang": row[1], "calendar_token": row[2],
            "first_task_done": row[3], "calendar_connected": row[4],
            "timezone": row[5] if len(row) > 5 and row[5] else "Europe/Moscow",
            "reminder_time": row[6] if len(row) > 6 and row[6] else "08:00",
            "reminder_enabled": row[7] if len(row) > 7 else 1,
            "reminder_before": row[8] if len(row) > 8 and row[8] is not None else 30,
            "reminder_minutes": row[9] if len(row) > 9 and row[9] is not None else 30,
            "pending_task_json": row[10] if len(row) > 10 else None,
            "last_active": row[11] if len(row) > 11 else None,
            "ical_token": row[12] if len(row) > 12 else None,
            "last_reengagement": row[13] if len(row) > 13 else None,
            "reengagement_count": row[14] if len(row) > 14 else 0,
            "first_name": row[15] if len(row) > 15 else None,
            "username": row[16] if len(row) > 16 else None,
        }
    return None


_ALLOWED_USER_COLS = {
    "lang", "calendar_token", "first_task_done", "calendar_connected",
    "timezone", "reminder_time", "reminder_enabled", "reminder_before",
    "reminder_minutes", "pending_task_json", "last_active", "ical_token",
    "last_reengagement", "reengagement_count",
    "first_name", "username", "registered_at",
}


def save_user(chat_id, **kwargs):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
    # Set registered_at only on first insert (when it's NULL)
    c.execute(
        "UPDATE users SET registered_at = datetime('now') WHERE chat_id = ? AND registered_at IS NULL",
        (chat_id,)
    )
    for key, val in kwargs.items():
        if key not in _ALLOWED_USER_COLS:
            logger.warning(f"save_user: ignoring unknown column '{key}'")
            continue
        c.execute(f"UPDATE users SET {key} = ? WHERE chat_id = ?", (val, chat_id))
    conn.commit()
    conn.close()


# ─── Reminder dedup ───────────────────────────────────────────────────────────

def reminder_already_sent(chat_id, event_id, remind_at):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT 1 FROM sent_reminders WHERE chat_id=? AND event_id=? AND remind_at=?",
              (chat_id, event_id, remind_at))
    result = c.fetchone()
    conn.close()
    return result is not None


def mark_reminder_sent(chat_id, event_id, remind_at):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO sent_reminders VALUES (?,?,?)", (chat_id, event_id, remind_at))
    conn.commit()
    conn.close()


# ─── Tasks ────────────────────────────────────────────────────────────────────

def get_active_task_count(chat_id):
    conn = sqlite3.connect("users.db")
    user = get_user(chat_id)
    tz_name = user["timezone"] if user else "Europe/Moscow"
    today = datetime.now(ZoneInfo(tz_name)).strftime("%Y-%m-%d")
    count = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE chat_id=? AND suggested_date = ? AND done=0",
        (chat_id, today)
    ).fetchone()[0]
    conn.close()
    return count


def find_upcoming_tasks(chat_id: int, query: str) -> list[dict]:
    """Search undone future tasks by title (case-insensitive substring match)."""
    user = get_user(chat_id)
    tz_name = user["timezone"] if user else "Europe/Moscow"
    today = datetime.now(ZoneInfo(tz_name)).strftime("%Y-%m-%d")
    conn = sqlite3.connect("users.db")
    rows = conn.execute(
        "SELECT id, title, suggested_date, suggested_time, google_event_id "
        "FROM tasks WHERE chat_id=? AND done=0 AND suggested_date >= ? "
        "AND LOWER(title) LIKE ? ORDER BY suggested_date, suggested_time",
        (chat_id, today, f"%{query.lower()}%")
    ).fetchall()
    conn.close()
    return [
        {"id": r[0], "title": r[1], "suggested_date": r[2],
         "suggested_time": r[3], "google_event_id": r[4]}
        for r in rows
    ]


def reschedule_task_in_db(task_id: int, new_date: str, new_time: str | None = None):
    """Update suggested_date (and optionally suggested_time) of a saved task."""
    conn = sqlite3.connect("users.db")
    if new_time is not None:
        conn.execute(
            "UPDATE tasks SET suggested_date=?, suggested_time=? WHERE id=?",
            (new_date, new_time, task_id)
        )
    else:
        conn.execute(
            "UPDATE tasks SET suggested_date=? WHERE id=?",
            (new_date, task_id)
        )
    conn.commit()
    conn.close()


def save_task_to_db(chat_id, task, synced_to_calendar=0, google_event_id=None):
    conn = sqlite3.connect("users.db")
    cur = conn.execute(
        "INSERT INTO tasks (chat_id, title, description, quadrant, quadrant_name, suggested_date, "
        "suggested_time, done, synced_to_calendar, google_event_id, task_url, goal_id) "
        "VALUES (?,?,?,?,?,?,?,0,?,?,?,?)",
        (chat_id, task["title"], task.get("description", ""), task.get("quadrant", ""),
         task.get("quadrant_name", ""), task.get("suggested_date", ""), task.get("suggested_time", ""),
         synced_to_calendar, google_event_id,
         task.get("url") or task.get("task_url"), task.get("goal_id"))
    )
    conn.commit()
    task_id = cur.lastrowid
    conn.close()
    return task_id


def link_task_to_goal(task_id: int, goal_id: int):
    """Update an already-saved task row to link it to a goal (no duplicate insert)."""
    conn = sqlite3.connect("users.db")
    conn.execute("UPDATE tasks SET goal_id=? WHERE id=?", (goal_id, task_id))
    conn.commit()
    conn.close()


def get_recurring_tasks_for_today(chat_id: int, today: str) -> list[dict]:
    """Return recurring tasks that fire on the given date based on their rrule."""
    conn = sqlite3.connect("users.db")
    rows = conn.execute(
        "SELECT title, rrule, suggested_time FROM recurring_tasks WHERE chat_id=?",
        (chat_id,)
    ).fetchall()
    conn.close()
    _WD = {0: "MO", 1: "TU", 2: "WE", 3: "TH", 4: "FR", 5: "SA", 6: "SU"}
    today_wd = _WD[datetime.strptime(today, "%Y-%m-%d").weekday()]
    result = []
    for title, rrule, suggested_time in rows:
        if not rrule:
            continue
        if "FREQ=DAILY" in rrule:
            result.append({"title": title, "suggested_time": suggested_time or ""})
        elif "FREQ=WEEKLY" in rrule and "BYDAY=" in rrule:
            byday = rrule.split("BYDAY=")[1].split(";")[0]
            if today_wd in byday.split(","):
                result.append({"title": title, "suggested_time": suggested_time or ""})
    return result


def save_recurring_task_to_db(chat_id: int, title: str, event_id: str, rrule: str, time: str | None):
    conn = sqlite3.connect("users.db")
    conn.execute(
        "INSERT INTO recurring_tasks (chat_id, title, google_event_id, rrule, suggested_time) VALUES (?,?,?,?,?)",
        (chat_id, title, event_id, rrule, time)
    )
    conn.commit()
    conn.close()


# ─── Goals ────────────────────────────────────────────────────────────────────

def save_goal_to_db(chat_id: int, title: str, criteria: str, deadline: str,
                    quadrant: str = "Q2", quadrant_name: str = "") -> int:
    conn = sqlite3.connect("users.db")
    cur = conn.execute(
        "INSERT INTO goals (chat_id, title, criteria, deadline, quadrant, quadrant_name) VALUES (?,?,?,?,?,?)",
        (chat_id, title, criteria, deadline, quadrant, quadrant_name)
    )
    goal_id = cur.lastrowid
    conn.commit()
    conn.close()
    return goal_id


def get_active_goals(chat_id: int) -> list[dict]:
    conn = sqlite3.connect("users.db")
    rows = conn.execute(
        "SELECT id, title, criteria, deadline, quadrant, quadrant_name, status FROM goals "
        "WHERE chat_id=? AND status='active' ORDER BY created_at DESC",
        (chat_id,)
    ).fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "criteria": r[2], "deadline": r[3],
             "quadrant": r[4], "quadrant_name": r[5], "status": r[6]} for r in rows]


def delete_goal_from_db(goal_id: int, delete_tasks: bool) -> int:
    """Delete a goal and handle linked tasks.
    If delete_tasks=True, deletes all linked tasks.
    If delete_tasks=False, unlinks them (goal_id=NULL).
    Returns count of affected tasks."""
    conn = sqlite3.connect("users.db")
    n = conn.execute("SELECT COUNT(*) FROM tasks WHERE goal_id=?", (goal_id,)).fetchone()[0]
    if delete_tasks:
        conn.execute("DELETE FROM tasks WHERE goal_id=?", (goal_id,))
    else:
        conn.execute("UPDATE tasks SET goal_id=NULL WHERE goal_id=?", (goal_id,))
    conn.execute("UPDATE goals SET status='deleted' WHERE id=?", (goal_id,))
    conn.commit()
    conn.close()
    return n


def get_goal_progress(goal_id: int) -> tuple[int, int]:
    """Returns (done_count, total_count) for tasks linked to this goal."""
    conn = sqlite3.connect("users.db")
    total = conn.execute("SELECT COUNT(*) FROM tasks WHERE goal_id=?", (goal_id,)).fetchone()[0]
    done = conn.execute("SELECT COUNT(*) FROM tasks WHERE goal_id=? AND done=1", (goal_id,)).fetchone()[0]
    conn.close()
    return done, total


# ─── OAuth states ─────────────────────────────────────────────────────────────

def save_oauth_state(state, chat_id, code_verifier=None):
    conn = sqlite3.connect("users.db")
    conn.execute("DELETE FROM oauth_states WHERE created_at < datetime('now', '-1 hour')")
    conn.execute(
        "INSERT OR REPLACE INTO oauth_states (state, chat_id, code_verifier) VALUES (?, ?, ?)",
        (state, chat_id, code_verifier)
    )
    conn.commit()
    conn.close()


def pop_oauth_state(state):
    """Returns (chat_id, code_verifier) for state and deletes it, or (None, None) if not found."""
    conn = sqlite3.connect("users.db")
    row = conn.execute("SELECT chat_id, code_verifier FROM oauth_states WHERE state=?", (state,)).fetchone()
    if row:
        conn.execute("DELETE FROM oauth_states WHERE state=?", (state,))
        conn.commit()
    conn.close()
    return (row[0], row[1]) if row else (None, None)
