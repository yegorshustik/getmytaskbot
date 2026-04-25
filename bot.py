import os
import io
import re
import uuid
import json
import base64
import hashlib
import random
import secrets
import logging
import sqlite3
import asyncio
import tempfile
from datetime import datetime, timedelta, timezone as _utc, date as _date
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from dotenv import load_dotenv
from groq import Groq
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiohttp import web

from collections import defaultdict, deque
import time as _time

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")
BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID", "114978994"))

groq_client = Groq(api_key=GROQ_API_KEY)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Announce (broadcast to users) ───────────────────────────────────────────
# Pending announcements stored in memory until owner confirms send
_pending_announcements: dict[str, dict] = {}

# ─── Feedback Limits ──────────────────────────────────────────────────────────
_FEEDBACK_COOLDOWN_SEC = 3600   # 1 hour between feedback messages
_FEEDBACK_MAX_TEXT_LEN = 1000   # max characters for text feedback
_feedback_last_sent: dict[int, float] = {}

def check_feedback_cooldown(chat_id: int) -> tuple[bool, int]:
    """Returns (allowed, minutes_remaining)."""
    now = _time.monotonic()
    last = _feedback_last_sent.get(chat_id, 0)
    elapsed = now - last
    if elapsed < _FEEDBACK_COOLDOWN_SEC:
        remaining_min = int((_FEEDBACK_COOLDOWN_SEC - elapsed) / 60) + 1
        return False, remaining_min
    return True, 0

def mark_feedback_sent(chat_id: int):
    _feedback_last_sent[chat_id] = _time.monotonic()

# ─── Rate Limiting ─────────────────────────────────────────────────────────────
_RATE_LIMIT_MAX = 10       # max AI requests
_RATE_LIMIT_WINDOW = 60    # per N seconds
_rate_store: dict[int, deque] = defaultdict(deque)

def check_rate_limit(chat_id: int) -> bool:
    """Returns True if allowed, False if rate limited."""
    now = _time.monotonic()
    cutoff = now - _RATE_LIMIT_WINDOW
    dq = _rate_store[chat_id]
    while dq and dq[0] < cutoff:
        dq.popleft()
    if len(dq) >= _RATE_LIMIT_MAX:
        return False
    dq.append(now)
    return True

SCOPES = ["https://www.googleapis.com/auth/calendar"]

# ─── Monitoring & Alerting ─────────────────────────────────────────────────────
import shutil

_alert_cooldowns: dict[str, float] = {}
_ALERT_COOLDOWN_SEC = 1800          # 30 min between same alert type
_job_error_counts: dict[str, int] = defaultdict(int)  # consecutive failures per job

# Rolling window for user-facing errors (5-min window)
_ux_error_count = 0
_ux_error_window_start: float = 0.0

bot_app = None   # set in main(), needed for alerts

async def send_owner_alert(alert_key: str, text: str) -> None:
    """Send a Telegram alert to the bot owner with per-key cooldown."""
    now = _time.monotonic()
    if now - _alert_cooldowns.get(alert_key, 0) < _ALERT_COOLDOWN_SEC:
        return
    _alert_cooldowns[alert_key] = now
    try:
        await bot_app.bot.send_message(
            chat_id=BOT_OWNER_ID,
            text=text,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"[alert] failed to send alert '{alert_key}': {e}")

async def _safe_job(job_fn, job_name: str) -> None:
    """Wrapper for APScheduler jobs: resets error counter on success, alerts on 3+ consecutive failures."""
    try:
        await job_fn()
        _job_error_counts[job_name] = 0
    except Exception as e:
        _job_error_counts[job_name] += 1
        count = _job_error_counts[job_name]
        logger.error(f"[job:{job_name}] failure #{count}: {e}", exc_info=True)
        if count >= 3:
            await send_owner_alert(
                f"job_fail_{job_name}",
                f"🚨 *Ошибка в задаче `{job_name}`*\n"
                f"_{count} раз подряд_\n\n`{str(e)[:300]}`"
            )

async def monitor_system() -> None:
    """Every 10 min: check disk, memory and DB. Alert owner if anything is critical."""
    alerts: list[str] = []

    # 1. DB health
    try:
        with sqlite3.connect("users.db") as db:
            db.execute("SELECT COUNT(*) FROM users").fetchone()
    except Exception as e:
        alerts.append(f"🔴 *БД недоступна*\n`{e}`")

    # 2. Disk space
    try:
        total, used, free = shutil.disk_usage("/")
        pct = used / total * 100
        if pct > 90:
            free_gb = free / (1024 ** 3)
            alerts.append(f"💾 *Диск заполнен на {pct:.0f}%*\nОсталось {free_gb:.1f} ГБ")
    except Exception:
        pass

    # 3. RAM (Linux /proc/meminfo)
    try:
        mem: dict[str, int] = {}
        with open("/proc/meminfo") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    mem[parts[0].rstrip(":")] = int(parts[1])
        total_kb = mem.get("MemTotal", 0)
        avail_kb = mem.get("MemAvailable", 0)
        if total_kb > 0:
            used_pct = (1 - avail_kb / total_kb) * 100
            if used_pct > 90:
                avail_mb = avail_kb // 1024
                alerts.append(f"🧠 *Память {used_pct:.0f}% занята*\nДоступно {avail_mb} МБ")
    except Exception:
        pass

    for msg in alerts:
        await send_owner_alert(msg[:40], f"🚨 *Системный алерт*\n{msg}")

# ─── Database ─────────────────────────────────────────────────────────────────

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
    # ── Remove duplicate tasks ─────────────────────────────────────────────────
    # Step 1: if a group has both a bot-created (no event_id) and a Calendar-synced row, drop the bot one
    c.execute("""
        DELETE FROM tasks
        WHERE google_event_id IS NULL
          AND (chat_id || '|' || title || '|' || suggested_date || '|' || COALESCE(suggested_time,'')) IN (
              SELECT chat_id || '|' || title || '|' || suggested_date || '|' || COALESCE(suggested_time,'')
              FROM tasks WHERE google_event_id IS NOT NULL
          )
    """)
    # Step 2: for any remaining duplicates (both without event_id), keep the latest
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
    # Migrate oauth_states: add code_verifier column if missing
    try:
        c.execute("ALTER TABLE oauth_states ADD COLUMN code_verifier TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

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
        }
    return None

_ALLOWED_USER_COLS = {
    "lang", "calendar_token", "first_task_done", "calendar_connected",
    "timezone", "reminder_time", "reminder_enabled", "reminder_before",
    "reminder_minutes", "pending_task_json", "last_active", "ical_token",
    "last_reengagement", "reengagement_count",
}

def save_user(chat_id, **kwargs):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
    for key, val in kwargs.items():
        if key not in _ALLOWED_USER_COLS:
            logger.warning(f"save_user: ignoring unknown column '{key}'")
            continue
        c.execute(f"UPDATE users SET {key} = ? WHERE chat_id = ?", (val, chat_id))
    conn.commit()
    conn.close()

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

# ─── Texts ────────────────────────────────────────────────────────────────────

TEXTS = {
    "ru": {
        "choose_lang": "Привет! Выбери язык / Choose language / Оберіть мову:",
        "lang_set": "Язык установлен: Русский 🇷🇺\n\nПросто напишите или надиктуйте голосовое — я извлеку задачи и расставлю их по матрице Эйзенхауэра.",
        "processing": "Обрабатываю...",
        "transcribing": "Транскрибирую голосовое...",
        "recognized": "Распознал: ",
        "rate_limit": "⚠️ Слишком много запросов. Подождите минуту и попробуйте снова.",
        "feedback_too_long": f"⚠️ Сообщение слишком длинное. Максимум {_FEEDBACK_MAX_TEXT_LEN} символов.",
        "feedback_cooldown": "⏳ Вы уже отправляли сообщение. Следующее можно отправить через {{min}} мин.",
        "too_long": "⚠️ Голосовое слишком длинное (больше 60 сек). Запишите несколько коротких сообщений.",
        "too_short": "⚠️ Сообщение слишком короткое. Попробуйте записать подробнее.",
        "no_text": "⚠️ Не удалось распознать речь. Проверьте качество записи и попробуйте снова.",
        "no_tasks": "⚠️ Не нашёл задач в сообщении. Опишите что нужно сделать.",
        "add_calendar": "📅 Google Calendar",
        "apple_cal": "🍎 Apple Calendar",
        "save": "✅ Сохранить",
        "skip": "❌ Пропустить",
        "adding": "⏳ Добавляю в Календарь...",
        "added": "✅ Добавлено в Календарь",
        "added_btn": "📅 Открыть в Календаре",
        "task_saved": "✅ _Задача сохранена_",
        "task_skipped": "❌ _Задача не сохранена_",
        "skip_invite": "🎙 Надиктуй следующую задачу или напиши текстом",
        "task_time_past": "⚠️ Указанное время уже прошло. Уточните, пожалуйста, когда именно нужно выполнить задачу.",
        "calendar_error": "Ошибка Календаря: ",
        "error": "Ошибка: ",
        "offer_calendar": "📅 Хотите добавлять задачи в Google Calendar и получать напоминания?",
        "connect_calendar": "📅 Подключить календарь",
        "skip_calendar": "➡️ Пропустить",
        "connect_link": "🔗 Подключите Google Calendar:",
        "calendar_connected": "✅ Google Calendar подключён! Теперь я буду напоминать вам о задачах.",
        "btn_apple_cal": "🍎 Apple Calendar",
        "btn_apple_cal_connected": "🍎 Apple Calendar ✅",
        "apple_cal_info": (
            "🍎 *Подписка на Apple Calendar*\n\n"
            "Нажми кнопку ниже — Apple Calendar откроется и предложит подписаться.\n\n"
            "Все задачи из бота автоматически появятся в твоём календаре и будут обновляться каждый час."
        ),
        "apple_cal_info_gcal": (
            "🍎 *Подписка на Apple Calendar*\n\n"
            "⚠️ У тебя уже подключён Google Calendar — задачи из бота уже попадают в Apple Calendar через него.\n\n"
            "Подписка нужна только если ты хочешь видеть задачи в отдельном календаре, не через Google.\n\n"
            "_Если подпишешься — задачи появятся дважды._"
        ),
        "apple_cal_status": "✅ Подписка активна",
        "btn_apple_cal_open": "🍎 Открыть в Apple Calendar",
        "btn_feedback": "✉️ Написать нам",
        "feedback_prompt": "✉️ Напишите ваше сообщение — текст или голосовое. Мы читаем каждое обращение.",
        "feedback_sent": "✅ Сообщение отправлено! Спасибо за обратную связь.",
        "feedback_from": "📨 *Новое сообщение*\n👤 {name}\n📱 @{username}\n🆔 `{chat_id}`\n🌐 Язык: {lang}\n📱 Get My Task Bot",
        "cal_sync_new": "Google Calendar:\n*{title}*\n{date}",
        "cal_sync_removed": "🗑 Удалено из Google Calendar: *{title}*",
        "recurring_label": "🔄 Повторяющаяся задача",
        "recurring_schedule_daily": "каждый день",
        "recurring_schedule_weekly": "каждый {days}",
        "recurring_day_names": {"MO":"пн","TU":"вт","WE":"ср","TH":"чт","FR":"пт","SA":"сб","SU":"вс"},
        "btn_recur_yes": "🔄 Повторяющаяся",
        "btn_recur_once": "1️⃣ Один раз",
        "recur_created": "✅ *{title}* сохранена\n🔄 {schedule}",
        "btn_recur_continue": "✅ Продолжить серию",
        "btn_recur_delete": "🗑 Удалить серию",
        "recur_continued": "✅ Серия продолжается",
        "recur_deleted": "🗑 Повторяющаяся задача *{title}* удалена",
        "calendar_not_connected": "❌ Календарь не подключён. Используйте /connect чтобы подключить.",
        "reminder": "🔔 Напоминание: *{title}*\n📅 {time}",
        "conflict_found": "⚠️ В это время уже есть: *{event}*.\n\nНапишите или надиктуйте другое время для задачи *{title}*:",
        "conflict_confirm": "⚠️ В это время уже есть: *{event}*.\n\nСохранить *{title}* всё равно?",
        "conflict_save_anyway": "✅ Сохранить всё равно",
        "conflict_no_save": "❌ Не сохранять",
        "saved_with_calendar": "✅ *{title}* сохранена в задачах и добавлена в Google Calendar",
        "correction_unclear": "⚠️ Не понял новое время. Попробуйте написать например: «в 11 утра» или «завтра в 15:00»",
        "rescheduled": "✅ Время обновлено: {date} в {time}",
        "timezone_current": "🕐 Ваша текущая временная зона: *{tz}*\n\nВыберите из списка или введите вручную:",
        "timezone_set": "✅ Временная зона установлена: *{tz}*",
        "timezone_manual": "✍️ Ввести вручную",
        "timezone_prompt": "Введите название временной зоны, например:\n`Europe/Moscow`, `Asia/Almaty`, `America/New_York`",
        "timezone_invalid": "❌ Не удалось распознать временную зону. Попробуйте формат: `Europe/Moscow`",
        "help": (
            "📋 *Что я умею:*\n\n"
            "• Напишите или надиктуйте голосовое — извлеку задачи и расставлю по матрице Эйзенхауэра\n"
            "• Предложу дату и время для каждой задачи\n"
            "• Сохраню задачу в боте и автоматически добавлю в Google Календарь (если подключён)\n"
            "• Синхронизирую Google Календарь — новые события подтягиваются каждые 15 минут\n"
            "• Распознаю повторяющиеся задачи — создам серию в Календаре и напомню о каждой\n"
            "• Напомню о событии заранее — за выбранное вами время\n\n"
            "⚙️ *Команды:*\n"
            "/tasks — мои задачи\n"
            "/connect — подключить Google Календарь\n"
            "/settings — напоминания, Calendar, временная зона\n"
            "/timezone — изменить временную зону\n"
            "/help — эта справка"
        ),
        "tasks_header": "📋 *Мои задачи:*\n\n",
        "tasks_empty": "У вас пока нет предстоящих задач.",
        "tasks_item": "{emoji} *{title}* — {date}\n",
        "tasks_today": "Задачи на сегодня",
        "tasks_tomorrow": "Завтра",
        "tasks_birthdays": "🎂 Дни рождения",
        "tasks_allday": "📅 Весь день",
        "tasks_more_days": "...и ещё {n} {days}",
        "tasks_day": "день",
        "tasks_days_2_4": "дня",
        "tasks_days_5": "дней",
        "btn_new_task": "📝 Новая задача",
        "btn_my_tasks": "📋 Мои задачи",
        "btn_settings": "⚙️ Настройки",
        "btn_timezone": "🕐 Таймзона",
        "btn_help": "❓ Помощь",
        "btn_connect": "📅 Подключить календарь",
        "btn_view_calendar": "📅 Календарь",
        "btn_disconnect_calendar": "🔌 Отключить календарь",
        "calendar_disconnected": "📅 Календарь отключён.",
        "btn_reminder": "☀️ Утренний дайджест",
        "reminder_settings": "🔔 *Утреннее напоминание*\nСейчас: {time}",
        "reminder_disabled_text": "🔕 Отключено",
        "reminder_set": "✅ Напоминание установлено на {time}",
        "reminder_off": "🔕 Напоминания отключены.",
        "morning_digest": "☀️ *Доброе утро!* Вот ваши задачи на сегодня:\n\n{tasks}",
        "morning_digest_future": "☀️ *Доброе утро!* Задач на сегодня нет.\n\nБлижайшие дела:\n\n{tasks}",
        "morning_digest_empty": "☀️ *Доброе утро!* У вас нет запланированных задач.",
        "morning_first_offer": "\n\n_Напоминание приходит в {time}. Хотите изменить время?_",
        "btn_reminder_change": "🕐 Изменить время",
        "btn_reminder_disable": "🔕 Отключить",
        "reengagement": [
            "Давно не было задач 👀\n\nЕсть что запланировать? Просто напиши или надиктуй — я разберу за секунду.",
            "Кстати, задачи можно надиктовывать голосом 🎙\n\nСкажи что нужно сделать — я сам создам задачу и добавлю в календарь.",
            "Уже несколько дней без задач 🙂\n\nЕсли решишь вернуться — просто напиши. Я здесь.",
        ],
        "btn_archive": "🗂 Архив задач",
        "archive_header": "🗂 *Архив выполненных задач*",
        "archive_empty": "Архив пуст — нет прошедших задач.",
        "btn_archive_next": "Далее →",
        "btn_reminder_before": "⏰ Напомнить за {min} мин",
        "goal_detected": (
            "🎯 Похоже, это не просто задача — это *цель!*\n\n"
            "Хочешь оформить её как цель? Я помогу сделать её чёткой и достижимой — "
            "задам пару вопросов и сформирую готовую цель."
        ),
        "btn_goal_yes": "🎯 Да, создать цель",
        "btn_goal_no": "📝 Сохранить как задачу",
        "goal_ask_deadline": (
            "📅 Отлично, начинаем!\n\n"
            "К какому сроку хочешь достичь этой цели?\n\n"
            "_Например: «к 1 июля», «через 3 месяца», «до конца года»_"
        ),
        "goal_ask_criteria": (
            "✨ Почти готово!\n\n"
            "Как поймёшь, что цель достигнута? Опиши результат конкретно.\n\n"
            "_Например: «100 пользователей», «минус 8 кг», «запущен сайт»_"
        ),
        "goal_created": (
            "🎯 *Цель создана!*\n\n"
            "*{title}*\n"
            "📅 Дедлайн: {deadline}\n"
            "✅ Критерий успеха: _{criteria}_\n\n"
            "Теперь добавляй задачи как обычно — я буду предлагать привязывать их к этой цели. "
            "Так сможешь видеть прогресс 💪"
        ),
        "goals_empty": (
            "🎯 У тебя пока нет активных целей.\n\n"
            "Просто опиши что-то масштабное голосом или текстом — "
            "я распознаю цель и предложу оформить её."
        ),
        "goals_header": "🎯 *Твои цели:*\n\n",
        "goal_progress": "{bar} {pct}% — {done}/{total} задач",
        "goal_no_tasks": "_задачи ещё не добавлены_",
        "goal_deadline_label": "до {date}",
        "goal_done_msg": "🏆 *Цель выполнена!*\n\nВсе задачи закрыты — ты это сделал! 🎉",
        "goal_link_ask": "📎 Эта задача похожа на шаг к цели *\"{goal}\"*. Привязать её?",
        "btn_goal_link_yes": "✅ Привязать",
        "btn_goal_link_no": "➡️ Нет",
        "goal_linked": "✅ Привязано к цели *\"{goal}\"*",
        "btn_goal_delete": "🗑 Удалить цель",
        "goal_delete_confirm": "Удалить цель *\"{title}\"*?\n\nЧто делать со связанными задачами?",
        "btn_goal_del_tasks": "🗑 Удалить задачи",
        "btn_goal_del_keep": "🔗 Оставить задачи",
        "btn_goal_del_cancel": "❌ Отмена",
        "goal_deleted_with_tasks": "🗑 Цель удалена вместе с задачами ({n} шт.).",
        "goal_deleted_tasks_kept": "🗑 Цель удалена. {n} задач(и) откреплены и остались в списке.",
        "goal_deleted_no_tasks": "🗑 Цель удалена.",
        "ask_when": "📅 Когда планируешь это сделать?\n\nНапример: *сегодня в 17:00*, *завтра в 10:00*, *25 апреля*",
        "ask_when_unclear": "🤔 Не понял дату. Попробуй написать, например: *завтра в 15:00* или *25 апреля в 9:00*",
        "btn_goals": "🎯 Цели",
        "reminder_before_settings": "⏰ *Напоминание о задачах*\nСейчас: за {min} мин до начала",
        "reminder_before_set": "✅ Буду напоминать за {min} мин до задачи.",
        "task_reminder": "⏰ Напоминание: *{title}* начнётся в {time}",
        "menu_hint": [
            "Скажи — и забудь. Я напомню в нужный момент 🔔",
            "Есть что-то важное сегодня? Надиктуй — я не забуду 🎙",
            "Что нельзя упустить? Просто скажи — и я прослежу 📌",
            "Надиктуй задачу за 10 секунд — я возьму её на контроль:",
            "Голос или текст — как удобно. Что нужно не забыть? 📝",
            "Есть встреча или дедлайн? Скажи — запишу и напомню:",
            "Поставь напоминание прямо сейчас — голосом или текстом:",
            "Создай задачу — я напомню именно тогда, когда нужно 🕐",
        ],
        "reminder_ask": "⏰ За сколько минут напоминать о задачах?",
        "reminder_ask_set": "✅ Буду напоминать за {min} мин до задачи.",
    },
    "en": {
        "choose_lang": "Привет! Выбери язык / Choose language / Оберіть мову:",
        "lang_set": "Language set: English 🇬🇧\n\nJust type or send a voice message — I'll extract tasks and classify them using the Eisenhower Matrix.",
        "processing": "Processing...",
        "transcribing": "Transcribing voice message...",
        "recognized": "Recognized: ",
        "rate_limit": "⚠️ Too many requests. Please wait a minute and try again.",
        "feedback_too_long": f"⚠️ Message is too long. Maximum {_FEEDBACK_MAX_TEXT_LEN} characters.",
        "feedback_cooldown": "⏳ You've already sent a message. You can send another in {{min}} min.",
        "too_long": "⚠️ Voice message is too long (over 60 sec). Please record shorter messages.",
        "too_short": "⚠️ Message is too short. Try recording with more detail.",
        "no_text": "⚠️ Could not recognize speech. Check audio quality and try again.",
        "no_tasks": "⚠️ No tasks found in the message. Describe what needs to be done.",
        "add_calendar": "📅 Google Calendar",
        "apple_cal": "🍎 Apple Calendar",
        "save": "✅ Save",
        "skip": "❌ Skip",
        "adding": "⏳ Adding to Calendar...",
        "added": "✅ Added to Calendar",
        "added_btn": "📅 Open in Calendar",
        "task_saved": "✅ _Task saved_",
        "task_skipped": "❌ _Task not saved_",
        "skip_invite": "🎙 Dictate your next task or type it",
        "task_time_past": "⚠️ The specified time has already passed. Please clarify when exactly you need to complete this task.",
        "calendar_error": "Calendar error: ",
        "error": "Error: ",
        "offer_calendar": "📅 Want to add tasks to Google Calendar and get reminders?",
        "connect_calendar": "📅 Connect calendar",
        "skip_calendar": "➡️ Skip",
        "connect_link": "🔗 Connect Google Calendar:",
        "calendar_connected": "✅ Google Calendar connected! I'll remind you about your tasks.",
        "btn_apple_cal": "🍎 Apple Calendar",
        "btn_apple_cal_connected": "🍎 Apple Calendar ✅",
        "apple_cal_info": (
            "🍎 *Apple Calendar Subscription*\n\n"
            "Tap the button below — Apple Calendar will open and offer to subscribe.\n\n"
            "All your bot tasks will appear in your calendar and update every hour."
        ),
        "apple_cal_info_gcal": (
            "🍎 *Apple Calendar Subscription*\n\n"
            "⚠️ You already have Google Calendar connected — bot tasks already appear in Apple Calendar through it.\n\n"
            "Subscribe only if you want tasks in a separate calendar, not via Google.\n\n"
            "_If you subscribe, tasks will appear twice._"
        ),
        "apple_cal_status": "✅ Subscription active",
        "btn_apple_cal_open": "🍎 Open in Apple Calendar",
        "btn_feedback": "✉️ Contact us",
        "feedback_prompt": "✉️ Send us a message — text or voice. We read every submission.",
        "feedback_sent": "✅ Message sent! Thank you for your feedback.",
        "feedback_from": "📨 *New message*\n👤 {name}\n📱 @{username}\n🆔 `{chat_id}`\n🌐 Lang: {lang}\n📱 Get My Task Bot",
        "cal_sync_new": "Google Calendar:\n*{title}*\n{date}",
        "cal_sync_removed": "🗑 Removed from Google Calendar: *{title}*",
        "recurring_label": "🔄 Recurring task",
        "recurring_schedule_daily": "every day",
        "recurring_schedule_weekly": "every {days}",
        "recurring_day_names": {"MO":"Mon","TU":"Tue","WE":"Wed","TH":"Thu","FR":"Fri","SA":"Sat","SU":"Sun"},
        "btn_recur_yes": "🔄 Recurring",
        "btn_recur_once": "1️⃣ One time",
        "recur_created": "✅ *{title}* saved\n🔄 {schedule}",
        "btn_recur_continue": "✅ Continue series",
        "btn_recur_delete": "🗑 Delete series",
        "recur_continued": "✅ Series continues",
        "recur_deleted": "🗑 Recurring task *{title}* deleted",
        "calendar_not_connected": "❌ Calendar not connected. Use /connect to connect.",
        "reminder": "🔔 Reminder: *{title}*\n📅 {time}",
        "conflict_found": "⚠️ There's already an event at this time: *{event}*.\n\nWrite or say a new time for *{title}*:",
        "conflict_confirm": "⚠️ There's already an event at this time: *{event}*.\n\nSave *{title}* anyway?",
        "conflict_save_anyway": "✅ Save anyway",
        "conflict_no_save": "❌ Don't save",
        "saved_with_calendar": "✅ *{title}* saved to tasks and added to Google Calendar",
        "correction_unclear": "⚠️ Couldn't understand the new time. Try something like: 'at 11am' or 'tomorrow at 3pm'",
        "rescheduled": "✅ Time updated: {date} at {time}",
        "timezone_current": "🕐 Your current timezone: *{tz}*\n\nChoose from the list or enter manually:",
        "timezone_set": "✅ Timezone set: *{tz}*",
        "timezone_manual": "✍️ Enter manually",
        "timezone_prompt": "Enter a timezone name, for example:\n`Europe/London`, `America/New_York`, `Asia/Tokyo`",
        "timezone_invalid": "❌ Could not recognize timezone. Try format: `America/New_York`",
        "help": (
            "📋 *What I can do:*\n\n"
            "• Type or send a voice message — I'll extract tasks and classify them using the Eisenhower Matrix\n"
            "• Suggest a date and time for each task\n"
            "• Save the task and auto-sync it to Google Calendar (if connected)\n"
            "• Sync Google Calendar — new events are imported every 15 minutes\n"
            "• Detect recurring tasks — create a series in Calendar and remind you of each one\n"
            "• Remind you before events — at your chosen lead time\n\n"
            "⚙️ *Commands:*\n"
            "/tasks — my tasks\n"
            "/connect — connect Google Calendar\n"
            "/settings — reminders, Calendar, timezone\n"
            "/timezone — change timezone\n"
            "/help — this help"
        ),
        "tasks_header": "📋 *My tasks:*\n\n",
        "tasks_empty": "You have no upcoming tasks.",
        "tasks_item": "{emoji} *{title}* — {date}\n",
        "tasks_today": "Tasks for today",
        "tasks_tomorrow": "Tomorrow",
        "tasks_birthdays": "🎂 Birthdays",
        "tasks_allday": "📅 All day",
        "tasks_more_days": "...and {n} more {days}",
        "tasks_day": "day",
        "tasks_days_2_4": "days",
        "tasks_days_5": "days",
        "btn_new_task": "📝 New task",
        "btn_my_tasks": "📋 My tasks",
        "btn_settings": "⚙️ Settings",
        "btn_timezone": "🕐 Timezone",
        "btn_help": "❓ Help",
        "btn_connect": "📅 Connect calendar",
        "btn_view_calendar": "📅 Calendar",
        "btn_disconnect_calendar": "🔌 Disconnect calendar",
        "calendar_disconnected": "📅 Calendar disconnected.",
        "btn_reminder": "☀️ Morning digest",
        "reminder_settings": "🔔 *Morning reminder*\nNow: {time}",
        "reminder_disabled_text": "🔕 Disabled",
        "reminder_set": "✅ Reminder set to {time}",
        "reminder_off": "🔕 Reminders disabled.",
        "morning_digest": "☀️ *Good morning!* Here are your tasks for today:\n\n{tasks}",
        "morning_digest_future": "☀️ *Good morning!* No tasks today.\n\nUpcoming:\n\n{tasks}",
        "morning_digest_empty": "☀️ *Good morning!* You have no scheduled tasks.",
        "morning_first_offer": "\n\n_Reminder comes at {time}. Want to change it?_",
        "btn_reminder_change": "🕐 Change time",
        "btn_reminder_disable": "🔕 Disable",
        "reengagement": [
            "No tasks in a while 👀\n\nSomething to plan? Just type or record a voice message — I'll handle it in seconds.",
            "Quick tip: you can dictate tasks by voice 🎙\n\nJust say what needs to be done — I'll create a task and add it to your calendar.",
            "A few days without tasks 🙂\n\nIf you feel like coming back — just say the word. I'm here.",
        ],
        "btn_archive": "🗂 Task archive",
        "archive_header": "🗂 *Completed tasks archive*",
        "archive_empty": "Archive is empty — no past tasks.",
        "btn_archive_next": "Next →",
        "goal_detected": (
            "🎯 This looks like more than a task — it's a *goal!*\n\n"
            "Want to set it up as a goal? I'll ask a couple of quick questions "
            "and help you turn it into something clear and achievable."
        ),
        "btn_goal_yes": "🎯 Yes, create a goal",
        "btn_goal_no": "📝 Save as a task",
        "goal_ask_deadline": (
            "📅 Great, let's go!\n\n"
            "By when do you want to achieve this goal?\n\n"
            "_For example: 'by July 1st', 'in 3 months', 'by end of year'_"
        ),
        "goal_ask_criteria": (
            "✨ Almost there!\n\n"
            "How will you know the goal is achieved? Describe the result concretely.\n\n"
            "_For example: '100 users', 'lost 8 kg', 'website launched'_"
        ),
        "goal_created": (
            "🎯 *Goal created!*\n\n"
            "*{title}*\n"
            "📅 Deadline: {deadline}\n"
            "✅ Success criteria: _{criteria}_\n\n"
            "Keep adding tasks as usual — I'll suggest linking them to this goal "
            "so you can track your progress 💪"
        ),
        "goals_empty": (
            "🎯 You don't have any active goals yet.\n\n"
            "Just describe something big by voice or text — "
            "I'll recognize it as a goal and offer to set it up."
        ),
        "goals_header": "🎯 *Your goals:*\n\n",
        "goal_progress": "{bar} {pct}% — {done}/{total} tasks",
        "goal_no_tasks": "_no tasks added yet_",
        "goal_deadline_label": "due {date}",
        "goal_done_msg": "🏆 *Goal achieved!*\n\nAll tasks are done — you did it! 🎉",
        "goal_link_ask": "📎 This task looks like a step toward your goal *\"{goal}\"*. Link it?",
        "btn_goal_link_yes": "✅ Link it",
        "btn_goal_link_no": "➡️ No",
        "goal_linked": "✅ Linked to goal *\"{goal}\"*",
        "btn_goal_delete": "🗑 Delete goal",
        "goal_delete_confirm": "Delete goal *\"{title}\"*?\n\nWhat should happen to linked tasks?",
        "btn_goal_del_tasks": "🗑 Delete tasks",
        "btn_goal_del_keep": "🔗 Keep tasks",
        "btn_goal_del_cancel": "❌ Cancel",
        "goal_deleted_with_tasks": "🗑 Goal deleted along with {n} task(s).",
        "goal_deleted_tasks_kept": "🗑 Goal deleted. {n} task(s) unlinked and kept in your list.",
        "goal_deleted_no_tasks": "🗑 Goal deleted.",
        "ask_when": "📅 When do you plan to do this?\n\nFor example: *today at 5pm*, *tomorrow at 10am*, *April 25*",
        "ask_when_unclear": "🤔 Couldn't understand the date. Try something like: *tomorrow at 3pm* or *April 25 at 9am*",
        "btn_goals": "🎯 Goals",
        "btn_reminder_before": "⏰ Remind {min} min before",
        "reminder_before_settings": "⏰ *Task reminders*\nNow: {min} min before start",
        "reminder_before_set": "✅ Will remind {min} min before task.",
        "task_reminder": "⏰ Reminder: *{title}* starts at {time}",
        "menu_hint": [
            "Say it and forget it — I'll remind you at the right time 🔔",
            "Something important today? Dictate it — I won't forget 🎙",
            "What can't you miss? Just say it and I'll keep track 📌",
            "Dictate a task in 10 seconds — I'll take care of the rest:",
            "Voice or text — your call. What do you need to remember? 📝",
            "Got a meeting or deadline? Tell me — I'll note and remind you:",
            "Set a reminder right now — by voice or text:",
            "Create a task — I'll ping you exactly when you need it 🕐",
        ],
        "reminder_ask": "⏰ How many minutes before a task should I remind you?",
        "reminder_ask_set": "✅ I'll remind you {min} min before each task.",
    },
    "uk": {
        "choose_lang": "Привет! Выбери язык / Choose language / Оберіть мову:",
        "lang_set": "Мову встановлено: Українська 🇺🇦\n\nПросто напишіть або надиктуйте голосове — я витягну задачі та розставлю їх по матриці Ейзенхауера.",
        "processing": "Обробляю...",
        "transcribing": "Транскрибую голосове...",
        "recognized": "Розпізнав: ",
        "rate_limit": "⚠️ Забагато запитів. Зачекайте хвилину і спробуйте знову.",
        "feedback_too_long": f"⚠️ Повідомлення занадто довге. Максимум {_FEEDBACK_MAX_TEXT_LEN} символів.",
        "feedback_cooldown": "⏳ Ви вже надсилали повідомлення. Наступне можна надіслати через {{min}} хв.",
        "too_long": "⚠️ Голосове занадто довге (більше 60 сек). Запишіть кілька коротких повідомлень.",
        "too_short": "⚠️ Повідомлення занадто коротке. Спробуйте записати детальніше.",
        "no_text": "⚠️ Не вдалося розпізнати мову. Перевірте якість запису і спробуйте знову.",
        "no_tasks": "⚠️ Не знайшов задач у повідомленні. Опишіть що потрібно зробити.",
        "add_calendar": "📅 Google Calendar",
        "apple_cal": "🍎 Apple Calendar",
        "save": "✅ Зберегти",
        "skip": "❌ Пропустити",
        "adding": "⏳ Додаю до Календаря...",
        "added": "✅ Додано до Календаря",
        "added_btn": "📅 Відкрити в Календарі",
        "task_saved": "✅ _Задачу збережено_",
        "task_skipped": "❌ _Задачу не збережено_",
        "skip_invite": "🎙 Надиктуй наступну задачу або напиши текстом",
        "task_time_past": "⚠️ Вказаний час вже минув. Уточніть, будь ласка, коли саме потрібно виконати задачу.",
        "calendar_error": "Помилка Календаря: ",
        "error": "Помилка: ",
        "offer_calendar": "📅 Хочете додавати задачі до Google Calendar і отримувати нагадування?",
        "connect_calendar": "📅 Підключити календар",
        "skip_calendar": "➡️ Пропустити",
        "connect_link": "🔗 Підключіть Google Calendar:",
        "calendar_connected": "✅ Google Calendar підключено! Тепер я нагадуватиму вам про задачі.",
        "btn_apple_cal": "🍎 Apple Calendar",
        "btn_apple_cal_connected": "🍎 Apple Calendar ✅",
        "apple_cal_info": (
            "🍎 *Підписка на Apple Calendar*\n\n"
            "Натисни кнопку нижче — Apple Calendar відкриється і запропонує підписатися.\n\n"
            "Всі задачі з бота автоматично з'являться у твоєму календарі й оновлюватимуться щогодини."
        ),
        "apple_cal_info_gcal": (
            "🍎 *Підписка на Apple Calendar*\n\n"
            "⚠️ У тебе вже підключено Google Calendar — задачі з бота вже потрапляють в Apple Calendar через нього.\n\n"
            "Підписка потрібна лише якщо хочеш бачити задачі в окремому календарі, не через Google.\n\n"
            "_Якщо підпишешся — задачі з'являться двічі._"
        ),
        "apple_cal_status": "✅ Підписка активна",
        "btn_apple_cal_open": "🍎 Відкрити в Apple Calendar",
        "btn_feedback": "✉️ Написати нам",
        "feedback_prompt": "✉️ Напишіть ваше повідомлення — текст або голосове. Ми читаємо кожне звернення.",
        "feedback_sent": "✅ Повідомлення надіслано! Дякуємо за зворотній зв'язок.",
        "feedback_from": "📨 *Нове повідомлення*\n👤 {name}\n📱 @{username}\n🆔 `{chat_id}`\n🌐 Мова: {lang}\n📱 Get My Task Bot",
        "cal_sync_new": "Google Calendar:\n*{title}*\n{date}",
        "cal_sync_removed": "🗑 Видалено з Google Calendar: *{title}*",
        "recurring_label": "🔄 Повторювана задача",
        "recurring_schedule_daily": "щодня",
        "recurring_schedule_weekly": "кожен {days}",
        "recurring_day_names": {"MO":"пн","TU":"вт","WE":"ср","TH":"чт","FR":"пт","SA":"сб","SU":"нд"},
        "btn_recur_yes": "🔄 Повторювана",
        "btn_recur_once": "1️⃣ Один раз",
        "recur_created": "✅ *{title}* збережена\n🔄 {schedule}",
        "btn_recur_continue": "✅ Продовжити серію",
        "btn_recur_delete": "🗑 Видалити серію",
        "recur_continued": "✅ Серія продовжується",
        "recur_deleted": "🗑 Повторювана задача *{title}* видалена",
        "calendar_not_connected": "❌ Календар не підключено. Використайте /connect щоб підключити.",
        "reminder": "🔔 Нагадування: *{title}*\n📅 {time}",
        "conflict_found": "⚠️ На цей час вже є подія: *{event}*.\n\nНапишіть або надиктуйте інший час для задачі *{title}*:",
        "conflict_confirm": "⚠️ На цей час вже є подія: *{event}*.\n\nЗберегти *{title}* все одно?",
        "conflict_save_anyway": "✅ Зберегти все одно",
        "conflict_no_save": "❌ Не зберігати",
        "saved_with_calendar": "✅ *{title}* збережено у задачах та додано до Google Calendar",
        "correction_unclear": "⚠️ Не зрозумів новий час. Спробуйте написати, наприклад: «об 11 ранку» або «завтра о 15:00»",
        "rescheduled": "✅ Час оновлено: {date} о {time}",
        "timezone_current": "🕐 Ваш поточний часовий пояс: *{tz}*\n\nОберіть зі списку або введіть вручну:",
        "timezone_set": "✅ Часовий пояс встановлено: *{tz}*",
        "timezone_manual": "✍️ Ввести вручну",
        "timezone_prompt": "Введіть назву часового поясу, наприклад:\n`Europe/Kyiv`, `Asia/Almaty`, `America/New_York`",
        "timezone_invalid": "❌ Не вдалося розпізнати часовий пояс. Спробуйте формат: `Europe/Kyiv`",
        "help": (
            "📋 *Що я вмію:*\n\n"
            "• Напишіть або надиктуйте голосове — витягну задачі та розставлю по матриці Ейзенхауера\n"
            "• Запропоную дату і час для кожної задачі\n"
            "• Збережу задачу в боті та автоматично додам до Google Календаря (якщо підключено)\n"
            "• Синхронізую Google Календар — нові події підтягуються кожні 15 хвилин\n"
            "• Розпізнаю повторювані задачі — створю серію в Календарі та нагадаю про кожну\n"
            "• Нагадаю про подію заздалегідь — за обраний вами час\n\n"
            "⚙️ *Команди:*\n"
            "/tasks — мої задачі\n"
            "/connect — підключити Google Календар\n"
            "/settings — нагадування, Календар, часовий пояс\n"
            "/timezone — змінити часовий пояс\n"
            "/help — ця довідка"
        ),
        "tasks_header": "📋 *Мої задачі:*\n\n",
        "tasks_empty": "У вас поки немає майбутніх задач.",
        "tasks_item": "{emoji} *{title}* — {date}\n",
        "tasks_today": "Задачі на сьогодні",
        "tasks_tomorrow": "Завтра",
        "tasks_birthdays": "🎂 Дні народження",
        "tasks_allday": "📅 Весь день",
        "tasks_more_days": "...і ще {n} {days}",
        "tasks_day": "день",
        "tasks_days_2_4": "дні",
        "tasks_days_5": "днів",
        "btn_new_task": "📝 Нова задача",
        "btn_my_tasks": "📋 Мої задачі",
        "btn_settings": "⚙️ Налаштування",
        "btn_timezone": "🕐 Часовий пояс",
        "btn_help": "❓ Допомога",
        "btn_connect": "📅 Підключити календар",
        "btn_view_calendar": "📅 Календар",
        "btn_disconnect_calendar": "🔌 Відключити календар",
        "calendar_disconnected": "📅 Календар відключено.",
        "btn_reminder": "☀️ Ранковий дайджест",
        "reminder_settings": "🔔 *Ранкове нагадування*\nЗараз: {time}",
        "reminder_disabled_text": "🔕 Вимкнено",
        "reminder_set": "✅ Нагадування встановлено на {time}",
        "reminder_off": "🔕 Нагадування вимкнено.",
        "morning_digest": "☀️ *Доброго ранку!* Ось ваші задачі на сьогодні:\n\n{tasks}",
        "morning_digest_future": "☀️ *Доброго ранку!* Задач на сьогодні немає.\n\nНайближчі справи:\n\n{tasks}",
        "morning_digest_empty": "☀️ *Доброго ранку!* У вас немає запланованих задач.",
        "morning_first_offer": "\n\n_Нагадування приходить о {time}. Бажаєте змінити час?_",
        "btn_reminder_change": "🕐 Змінити час",
        "btn_reminder_disable": "🔕 Вимкнути",
        "reengagement": [
            "Давно не було задач 👀\n\nЄ що запланувати? Просто напиши або надиктуй — я розберу за секунду.",
            "До речі, задачі можна надиктовувати голосом 🎙\n\nСкажи що треба зробити — я сам створю задачу і додам до календаря.",
            "Вже кілька днів без задач 🙂\n\nЯкщо вирішиш повернутись — просто напиши. Я тут.",
        ],
        "btn_archive": "🗂 Архів задач",
        "archive_header": "🗂 *Архів виконаних задач*",
        "archive_empty": "Архів порожній — немає минулих задач.",
        "btn_archive_next": "Далі →",
        "goal_detected": (
            "🎯 Схоже, це не просто задача — це *ціль!*\n\n"
            "Хочеш оформити її як ціль? Я допоможу зробити її чіткою і досяжною — "
            "поставлю кілька запитань і сформую готову ціль."
        ),
        "btn_goal_yes": "🎯 Так, створити ціль",
        "btn_goal_no": "📝 Зберегти як задачу",
        "goal_ask_deadline": (
            "📅 Чудово, починаємо!\n\n"
            "До якого терміну хочеш досягти цієї цілі?\n\n"
            "_Наприклад: «до 1 липня», «через 3 місяці», «до кінця року»_"
        ),
        "goal_ask_criteria": (
            "✨ Майже готово!\n\n"
            "Як зрозумієш, що ціль досягнута? Опиши результат конкретно.\n\n"
            "_Наприклад: «100 користувачів», «мінус 8 кг», «запущений сайт»_"
        ),
        "goal_created": (
            "🎯 *Ціль створено!*\n\n"
            "*{title}*\n"
            "📅 Дедлайн: {deadline}\n"
            "✅ Критерій успіху: _{criteria}_\n\n"
            "Додавай задачі як зазвичай — я буду пропонувати прив'язувати їх до цієї цілі. "
            "Так побачиш прогрес 💪"
        ),
        "goals_empty": (
            "🎯 У тебе поки немає активних цілей.\n\n"
            "Просто опиши щось масштабне голосом або текстом — "
            "я розпізнаю ціль і запропоную оформити її."
        ),
        "goals_header": "🎯 *Твої цілі:*\n\n",
        "goal_progress": "{bar} {pct}% — {done}/{total} задач",
        "goal_no_tasks": "_задачі ще не додані_",
        "goal_deadline_label": "до {date}",
        "goal_done_msg": "🏆 *Ціль виконана!*\n\nВсі задачі закриті — ти це зробив! 🎉",
        "goal_link_ask": "📎 Ця задача схожа на крок до цілі *\"{goal}\"*. Прив'язати її?",
        "btn_goal_link_yes": "✅ Прив'язати",
        "btn_goal_link_no": "➡️ Ні",
        "goal_linked": "✅ Прив'язано до цілі *\"{goal}\"*",
        "btn_goal_delete": "🗑 Видалити ціль",
        "goal_delete_confirm": "Видалити ціль *\"{title}\"*?\n\nЩо робити з пов'язаними задачами?",
        "btn_goal_del_tasks": "🗑 Видалити задачі",
        "btn_goal_del_keep": "🔗 Залишити задачі",
        "btn_goal_del_cancel": "❌ Скасувати",
        "goal_deleted_with_tasks": "🗑 Ціль видалена разом із задачами ({n} шт.).",
        "goal_deleted_tasks_kept": "🗑 Ціль видалена. {n} задач(і) від'єднані і залишились у списку.",
        "goal_deleted_no_tasks": "🗑 Ціль видалена.",
        "ask_when": "📅 Коли плануєш це зробити?\n\nНаприклад: *сьогодні о 17:00*, *завтра о 10:00*, *25 квітня*",
        "ask_when_unclear": "🤔 Не зрозумів дату. Спробуй написати, наприклад: *завтра о 15:00* або *25 квітня о 9:00*",
        "btn_goals": "🎯 Цілі",
        "btn_reminder_before": "⏰ Нагадати за {min} хв",
        "reminder_before_settings": "⏰ *Нагадування про задачі*\nЗараз: за {min} хв до початку",
        "reminder_before_set": "✅ Нагадуватиму за {min} хв до задачі.",
        "task_reminder": "⏰ Нагадування: *{title}* починається о {time}",
        "menu_hint": [
            "Скажи — і забудь. Я нагадаю в потрібний момент 🔔",
            "Є щось важливе сьогодні? Надиктуй — я не забуду 🎙",
            "Що не можна пропустити? Просто скажи — і я прослідкую 📌",
            "Надиктуй задачу за 10 секунд — я візьму її під контроль:",
            "Голос або текст — як зручно. Що потрібно не забути? 📝",
            "Є зустріч або дедлайн? Скажи — запишу і нагадаю:",
            "Постав нагадування прямо зараз — голосом або текстом:",
            "Створи задачу — я нагадаю саме тоді, коли потрібно 🕐",
        ],
        "reminder_ask": "⏰ За скільки хвилин нагадувати про задачі?",
        "reminder_ask_set": "✅ Нагадуватиму за {min} хв до задачі.",
    },
}

_URL_RE = re.compile(r'https?://[^\s\]\)>\"\']+')

def extract_url(text: str) -> str | None:
    """Return the first http/https URL found in text, or None."""
    if not text:
        return None
    m = _URL_RE.search(text)
    return m.group(0).rstrip('.,;') if m else None

def fmt_title(title: str, url: str | None, bold: bool = True) -> str:
    """Format task title: clickable link if URL present, bold otherwise."""
    if url:
        return f"[{title}]({url})"
    return f"*{title}*" if bold else title


def get_menu_hint(lang: str) -> str:
    hints = TEXTS.get(lang, TEXTS["ru"]).get("menu_hint", [])
    return random.choice(hints) if hints else "Надиктуйте или опишите задачу:"


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

def main_menu_keyboard(lang: str, calendar_connected: bool, task_count: int = 0) -> ReplyKeyboardMarkup:
    t = TEXTS[lang]
    tasks_label = t["btn_my_tasks"] + (f" ({task_count})" if task_count > 0 else "")
    row1 = [KeyboardButton(tasks_label), KeyboardButton(t["btn_settings"])]
    return ReplyKeyboardMarkup([row1], resize_keyboard=True)

def get_system_prompt(lang: str, tz_name: str = "Europe/Moscow") -> str:
    now = datetime.now(ZoneInfo(tz_name))
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    prompts = {
        "ru": f"""Ты — ассистент по управлению задачами. Сейчас {today} {current_time} (часовой пояс {tz_name}). Из текста извлеки все задачи и классифицируй по матрице Эйзенхауэра.
Для каждой задачи верни JSON с полями: title, description, quadrant (Q1/Q2/Q3/Q4), quadrant_name (на русском), suggested_date (YYYY-MM-DD), suggested_time (HH:MM если указано время или относительное время вроде "через 15 минут" — считай от {current_time}, иначе null), reason (на русском, пиши от второго лица: "Вы указали...", "Вы упомянули..." и т.д.).
ВАЖНО про title: (1) Каждый title обязан содержать глагол-действие — никаких безглагольных фрагментов. (2) Если пользователь перечисляет несколько объектов при одном глаголе ("протестировать X, Y и Z") — ВСЕГДА создавай ОДНУ задачу: "Протестировать X, Y и Z". Разбивай на несколько задач ТОЛЬКО если у каждой явно разные дата/время или контекст. (3) Каждый title должен быть самодостаточным законченным действием.
ВАЖНО про даты: (1) Если пользователь НЕ указал дату/время явно — верни suggested_date: null, suggested_time: null. (2) Никогда не выдумывай дату или время — только то, что пользователь сказал напрямую. (3) Явное указание — это: "сегодня", "завтра", конкретное число, "через N минут/часов/дней", "утром", "вечером", конкретное время ("в 15:00", "в 3 часа"). Общие фразы вроде "нужно сделать", "хочу", "планирую" без указания когда — НЕ явное.
Правила вычисления времени: "через N минут/часов" — прибавь к {current_time} и верни конкретные suggested_date + suggested_time; "через N дней" — прибавь к сегодня; "завтра", "послезавтра" — только дата, время null если не указано явно.
ВАЖНО про suggested_time: (1) Всегда записывай время в поле suggested_time (HH:MM), НИКОГДА не включай время в поле title. (2) Убирай из title слова "утра", "вечера", "ночи", "дня" и сами цифры времени — они идут в suggested_time. (3) Если время указано явно и уже прошло — флипни AM/PM (+12 ч).
Если задача повторяющаяся (например: "каждый день", "по вторникам и четвергам", "каждую неделю по пятницам", "всегда в 7 утра"), добавь поле recurring: true и recurrence: {{"freq": "DAILY" или "WEEKLY", "days": ["MO","TU","WE","TH","FR","SA","SU"] — только для WEEKLY, только нужные дни}}. suggested_date — ближайшая дата первого повторения. Если задача одиночная — не включай поле recurring.
Если в тексте есть URL (ссылка на Zoom, Meet, сайт и т.д.) — добавь поле url с этой ссылкой. Иначе не включай поле url.
Верни ТОЛЬКО валидный JSON массив. Без пояснений.""",
        "en": f"""You are a task management assistant. Current time is {today} {current_time} (timezone {tz_name}). Extract all tasks from the text and classify them using the Eisenhower Matrix.
For each task return JSON with fields: title, description, quadrant (Q1/Q2/Q3/Q4), quadrant_name (in English), suggested_date (YYYY-MM-DD), suggested_time (HH:MM if a time or relative time like "in 15 minutes" is specified — calculate from {current_time}, otherwise null), reason (in English, write in second person: "You specified...", "You mentioned..." etc).
IMPORTANT about title: (1) Every title must contain an action verb — no fragment-only titles. (2) If the user lists multiple objects under one verb ("test X, Y and Z") — ALWAYS create ONE task: "Test X, Y and Z". Split into multiple tasks ONLY if each has a clearly different date/time or context. (3) Each title must be a complete self-contained action.
IMPORTANT about dates: (1) If the user did NOT explicitly mention a date/time — return suggested_date: null, suggested_time: null. (2) Never invent a date or time — only use what the user said directly. (3) Explicit indicators: "today", "tomorrow", a specific date, "in N minutes/hours/days", "morning", "evening", a specific time ("at 3pm", "at 15:00"). Generic phrases like "need to do", "want to", "planning to" without saying when — are NOT explicit.
Time calculation rules: "in N minutes/hours" — add to {current_time} and return concrete suggested_date + suggested_time; "in N days" — add to today's date; "tomorrow", "next week" — date only, time null unless stated.
IMPORTANT about suggested_time: (1) Always put time in suggested_time field (HH:MM), NEVER include time in the title. (2) Strip words like "am", "pm", "morning", "evening" and the time digits from title — they go into suggested_time. (3) If time was explicitly stated but is in the past — flip AM/PM (+12h).
If the task is recurring (e.g. "every day", "every Tuesday and Thursday", "every week on Friday", "always at 7am"), add field recurring: true and recurrence: {{"freq": "DAILY" or "WEEKLY", "days": ["MO","TU","WE","TH","FR","SA","SU"] — only for WEEKLY, only needed days}}. suggested_date — nearest first occurrence. If the task is one-time — do not include recurring field.
If the text contains a URL (Zoom, Meet, website link, etc.) — add a url field with that link. Otherwise don't include the url field.
Return ONLY a valid JSON array. No explanations.""",
        "uk": f"""Ти — асистент з управління задачами. Зараз {today} {current_time} (часовий пояс {tz_name}). З тексту витягни всі задачі та класифікуй за матрицею Ейзенхауера.
Для кожної задачі поверни JSON з полями: title, description, quadrant (Q1/Q2/Q3/Q4), quadrant_name (українською), suggested_date (YYYY-MM-DD), suggested_time (HH:MM якщо вказано час або відносний час на кшталт "через 15 хвилин" — рахуй від {current_time}, інакше null), reason (українською, пиши від другої особи: "Ви вказали...", "Ви згадали..." тощо).
ВАЖЛИВО про title: (1) Кожен title зобов'язаний містити дієслово-дію — жодних фрагментів без дієслова. (2) Якщо користувач перелічує кілька об'єктів при одному дієслові ("протестувати X, Y і Z") — ЗАВЖДИ створюй ОДНУ задачу: "Протестувати X, Y і Z". Ділити на кілька задач ТІЛЬКИ якщо у кожної явно різна дата/час або контекст. (3) Кожен title має бути самодостатньою завершеною дією.
ВАЖЛИВО про дати: (1) Якщо користувач НЕ вказав дату/час явно — повертай suggested_date: null, suggested_time: null. (2) Ніколи не вигадуй дату або час — тільки те, що користувач сказав напряму. (3) Явна вказівка — це: "сьогодні", "завтра", конкретне число, "через N хвилин/годин/днів", "вранці", "ввечері", конкретний час ("о 15:00", "о 3 годині"). Загальні фрази на кшталт "треба зробити", "хочу", "планую" без вказівки коли — НЕ явні.
Правила обчислення часу: "через N хвилин/годин" — додай до {current_time} і поверни конкретні suggested_date + suggested_time; "через N днів" — додай до сьогоднішньої дати; "завтра", "післязавтра" — лише дата, час null якщо не вказано.
ВАЖЛИВО про suggested_time: (1) Завжди записуй час у поле suggested_time (HH:MM), НІКОЛИ не включай час у поле title. (2) Прибирай з title слова "ранку", "вечора", "ночі", "дня" та самі цифри часу — вони йдуть у suggested_time. (3) Якщо час вказано явно, але вже минув — флипни AM/PM (+12 год).
Якщо задача повторювана (наприклад: "щодня", "щовівторка та четверга", "щотижня по п'ятницях", "завжди о 7 ранку"), додай поле recurring: true та recurrence: {{"freq": "DAILY" або "WEEKLY", "days": ["MO","TU","WE","TH","FR","SA","SU"] — лише для WEEKLY, лише потрібні дні}}. suggested_date — найближча дата першого повторення. Якщо задача одноразова — не включай поле recurring.
Якщо в тексті є URL (посилання на Zoom, Meet, сайт тощо) — додай поле url з цим посиланням. Інакше не включай поле url.
Поверни ТІЛЬКИ валідний JSON масив. Без пояснень.""",
    }
    return prompts[lang]

# ─── Google Calendar ──────────────────────────────────────────────────────────

def get_calendar_service_for_user(chat_id):
    user = get_user(chat_id)
    if not user or not user["calendar_token"]:
        return None
    creds = Credentials.from_authorized_user_info(json.loads(user["calendar_token"]), SCOPES)
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            save_user(chat_id, calendar_token=creds.to_json())
        except Exception as e:
            logger.error(f"Token refresh failed for {chat_id}: {e}")
            save_user(chat_id, calendar_token=None, calendar_connected=0)
            return None
    return build("calendar", "v3", credentials=creds)

def check_conflicts(service, date, time, timezone="Europe/Moscow"):
    if not time:
        return []
    try:
        offset = get_tz_offset_str(timezone)
        start_dt = datetime.fromisoformat(f"{date}T{time}:00")
        end_dt = start_dt + timedelta(minutes=30)
        time_min = start_dt.strftime(f"%Y-%m-%dT%H:%M:%S{offset}")
        time_max = end_dt.strftime(f"%Y-%m-%dT%H:%M:%S{offset}")
        result = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
        ).execute()
        # Только события с конкретным временем — целодневные игнорируем
        timed_events = [
            e for e in result.get("items", [])
            if "dateTime" in e.get("start", {})
        ]
        return timed_events
    except Exception as e:
        logger.error(f"Conflict check error: {e}")
        return []

def add_to_calendar(chat_id, task):
    service = get_calendar_service_for_user(chat_id)
    if not service:
        return None
    user = get_user(chat_id)
    tz_name = user["timezone"] if user else "Europe/Moscow"
    reminder_mins = user.get("reminder_minutes", 30) if user else 30
    date = task.get("suggested_date", datetime.now().strftime("%Y-%m-%d"))
    time = task.get("suggested_time")
    if time:
        start_dt = datetime.strptime(f"{date}T{time}", "%Y-%m-%dT%H:%M")
        end_dt = start_dt + timedelta(minutes=30)
        end_date = end_dt.strftime("%Y-%m-%d")
        start = {"dateTime": f"{date}T{time}:00", "timeZone": tz_name}
        end = {"dateTime": f"{end_date}T{end_dt.strftime('%H:%M')}:00", "timeZone": tz_name}
    else:
        next_day = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        start = {"date": date}
        end = {"date": next_day}
    event = {
        "summary": task["title"],
        "description": f"{task['description']}\n\n{task['quadrant']} — {task['quadrant_name']}\n{task['reason']}",
        "start": start,
        "end": end,
        "reminders": {
            "useDefault": False,
            "overrides": [{"method": "popup", "minutes": reminder_mins}]
        }
    }
    result = service.events().insert(calendarId="primary", body=event).execute()
    task_id = save_task_to_db(chat_id, task, synced_to_calendar=1, google_event_id=result.get("id"))
    return result.get("htmlLink"), task_id

def describe_recurrence(recurrence: dict, lang: str) -> str:
    t = TEXTS[lang]
    freq = recurrence.get("freq", "DAILY")
    days = recurrence.get("days", [])
    if freq == "DAILY":
        return t["recurring_schedule_daily"]
    if freq == "WEEKLY":
        names = t.get("recurring_day_names", {})
        day_str = ", ".join(names.get(d, d) for d in days) if days else t["recurring_schedule_daily"]
        return t["recurring_schedule_weekly"].format(days=day_str)
    logger.warning(f"describe_recurrence: unknown freq '{freq}'")
    return freq.lower()

def add_recurring_to_calendar(chat_id, task):
    service = get_calendar_service_for_user(chat_id)
    if not service:
        return None, None
    user = get_user(chat_id)
    tz_name = user["timezone"] if user else "Europe/Moscow"
    reminder_mins = user.get("reminder_minutes", 30) if user else 30
    date = task.get("suggested_date", datetime.now().strftime("%Y-%m-%d"))
    time = task.get("suggested_time")
    recurrence_obj = task.get("recurrence", {})
    freq = recurrence_obj.get("freq", "DAILY")
    days = recurrence_obj.get("days", [])
    rrule = f"RRULE:FREQ={freq}" + (f";BYDAY={','.join(days)}" if days else "")
    if time:
        start_dt = datetime.strptime(f"{date}T{time}", "%Y-%m-%dT%H:%M")
        end_dt = start_dt + timedelta(minutes=30)
        start = {"dateTime": f"{date}T{time}:00", "timeZone": tz_name}
        end = {"dateTime": f"{end_dt.strftime('%Y-%m-%d')}T{end_dt.strftime('%H:%M')}:00", "timeZone": tz_name}
    else:
        next_day = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        start = {"date": date}
        end = {"date": next_day}
    event = {
        "summary": task["title"],
        "description": task.get("description", ""),
        "start": start,
        "end": end,
        "recurrence": [rrule],
        "reminders": {
            "useDefault": False,
            "overrides": [{"method": "popup", "minutes": reminder_mins}]
        }
    }
    result = service.events().insert(calendarId="primary", body=event).execute()
    event_id = result.get("id")
    conn = sqlite3.connect("users.db")
    conn.execute(
        "INSERT INTO recurring_tasks (chat_id, title, google_event_id, rrule, suggested_time) VALUES (?,?,?,?,?)",
        (chat_id, task["title"], event_id, rrule, time)
    )
    conn.commit()
    conn.close()
    save_task_to_db(chat_id, task, synced_to_calendar=1, google_event_id=event_id)
    return event_id, result.get("htmlLink")

def save_task_to_db(chat_id, task, synced_to_calendar=0, google_event_id=None):
    conn = sqlite3.connect("users.db")
    cur = conn.execute(
        "INSERT INTO tasks (chat_id, title, description, quadrant, quadrant_name, suggested_date, suggested_time, done, synced_to_calendar, google_event_id, task_url, goal_id) VALUES (?,?,?,?,?,?,?,0,?,?,?,?)",
        (chat_id, task["title"], task.get("description",""), task.get("quadrant",""), task.get("quadrant_name",""),
         task.get("suggested_date",""), task.get("suggested_time",""), synced_to_calendar, google_event_id,
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

# ─── Time correction parser ───────────────────────────────────────────────────

async def parse_time_correction(text, lang, tz_name="Europe/Moscow"):
    now = datetime.now(ZoneInfo(tz_name))
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    prompts = {
        "ru": f"Пользователь хочет перенести задачу. Сейчас {today} {current_time} (пояс {tz_name}). Извлеки новую дату и/или время из: '{text}'. Верни ТОЛЬКО JSON: {{\"date\": \"YYYY-MM-DD\", \"time\": \"HH:MM\"}} или {{\"error\": \"unclear\"}} если непонятно. Время рассчитывай от текущего {current_time}.",
        "en": f"User wants to reschedule. Current time is {today} {current_time} (timezone {tz_name}). Extract new date/time from: '{text}'. Return ONLY JSON: {{\"date\": \"YYYY-MM-DD\", \"time\": \"HH:MM\"}} or {{\"error\": \"unclear\"}} if unclear. Calculate time from current {current_time}.",
        "uk": f"Користувач хоче перенести задачу. Зараз {today} {current_time} (пояс {tz_name}). Витягни нову дату/час з: '{text}'. Поверни ТІЛЬКИ JSON: {{\"date\": \"YYYY-MM-DD\", \"time\": \"HH:MM\"}} або {{\"error\": \"unclear\"}} якщо незрозуміло. Час розраховуй від поточного {current_time}.",
    }
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompts[lang]}],
        temperature=0.1,
    )
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError as e:
        logger.error(f"parse_time_correction JSON parse error: {e}\nRaw: {raw[:200]}")
        return {"error": "unclear"}

# ─── OAuth ────────────────────────────────────────────────────────────────────

def save_oauth_state(state, chat_id, code_verifier=None):
    conn = sqlite3.connect("users.db")
    conn.execute("DELETE FROM oauth_states WHERE created_at < datetime('now', '-1 hour')")  # cleanup old
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

def _pkce_pair():
    """Generate a PKCE code_verifier and corresponding S256 code_challenge."""
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(96)).rstrip(b"=").decode()
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge

def get_auth_url(chat_id):
    flow = Flow.from_client_secrets_file(
        "credentials.json",
        scopes=SCOPES,
        redirect_uri=f"{BASE_URL}/oauth/callback"
    )
    code_verifier, code_challenge = _pkce_pair()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
        code_challenge=code_challenge,
        code_challenge_method="S256",
    )
    save_oauth_state(state, chat_id, code_verifier=code_verifier)
    return auth_url


# ─── Reminders ────────────────────────────────────────────────────────────────

async def check_reminders():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT chat_id, lang, calendar_token FROM users WHERE calendar_connected = 1")
    users = c.fetchall()
    conn.close()
    now = datetime.utcnow()
    time_min = now.isoformat() + "Z"
    time_max = (now + timedelta(hours=24)).isoformat() + "Z"
    for chat_id, lang, token in users:
        try:
            service = get_calendar_service_for_user(chat_id)
            if not service:
                continue
            events_result = service.events().list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            events = events_result.get("items", [])
            for event in events:
                event_id = event["id"]
                title = event.get("summary", "—")
                start = event.get("start", {})
                start_str = start.get("dateTime") or start.get("date")
                if not start_str or "dateTime" not in start:
                    continue
                try:
                    start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    continue
                reminders = event.get("reminders", {})
                overrides = reminders.get("overrides", [])
                if not overrides and reminders.get("useDefault", True):
                    overrides = [{"method": "popup", "minutes": 30}]
                for reminder in overrides:
                    minutes_before = reminder.get("minutes", 30)
                    remind_at = start_dt - timedelta(minutes=minutes_before)
                    remind_at_utc = remind_at.astimezone(_utc.utc).replace(tzinfo=None)
                    diff = abs((remind_at_utc - now).total_seconds())
                    if diff <= 150:
                        remind_key = remind_at_utc.strftime("%Y-%m-%dT%H:%M")
                        if not reminder_already_sent(chat_id, event_id, remind_key):
                            eff_lang = lang or "ru"
                            user_obj = get_user(chat_id)
                            tz_name = user_obj["timezone"] if user_obj else "Europe/Moscow"
                            local_dt = start_dt.astimezone(ZoneInfo(tz_name))
                            date_part = format_date(local_dt.strftime("%Y-%m-%d"), eff_lang)
                            time_part = local_dt.strftime("%H:%M")
                            time_sep = _TIME_SEP.get(eff_lang, " ")
                            time_str = f"{date_part}{time_sep}{time_part}"
                            text = TEXTS[eff_lang]["reminder"].format(title=title, time=time_str)
                            event_link = event.get("htmlLink")
                            open_labels = {
                                "ru": "📅 Открыть в Google Календаре",
                                "en": "📅 Open in Google Calendar",
                                "uk": "📅 Відкрити в Google Календарі",
                            }
                            # Check if this is a recurring event instance
                            master_event_id = event.get("recurringEventId")
                            recurring_row = None
                            if master_event_id:
                                rc = sqlite3.connect("users.db")
                                recurring_row = rc.execute(
                                    "SELECT id FROM recurring_tasks WHERE chat_id=? AND google_event_id=?",
                                    (chat_id, master_event_id)
                                ).fetchone()
                                rc.close()
                            t_lang = TEXTS[eff_lang]
                            if recurring_row:
                                rid = recurring_row[0]
                                btn_rows = []
                                if event_link:
                                    btn_rows.append([InlineKeyboardButton(open_labels.get(eff_lang, open_labels["ru"]), url=event_link)])
                                btn_rows.append([
                                    InlineKeyboardButton(t_lang["btn_recur_continue"], callback_data=f"recur_continue_{rid}"),
                                    InlineKeyboardButton(t_lang["btn_recur_delete"], callback_data=f"recur_delete_{rid}"),
                                ])
                                markup = InlineKeyboardMarkup(btn_rows)
                            else:
                                markup = InlineKeyboardMarkup([[
                                    InlineKeyboardButton(open_labels.get(eff_lang, open_labels["ru"]), url=event_link)
                                ]]) if event_link else None
                            await bot_app.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown", reply_markup=markup)
                            mark_reminder_sent(chat_id, event_id, remind_key)
        except Exception as e:
            logger.error(f"Reminder error for {chat_id}: {e}")

async def sync_calendar_events():
    """Sync Google Calendar events (next 24 h) to bot tasks DB every 15 min."""
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT chat_id, lang FROM users WHERE calendar_connected = 1 AND lang IS NOT NULL")
    users = c.fetchall()
    conn.close()

    now = datetime.utcnow()
    time_min = now.isoformat() + "Z"
    time_max = (now + timedelta(days=1)).isoformat() + "Z"

    for chat_id, lang in users:
        try:
            service = get_calendar_service_for_user(chat_id)
            if not service:
                continue
            lang = lang or "ru"
            user_obj = get_user(chat_id)
            tz_name = user_obj["timezone"] if user_obj else "Europe/Moscow"

            # ── Fetch events from Google Calendar ──────────────────────────
            result = service.events().list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            cal_events = result.get("items", [])
            cal_event_ids = {e["id"] for e in cal_events}

            # ── Add new events not yet in bot DB ───────────────────────────
            with sqlite3.connect("users.db") as db:
                # Dedup by google_event_id
                existing_ids = {
                    row[0] for row in
                    db.execute("SELECT google_event_id FROM tasks WHERE chat_id=? AND google_event_id IS NOT NULL", (chat_id,)).fetchall()
                }
                # Dedup by (title, date, time) — catches tasks created via bot that are also in Calendar
                existing_keys = {
                    (row[0], row[1], row[2]) for row in
                    db.execute("SELECT title, suggested_date, suggested_time FROM tasks WHERE chat_id=?", (chat_id,)).fetchall()
                }

                for event in cal_events:
                    event_id = event["id"]
                    if event_id in existing_ids:
                        continue
                    title = event.get("summary", "—")
                    start = event.get("start", {})
                    if "dateTime" in start:
                        dt = datetime.fromisoformat(start["dateTime"])
                        suggested_date = dt.strftime("%Y-%m-%d")
                        suggested_time = dt.astimezone(ZoneInfo(tz_name)).strftime("%H:%M")
                    else:
                        suggested_date = start.get("date", now.strftime("%Y-%m-%d"))
                        suggested_time = None

                    # Extract URL from event: hangoutLink > conferenceData > location > description
                    event_url = (
                        event.get("hangoutLink")
                        or next((ep.get("uri") for ep in
                                 event.get("conferenceData", {}).get("entryPoints", [])
                                 if ep.get("uri", "").startswith("http")), None)
                        or (event.get("location", "") if event.get("location", "").startswith("http") else None)
                        or extract_url(event.get("description", ""))
                    )

                    # If a task with same title+date+time already exists — just link it to Calendar, don't create duplicate
                    task_key = (title, suggested_date, suggested_time)
                    if task_key in existing_keys:
                        db.execute(
                            "UPDATE tasks SET google_event_id=?, synced_to_calendar=1, task_url=COALESCE(task_url, ?) WHERE chat_id=? AND title=? AND suggested_date=? AND suggested_time IS ? AND google_event_id IS NULL",
                            (event_id, event_url, chat_id, title, suggested_date, suggested_time)
                        )
                        db.commit()
                        continue

                    db.execute(
                        "INSERT INTO tasks (chat_id, title, description, quadrant, quadrant_name, suggested_date, suggested_time, done, synced_to_calendar, google_event_id, task_url) VALUES (?,?,?,?,?,?,?,0,1,?,?)",
                        (chat_id, title, event.get("description", ""), "", "", suggested_date, suggested_time, event_id, event_url)
                    )
                    db.commit()

                    date_display = format_date(suggested_date, lang)
                    time_sep = _TIME_SEP.get(lang, " ")
                    date_str = date_display + (f"{time_sep}{suggested_time}" if suggested_time else "")
                    await bot_app.bot.send_message(
                        chat_id=chat_id,
                        text=TEXTS[lang]["cal_sync_new"].format(emoji="📌", title=title, date=date_str),
                        parse_mode="Markdown"
                    )

                # ── Remove tasks whose Calendar event was deleted ──────────────
                tracked = db.execute(
                    "SELECT id, title, google_event_id FROM tasks WHERE chat_id=? AND google_event_id IS NOT NULL AND done=0",
                    (chat_id,)
                ).fetchall()

                for task_id, title, event_id in tracked:
                    if event_id not in cal_event_ids:
                        # Check if it's truly gone (event might be outside 24h window but still future)
                        try:
                            service.events().get(calendarId="primary", eventId=event_id).execute()
                            # Still exists (just outside 3-day window) — skip
                        except Exception:
                            # 404 or gone — delete from bot DB
                            db.execute("DELETE FROM tasks WHERE id=?", (task_id,))
                            db.commit()
                            await bot_app.bot.send_message(
                                chat_id=chat_id,
                                text=TEXTS[lang]["cal_sync_removed"].format(title=title),
                                parse_mode="Markdown"
                            )

        except Exception as e:
            logger.error(f"Calendar sync error for {chat_id}: {e}")

async def check_task_reminders():
    conn = sqlite3.connect("users.db")
    users = conn.execute(
        "SELECT chat_id, lang, timezone, reminder_minutes FROM users WHERE reminder_minutes > 0 AND lang IS NOT NULL"
    ).fetchall()
    for chat_id, lang, tz_name, reminder_minutes in users:
        try:
            tz = ZoneInfo(tz_name or "Europe/Moscow")
            now = datetime.now(tz)
            lang = lang or "ru"

            # Find tasks where the reminder window has opened:
            #   task_time - reminder_minutes <= now  →  task_time <= now + reminder_minutes
            # AND task hasn't happened yet (with 5-min grace for tasks just passed):
            #   task_time >= now - 5min
            # This range approach avoids missing tasks due to scheduler timing / exact-minute mismatch.
            lo = now - timedelta(minutes=5)
            hi = now + timedelta(minutes=reminder_minutes)

            lo_date, lo_time = lo.strftime("%Y-%m-%d"), lo.strftime("%H:%M")
            hi_date, hi_time = hi.strftime("%Y-%m-%d"), hi.strftime("%H:%M")

            tasks = conn.execute(
                """SELECT id, title, suggested_date, suggested_time, task_url FROM tasks
                   WHERE chat_id=?
                   AND suggested_time IS NOT NULL
                   AND synced_to_calendar = 0
                   AND (suggested_date > ? OR (suggested_date = ? AND suggested_time >= ?))
                   AND (suggested_date < ? OR (suggested_date = ? AND suggested_time <= ?))""",
                (chat_id, lo_date, lo_date, lo_time, hi_date, hi_date, hi_time)
            ).fetchall()

            for task_id, title, date, time, task_url in tasks:
                remind_key = f"task_{task_id}"
                sent_key = f"{date}T{time}"
                if reminder_already_sent(chat_id, remind_key, sent_key):
                    continue
                title_fmt = fmt_title(title, task_url)
                await bot_app.bot.send_message(
                    chat_id=chat_id,
                    text=TEXTS[lang]["task_reminder"].format(title=title_fmt, time=time),
                    parse_mode="Markdown"
                )
                mark_reminder_sent(chat_id, remind_key, sent_key)
        except Exception as e:
            logger.error(f"Task reminder error for {chat_id}: {e}")
    conn.close()

# Morning digest deduplication stored in DB via sent_reminders table
_MORNING_DIGEST_EVENT_ID = "__morning_digest__"

async def send_morning_digests():
    conn = sqlite3.connect("users.db")
    users = conn.execute("SELECT chat_id, lang, timezone, reminder_time, reminder_enabled FROM users WHERE reminder_enabled=1 AND lang IS NOT NULL").fetchall()
    conn.close()
    for chat_id, lang, tz_name, reminder_time, reminder_enabled in users:
        try:
            tz = ZoneInfo(tz_name or "Europe/Moscow")
            now = datetime.now(tz)
            today = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M")
            rtime = reminder_time or "08:00"
            if current_time != rtime:
                continue
            if reminder_already_sent(chat_id, _MORNING_DIGEST_EVENT_ID, today):
                continue
            mark_reminder_sent(chat_id, _MORNING_DIGEST_EVENT_ID, today)
            lang = lang or "ru"
            t = TEXTS[lang]
            tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
            _birthday_kw = ("день рождения", "birthday", "народження", "день народження")
            def _is_bday(title): return any(kw in title.lower() for kw in _birthday_kw)
            def _strip_bday(title):
                for suffix in (" – день рождения", " – birthday", " – день народження", "'s Birthday"):
                    if title.lower().endswith(suffix.lower()):
                        return title[:-len(suffix)].strip(" –")
                return title

            db = sqlite3.connect("users.db")
            # All tasks today (timed + untimed)
            today_rows = db.execute(
                "SELECT title, suggested_time, task_url FROM tasks WHERE chat_id=? AND suggested_date=? ORDER BY suggested_time ASC NULLS LAST, id ASC",
                (chat_id, today)
            ).fetchall()
            # Future tasks (next 7 days, untimed only — timed ones get separate reminders)
            future_rows = db.execute(
                "SELECT title, suggested_date, task_url FROM tasks WHERE chat_id=? AND suggested_date>? AND suggested_date<=date(?,'+7 days') AND (suggested_time IS NULL OR suggested_time='') ORDER BY suggested_date ASC LIMIT 7",
                (chat_id, today, today)
            ).fetchall() if not today_rows else []
            db.close()

            def _build_digest_block(rows_today, rows_future):
                """Return formatted digest body with separate birthday / task sections."""
                lines = []
                if rows_today:
                    bdays   = [(ti, tm, u) for ti, tm, u in rows_today if _is_bday(ti)]
                    regular = [(ti, tm, u) for ti, tm, u in rows_today if not _is_bday(ti)]
                    if regular:
                        for title, timed, url in regular:
                            prefix = f"{timed}  " if timed else ""
                            lines.append(f"• {prefix}{fmt_title(title, url)}")
                    if bdays:
                        lines.append("")
                        lines.append(f"🎂 *{t['tasks_birthdays']}:*")
                        for title, _, _ in bdays:
                            lines.append(f"• {_strip_bday(title)}")
                else:
                    bdays_f   = [(ti, d, u) for ti, d, u in rows_future if _is_bday(ti)]
                    regular_f = [(ti, d, u) for ti, d, u in rows_future if not _is_bday(ti)]
                    if regular_f:
                        for title, date, url in regular_f:
                            rel = format_date_relative(date, today, tomorrow, lang)
                            lines.append(f"• {fmt_title(title, url)} — {rel}")
                    if bdays_f:
                        lines.append("")
                        lines.append(f"🎂 *{t['tasks_birthdays']}:*")
                        for title, date, _ in bdays_f:
                            rel = format_date_relative(date, today, tomorrow, lang)
                            lines.append(f"• {_strip_bday(title)} — {rel}")
                return "\n".join(lines)

            if today_rows:
                body = _build_digest_block(today_rows, [])
                text = t["morning_digest"].format(tasks=body)
            elif future_rows:
                body = _build_digest_block([], future_rows)
                text = t["morning_digest_future"].format(tasks=body)
            else:
                text = t["morning_digest_empty"]
            # First reminder offer
            user = get_user(chat_id)
            if user and not user.get("first_task_done"):
                text += t["morning_first_offer"].format(time=rtime)
                markup = InlineKeyboardMarkup([[
                    InlineKeyboardButton(t["btn_reminder_change"], callback_data="settings_reminder"),
                    InlineKeyboardButton(t["btn_reminder_disable"], callback_data="reminder_disable"),
                ]])
            else:
                markup = None
            await bot_app.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown", reply_markup=markup)
        except Exception as e:
            logger.error(f"Morning digest error for {chat_id}: {e}")

# ─── Re-engagement ────────────────────────────────────────────────────────────

_REENGAGEMENT_HOUR = 10      # send at 10:xx in user's local timezone
_REENGAGEMENT_INACTIVE_DAYS = 3   # trigger after 3 days of inactivity
_REENGAGEMENT_COOLDOWN_DAYS = 7   # minimum gap between messages
_REENGAGEMENT_MAX_COUNT = 3       # stop after 3 messages total

async def check_reengagement():
    """Send re-engagement nudges to inactive users at 10:00 their local time."""
    conn = sqlite3.connect("users.db")
    candidates = conn.execute("""
        SELECT chat_id, lang, timezone, reengagement_count
        FROM users
        WHERE lang IS NOT NULL
          AND last_active < datetime('now', ?)
          AND reengagement_count < ?
          AND (last_reengagement IS NULL OR last_reengagement < datetime('now', ?))
    """, (
        f"-{_REENGAGEMENT_INACTIVE_DAYS} days",
        _REENGAGEMENT_MAX_COUNT,
        f"-{_REENGAGEMENT_COOLDOWN_DAYS} days",
    )).fetchall()
    conn.close()

    for chat_id, lang, tz_name, count in candidates:
        try:
            tz = ZoneInfo(tz_name or "Europe/Moscow")
            now = datetime.now(tz)
            if now.hour != _REENGAGEMENT_HOUR:
                continue
            # Dedup: only once per day using sent_reminders
            today = now.strftime("%Y-%m-%d")
            if reminder_already_sent(chat_id, "__reengagement__", today):
                continue
            mark_reminder_sent(chat_id, "__reengagement__", today)

            lang = lang or "ru"
            messages = TEXTS[lang]["reengagement"]
            text = messages[min(count, len(messages) - 1)]

            await bot_app.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")

            # Update counters
            save_user(chat_id,
                      last_reengagement=datetime.now(_utc.utc).strftime("%Y-%m-%d %H:%M:%S"),
                      reengagement_count=count + 1)
            logger.info(f"[reengagement] sent #{count+1} to {chat_id}")
        except Exception as e:
            logger.warning(f"[reengagement] failed for {chat_id}: {e}")

# ─── Helpers ──────────────────────────────────────────────────────────────────

def adjust_task_to_future(task: dict, tz_name: str):
    """
    Checks if a task's suggested_date+time is in the past.
    Returns (adjusted_task, status) where status is:
      "ok"          — already in the future (no change)
      "flipped"     — AM/PM flipped automatically (07:00 → 19:00)
      "past"        — time is fully in the past, user must clarify
    """
    date_str = task.get("suggested_date")
    time_str = task.get("suggested_time")
    if not date_str or not time_str:
        return task, "ok"
    try:
        tz = ZoneInfo(tz_name)
        now = datetime.now(tz)
        task_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M").replace(tzinfo=tz)
        if task_dt > now:
            return task, "ok"
        # Try flipping AM/PM (+12 hours)
        flipped_dt = task_dt + timedelta(hours=12)
        if flipped_dt > now:
            adjusted = dict(task)
            adjusted["suggested_date"] = flipped_dt.strftime("%Y-%m-%d")
            adjusted["suggested_time"] = flipped_dt.strftime("%H:%M")
            return adjusted, "flipped"
        return task, "past"
    except Exception:
        return task, "ok"

async def process_text(text, lang, tz_name="Europe/Moscow"):
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": get_system_prompt(lang, tz_name)},
            {"role": "user", "content": text}
        ],
        temperature=0.3,
    )
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError as e:
        logger.error(f"process_text JSON parse error: {e}\nRaw: {raw[:200]}")
        return []

QUADRANT_EMOJI = {"Q1": "🔴", "Q2": "🟡", "Q3": "🔵", "Q4": "⚫"}

POPULAR_TIMEZONES = [
    ("UTC−8  Los Angeles",  "America/Los_Angeles"),
    ("UTC−6  Chicago",      "America/Chicago"),
    ("UTC−5  New York",     "America/New_York"),
    ("UTC−3  São Paulo",    "America/Sao_Paulo"),
    ("UTC+0  London",       "Europe/London"),
    ("UTC+1  Paris",        "Europe/Paris"),
    ("UTC+2  Kyiv",         "Europe/Kyiv"),
    ("UTC+3  Moscow",       "Europe/Moscow"),
    ("UTC+3  Istanbul",     "Europe/Istanbul"),
    ("UTC+4  Dubai",        "Asia/Dubai"),
    ("UTC+4  Tbilisi",      "Asia/Tbilisi"),
    ("UTC+5  Tashkent",     "Asia/Tashkent"),
    ("UTC+5  Yekaterinburg","Asia/Yekaterinburg"),
    ("UTC+6  Almaty",       "Asia/Almaty"),
    ("UTC+7  Novosibirsk",  "Asia/Novosibirsk"),
    ("UTC+8  Shanghai",     "Asia/Shanghai"),
    ("UTC+9  Tokyo",        "Asia/Tokyo"),
    ("UTC+10 Sydney",       "Australia/Sydney"),
    ("UTC+12 Auckland",     "Pacific/Auckland"),
]

def get_tz_offset_str(tz_name: str) -> str:
    tz = ZoneInfo(tz_name)
    offset = datetime.now(tz).utcoffset()
    total = int(offset.total_seconds())
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    h, m = divmod(total // 60, 60)
    return f"{sign}{h:02d}:{m:02d}"

_MONTHS = {
    "ru": ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"],
    "uk": ["січня","лютого","березня","квітня","травня","червня","липня","серпня","вересня","жовтня","листопада","грудня"],
    "en": ["January","February","March","April","May","June","July","August","September","October","November","December"],
}
_TIME_SEP = {"ru": " в ", "uk": " о ", "en": " at "}

def format_date(date_str: str, lang: str) -> str:
    try:
        d = _date.fromisoformat(date_str)
        months = _MONTHS.get(lang, _MONTHS["en"])
        if lang == "en":
            return f"{months[d.month - 1]} {d.day}, {d.year}"
        return f"{d.day} {months[d.month - 1]} {d.year}"
    except Exception:
        return date_str

def format_date_relative(date_str: str, today_str: str, tomorrow_str: str, lang: str) -> str:
    """Return 'сегодня'/'завтра'/'послезавтра' when close, full date otherwise."""
    _REL = {
        "ru": {"today": "сегодня", "tomorrow": "завтра", "day_after": "послезавтра"},
        "en": {"today": "today",   "tomorrow": "tomorrow", "day_after": "in 2 days"},
        "uk": {"today": "сьогодні","tomorrow": "завтра",   "day_after": "післязавтра"},
    }
    rel = _REL.get(lang, _REL["ru"])
    try:
        d = _date.fromisoformat(date_str)
        today = _date.fromisoformat(today_str)
        diff = (d - today).days
        if diff == 0:
            return rel["today"]
        if diff == 1:
            return rel["tomorrow"]
        if diff == 2:
            return rel["day_after"]
    except Exception:
        pass
    return format_date(date_str, lang)

def _days_word(n: int, lang: str, t: dict) -> str:
    """Russian/Ukrainian declension for N days."""
    if lang in ("ru", "uk"):
        if n % 100 in range(11, 20):
            return t["tasks_days_5"]
        r = n % 10
        if r == 1:
            return t["tasks_day"]
        if r in (2, 3, 4):
            return t["tasks_days_2_4"]
        return t["tasks_days_5"]
    return t["tasks_days_5"]  # English "days"

def build_tasks_by_day(rows, lang: str, today_str: str, tomorrow_str: str, current_time_str: str) -> str:
    """
    rows: (title, quadrant, suggested_date, suggested_time)
    A task is visually done when its date+time has passed:
      - has time: date < today OR (date == today AND time < current_time)
      - no time:  date < today
    """
    from collections import defaultdict
    t = TEXTS[lang]
    time_sep = _TIME_SEP.get(lang, " ")

    by_date: dict = defaultdict(list)
    for title, quadrant, date, time in rows:
        is_done = (date < today_str) or (date == today_str and bool(time) and time < current_time_str)
        by_date[date].append((title, quadrant, time, is_done))

    sorted_dates = sorted(by_date.keys())
    visible_dates = [d for d in sorted_dates if d <= tomorrow_str]  # Show today and tomorrow only

    blocks = []
    for date in visible_dates:
        formatted = format_date(date, lang)
        if date == today_str:
            header = f"*{t['tasks_today']} — {formatted}:*"
        elif date == tomorrow_str:
            header = f"*{t['tasks_tomorrow']}* — {formatted}"
        else:
            header = f"*{formatted}*"

        _birthday_kw = ("день рождения", "birthday", "народження", "день народження")
        def _is_birthday(title): return any(kw in title.lower() for kw in _birthday_kw)

        timed   = [(ti, q, tm, d) for ti, q, tm, d in by_date[date] if tm]
        untimed = [(ti, q, tm, d) for ti, q, tm, d in by_date[date] if not tm]
        birthdays = [x for x in untimed if _is_birthday(x[0])]
        allday    = [x for x in untimed if not _is_birthday(x[0])]

        lines = [header, ""]   # blank line after header
        for title, quadrant, time, is_done in timed:
            icon = "✅" if is_done else QUADRANT_EMOJI.get(quadrant, "⚪")
            lines.append(f"{time}  {icon} {title}")

        if birthdays:
            lines.append("")
            lines.append(f"*{t['tasks_birthdays']}:*")
            for title, _, _, _ in birthdays:
                # strip trailing "– день рождения" / "– birthday" etc.
                clean = title
                for suffix in (" – день рождения", " – birthday", " – день народження", "'s Birthday", "Birthday"):
                    if clean.lower().endswith(suffix.lower()):
                        clean = clean[:-len(suffix)].strip(" –")
                lines.append(clean)

        if allday:
            lines.append("")
            lines.append(f"*{t['tasks_allday']}:*")
            for title, quadrant, _, is_done in allday:
                icon = "✅" if is_done else QUADRANT_EMOJI.get(quadrant, "⚪")
                lines.append(f"{icon} {title}")

        blocks.append("\n".join(lines))

    text = "\n\n".join(blocks)
    return text

def generate_ics(task, tz_name="Europe/Moscow") -> bytes:
    date = task.get("suggested_date", datetime.now().strftime("%Y-%m-%d"))
    time = task.get("suggested_time")
    title = task.get("title", "Task").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
    description = task.get("reason", "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
    now_utc = datetime.now(_utc.utc).strftime("%Y%m%dT%H%M%SZ")
    uid = str(uuid.uuid4())

    if time:
        tz = ZoneInfo(tz_name)
        dt_start = datetime.strptime(f"{date}T{time}", "%Y-%m-%dT%H:%M").replace(tzinfo=tz)
        dt_end = dt_start + timedelta(minutes=30)
        fmt = "%Y%m%dT%H%M%S"
        dtstart_line = f"DTSTART;TZID={tz_name}:{dt_start.strftime(fmt)}"
        dtend_line = f"DTEND;TZID={tz_name}:{dt_end.strftime(fmt)}"
    else:
        next_day = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y%m%d")
        dtstart_line = f"DTSTART;VALUE=DATE:{date.replace('-', '')}"
        dtend_line = f"DTEND;VALUE=DATE:{next_day}"

    ics = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//Get My Task//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:PUBLISH\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{uid}\r\n"
        f"DTSTAMP:{now_utc}\r\n"
        f"{dtstart_line}\r\n"
        f"{dtend_line}\r\n"
        f"SUMMARY:{title}\r\n"
        f"DESCRIPTION:{description}\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )
    return ics.encode("utf-8")

async def show_tasks(update, chat_id, tasks, lang, context=None, indices=None):
    """Show task cards.
    indices: list mapping position→index in context.user_data["tasks"] for callbacks.
             If None, position == index (default behaviour).
    """
    user = get_user(chat_id)
    master_tasks = (context.user_data.get("tasks") or []) if context else []
    for pos, task in enumerate(tasks):
        i = indices[pos] if indices is not None else pos
        emoji = QUADRANT_EMOJI.get(task["quadrant"], "⚪")
        time_sep = _TIME_SEP.get(lang, " ")
        if task.get("suggested_date"):
            date_display = format_date(task["suggested_date"], lang)
            date_line = f"📅 {date_display}" + (f"{time_sep}{task['suggested_time']}" if task.get("suggested_time") else "")
        else:
            date_line = ""
        base_text = (
            f"{emoji} *{task['title']}*\n"
            f"{task['quadrant']} — {task['quadrant_name']}\n"
            + (date_line + "\n" if date_line else "")
        )
        save_skip_row = [
            InlineKeyboardButton(TEXTS[lang]["save"], callback_data=f"save_{i}"),
            InlineKeyboardButton(TEXTS[lang]["skip"], callback_data=f"skip_{i}"),
        ]
        if task.get("recurring") and task.get("recurrence"):
            schedule = describe_recurrence(task["recurrence"], lang)
            text = base_text + f"🔄 _{schedule}_"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(TEXTS[lang]["btn_recur_yes"], callback_data=f"recur_yes_{i}")],
                [InlineKeyboardButton(TEXTS[lang]["btn_recur_once"], callback_data=f"recur_once_{i}"),
                 InlineKeyboardButton(TEXTS[lang]["skip"], callback_data=f"skip_{i}")],
            ])
        else:
            text = base_text + f"_{task['reason']}_"
            gcal_connected = bool(user and user.get("calendar_connected"))
            ical_subscribed = bool(user and user.get("ical_token"))
            if gcal_connected or ical_subscribed:
                # Calendar is already set up — sync happens automatically, no extra button needed
                keyboard = InlineKeyboardMarkup([save_skip_row])
            else:
                # No calendar connected — offer both options
                gcal_btn = InlineKeyboardButton(TEXTS[lang]["add_calendar"], callback_data="connect_calendar")
                apple_btn = InlineKeyboardButton(TEXTS[lang]["apple_cal"], callback_data=f"ics_{i}")
                keyboard = InlineKeyboardMarkup([
                    [gcal_btn, apple_btn],
                    save_skip_row,
                ])
        card_msg = await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)
        # Store all message_ids needed for skip-cleanup in the task itself
        if context is not None:
            cleanup = list(context.user_data.get("_cleanup_ids", []))
            cleanup.append(card_msg.message_id)
            # Update cleanup_ids on the master tasks list by correct index
            if i < len(master_tasks):
                master_tasks[i]["_cleanup_ids"] = cleanup
            else:
                tasks[pos]["_cleanup_ids"] = cleanup

async def offer_calendar(update, chat_id, lang):
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(TEXTS[lang]["connect_calendar"], callback_data="connect_calendar"),
        InlineKeyboardButton(TEXTS[lang]["skip_calendar"], callback_data="skip_calendar"),
    ]])
    await update.message.reply_text(TEXTS[lang]["offer_calendar"], reply_markup=keyboard)

async def ask_reminder_minutes(target, chat_id, lang):
    """target can be update.message or bot (for send_message)"""
    t = TEXTS[lang]
    opts = [5, 15, 30, 60, 120]
    labels = {
        "ru": {5:"5 мин", 15:"15 мин", 30:"30 мин", 60:"1 час", 120:"2 часа"},
        "en": {5:"5 min", 15:"15 min", 30:"30 min", 60:"1 hour", 120:"2 hours"},
        "uk": {5:"5 хв", 15:"15 хв", 30:"30 хв", 60:"1 год", 120:"2 год"},
    }
    lang_labels = labels.get(lang, labels["en"])
    rows = [[InlineKeyboardButton(lang_labels[m], callback_data=f"set_remind_min_{m}") for m in opts]]
    markup = InlineKeyboardMarkup(rows)
    if hasattr(target, 'reply_text'):
        await target.reply_text(t["reminder_ask"], reply_markup=markup)
    else:
        await target.send_message(chat_id=chat_id, text=t["reminder_ask"], reply_markup=markup)

async def handle_reschedule(update, context, text, chat_id, lang):
    try:
        user_tz = get_user(chat_id)["timezone"]
        correction = await parse_time_correction(text, lang, user_tz)
        if "error" in correction:
            await update.message.reply_text(TEXTS[lang]["correction_unclear"])
            return
        task = context.user_data["pending_task"]
        if "date" in correction:
            task["suggested_date"] = correction["date"]
        if "time" in correction:
            task["suggested_time"] = correction["time"]
        await update.message.reply_text(
            TEXTS[lang]["rescheduled"].format(
                date=format_date(task["suggested_date"], lang),
                time=task.get("suggested_time", "—")
            )
        )
        service = get_calendar_service_for_user(chat_id)
        user_tz = get_user(chat_id)["timezone"]
        conflicts = check_conflicts(service, task["suggested_date"], task.get("suggested_time"), user_tz)
        if conflicts:
            conflict_title = conflicts[0].get("summary", "—")
            await update.message.reply_text(
                TEXTS[lang]["conflict_found"].format(event=conflict_title, title=task["title"]),
                parse_mode="Markdown"
            )
            context.user_data["pending_task"] = task
            return
        del context.user_data["pending_task"]
        msg = await update.message.reply_text(TEXTS[lang]["adding"])
        link, _ = add_to_calendar(chat_id, task)
        added_markup = InlineKeyboardMarkup([[InlineKeyboardButton(TEXTS[lang]["added_btn"], url=link)]]) if link else None
        await msg.edit_text(TEXTS[lang]["added"], reply_markup=added_markup)
        user = get_user(chat_id)
        await update.message.reply_text(
            get_menu_hint(lang),
            reply_markup=main_menu_keyboard(lang, user["calendar_connected"], get_active_task_count(chat_id))
        )
    except Exception as e:
        await update.message.reply_text(TEXTS[lang]["error"] + str(e))

async def process_and_show_from_callback(query, context, text, chat_id, lang):
    """Same as process_and_show but triggered from a callback (no Update object)."""
    user = get_user(chat_id)
    tz_name = user["timezone"] if user else "Europe/Moscow"
    tasks = await process_text(text, lang, tz_name)
    if not tasks:
        await query.message.reply_text(TEXTS[lang]["no_tasks"])
        return
    valid_tasks = []
    for task in tasks:
        adjusted, status = adjust_task_to_future(task, tz_name)
        if status != "past":
            valid_tasks.append(adjusted)
    if not valid_tasks:
        return
    context.user_data["tasks"] = valid_tasks
    # Reuse show_tasks with a minimal update-like object
    class _FakeUpdate:
        message = query.message
        effective_chat = query.message.chat
    await show_tasks(_FakeUpdate(), chat_id, valid_tasks, lang, context=context)


async def process_and_show(update, context, text, chat_id, lang):
    user = get_user(chat_id)
    tz_name = user["timezone"] if user else "Europe/Moscow"
    # ── Goal detection ────────────────────────────────────────────────────────
    goal_info = await classify_goal_or_task(text, lang, tz_name)
    if goal_info.get("is_goal"):
        context.user_data["goal_draft"] = {
            "title": text[:200],
            "deadline": goal_info.get("deadline"),
            "criteria": goal_info.get("criteria"),
        }
        t = TEXTS[lang]
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(t["btn_goal_yes"], callback_data="goal_confirm_yes"),
            InlineKeyboardButton(t["btn_goal_no"],  callback_data="goal_confirm_no"),
        ]])
        await update.message.reply_text(t["goal_detected"], parse_mode="Markdown", reply_markup=keyboard)
        return
    tasks = await process_text(text, lang, tz_name)
    if not tasks:
        await update.message.reply_text(TEXTS[lang]["no_tasks"])
        return
    # Validate and adjust task times — never allow past datetimes
    valid_tasks = []
    for task in tasks:
        adjusted, status = adjust_task_to_future(task, tz_name)
        if status == "past":
            await update.message.reply_text(
                f"⚠️ *{task.get('title', '')}*\n" + TEXTS[lang]["task_time_past"],
                parse_mode="Markdown"
            )
        else:
            valid_tasks.append(adjusted)
    if not valid_tasks:
        return
    # Store all tasks with correct indices upfront
    context.user_data["tasks"] = valid_tasks
    with_date_idx = [i for i, t in enumerate(valid_tasks) if t.get("suggested_date")]
    no_date_idx   = [i for i, t in enumerate(valid_tasks) if not t.get("suggested_date")]
    # Show tasks that already have a date
    if with_date_idx:
        await show_tasks(update, chat_id,
                         [valid_tasks[i] for i in with_date_idx],
                         lang, context=context, indices=with_date_idx)
    # For tasks without a date — ask when
    if no_date_idx:
        context.user_data["pending_when_indices"] = no_date_idx
        await update.message.reply_text(TEXTS[lang]["ask_when"], parse_mode="Markdown")

# ─── Handlers ─────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    save_user(chat_id)
    user = get_user(chat_id)
    if user and user["lang"]:
        lang = user["lang"]
        await update.message.reply_text(
            get_menu_hint(lang),
            reply_markup=main_menu_keyboard(lang, user["calendar_connected"], get_active_task_count(chat_id))
        )
        return
    # Auto-detect language from Telegram settings
    tg_lang = (update.effective_user.language_code or "en").lower()
    if tg_lang.startswith("ru"):
        lang = "ru"
    elif tg_lang.startswith("uk"):
        lang = "uk"
    else:
        lang = "en"
    save_user(chat_id, lang=lang)
    log_event(chat_id, "new_user")
    # Ask timezone during onboarding — required for correct reminders and calendar times
    await show_timezone_menu(update.message, chat_id, lang, onboarding=True)

async def connect_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    lang = user["lang"] if user else "ru"
    auth_url = get_auth_url(chat_id)
    await update.message.reply_text(
        TEXTS[lang]["connect_link"],
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Google Calendar", url=auth_url)]])
    )

async def _send_feedback_to_owner(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, lang: str):
    t = TEXTS[lang]
    # Cooldown check
    allowed, remaining_min = check_feedback_cooldown(chat_id)
    if not allowed:
        await update.message.reply_text(t["feedback_cooldown"].format(min=remaining_min))
        return
    # Text length check
    if update.message.text and len(update.message.text) > _FEEDBACK_MAX_TEXT_LEN:
        await update.message.reply_text(t["feedback_too_long"])
        return
    mark_feedback_sent(chat_id)
    tg_user = update.effective_user
    name = (tg_user.full_name or "—") if tg_user else "—"
    username = tg_user.username or "нет" if tg_user else "—"
    header = TEXTS[lang]["feedback_from"].format(
        name=name, username=username, chat_id=chat_id, lang=lang
    )
    try:
        await context.bot.send_message(chat_id=BOT_OWNER_ID, text=header, parse_mode="Markdown")
        await context.bot.forward_message(
            chat_id=BOT_OWNER_ID,
            from_chat_id=chat_id,
            message_id=update.message.message_id
        )
    except Exception as e:
        logger.error(f"Failed to forward feedback to owner: {e}")
    await update.message.reply_text(TEXTS[lang]["feedback_sent"])

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    if not user or not user["lang"]:
        await start(update, context)
        return
    lang = user["lang"]
    user_text = update.message.text.strip()
    if context.user_data.get("awaiting_feedback"):
        context.user_data.pop("awaiting_feedback")
        await _send_feedback_to_owner(update, context, chat_id, lang)
        return
    t_check = TEXTS[lang]
    _menu_buttons = {t_check["btn_my_tasks"].split("(")[0].strip(), t_check["btn_settings"],
                     t_check["btn_help"], t_check["btn_timezone"], t_check["btn_connect"]}
    if context.user_data.get("awaiting_timezone") and any(user_text.startswith(b) for b in _menu_buttons):
        context.user_data.pop("awaiting_timezone", None)
        context.user_data.pop("timezone_onboarding", None)
    if context.user_data.get("awaiting_timezone"):
        onboarding = context.user_data.pop("timezone_onboarding", False)
        context.user_data.pop("awaiting_timezone")
        try:
            ZoneInfo(user_text)
            save_user(chat_id, timezone=user_text)
            await update.message.reply_text(
                TEXTS[lang]["timezone_set"].format(tz=user_text), parse_mode="Markdown"
            )
            if onboarding:
                updated_user = get_user(chat_id)
                await update.message.reply_text(
                    TEXTS[lang]["lang_set"],
                    reply_markup=main_menu_keyboard(lang, updated_user["calendar_connected"], get_active_task_count(chat_id))
                )
        except (ZoneInfoNotFoundError, KeyError):
            await update.message.reply_text(TEXTS[lang]["timezone_invalid"], parse_mode="Markdown")
        return
    t = TEXTS[lang]
    if user_text.startswith(t["btn_my_tasks"]):
        await tasks_command(update, context)
        return
    if user_text == t["btn_timezone"]:
        await timezone_command(update, context)
        return
    if user_text == t["btn_settings"]:
        await settings_command(update, context)
        return
    if user_text == t["btn_help"]:
        await help_command(update, context)
        return
    if user_text == t["btn_connect"]:
        await connect_command(update, context)
        return
    # ── "When?" follow-up for tasks without date ─────────────────────────────
    pending_when = context.user_data.get("pending_when_indices")
    if pending_when is not None:
        tz_name = user["timezone"] if user else "Europe/Moscow"
        parsed = await parse_time_correction(user_text, lang, tz_name)
        if parsed.get("error"):
            await update.message.reply_text(TEXTS[lang]["ask_when_unclear"], parse_mode="Markdown")
            return
        tasks = context.user_data.get("tasks", [])
        for idx in pending_when:
            if idx < len(tasks):
                if parsed.get("date"):
                    tasks[idx]["suggested_date"] = parsed["date"]
                if parsed.get("time"):
                    tasks[idx]["suggested_time"] = parsed["time"]
        context.user_data.pop("pending_when_indices", None)
        tasks_to_show = [tasks[idx] for idx in pending_when if idx < len(tasks)]
        await show_tasks(update, chat_id, tasks_to_show, lang, context=context, indices=pending_when)
        return
    # ── Goal creation state machine ───────────────────────────────────────────
    goal_step = context.user_data.get("goal_creation_step")
    if goal_step == "deadline":
        user_tz = user["timezone"] if user else "Europe/Moscow"
        deadline = await parse_goal_deadline(user_text, lang, user_tz)
        if not deadline:
            await update.message.reply_text(
                "🤔 Не могу разобрать дату. Попробуй ещё раз — например: _«1 июля»_, _«через 3 месяца»_",
                parse_mode="Markdown"
            )
            return
        context.user_data["goal_draft"]["deadline"] = deadline
        context.user_data["goal_creation_step"] = "criteria"
        await update.message.reply_text(t["goal_ask_criteria"], parse_mode="Markdown")
        return
    if goal_step == "criteria":
        context.user_data.pop("goal_creation_step", None)
        draft = context.user_data.pop("goal_draft", {})
        goal_id = save_goal_to_db(
            chat_id=chat_id,
            title=draft.get("title", ""),
            criteria=user_text,
            deadline=draft.get("deadline", ""),
        )
        deadline_display = format_date(draft.get("deadline", ""), lang)
        await update.message.reply_text(
            t["goal_created"].format(
                title=draft.get("title", ""),
                deadline=deadline_display,
                criteria=user_text,
            ),
            parse_mode="Markdown"
        )
        return
    # ── Reschedule ────────────────────────────────────────────────────────────
    if "pending_task" in context.user_data:
        if len(user_text) < 3:
            await update.message.reply_text(t["correction_unclear"])
            return
        await handle_reschedule(update, context, user_text, chat_id, lang)
        return
    if len(user_text) < 3:
        await update.message.reply_text(t["too_short"])
        return
    if not check_rate_limit(chat_id):
        await update.message.reply_text(t["rate_limit"])
        return
    proc_msg = await update.message.reply_text(t["processing"])
    context.user_data["_cleanup_ids"] = [update.message.message_id, proc_msg.message_id]
    log_event(chat_id, "text_task")
    try:
        await process_and_show(update, context, user_text, chat_id, lang)
    except Exception as e:
        await update.message.reply_text(t["error"] + str(e))

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logger.info(f"handle_voice called for chat_id={chat_id}")
    user = get_user(chat_id)
    if not user or not user["lang"]:
        await start(update, context)
        return
    lang = user["lang"]
    voice = update.message.voice or update.message.audio
    if voice.duration > 60:
        await update.message.reply_text(TEXTS[lang]["too_long"])
        return
    if voice.duration < 1:
        await update.message.reply_text(TEXTS[lang]["too_short"])
        return
    if context.user_data.get("awaiting_feedback"):
        context.user_data.pop("awaiting_feedback")
        await _send_feedback_to_owner(update, context, chat_id, lang)
        return
    if not check_rate_limit(chat_id):
        await update.message.reply_text(TEXTS[lang]["rate_limit"])
        return
    transcribing_msg = await update.message.reply_text(TEXTS[lang]["transcribing"])
    cleanup_ids = [update.message.message_id, transcribing_msg.message_id]
    log_event(chat_id, "voice_task")
    try:
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            file = await context.bot.get_file(voice.file_id)
            await file.download_to_drive(tmp_path)
            with open(tmp_path, "rb") as f:
                transcription = groq_client.audio.transcriptions.create(
                    model="whisper-large-v3", file=f)
        finally:
            os.unlink(tmp_path)
        text = transcription.text.strip()
        if not text or len(text) < 5:
            await update.message.reply_text(TEXTS[lang]["no_text"])
            return
        recognized_msg = await update.message.reply_text(TEXTS[lang]["recognized"] + text)
        cleanup_ids.append(recognized_msg.message_id)
        context.user_data["_cleanup_ids"] = cleanup_ids
        # Route through goal state machine if active
        goal_step = context.user_data.get("goal_creation_step")
        if goal_step == "deadline":
            user_tz = user["timezone"] if user else "Europe/Moscow"
            deadline = await parse_goal_deadline(text, lang, user_tz)
            if not deadline:
                await update.message.reply_text(
                    "🤔 Не могу разобрать дату. Попробуй ещё раз — например: _«1 июля»_, _«через 3 месяца»_",
                    parse_mode="Markdown"
                )
                return
            context.user_data["goal_draft"]["deadline"] = deadline
            context.user_data["goal_creation_step"] = "criteria"
            await update.message.reply_text(TEXTS[lang]["goal_ask_criteria"], parse_mode="Markdown")
            return
        if goal_step == "criteria":
            context.user_data.pop("goal_creation_step", None)
            draft = context.user_data.pop("goal_draft", {})
            save_goal_to_db(
                chat_id=chat_id,
                title=draft.get("title", ""),
                criteria=text,
                deadline=draft.get("deadline", ""),
            )
            deadline_display = format_date(draft.get("deadline", ""), lang)
            await update.message.reply_text(
                TEXTS[lang]["goal_created"].format(
                    title=draft.get("title", ""),
                    deadline=deadline_display,
                    criteria=text,
                ),
                parse_mode="Markdown"
            )
            return
        # ── "When?" follow-up for tasks without date ─────────────────────────
        pending_when = context.user_data.get("pending_when_indices")
        if pending_when is not None:
            tz_name = user["timezone"] if user else "Europe/Moscow"
            parsed = await parse_time_correction(text, lang, tz_name)
            if parsed.get("error"):
                await update.message.reply_text(TEXTS[lang]["ask_when_unclear"], parse_mode="Markdown")
                return
            all_tasks = context.user_data.get("tasks", [])
            for idx in pending_when:
                if idx < len(all_tasks):
                    if parsed.get("date"):
                        all_tasks[idx]["suggested_date"] = parsed["date"]
                    if parsed.get("time"):
                        all_tasks[idx]["suggested_time"] = parsed["time"]
            context.user_data.pop("pending_when_indices", None)
            tasks_to_show = [all_tasks[idx] for idx in pending_when if idx < len(all_tasks)]
            await show_tasks(update, chat_id, tasks_to_show, lang, context=context, indices=pending_when)
            return
        if "pending_task" in context.user_data:
            await handle_reschedule(update, context, text, chat_id, lang)
            return
        await process_and_show(update, context, text, chat_id, lang)
    except Exception as e:
        await update.message.reply_text(TEXTS[lang]["error"] + str(e))

_ARCHIVE_DATES_PER_PAGE = 3

async def send_archive_page(query, chat_id: int, lang: str, page: int = 0):
    t = TEXTS[lang]
    user = get_user(chat_id)
    tz_name = user["timezone"] if user else "Europe/Moscow"
    today = datetime.now(ZoneInfo(tz_name)).strftime("%Y-%m-%d")

    with sqlite3.connect("users.db") as db:
        all_dates = [
            r[0] for r in db.execute(
                "SELECT DISTINCT suggested_date FROM tasks WHERE chat_id=? AND suggested_date < ? ORDER BY suggested_date DESC",
                (chat_id, today)
            ).fetchall()
        ]

    if not all_dates:
        await query.message.reply_text(t["archive_empty"])
        return

    start = page * _ARCHIVE_DATES_PER_PAGE
    page_dates = all_dates[start: start + _ARCHIVE_DATES_PER_PAGE]
    has_more = len(all_dates) > start + _ARCHIVE_DATES_PER_PAGE

    placeholders = ",".join("?" * len(page_dates))
    with sqlite3.connect("users.db") as db:
        rows = db.execute(
            f"""SELECT title, quadrant, suggested_date, suggested_time FROM tasks
                WHERE chat_id=? AND suggested_date IN ({placeholders})
                ORDER BY suggested_date DESC, COALESCE(suggested_time, '00:00') ASC""",
            (chat_id, *page_dates)
        ).fetchall()

    from collections import defaultdict as _dd
    by_date = _dd(list)
    for title, quadrant, date, time in rows:
        by_date[date].append((title, quadrant, time))

    blocks = [t["archive_header"]]
    for date in page_dates:
        lines = [f"*{format_date(date, lang)}*"]
        for title, quadrant, time in by_date[date]:
            emoji = QUADRANT_EMOJI.get(quadrant, "⚪")
            if time:
                lines.append(f"{time}  {emoji} {title}")
            else:
                lines.append(f"{emoji} {title}")
        blocks.append("\n".join(lines))

    text = "\n\n".join(blocks)
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(t["btn_archive_next"], callback_data=f"archive_page_{page + 1}")
    ]]) if has_more else None

    await query.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    lang = user["lang"] if user else "ru"
    data = query.data
    if data.startswith("lang_"):
        lang = data.split("_")[1]
        save_user(chat_id, lang=lang)
        log_event(chat_id, "new_user")
        await query.edit_message_reply_markup(reply_markup=None)
        updated_user = get_user(chat_id)
        # If this is a new user (no timezone set yet), ask for timezone before showing menu
        if not updated_user or updated_user.get("timezone") == "Europe/Moscow":
            await show_timezone_menu(query.message, chat_id, lang, onboarding=True)
        else:
            await query.message.reply_text(
                TEXTS[lang]["lang_set"],
                reply_markup=main_menu_keyboard(lang, updated_user["calendar_connected"], get_active_task_count(chat_id))
            )
        return
    if data == "goal_confirm_yes":
        t = TEXTS[lang]
        draft = context.user_data.get("goal_draft", {})
        await query.edit_message_reply_markup(reply_markup=None)
        # Skip questions for info already present in the original message
        if draft.get("deadline") and draft.get("criteria"):
            # Have everything — create goal immediately
            context.user_data.pop("goal_draft", None)
            save_goal_to_db(chat_id, draft["title"], draft["criteria"], draft["deadline"])
            await query.message.reply_text(
                t["goal_created"].format(
                    title=draft["title"],
                    deadline=format_date(draft["deadline"], lang),
                    criteria=draft["criteria"],
                ), parse_mode="Markdown"
            )
        elif draft.get("deadline"):
            # Have deadline, only need criteria
            context.user_data["goal_creation_step"] = "criteria"
            await query.message.reply_text(t["goal_ask_criteria"], parse_mode="Markdown")
        else:
            # Need deadline (and maybe criteria after)
            context.user_data["goal_creation_step"] = "deadline"
            await query.message.reply_text(t["goal_ask_deadline"], parse_mode="Markdown")
        return
    if data == "goal_confirm_no":
        await query.edit_message_reply_markup(reply_markup=None)
        draft = context.user_data.pop("goal_draft", {})
        raw = draft.get("title", "")
        if raw:
            await process_and_show_from_callback(query, context, raw, chat_id, lang)
        return
    if data.startswith("goal_link_yes_"):
        goal_id = int(data.split("_")[3])
        task_idx = int(data.split("_")[4])
        tasks = context.user_data.get("tasks", [])
        if task_idx < len(tasks):
            task = tasks[task_idx]
            task["goal_id"] = goal_id
            # UPDATE the already-saved row instead of inserting a duplicate
            saved_task_id = context.user_data.get("saved_task_ids", {}).get(task_idx)
            if saved_task_id:
                link_task_to_goal(saved_task_id, goal_id)
            else:
                save_task_to_db(chat_id, task)  # fallback: task wasn't tracked
            goals = get_active_goals(chat_id)
            goal_title = next((g["title"] for g in goals if g["id"] == goal_id), "")
            await query.edit_message_text(
                TEXTS[lang]["goal_linked"].format(goal=goal_title), parse_mode="Markdown"
            )
        return
    if data.startswith("goal_link_no_"):
        task_idx = int(data.split("_")[3])
        tasks = context.user_data.get("tasks", [])
        if task_idx < len(tasks):
            # Task already saved, card already shown — just remove the link-offer message
            try:
                await query.message.delete()
            except Exception:
                await query.edit_message_reply_markup(reply_markup=None)
        return
    # ── Goal delete flow ──────────────────────────────────────────────────────
    if data.startswith("gdel_") and not any(data.startswith(p) for p in ("gdel_tasks_", "gdel_keep_", "gdel_cancel_")):
        goal_id = int(data.split("_")[1])
        t = TEXTS[lang]
        # fetch goal title for confirmation message
        conn = sqlite3.connect("users.db")
        row = conn.execute("SELECT title FROM goals WHERE id=?", (goal_id,)).fetchone()
        conn.close()
        if not row:
            await query.answer("Цель не найдена", show_alert=True)
            return
        title = row[0]
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(t["btn_goal_del_tasks"], callback_data=f"gdel_tasks_{goal_id}"),
             InlineKeyboardButton(t["btn_goal_del_keep"],  callback_data=f"gdel_keep_{goal_id}")],
            [InlineKeyboardButton(t["btn_goal_del_cancel"], callback_data=f"gdel_cancel_{goal_id}")],
        ])
        await query.edit_message_text(
            t["goal_delete_confirm"].format(title=title),
            parse_mode="Markdown", reply_markup=keyboard
        )
        return
    if data.startswith("gdel_tasks_") or data.startswith("gdel_keep_"):
        delete_tasks = data.startswith("gdel_tasks_")
        goal_id = int(data.split("_")[2])
        t = TEXTS[lang]
        n = delete_goal_from_db(goal_id, delete_tasks=delete_tasks)
        if n == 0:
            result_text = t["goal_deleted_no_tasks"]
        elif delete_tasks:
            result_text = t["goal_deleted_with_tasks"].format(n=n)
        else:
            result_text = t["goal_deleted_tasks_kept"].format(n=n)
        await query.edit_message_text(result_text, parse_mode="Markdown")
        return
    if data.startswith("gdel_cancel_"):
        goal_id = int(data.split("_")[2])
        t = TEXTS[lang]
        conn = sqlite3.connect("users.db")
        row = conn.execute(
            "SELECT id, title, criteria, deadline, quadrant, quadrant_name, status FROM goals WHERE id=? AND status='active'",
            (goal_id,)
        ).fetchone()
        conn.close()
        if not row:
            await query.edit_message_reply_markup(reply_markup=None)
            return
        g = {"id": row[0], "title": row[1], "criteria": row[2], "deadline": row[3],
             "quadrant": row[4], "quadrant_name": row[5], "status": row[6]}
        text = _render_goal_card(g, lang)
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(t["btn_goal_delete"], callback_data=f"gdel_{goal_id}")
        ]])
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        return
    # ── End goal delete flow ──────────────────────────────────────────────────
    if data.startswith("announce_send_") or data.startswith("announce_cancel_"):
        if chat_id != BOT_OWNER_ID:
            await query.answer("Нет доступа", show_alert=True)
            return
        announce_id = data.split("_", 2)[2]
        ann = _pending_announcements.get(announce_id)
        if data.startswith("announce_cancel_"):
            _pending_announcements.pop(announce_id, None)
            await query.edit_message_text("❌ Рассылка отменена.")
            return
        if not ann:
            await query.answer("Анонс не найден или устарел", show_alert=True)
            return
        await query.edit_message_text("⏳ Рассылаю...")
        conn = sqlite3.connect("users.db")
        users_to_send = conn.execute(
            "SELECT chat_id, lang FROM users WHERE last_active > datetime('now', '-30 days')"
        ).fetchall()
        conn.close()
        sent = 0
        failed = 0
        for u_chat_id, u_lang in users_to_send:
            text = ann.get(u_lang or "ru") or ann["ru"]
            try:
                await bot_app.bot.send_message(
                    chat_id=u_chat_id, text=text, parse_mode="Markdown"
                )
                sent += 1
                await asyncio.sleep(0.05)  # ~20 msg/sec, well within Telegram limits
            except Exception as e:
                failed += 1
                logger.warning(f"[announce] failed to send to {u_chat_id}: {e}")
        _pending_announcements.pop(announce_id, None)
        await query.edit_message_text(
            f"✅ *Рассылка завершена*\n📤 Отправлено: {sent}\n❌ Ошибок: {failed}",
            parse_mode="Markdown"
        )
        return
    if data == "connect_calendar":
        await query.edit_message_reply_markup(reply_markup=None)
        # If triggered from a task card, save the task so we can resume after OAuth
        tasks = context.user_data.get("tasks", [])
        # Try to find which task index triggered this (store all pending tasks)
        if tasks:
            save_user(chat_id, pending_task_json=json.dumps(tasks))
        auth_url = get_auth_url(chat_id)
        await query.message.reply_text(
            TEXTS[lang]["connect_link"],
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Google Calendar", url=auth_url)]])
        )
        return
    if data == "settings_feedback":
        allowed, remaining_min = check_feedback_cooldown(chat_id)
        if not allowed:
            await query.answer(TEXTS[lang]["feedback_cooldown"].format(min=remaining_min), show_alert=True)
            return
        await query.edit_message_reply_markup(reply_markup=None)
        context.user_data["awaiting_feedback"] = True
        await query.message.reply_text(TEXTS[lang]["feedback_prompt"])
        return
    if data == "settings_help":
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(TEXTS[lang]["help"], parse_mode="Markdown")
        return
    if data == "settings_timezone":
        await query.edit_message_reply_markup(reply_markup=None)
        await timezone_command_for_query(query, chat_id, lang)
        return
    if data == "settings_reminder_before":
        await query.edit_message_reply_markup(reply_markup=None)
        user = get_user(chat_id)
        minutes = user["reminder_minutes"] if user else 30
        t = TEXTS[lang]
        opts = [10, 15, 30, 60, 120]
        rows = [[InlineKeyboardButton(f"{m} мин" if lang == "ru" else f"{m} min", callback_data=f"reminder_before_{m}") for m in opts]]
        rows.append([InlineKeyboardButton(t["btn_reminder_disable"], callback_data="reminder_before_off")])
        await query.message.reply_text(
            t["reminder_before_settings"].format(min=minutes),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(rows)
        )
        return
    if data.startswith("reminder_before_") and data != "reminder_before_off":
        mins = int(data[len("reminder_before_"):])
        save_user(chat_id, reminder_before=mins, reminder_minutes=mins)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(TEXTS[lang]["reminder_before_set"].format(min=mins))
        return
    if data == "reminder_before_off":
        save_user(chat_id, reminder_before=0, reminder_minutes=0)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(TEXTS[lang]["reminder_off"])
        return
    if data == "settings_apple_cal":
        t = TEXTS[lang]
        user = get_user(chat_id)
        token = user.get("ical_token") if user else None
        if not token:
            token = secrets.token_urlsafe(24)
            save_user(chat_id, ical_token=token)
        open_url = f"{BASE_URL}/ical-open/{token}"
        gcal_connected = bool(user and user.get("calendar_connected"))
        info_text = t["apple_cal_info_gcal"] if gcal_connected else t["apple_cal_info"]
        # If already subscribed — show status line on top
        if user and user.get("ical_token"):
            info_text = f"{t['apple_cal_status']}\n\n" + info_text
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(t["btn_apple_cal_open"], url=open_url)
        ]])
        await query.message.reply_text(
            info_text, parse_mode="Markdown", reply_markup=keyboard
        )
        return
    if data == "settings_archive" or data.startswith("archive_page_"):
        await query.edit_message_reply_markup(reply_markup=None)
        page = 0
        if data.startswith("archive_page_"):
            page = int(data.split("_")[-1])
        await send_archive_page(query, chat_id, lang, page)
        return
    if data == "settings_reminder":
        await query.edit_message_reply_markup(reply_markup=None)
        user = get_user(chat_id)
        reminder_time = user["reminder_time"] if user else "08:00"
        reminder_enabled = user["reminder_enabled"] if user else 1
        t = TEXTS[lang]
        status = reminder_time if reminder_enabled else t["reminder_disabled_text"]
        times = ["06:00","07:00","08:00","09:00","10:00","11:00","12:00"]
        rows = [[InlineKeyboardButton(h, callback_data=f"reminder_set_{h}") for h in times[:4]],
                [InlineKeyboardButton(h, callback_data=f"reminder_set_{h}") for h in times[4:]],
                [InlineKeyboardButton(t["btn_reminder_disable"], callback_data="reminder_disable")]]
        await query.message.reply_text(
            t["reminder_settings"].format(time=status),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(rows)
        )
        return
    if data.startswith("reminder_set_"):
        new_time = data[len("reminder_set_"):]
        save_user(chat_id, reminder_time=new_time, reminder_enabled=1)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(TEXTS[lang]["reminder_set"].format(time=new_time))
        return
    if data == "reminder_disable":
        save_user(chat_id, reminder_enabled=0)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(TEXTS[lang]["reminder_off"])
        return
    if data == "disconnect_calendar":
        save_user(chat_id, calendar_token=None, calendar_connected=0)
        await query.edit_message_reply_markup(reply_markup=None)
        user = get_user(chat_id)
        await query.message.reply_text(
            TEXTS[lang]["calendar_disconnected"],
            reply_markup=main_menu_keyboard(lang, False, get_active_task_count(chat_id))
        )
        return
    if data == "skip_calendar":
        await query.edit_message_reply_markup(reply_markup=None)
        return
    if data.startswith("tz_"):
        await query.edit_message_reply_markup(reply_markup=None)
        onboarding = data.endswith("_ob")
        clean_data = data[:-3] if onboarding else data  # strip _ob suffix
        if clean_data in ("tz_manual", "tz_manual_ob"):
            context.user_data["awaiting_timezone"] = True
            context.user_data["timezone_onboarding"] = onboarding
            await query.message.reply_text(TEXTS[lang]["timezone_prompt"], parse_mode="Markdown")
        else:
            idx_tz = int(clean_data[3:])
            tz_name = POPULAR_TIMEZONES[idx_tz][1]
            save_user(chat_id, timezone=tz_name)
            await query.message.reply_text(
                TEXTS[lang]["timezone_set"].format(tz=tz_name), parse_mode="Markdown"
            )
            if onboarding:
                updated_user = get_user(chat_id)
                await query.message.reply_text(
                    TEXTS[lang]["lang_set"],
                    reply_markup=main_menu_keyboard(lang, updated_user["calendar_connected"], get_active_task_count(chat_id))
                )
        return
    if data.startswith("ics_"):
        idx = int(data[4:])
        tasks = context.user_data.get("tasks", [])
        if idx >= len(tasks):
            await query.answer("Session expired. Please send the task again.")
            return
        task = tasks[idx]
        user_obj = get_user(chat_id)
        tz_name = user_obj["timezone"] if user_obj else "Europe/Moscow"
        ics_bytes = generate_ics(task, tz_name)
        safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in task.get("title", "task"))[:40]
        filename = f"{safe_title}.ics"
        ics_captions = {
            "ru": "📎 Откройте файл, чтобы добавить событие в Apple Calendar",
            "uk": "📎 Відкрийте файл, щоб додати подію в Apple Calendar",
            "en": "📎 Open the file to add the event to Apple Calendar",
        }
        await context.bot.send_document(
            chat_id=chat_id,
            document=io.BytesIO(ics_bytes),
            filename=filename,
            caption=ics_captions.get(lang, ics_captions["en"])
        )
        return
    if data.startswith("set_remind_min_"):
        mins = int(data[len("set_remind_min_"):])
        save_user(chat_id, reminder_minutes=mins, reminder_before=mins)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(TEXTS[lang]["reminder_ask_set"].format(min=mins))
        return
    if data.startswith("recur_continue_"):
        rid = int(data[len("recur_continue_"):])
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(TEXTS[lang]["recur_continued"])
        return
    if data.startswith("recur_delete_"):
        rid = int(data[len("recur_delete_"):])
        conn = sqlite3.connect("users.db")
        row = conn.execute("SELECT title, google_event_id FROM recurring_tasks WHERE id=? AND chat_id=?", (rid, chat_id)).fetchone()
        conn.close()
        if not row:
            await query.answer("Not found.")
            return
        title, event_id = row
        await query.edit_message_reply_markup(reply_markup=None)
        try:
            service = get_calendar_service_for_user(chat_id)
            if service and event_id:
                service.events().delete(calendarId="primary", eventId=event_id).execute()
        except Exception as e:
            logger.error(f"Failed to delete recurring calendar event {event_id}: {e}")
        conn = sqlite3.connect("users.db")
        conn.execute("DELETE FROM recurring_tasks WHERE id=?", (rid,))
        conn.execute("DELETE FROM tasks WHERE chat_id=? AND google_event_id=? AND done=0", (chat_id, event_id))
        conn.commit()
        conn.close()
        await query.message.reply_text(
            TEXTS[lang]["recur_deleted"].format(title=title), parse_mode="Markdown"
        )
        return
    if data.startswith("recur_yes_") or data.startswith("recur_once_"):
        is_recurring = data.startswith("recur_yes_")
        idx_str = data.split("_")[-1]
        idx_int = int(idx_str)
        tasks = context.user_data.get("tasks", [])
        if idx_int >= len(tasks):
            await query.answer("Session expired.")
            return
        task = tasks[idx_int]
        await query.edit_message_reply_markup(reply_markup=None)
        if is_recurring:
            try:
                _, link = add_recurring_to_calendar(chat_id, task)
                schedule = describe_recurrence(task.get("recurrence", {}), lang)
                added_markup = InlineKeyboardMarkup([[InlineKeyboardButton(TEXTS[lang]["added_btn"], url=link)]]) if link else None
                await query.message.reply_text(
                    TEXTS[lang]["recur_created"].format(title=task["title"], schedule=schedule),
                    parse_mode="Markdown", reply_markup=added_markup
                )
            except Exception as e:
                logger.error(f"recurring calendar error {chat_id}: {e}", exc_info=True)
                await query.message.reply_text(TEXTS[lang]["calendar_error"] + str(e))
        else:
            # treat as normal one-time save
            if user and user["calendar_connected"]:
                service = get_calendar_service_for_user(chat_id)
                if service:
                    user_tz = user["timezone"] if user else "Europe/Moscow"
                    conflicts = check_conflicts(service, task["suggested_date"], task.get("suggested_time"), user_tz)
                    if conflicts:
                        conflict_title = conflicts[0].get("summary", "—")
                        context.user_data[f"conflict_{idx_str}"] = {
                            "task": task,
                            "cleanup_ids": task.get("_cleanup_ids", [query.message.message_id]),
                        }
                        await query.message.reply_text(
                            TEXTS[lang]["conflict_confirm"].format(event=conflict_title, title=task["title"]),
                            parse_mode="Markdown",
                            reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton(TEXTS[lang]["conflict_save_anyway"], callback_data=f"force_save_{idx_str}"),
                                InlineKeyboardButton(TEXTS[lang]["conflict_no_save"], callback_data=f"cancel_save_{idx_str}"),
                            ]])
                        )
                        return
                    msg = await query.message.reply_text(TEXTS[lang]["adding"])
                    try:
                        link, _ = add_to_calendar(chat_id, task)
                        await msg.delete()
                        added_markup = InlineKeyboardMarkup([[InlineKeyboardButton(TEXTS[lang]["added_btn"], url=link)]]) if link else None
                        await query.message.reply_text(
                            TEXTS[lang]["saved_with_calendar"].format(title=task["title"]),
                            parse_mode="Markdown", reply_markup=added_markup
                        )
                    except Exception as e:
                        save_task_to_db(chat_id, task)
                        await msg.edit_text(TEXTS[lang]["calendar_error"] + str(e))
            else:
                save_task_to_db(chat_id, task)
                await query.message.reply_text(TEXTS[lang]["task_saved"], parse_mode="Markdown")
        return
    if data.startswith("force_save_") or data.startswith("cancel_save_"):
        idx_str = data.split("_")[-1]
        is_force = data.startswith("force_save_")
        conflict_key = f"conflict_{idx_str}"
        conflict_data = context.user_data.get(conflict_key)
        if not conflict_data:
            await query.answer("Session expired.")
            return
        task = conflict_data["task"]
        cleanup_ids = conflict_data.get("cleanup_ids", [])
        await query.edit_message_reply_markup(reply_markup=None)
        if is_force:
            msg = await query.message.reply_text(TEXTS[lang]["adding"])
            try:
                link, _ = add_to_calendar(chat_id, task)
                await msg.delete()
                added_markup = InlineKeyboardMarkup([[InlineKeyboardButton(TEXTS[lang]["added_btn"], url=link)]]) if link else None
                await query.message.reply_text(
                    TEXTS[lang]["saved_with_calendar"].format(title=task["title"]),
                    parse_mode="Markdown",
                    reply_markup=added_markup
                )
                user_fresh = get_user(chat_id)
                if not user_fresh["first_task_done"]:
                    save_user(chat_id, first_task_done=1)
                    await ask_reminder_minutes(query.message, chat_id, lang)
            except Exception as e:
                save_task_to_db(chat_id, task)
                await msg.edit_text(TEXTS[lang]["calendar_error"] + str(e), parse_mode="Markdown")
        else:
            for msg_id in cleanup_ids:
                try:
                    await context.bot.delete_message(chat_id, msg_id)
                except Exception:
                    pass
            try:
                await query.message.delete()
            except Exception:
                pass
        context.user_data.pop(conflict_key, None)
        return
    action, idx = data.split("_")
    tasks = context.user_data.get("tasks", [])
    idx_int = int(idx)
    # If tasks not in context (e.g. after OAuth redirect), try to restore from DB
    if idx_int >= len(tasks):
        pending_json = user.get("pending_task_json") if user else None
        if pending_json:
            try:
                tasks = json.loads(pending_json)
                context.user_data["tasks"] = tasks
                # Clear DB copy — tasks are now cached in memory for this session
                save_user(chat_id, pending_task_json=None)
            except Exception:
                pass
    if idx_int >= len(tasks):
        await query.answer("Session expired. Please send the task again.")
        return
    task = tasks[idx_int]
    if action == "add":
        await query.edit_message_reply_markup(reply_markup=None)
        service = get_calendar_service_for_user(chat_id)
        if not service:
            await query.message.reply_text(TEXTS[lang]["calendar_not_connected"])
            return
        user_tz = user["timezone"] if user else "Europe/Moscow"
        conflicts = check_conflicts(service, task["suggested_date"], task.get("suggested_time"), user_tz)
        if conflicts:
            conflict_title = conflicts[0].get("summary", "—")
            context.user_data["pending_task"] = task
            await query.message.reply_text(
                TEXTS[lang]["conflict_found"].format(event=conflict_title, title=task["title"]),
                parse_mode="Markdown"
            )
            return
        msg = await query.message.reply_text(TEXTS[lang]["adding"])
        try:
            link, task_id = add_to_calendar(chat_id, task)  # saves to DB internally
            context.user_data.setdefault("saved_task_ids", {})[idx_int] = task_id
            await msg.delete()
            success_texts = {
                "ru": f"✅ *{task['title']}* сохранена в задачах и добавлена в Google Calendar",
                "en": f"✅ *{task['title']}* saved to tasks and added to Google Calendar",
                "uk": f"✅ *{task['title']}* збережено у задачах та додано до Google Calendar",
            }
            added_markup = InlineKeyboardMarkup([[InlineKeyboardButton(TEXTS[lang]["added_btn"], url=link)]]) if link else None
            await query.message.reply_text(
                success_texts.get(lang, success_texts["ru"]),
                parse_mode="Markdown",
                reply_markup=added_markup
            )
            await _offer_goal_link_if_relevant(query.message, chat_id, lang, task, idx)
            user_fresh = get_user(chat_id)
            if not user_fresh["first_task_done"]:
                save_user(chat_id, first_task_done=1)
                await ask_reminder_minutes(query.message, chat_id, lang)
        except Exception as e:
            logger.error(f"add_to_calendar error for {chat_id}: {e}", exc_info=True)
            error_texts = {
                "ru": f"❌ Не удалось добавить в Google Calendar.\n\nОшибка: `{str(e)}`\n\nЗадача сохранена в списке задач.",
                "en": f"❌ Failed to add to Google Calendar.\n\nError: `{str(e)}`\n\nTask saved to your task list.",
                "uk": f"❌ Не вдалося додати до Google Calendar.\n\nПомилка: `{str(e)}`\n\nЗадачу збережено у списку задач.",
            }
            save_task_to_db(chat_id, task)
            await msg.edit_text(error_texts.get(lang, error_texts["ru"]), parse_mode="Markdown")
    elif action == "save":
        if user and user["calendar_connected"]:
            service = get_calendar_service_for_user(chat_id)
            if service:
                user_tz = user["timezone"] if user else "Europe/Moscow"
                conflicts = check_conflicts(service, task["suggested_date"], task.get("suggested_time"), user_tz)
                if conflicts:
                    conflict_title = conflicts[0].get("summary", "—")
                    context.user_data[f"conflict_{idx}"] = {
                        "task": task,
                        "cleanup_ids": task.get("_cleanup_ids", [query.message.message_id]),
                    }
                    await query.edit_message_reply_markup(reply_markup=None)
                    await query.message.reply_text(
                        TEXTS[lang]["conflict_confirm"].format(event=conflict_title, title=task["title"]),
                        parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton(TEXTS[lang]["conflict_save_anyway"], callback_data=f"force_save_{idx}"),
                            InlineKeyboardButton(TEXTS[lang]["conflict_no_save"], callback_data=f"cancel_save_{idx}"),
                        ]])
                    )
                    return
                await query.edit_message_reply_markup(reply_markup=None)
                msg = await query.message.reply_text(TEXTS[lang]["adding"])
                try:
                    link, task_id = add_to_calendar(chat_id, task)
                    context.user_data.setdefault("saved_task_ids", {})[idx_int] = task_id
                    await msg.delete()
                    added_markup = InlineKeyboardMarkup([[InlineKeyboardButton(TEXTS[lang]["added_btn"], url=link)]]) if link else None
                    await query.message.reply_text(
                        TEXTS[lang]["saved_with_calendar"].format(title=task["title"]),
                        parse_mode="Markdown",
                        reply_markup=added_markup
                    )
                    await _offer_goal_link_if_relevant(query.message, chat_id, lang, task, idx)
                    user_fresh = get_user(chat_id)
                    if not user_fresh["first_task_done"]:
                        save_user(chat_id, first_task_done=1)
                        await ask_reminder_minutes(query.message, chat_id, lang)
                except Exception as e:
                    logger.error(f"auto calendar sync error for {chat_id}: {e}", exc_info=True)
                    save_task_to_db(chat_id, task)
                    await msg.edit_text(TEXTS[lang]["calendar_error"] + str(e), parse_mode="Markdown")
                return
        task_id = save_task_to_db(chat_id, task)
        context.user_data.setdefault("saved_task_ids", {})[idx_int] = task_id
        emoji = QUADRANT_EMOJI.get(task["quadrant"], "⚪")
        date_display = format_date(task["suggested_date"], lang)
        time_sep = _TIME_SEP.get(lang, " ")
        card = (
            f"{emoji} *{task['title']}*\n"
            f"{task['quadrant']} — {task['quadrant_name']}\n"
            f"📅 {date_display}"
            + (f"{time_sep}{task['suggested_time']}" if task.get("suggested_time") else "") + "\n"
            f"_{task['reason']}_\n\n"
            + TEXTS[lang]["task_saved"]
        )
        await query.edit_message_text(card, parse_mode="Markdown")
        await _offer_goal_link_if_relevant(query.message, chat_id, lang, task, idx)
        user_fresh = get_user(chat_id)
        if not user_fresh["first_task_done"]:
            save_user(chat_id, first_task_done=1)
            await ask_reminder_minutes(query.message, chat_id, lang)
    elif action == "skip":
        # Delete task card + original user message + "Обрабатываю..."
        cleanup_ids = task.get("_cleanup_ids", [query.message.message_id])
        for msg_id in cleanup_ids:
            try:
                await context.bot.delete_message(chat_id, msg_id)
            except Exception:
                pass

async def show_timezone_menu(message, chat_id, lang, onboarding=False):
    user = get_user(chat_id)
    current_tz = user["timezone"] if user else "Europe/Moscow"
    rows = []
    for i in range(0, len(POPULAR_TIMEZONES), 2):
        row = [InlineKeyboardButton(POPULAR_TIMEZONES[i][0], callback_data=f"tz_{i}{'_ob' if onboarding else ''}")]
        if i + 1 < len(POPULAR_TIMEZONES):
            row.append(InlineKeyboardButton(POPULAR_TIMEZONES[i + 1][0], callback_data=f"tz_{i+1}{'_ob' if onboarding else ''}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(TEXTS[lang]["timezone_manual"], callback_data=f"tz_manual{'_ob' if onboarding else ''}")])
    prompt = {
        "ru": "🌍 Укажи свой часовой пояс — это нужно для точных напоминаний:",
        "en": "🌍 Choose your timezone — needed for accurate reminders:",
        "uk": "🌍 Вкажи свій часовий пояс — це потрібно для точних нагадувань:",
    }
    text = prompt.get(lang, prompt["ru"]) if onboarding else TEXTS[lang]["timezone_current"].format(tz=current_tz)
    await message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(rows)
    )

async def timezone_command_for_query(query, chat_id, lang):
    await show_timezone_menu(query.message, chat_id, lang)

async def timezone_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    lang = user["lang"] if user else "ru"
    await show_timezone_menu(update.message, chat_id, lang)

def get_stats_data(days=7):
    conn = sqlite3.connect("users.db")
    now = datetime.utcnow()
    # days=0 means "all time"
    if days == 0:
        since = "2000-01-01 00:00:00"
    else:
        since = (now - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    day_ago = (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    total_users = conn.execute("SELECT COUNT(*) FROM users WHERE lang IS NOT NULL").fetchone()[0]
    cal_users   = conn.execute("SELECT COUNT(*) FROM users WHERE calendar_connected=1").fetchone()[0]
    dau         = conn.execute("SELECT COUNT(DISTINCT chat_id) FROM events WHERE created_at >= ?", (day_ago,)).fetchone()[0]
    active      = conn.execute("SELECT COUNT(DISTINCT chat_id) FROM events WHERE created_at >= ?", (since,)).fetchone()[0]
    new_users   = conn.execute("SELECT COUNT(*) FROM events WHERE event_type='new_user' AND created_at >= ?", (since,)).fetchone()[0]
    tasks_total = conn.execute("SELECT COUNT(*) FROM tasks WHERE created_at >= ?", (since,)).fetchone()[0]
    voice_total = conn.execute("SELECT COUNT(*) FROM events WHERE event_type='voice_task' AND created_at >= ?", (since,)).fetchone()[0]
    text_total  = conn.execute("SELECT COUNT(*) FROM events WHERE event_type='text_task' AND created_at >= ?", (since,)).fetchone()[0]
    cal_connects= conn.execute("SELECT COUNT(*) FROM events WHERE event_type='calendar_connected' AND created_at >= ?", (since,)).fetchone()[0]
    # Chart: daily for ≤30 days, monthly for 90 days or all time
    use_monthly = (days == 0 or days >= 90)
    if use_monthly:
        rows = conn.execute(
            "SELECT strftime('%Y-%m', created_at) as mo, COUNT(DISTINCT chat_id) "
            "FROM events WHERE created_at >= ? GROUP BY mo ORDER BY mo",
            (since,)
        ).fetchall()
        chart_data = list(rows)
    else:
        chart_data = []
        for i in range(days - 1, -1, -1):
            d_start = (now - timedelta(days=i+1)).strftime("%Y-%m-%d %H:%M:%S")
            d_end   = (now - timedelta(days=i)).strftime("%Y-%m-%d %H:%M:%S")
            cnt = conn.execute(
                "SELECT COUNT(DISTINCT chat_id) FROM events WHERE created_at >= ? AND created_at < ?",
                (d_start, d_end)
            ).fetchone()[0]
            label = (now - timedelta(days=i)).strftime("%d.%m")
            chart_data.append((label, cnt))
    conn.close()
    return dict(total_users=total_users, cal_users=cal_users, dau=dau,
                active=active, new_users=new_users, tasks_total=tasks_total,
                voice_total=voice_total, text_total=text_total,
                cal_connects=cal_connects, chart_data=chart_data,
                use_monthly=use_monthly, days=days)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id != BOT_OWNER_ID:
        return
    s = get_stats_data()
    text = (
        "📊 *Статистика Get My Task*\n\n"
        f"👥 Всего пользователей: *{s['total_users']}*\n"
        f"📅 С Google Calendar: *{s['cal_users']}*\n\n"
        f"*Активность:*\n"
        f"• DAU (сегодня): *{s['dau']}*\n"
        f"• WAU (7 дней): *{s['wau']}*\n"
        f"• MAU (30 дней): *{s['mau']}*\n\n"
        f"*Новые пользователи:*\n"
        f"• Сегодня: *{s['new_today']}*\n"
        f"• За 7 дней: *{s['new_week']}*\n\n"
        f"*Задачи созданы:*\n"
        f"• Сегодня: *{s['tasks_today']}*\n"
        f"• За 7 дней: *{s['tasks_week']}*\n\n"
        f"*Голосовые:*\n"
        f"• Сегодня: *{s['voice_today']}*\n"
        f"• За 7 дней: *{s['voice_week']}*"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ─── Goals ────────────────────────────────────────────────────────────────────

_STOP_WORDS = {
    "я", "в", "на", "с", "к", "по", "и", "или", "не", "это", "то", "что", "как",
    "до", "за", "из", "для", "при", "хочу", "хочет", "нужно", "надо", "буду",
    "i", "to", "the", "a", "an", "of", "is", "my", "do", "want", "need", "will",
    "я", "у", "від", "до", "та", "або", "не", "що", "як", "це",
}

def _task_matches_goal(task_title: str, goal_title: str) -> bool:
    """True if task title shares meaningful words with the goal title."""
    def words(s):
        return {w.lower().strip(".,!?") for w in s.split()} - _STOP_WORDS
    return bool(words(task_title) & words(goal_title))

async def _offer_goal_link_if_relevant(message, chat_id: int, lang: str, task: dict, task_idx: str):
    """After saving a task, offer to link it to an active goal if relevant."""
    if task.get("goal_id"):
        return  # already linked
    active_goals = get_active_goals(chat_id)
    if not active_goals:
        return
    goal = next(
        (g for g in active_goals if _task_matches_goal(task.get("title", ""), g["title"])),
        None
    )
    if not goal:
        return
    t = TEXTS[lang]
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(t["btn_goal_link_yes"], callback_data=f"goal_link_yes_{goal['id']}_{task_idx}"),
        InlineKeyboardButton(t["btn_goal_link_no"],  callback_data=f"goal_link_no_{task_idx}"),
    ]])
    await message.reply_text(
        t["goal_link_ask"].format(goal=goal["title"]),
        parse_mode="Markdown",
        reply_markup=keyboard
    )


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
        "SELECT id, title, criteria, deadline, quadrant, quadrant_name, status FROM goals WHERE chat_id=? AND status='active' ORDER BY created_at DESC",
        (chat_id,)
    ).fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "criteria": r[2], "deadline": r[3],
             "quadrant": r[4], "quadrant_name": r[5], "status": r[6]} for r in rows]

def delete_goal_from_db(goal_id: int, delete_tasks: bool) -> int:
    """Delete a goal (set status='deleted') and handle linked tasks.
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

def _progress_bar(pct: int, length: int = 8) -> str:
    filled = round(pct / 100 * length)
    return "█" * filled + "░" * (length - filled)

async def classify_goal_or_task(text: str, lang: str, tz_name: str = "Europe/Moscow") -> dict:
    """
    Classify input as goal or task, and extract deadline/criteria if already present.
    Returns dict: {is_goal, deadline (YYYY-MM-DD or null), criteria (str or null)}
    """
    today = datetime.now(ZoneInfo(tz_name)).strftime("%Y-%m-%d")
    prompts = {
        "ru": (
            f"Сегодня {today}. Проанализируй текст и ответь на вопросы:\n"
            "1. Это ЦЕЛЬ (намерение, желание достичь чего-то масштабного) или ЗАДАЧА (конкретное действие)?\n"
            "   Цель: «хочу похудеть», «планирую запустить бизнес», «хочу выучить язык»\n"
            "   Задача: «позвонить врачу», «купить молоко», «встреча в 15:00»\n"
            "2. Если это цель — есть ли в тексте дедлайн? Если да — верни дату в формате YYYY-MM-DD.\n"
            "3. Если это цель — есть ли в тексте конкретный критерий успеха (измеримый результат)?\n"
            f"Текст: «{text}»\n"
            'Ответь ТОЛЬКО JSON: {"is_goal": true/false, "deadline": "YYYY-MM-DD" или null, "criteria": "текст" или null}'
        ),
        "en": (
            f"Today is {today}. Analyze the text and answer:\n"
            "1. Is this a GOAL (aspiration, desire to achieve something big) or a TASK (specific one-time action)?\n"
            "   Goal: 'I want to lose weight', 'planning to start a business', 'want to learn a language'\n"
            "   Task: 'call the doctor', 'buy milk', 'meeting at 3pm'\n"
            "2. If it's a goal — is there a deadline mentioned? If yes, return date as YYYY-MM-DD.\n"
            "3. If it's a goal — is there a specific measurable success criterion?\n"
            f"Text: '{text}'\n"
            'Answer ONLY JSON: {"is_goal": true/false, "deadline": "YYYY-MM-DD" or null, "criteria": "text" or null}'
        ),
        "uk": (
            f"Сьогодні {today}. Проаналізуй текст і дай відповідь:\n"
            "1. Це ЦІЛЬ (намір, бажання досягти чогось масштабного) чи ЗАДАЧА (конкретна одноразова дія)?\n"
            "   Ціль: «хочу схуднути», «планую запустити бізнес», «хочу вивчити мову»\n"
            "   Задача: «зателефонувати лікарю», «купити молоко», «зустріч о 15:00»\n"
            "2. Якщо це ціль — чи є в тексті дедлайн? Якщо так — поверни дату у форматі YYYY-MM-DD.\n"
            "3. Якщо це ціль — чи є конкретний вимірюваний критерій успіху?\n"
            f"Текст: «{text}»\n"
            'Відповідай ТІЛЬКИ JSON: {"is_goal": true/false, "deadline": "YYYY-MM-DD" або null, "criteria": "текст" або null}'
        ),
    }
    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompts.get(lang, prompts["ru"])}],
            max_tokens=80, temperature=0,
        )
        return json.loads(resp.choices[0].message.content.strip())
    except Exception:
        return {"is_goal": False, "deadline": None, "criteria": None}

async def parse_goal_deadline(text: str, lang: str, tz_name: str) -> str:
    """Parse a natural language deadline into YYYY-MM-DD using Groq."""
    today = datetime.now(ZoneInfo(tz_name)).strftime("%Y-%m-%d")
    prompts = {
        "ru": f"Сегодня {today}. Определи дату из текста: «{text}». Верни ТОЛЬКО JSON: {{\"date\": \"YYYY-MM-DD\"}} или {{\"date\": null}} если не ясно.",
        "en": f"Today is {today}. Parse the deadline from: '{text}'. Return ONLY JSON: {{\"date\": \"YYYY-MM-DD\"}} or {{\"date\": null}} if unclear.",
        "uk": f"Сьогодні {today}. Визнач дату з тексту: «{text}». Поверни ТІЛЬКИ JSON: {{\"date\": \"YYYY-MM-DD\"}} або {{\"date\": null}} якщо незрозуміло.",
    }
    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompts.get(lang, prompts["ru"])}],
            max_tokens=30, temperature=0,
        )
        return json.loads(resp.choices[0].message.content.strip()).get("date")
    except Exception:
        return None

def _render_goal_card(g: dict, lang: str) -> str:
    """Render a goal as a Markdown card string."""
    t = TEXTS[lang]
    done, total = get_goal_progress(g["id"])
    pct = round(done / total * 100) if total > 0 else 0
    bar = _progress_bar(pct)
    deadline_str = format_date(g["deadline"], lang) if g.get("deadline") else ""
    deadline_label = (t["goal_deadline_label"].format(date=deadline_str) + "\n") if deadline_str else ""
    progress_str = t["goal_progress"].format(bar=bar, pct=pct, done=done, total=total) if total > 0 else t["goal_no_tasks"]
    return f"📌 *{g['title']}*\n{deadline_label}{progress_str}"

async def goals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    lang = user["lang"] if user else "ru"
    t = TEXTS[lang]
    goals = get_active_goals(chat_id)
    if not goals:
        await update.message.reply_text(t["goals_empty"], parse_mode="Markdown")
        return
    for g in goals:
        text = _render_goal_card(g, lang)
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(t["btn_goal_delete"], callback_data=f"gdel_{g['id']}")
        ]])
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)


async def _translate_announce(text_ru: str, lang: str) -> str:
    """Translate Russian announcement text to target language via Groq."""
    if lang == "ru":
        return text_ru
    lang_name = {"en": "English", "uk": "Ukrainian"}.get(lang, "English")
    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": (
                    f"Translate this Telegram bot update notification from Russian to {lang_name}. "
                    "Keep it short, friendly and action-oriented. Preserve emojis and Markdown formatting (*bold*, _italic_). "
                    "Return ONLY the translated text, nothing else:\n\n" + text_ru
                )
            }],
            max_tokens=400,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"[announce] translation to {lang} failed: {e}")
        return text_ru  # fallback to Russian


async def announce_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner-only: /announce <text> — preview & broadcast update to all active users."""
    chat_id = update.effective_chat.id
    if chat_id != BOT_OWNER_ID:
        return
    if not context.args:
        await update.message.reply_text(
            "📢 Использование:\n`/announce <текст обновления>`\n\n"
            "Пример:\n`/announce 🆕 Теперь можно подписаться на Apple Calendar — все задачи автоматически появятся в твоём календаре. Попробуй в Настройках!`",
            parse_mode="Markdown"
        )
        return

    text_ru = " ".join(context.args)
    msg = await update.message.reply_text("⏳ Перевожу на другие языки...")

    text_en = await _translate_announce(text_ru, "en")
    text_uk = await _translate_announce(text_ru, "uk")

    # Count active users per language (last 30 days)
    conn = sqlite3.connect("users.db")
    rows = conn.execute(
        "SELECT lang, COUNT(*) FROM users WHERE last_active > datetime('now', '-30 days') GROUP BY lang"
    ).fetchall()
    conn.close()
    by_lang = {r[0]: r[1] for r in rows}
    total = sum(by_lang.values())

    announce_id = secrets.token_hex(4)
    _pending_announcements[announce_id] = {"ru": text_ru, "en": text_en, "uk": text_uk}

    preview = (
        f"📋 *Превью рассылки* `[{announce_id}]`\n\n"
        f"🇷🇺 *RU* ({by_lang.get('ru', 0)} польз.):\n{text_ru}\n\n"
        f"🇬🇧 *EN* ({by_lang.get('en', 0)} польз.):\n{text_en}\n\n"
        f"🇺🇦 *UK* ({by_lang.get('uk', 0)} польз.):\n{text_uk}\n\n"
        f"👥 *Итого получат:* {total} пользователей"
    )
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("📤 Отправить всем", callback_data=f"announce_send_{announce_id}"),
        InlineKeyboardButton("❌ Отменить", callback_data=f"announce_cancel_{announce_id}"),
    ]])
    await msg.edit_text(preview, parse_mode="Markdown", reply_markup=keyboard)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    lang = user["lang"] if user else "ru"
    await update.message.reply_text(TEXTS[lang]["help"], parse_mode="Markdown")

async def _send_tasks_grouped(update, chat_id: int, lang: str):
    """Shared logic for tasks_command and mytasks_command."""
    user = get_user(chat_id)
    user_tz = user["timezone"] if user else "Europe/Moscow"
    now = datetime.now(ZoneInfo(user_tz))
    today = now.strftime("%Y-%m-%d")
    tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    conn = sqlite3.connect("users.db")
    # Show all tasks from today onwards (today = active even if time passed).
    # Archive is yesterday and before.
    current_time = now.strftime("%H:%M")
    rows = conn.execute(
        """SELECT title, quadrant, suggested_date, suggested_time FROM tasks
           WHERE chat_id=? AND suggested_date >= ?
           ORDER BY suggested_date ASC, suggested_time ASC LIMIT 50""",
        (chat_id, today)
    ).fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text(TEXTS[lang]["tasks_empty"])
        return
    text = build_tasks_by_day(rows, lang, today, tomorrow, current_time)
    await update.message.reply_text(text, parse_mode="Markdown")

async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    lang = user["lang"] if user else "ru"
    await _send_tasks_grouped(update, chat_id, lang)

async def mytasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await tasks_command(update, context)

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    lang = user["lang"] if user else "ru"
    t = TEXTS[lang]
    reminder_time = user["reminder_time"] if user else "08:00"
    reminder_enabled = user["reminder_enabled"] if user else 1
    reminder_label = t["btn_reminder"] + f" ({reminder_time})" if reminder_enabled else t["btn_reminder"] + f" ({t['reminder_disabled_text']})"
    reminder_before = user["reminder_minutes"] if user else 30
    before_label = t["btn_reminder_before"].format(min=reminder_before)
    keyboard_rows = [
        [InlineKeyboardButton(reminder_label, callback_data="settings_reminder")],
        [InlineKeyboardButton(before_label, callback_data="settings_reminder_before")],
        [InlineKeyboardButton(t["btn_archive"], callback_data="settings_archive")],
    ]
    gcal_connected = bool(user and user.get("calendar_connected"))
    ical_subscribed = bool(user and user.get("ical_token"))
    if gcal_connected:
        # Google Calendar подключён → показываем только "Отключить", Apple Calendar скрываем
        keyboard_rows.append([InlineKeyboardButton(t["btn_disconnect_calendar"], callback_data="disconnect_calendar")])
    elif ical_subscribed:
        # Apple Calendar подписан → показываем только Apple (статус), Google скрываем
        keyboard_rows.append([InlineKeyboardButton(t["btn_apple_cal_connected"], callback_data="settings_apple_cal")])
    else:
        # Ничего не подключено → показываем оба варианта
        keyboard_rows.append([InlineKeyboardButton(t["btn_connect"], callback_data="connect_calendar")])
        keyboard_rows.append([InlineKeyboardButton(t["btn_apple_cal"], callback_data="settings_apple_cal")])
    current_tz = user["timezone"] if user else "Europe/Moscow"
    keyboard_rows.append([InlineKeyboardButton(t["btn_feedback"], callback_data="settings_feedback")])
    keyboard_rows.append([
        InlineKeyboardButton(t["btn_help"], callback_data="settings_help"),
        InlineKeyboardButton(f"🕐 {current_tz}", callback_data="settings_timezone")
    ])
    await update.message.reply_text(t["btn_settings"], reply_markup=InlineKeyboardMarkup(keyboard_rows))

# ─── OAuth Web Server ─────────────────────────────────────────────────────────

async def oauth_callback(request):
    state = request.rel_url.query.get("state")
    code = request.rel_url.query.get("code")
    if not state:
        return web.Response(text="Invalid state", status=400)
    chat_id, code_verifier = pop_oauth_state(state)
    if not chat_id:
        return web.Response(text="Session expired. Please connect calendar again in the bot.", status=400)
    flow = Flow.from_client_secrets_file(
        "credentials.json",
        scopes=SCOPES,
        redirect_uri=f"{BASE_URL}/oauth/callback",
        state=state
    )
    fetch_kwargs = {"code": code}
    if code_verifier:
        fetch_kwargs["code_verifier"] = code_verifier
    flow.fetch_token(**fetch_kwargs)
    creds = flow.credentials
    save_user(chat_id, calendar_token=creds.to_json(), calendar_connected=1)
    log_event(chat_id, "calendar_connected")
    user = get_user(chat_id)
    lang = user["lang"] if user else "ru"
    await bot_app.bot.send_message(
        chat_id=chat_id,
        text=TEXTS[lang]["calendar_connected"],
        reply_markup=main_menu_keyboard(lang, calendar_connected=True, task_count=get_active_task_count(chat_id))
    )
    # Restore pending tasks if user connected calendar from a task card
    pending_json = user.get("pending_task_json") if user else None
    if pending_json:
        try:
            pending_tasks = json.loads(pending_json)
            # Note: don't clear pending_task_json here — user hasn't acted on tasks yet.
            # It'll be cleared once they press add/save/skip (see handle_callback).
            resume_texts = {
                "ru": "📋 Вот ваши задачи — теперь можно добавить в Google Calendar:",
                "en": "📋 Here are your tasks — now you can add them to Google Calendar:",
                "uk": "📋 Ось ваші задачі — тепер можна додати до Google Calendar:",
            }
            await bot_app.bot.send_message(chat_id=chat_id, text=resume_texts.get(lang, resume_texts["ru"]))
            for i, task in enumerate(pending_tasks):
                emoji = QUADRANT_EMOJI.get(task.get("quadrant", ""), "⚪")
                date_display = format_date(task.get("suggested_date", ""), lang)
                time_sep = _TIME_SEP.get(lang, " ")
                text = (
                    f"{emoji} *{task['title']}*\n"
                    f"{task.get('quadrant', '')} — {task.get('quadrant_name', '')}\n"
                    f"📅 {date_display}"
                    + (f"{time_sep}{task['suggested_time']}" if task.get("suggested_time") else "") + "\n"
                    f"_{task.get('reason', '')}_"
                )
                # Google Calendar just connected — sync is automatic, no extra calendar buttons
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton(TEXTS[lang]["save"], callback_data=f"save_{i}"),
                     InlineKeyboardButton(TEXTS[lang]["skip"], callback_data=f"skip_{i}")],
                ])
                await bot_app.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown", reply_markup=keyboard)
        except Exception:
            pass
    return web.Response(text="✅ Calendar connected! You can close this tab.")

HOME_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Get My Task — AI Task Manager for Telegram</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
         background:#0f0f0f;color:#e0e0e0;min-height:100vh;
         display:flex;align-items:center;justify-content:center;padding:40px 20px}
    .wrap{max-width:540px;text-align:center}
    .icon{font-size:4rem;margin-bottom:16px}
    h1{font-size:2.2rem;font-weight:700;color:#fff;margin-bottom:12px}
    .sub{font-size:1.1rem;color:#aaa;margin-bottom:32px;line-height:1.6}
    .btn{display:inline-block;background:#229ED9;color:#fff;font-size:1rem;
         font-weight:600;padding:14px 32px;border-radius:12px;text-decoration:none;
         transition:opacity .2s}
    .btn:hover{opacity:.85}
    .features{display:flex;flex-direction:column;gap:12px;margin:40px 0;text-align:left}
    .feat{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:10px;
          padding:14px 18px;font-size:.95rem;color:#ccc}
    .feat span{margin-right:10px;font-size:1.1rem}
    footer{margin-top:40px;font-size:.85rem;color:#555}
    footer a{color:#555;text-decoration:none}
    footer a:hover{color:#aaa}
  </style>
</head>
<body>
<div class="wrap">
  <div class="icon">🤖</div>
  <h1>Get My Task</h1>
  <p class="sub">Turn voice notes and text into structured tasks —<br/>
  prioritised, scheduled, and synced with Google Calendar.</p>

  <a class="btn" href="https://t.me/getmytask_bot">Open in Telegram →</a>

  <div class="features">
    <div class="feat"><span>🎙</span>Dictate tasks by voice — AI extracts title, date and priority</div>
    <div class="feat"><span>📊</span>Eisenhower Matrix — tasks sorted by importance and urgency</div>
    <div class="feat"><span>📅</span>Google Calendar sync — add tasks as events in one tap</div>
    <div class="feat"><span>🔔</span>Smart reminders — get notified before each task</div>
  </div>

  <footer>
    <a href="/privacy">Privacy Policy</a>
  </footer>
</div>
</body>
</html>"""

async def home_page(request):
    return web.Response(text=HOME_HTML, content_type="text/html", charset="utf-8")

async def google_verification(request):
    return web.Response(text="google-site-verification: googled2363927b56587ef.html", content_type="text/html", charset="utf-8")

async def stats_page(request):
    try:
        days = int(request.rel_url.query.get("days", 7))
        if days not in (0, 7, 14, 30, 90):
            days = 7
    except ValueError:
        days = 7
    s = get_stats_data(days)
    period_labels = {0: "Всё время", 7: "7 дней", 14: "14 дней", 30: "30 дней", 90: "90 дней"}
    period_label = period_labels[days]

    # Build tabs — avoid nested quotes in f-string for Python <3.12 compat
    tabs_parts = []
    for d in (7, 14, 30, 90, 0):
        cls = "tab tab--active" if d == days else "tab"
        tabs_parts.append(f'<a href="/stats?days={d}" class="{cls}">{period_labels[d]}</a>')
    tabs_html = "".join(tabs_parts)

    # Build bars
    chart_data = s["chart_data"]
    max_val = max((v for _, v in chart_data), default=1) or 1
    bars_parts = []
    for lbl, v in chart_data:
        height = max(4, int(v / max_val * 140))
        val_str = str(v) if v > 0 else ""
        bars_parts.append(
            f'<div class="bar-col">'
            f'<span class="bar-val">{val_str}</span>'
            f'<div class="bar" style="height:{height}px"></div>'
            f'<div class="bar-lbl">{lbl}</div>'
            f'</div>'
        )
    bars_html = "".join(bars_parts)
    chart_heading = "Активных пользователей по месяцам" if s["use_monthly"] else "Активных пользователей по дням"
    chart_block = (
        f'<div class="chart-inner">{bars_html}</div>'
        if chart_data else
        '<div class="no-data">Нет данных за этот период</div>'
    )

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Analytics — Get My Task</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #0d1117;
      color: #e6edf3;
      min-height: 100vh;
      padding: 36px 20px 64px;
    }}
    .wrap {{ max-width: 840px; margin: 0 auto; }}

    /* ── Header ─────────────────────────── */
    .hdr {{ display: flex; align-items: center; gap: 12px; margin-bottom: 6px; }}
    .hdr-icon {{ font-size: 1.7rem; }}
    h1 {{ font-size: 1.45rem; font-weight: 700; color: #fff; }}
    .sub {{ color: #7d8590; font-size: 0.8rem; margin-bottom: 28px; }}

    /* ── Period tabs ────────────────────── */
    .tabs-wrap {{
      display: inline-flex;
      align-items: center;
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 999px;
      padding: 4px;
      gap: 2px;
      margin-bottom: 32px;
      flex-wrap: wrap;
    }}
    .tab {{
      padding: 7px 20px;
      border-radius: 999px;
      font-size: 0.82rem;
      font-weight: 600;
      color: #7d8590;
      text-decoration: none;
      transition: color 0.15s, background 0.15s;
      white-space: nowrap;
    }}
    .tab:hover {{ color: #e6edf3; background: #21262d; }}
    .tab--active {{
      background: #1f6feb;
      color: #fff !important;
      box-shadow: 0 0 0 1px rgba(31,111,235,.4), 0 2px 10px rgba(31,111,235,.35);
    }}

    /* ── Section label ──────────────────── */
    .sec {{
      font-size: 0.7rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.09em;
      color: #7d8590;
      margin: 0 0 10px;
    }}

    /* ── Metric grid ────────────────────── */
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(155px, 1fr));
      gap: 12px;
      margin-bottom: 28px;
    }}
    .card {{
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 12px;
      padding: 18px 20px 16px;
      position: relative;
      overflow: hidden;
    }}
    .card::after {{
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      border-radius: 12px 12px 0 0;
    }}
    .card.c-blue::after   {{ background: #1f6feb; }}
    .card.c-teal::after   {{ background: #39c5cf; }}
    .card.c-green::after  {{ background: #3fb950; }}
    .card.c-orange::after {{ background: #d29922; }}
    .card.c-purple::after {{ background: #a371f7; }}
    .card.c-pink::after   {{ background: #f778ba; }}
    .card .val {{
      font-size: 2.1rem;
      font-weight: 700;
      color: #fff;
      line-height: 1;
      margin-bottom: 6px;
    }}
    .card .lbl {{
      font-size: 0.76rem;
      color: #7d8590;
      line-height: 1.35;
    }}

    /* ── Chart ──────────────────────────── */
    .chart-box {{
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 12px;
      padding: 20px 20px 0;
      margin-bottom: 28px;
      overflow: hidden;
    }}
    .chart-title {{
      font-size: 0.84rem;
      font-weight: 600;
      color: #e6edf3;
      margin-bottom: 18px;
    }}
    .chart-inner {{
      display: flex;
      align-items: flex-end;
      gap: 3px;
      height: 180px;
      padding-bottom: 28px;
      position: relative;
    }}
    .bar-col {{
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: flex-end;
      height: 100%;
      position: relative;
      min-width: 0;
    }}
    .bar-val {{
      font-size: 0.59rem;
      color: #7d8590;
      margin-bottom: 3px;
      min-height: 13px;
      line-height: 13px;
    }}
    .bar {{
      width: 100%;
      background: linear-gradient(180deg, #388bfd 0%, #1f6feb 100%);
      border-radius: 4px 4px 0 0;
      min-height: 4px;
      transition: opacity 0.15s;
    }}
    .bar:hover {{ opacity: 0.75; cursor: default; }}
    .bar-lbl {{
      position: absolute;
      bottom: 4px;
      left: 0; right: 0;
      font-size: 0.57rem;
      color: #7d8590;
      text-align: center;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .no-data {{
      text-align: center;
      color: #7d8590;
      font-size: 0.9rem;
      padding: 48px 0;
    }}
  </style>
</head>
<body>
<div class="wrap">

  <div class="hdr">
    <span class="hdr-icon">📊</span>
    <h1>Get My Task — Analytics</h1>
  </div>
  <p class="sub">Live data · UTC · Auto-refresh on open</p>

  <div class="tabs-wrap">{tabs_html}</div>

  <p class="sec">Всего</p>
  <div class="grid">
    <div class="card c-blue">
      <div class="val">{s['total_users']}</div>
      <div class="lbl">Пользователей всего</div>
    </div>
    <div class="card c-teal">
      <div class="val">{s['cal_users']}</div>
      <div class="lbl">Google Calendar подключён</div>
    </div>
    <div class="card c-green">
      <div class="val">{s['dau']}</div>
      <div class="lbl">Активных сегодня (DAU)</div>
    </div>
  </div>

  <p class="sec">За {period_label}</p>
  <div class="grid">
    <div class="card c-blue">
      <div class="val">{s['active']}</div>
      <div class="lbl">Уникальных активных</div>
    </div>
    <div class="card c-green">
      <div class="val">{s['new_users']}</div>
      <div class="lbl">Новых пользователей</div>
    </div>
    <div class="card c-orange">
      <div class="val">{s['cal_connects']}</div>
      <div class="lbl">Подключений Calendar</div>
    </div>
    <div class="card c-purple">
      <div class="val">{s['tasks_total']}</div>
      <div class="lbl">Задач создано</div>
    </div>
    <div class="card c-pink">
      <div class="val">{s['voice_total']}</div>
      <div class="lbl">Голосовых задач</div>
    </div>
    <div class="card c-teal">
      <div class="val">{s['text_total']}</div>
      <div class="lbl">Текстовых задач</div>
    </div>
  </div>

  <div class="chart-box">
    <div class="chart-title">{chart_heading}</div>
    {chart_block}
  </div>

</div>
</body>
</html>"""
    return web.Response(text=html, content_type="text/html", charset="utf-8")

PRIVACY_POLICY_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Privacy Policy — Get My Task</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
         background:#0f0f0f;color:#e0e0e0;line-height:1.7;padding:40px 20px}
    .wrap{max-width:720px;margin:0 auto}
    h1{font-size:2rem;font-weight:700;margin-bottom:8px;color:#fff}
    .sub{color:#888;font-size:.95rem;margin-bottom:40px}
    h2{font-size:1.15rem;font-weight:600;color:#fff;margin:32px 0 10px}
    p,li{color:#ccc;font-size:.97rem}
    ul{padding-left:20px;margin-top:6px}
    li{margin-bottom:4px}
    a{color:#7c9ef5;text-decoration:none}
    a:hover{text-decoration:underline}
    .card{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:12px;
          padding:24px;margin-top:40px;font-size:.9rem;color:#888}
  </style>
</head>
<body>
<div class="wrap">
  <h1>Privacy Policy</h1>
  <p class="sub">Get My Task Bot &nbsp;·&nbsp; Last updated: April 2026</p>

  <h2>1. What we collect</h2>
  <p>When you use Get My Task, we store the minimum data necessary to provide the service:</p>
  <ul>
    <li>Your Telegram user ID and language preference</li>
    <li>Tasks you create (title, date, time, priority quadrant)</li>
    <li>Google OAuth token (only if you choose to connect Google Calendar)</li>
    <li>Timezone and reminder preferences</li>
  </ul>

  <h2>2. How we use your data</h2>
  <ul>
    <li>To create, store, and display your tasks</li>
    <li>To add events to your Google Calendar on your request</li>
    <li>To send reminders via Telegram</li>
    <li>To transcribe voice messages using Groq Whisper API</li>
  </ul>
  <p>We do not sell, share, or use your data for advertising.</p>

  <h2>3. Google Calendar access</h2>
  <p>If you connect Google Calendar, we request the
  <code>https://www.googleapis.com/auth/calendar</code> scope to create and read
  calendar events. Your OAuth token is stored securely in our database and is
  used solely to add tasks to your calendar. You can revoke access at any time
  via <a href="https://myaccount.google.com/permissions" target="_blank">Google Account Permissions</a>
  or by using the Disconnect button in the bot settings.</p>

  <h2>4. Third-party services</h2>
  <ul>
    <li><strong>Telegram</strong> — messaging platform (<a href="https://telegram.org/privacy" target="_blank">Privacy Policy</a>)</li>
    <li><strong>Google Calendar API</strong> — calendar sync (<a href="https://policies.google.com/privacy" target="_blank">Privacy Policy</a>)</li>
    <li><strong>Groq API</strong> — voice transcription (<a href="https://groq.com/privacy-policy/" target="_blank">Privacy Policy</a>)</li>
  </ul>

  <h2>5. Data retention</h2>
  <p>Your data is stored as long as you use the bot. You can request deletion of
  all your data at any time by contacting us. Disconnecting Google Calendar
  immediately removes your OAuth token from our database.</p>

  <h2>6. Security</h2>
  <p>Data is stored on a private server with restricted access. OAuth tokens are
  stored encrypted at rest. We do not log the content of your tasks beyond what
  is necessary for the service to function.</p>

  <h2>7. Your rights</h2>
  <p>You have the right to access, correct, or delete your personal data. To
  exercise these rights, contact us at the address below.</p>

  <h2>8. Contact</h2>
  <p>If you have any questions about this Privacy Policy, please contact:<br/>
  <a href="mailto:hello.egour@gmail.com">hello.egour@gmail.com</a></p>

  <div class="card">
    Get My Task is an independent project and is not affiliated with Google,
    Apple, or Telegram.
  </div>
</div>
</body>
</html>"""

async def privacy_policy(request):
    return web.Response(text=PRIVACY_POLICY_HTML, content_type="text/html", charset="utf-8")

async def health_check(request):
    """Simple liveness endpoint for uptime monitors."""
    try:
        with sqlite3.connect("users.db") as db:
            user_count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        return web.json_response({"status": "ok", "users": user_count})
    except Exception as e:
        return web.json_response({"status": "error", "detail": str(e)}, status=500)

async def ical_feed(request):
    """Personal iCal subscription feed: /ical/{token}"""
    token = request.match_info.get("token", "")
    with sqlite3.connect("users.db") as db:
        row = db.execute(
            "SELECT chat_id, timezone FROM users WHERE ical_token=?", (token,)
        ).fetchone()
    if not row:
        return web.Response(text="Not found", status=404)
    chat_id, tz_name = row
    tz_name = tz_name or "Europe/Moscow"
    tz = ZoneInfo(tz_name)

    with sqlite3.connect("users.db") as db:
        tasks = db.execute(
            """SELECT title, quadrant, suggested_date, suggested_time FROM tasks
               WHERE chat_id=? AND done=0 AND suggested_date >= date('now', '-1 day')
               ORDER BY suggested_date, suggested_time""",
            (chat_id,)
        ).fetchall()

    now_utc = datetime.now(_utc.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Get My Task//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Get My Task",
        f"X-WR-TIMEZONE:{tz_name}",
        "REFRESH-INTERVAL;VALUE=DURATION:PT1H",
        "X-PUBLISHED-TTL:PT1H",
    ]
    for title, quadrant, date, time in tasks:
        uid = f"gmt-{chat_id}-{date}-{title.replace(' ', '')}@getmytask"
        safe_title = title.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
        if time:
            dt_start = datetime.fromisoformat(f"{date}T{time}:00").replace(tzinfo=tz)
            dt_end = dt_start + timedelta(hours=1)
            dtstart = dt_start.astimezone(_utc.utc).strftime("%Y%m%dT%H%M%SZ")
            dtend = dt_end.astimezone(_utc.utc).strftime("%Y%m%dT%H%M%SZ")
            lines += [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{now_utc}",
                f"DTSTART:{dtstart}",
                f"DTEND:{dtend}",
                f"SUMMARY:{safe_title}",
                "END:VEVENT",
            ]
        else:
            date_compact = date.replace("-", "")
            lines += [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{now_utc}",
                f"DTSTART;VALUE=DATE:{date_compact}",
                f"DTEND;VALUE=DATE:{date_compact}",
                f"SUMMARY:{safe_title}",
                "END:VEVENT",
            ]
    lines.append("END:VCALENDAR")
    ics_content = "\r\n".join(lines) + "\r\n"
    return web.Response(
        text=ics_content,
        content_type="text/calendar",
        charset="utf-8",
        headers={"Content-Disposition": 'attachment; filename="getmytask.ics"'}
    )

async def ical_open(request):
    """Redirect to webcal:// — Telegram buttons only support https://, so we redirect."""
    token = request.match_info.get("token", "")
    base = BASE_URL.replace("https://", "").replace("http://", "")
    webcal_url = f"webcal://{base}/ical/{token}"
    raise web.HTTPFound(location=webcal_url)

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", home_page)
    app.router.add_get("/health", health_check)
    app.router.add_get("/ical/{token}", ical_feed)
    app.router.add_get("/ical-open/{token}", ical_open)
    app.router.add_get("/stats", stats_page)
    app.router.add_get("/googled2363927b56587ef.html", google_verification)
    app.router.add_get("/oauth/callback", oauth_callback)
    app.router.add_get("/privacy", privacy_policy)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    logger.info("OAuth server started on port 8080")

# ─── Main ─────────────────────────────────────────────────────────────────────

async def main():
    global bot_app
    init_db()
    bot_app = Application.builder().token(TELEGRAM_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("connect", connect_command))
    bot_app.add_handler(CommandHandler("timezone", timezone_command))
    bot_app.add_handler(CommandHandler("help", help_command))
    bot_app.add_handler(CommandHandler("tasks", tasks_command))
    bot_app.add_handler(CommandHandler("mytasks", mytasks_command))
    bot_app.add_handler(CommandHandler("settings", settings_command))
    bot_app.add_handler(CommandHandler("stats", stats_command))
    bot_app.add_handler(CommandHandler("announce", announce_command))
    bot_app.add_handler(CommandHandler("goals", goals_command))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    bot_app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    bot_app.add_handler(MessageHandler(filters.AUDIO, handle_voice))
    bot_app.add_handler(CallbackQueryHandler(handle_callback))
    async def log_all(update, context):
        msg = update.message
        if msg:
            logger.info(f"INCOMING: voice={bool(msg.voice)}, audio={bool(msg.audio)}, text={repr(msg.text)}, video_note={bool(msg.video_note)}, update_id={update.update_id}")
        else:
            logger.info(f"INCOMING non-message update: {update}")
    bot_app.add_handler(MessageHandler(filters.ALL, log_all), group=-1)
    async def error_handler(update, context):
        global _ux_error_count, _ux_error_window_start
        logger.error(f"Update {update} caused error: {context.error}", exc_info=context.error)
        now = _time.monotonic()
        # Rolling 5-minute window for user-facing errors
        if now - _ux_error_window_start > 300:
            _ux_error_count = 0
            _ux_error_window_start = now
        _ux_error_count += 1
        if _ux_error_count >= 5:
            await send_owner_alert(
                "ux_error_spike",
                f"⚠️ *Частые ошибки у пользователей*\n"
                f"{_ux_error_count} ошибок за 5 минут\n\n"
                f"`{str(context.error)[:300]}`"
            )
    bot_app.add_error_handler(error_handler)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(_safe_job, "interval", minutes=5,  args=[check_reminders,      "check_reminders"])
    scheduler.add_job(_safe_job, "interval", minutes=1,  args=[check_task_reminders, "check_task_reminders"])
    scheduler.add_job(_safe_job, "interval", minutes=1,  args=[send_morning_digests, "morning_digests"])
    scheduler.add_job(_safe_job, "interval", minutes=15, args=[sync_calendar_events, "sync_calendar"])
    scheduler.add_job(_safe_job, "interval", minutes=30, args=[check_reengagement,   "reengagement"])
    scheduler.add_job(monitor_system, "interval", minutes=10)
    scheduler.start()
    await start_web_server()
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.bot.set_my_commands([
        BotCommand("start", "🏠 Главное меню"),
        BotCommand("tasks", "📋 Мои задачи"),
        BotCommand("settings", "⚙️ Настройки"),
        BotCommand("timezone", "🕐 Таймзона"),
        BotCommand("connect", "📅 Подключить Calendar"),
        BotCommand("goals", "🎯 Мои цели"),
        BotCommand("help", "❓ Помощь"),
    ])
    await bot_app.updater.start_polling(allowed_updates=list(Update.ALL_TYPES))
    print("Бот запущен...")
    # Notify owner that bot started successfully
    try:
        await bot_app.bot.send_message(
            chat_id=BOT_OWNER_ID,
            text="✅ *Get My Task Bot* запущен",
            parse_mode="Markdown"
        )
    except Exception:
        pass
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())