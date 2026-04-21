import os
import json
import logging
import sqlite3
import asyncio
from datetime import datetime, timedelta, timezone as _utc
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

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")

groq_client = Groq(api_key=GROQ_API_KEY)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]

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
    ]:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
        except sqlite3.OperationalError:
            pass
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
        }
    return None

def save_user(chat_id, **kwargs):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
    for key, val in kwargs.items():
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
        "lang_set": "Язык установлен: Русский 🇷🇺\n\nПросто напиши или надиктуй голосовое — я извлеку задачи и расставлю их по матрице Эйзенхауэра.",
        "processing": "Обрабатываю...",
        "transcribing": "Транскрибирую голосовое...",
        "recognized": "Распознал: ",
        "too_long": "⚠️ Голосовое слишком длинное (больше 60 сек). Запиши несколько коротких сообщений.",
        "too_short": "⚠️ Сообщение слишком короткое. Попробуй записать подробнее.",
        "no_text": "⚠️ Не удалось распознать речь. Проверь качество записи и попробуй снова.",
        "no_tasks": "⚠️ Не нашёл задач в сообщении. Опиши что нужно сделать.",
        "add_calendar": "✅ Добавить в Calendar",
        "skip": "❌ Пропустить",
        "adding": "⏳ Добавляю в Calendar...",
        "added": "✅ Добавлено в Calendar",
        "added_btn": "📅 Открыть в Calendar",
        "skipped": "⏭ Пропустили: ",
        "calendar_error": "Ошибка Calendar: ",
        "error": "Ошибка: ",
        "offer_calendar": "📅 Хочешь добавлять задачи в Google Calendar и получать напоминания?",
        "connect_calendar": "🔗 Подключить Calendar",
        "skip_calendar": "➡️ Пропустить",
        "connect_link": "🔗 Подключи Google Calendar:",
        "calendar_connected": "✅ Google Calendar подключён! Теперь я буду напоминать тебе о задачах.",
        "calendar_not_connected": "❌ Календарь не подключён. Используй /connect чтобы подключить.",
        "reminder": "🔔 Напоминание: *{title}*\n📅 {time}",
        "conflict_found": "⚠️ В это время уже есть: *{event}*.\n\nНапиши или надиктуй другое время для задачи *{title}*:",
        "correction_unclear": "⚠️ Не понял новое время. Попробуй написать например: «в 11 утра» или «завтра в 15:00»",
        "rescheduled": "✅ Время обновлено: {date} в {time}",
        "timezone_current": "🕐 Твоя текущая временная зона: *{tz}*\n\nВыбери из списка или введи вручную:",
        "timezone_set": "✅ Временная зона установлена: *{tz}*",
        "timezone_manual": "✍️ Ввести вручную",
        "timezone_prompt": "Введи название временной зоны, например:\n`Europe/Moscow`, `Asia/Almaty`, `America/New_York`",
        "timezone_invalid": "❌ Не удалось распознать временную зону. Попробуй формат: `Europe/Moscow`",
        "help": (
            "📋 *Что я умею:*\n\n"
            "• Напиши или надиктуй голосовое — извлеку задачи и расставлю по матрице Эйзенхауэра\n"
            "• Предложу дату и время для каждой задачи\n"
            "• Добавлю задачи в Google Calendar\n"
            "• Напомню о событиях за 30 минут\n\n"
            "⚙️ *Команды:*\n"
            "/start — начать заново\n"
            "/connect — подключить Google Calendar\n"
            "/tasks — мои задачи (последние 10)\n"
            "/timezone — изменить временную зону\n"
            "/help — эта справка"
        ),
        "tasks_header": "📋 *Последние задачи:*\n\n",
        "tasks_empty": "У тебя пока нет сохранённых задач.",
        "tasks_item": "{emoji} *{title}* — {date}\n",
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
        "morning_digest": "☀️ *Доброе утро!* Вот твои задачи на сегодня:\n\n{tasks}",
        "morning_digest_future": "☀️ *Доброе утро!* Задач на сегодня нет.\n\nБлижайшие дела:\n\n{tasks}",
        "morning_digest_empty": "☀️ *Доброе утро!* У тебя нет запланированных задач.",
        "morning_first_offer": "\n\n_Напоминание приходит в {time}. Хочешь изменить время?_",
        "btn_reminder_change": "🕐 Изменить время",
        "btn_reminder_disable": "🔕 Отключить",
        "btn_archive": "🗂 Архив задач",
        "archive_header": "🗂 *Архив выполненных задач:*\n\n",
        "archive_empty": "Архив пуст — нет прошедших задач.",
        "btn_reminder_before": "⏰ Напомнить за {min} мин",
        "reminder_before_settings": "⏰ *Напоминание о задачах*\nСейчас: за {min} мин до начала",
        "reminder_before_set": "✅ Буду напоминать за {min} мин до задачи.",
        "task_reminder": "⏰ Напоминание: *{title}* начнётся в {time}",
        "menu_hint": "Надиктуй или опиши задачу:",
    },
    "en": {
        "choose_lang": "Привет! Выбери язык / Choose language / Оберіть мову:",
        "lang_set": "Language set: English 🇬🇧\n\nJust type or send a voice message — I'll extract tasks and classify them using the Eisenhower Matrix.",
        "processing": "Processing...",
        "transcribing": "Transcribing voice message...",
        "recognized": "Recognized: ",
        "too_long": "⚠️ Voice message is too long (over 60 sec). Please record shorter messages.",
        "too_short": "⚠️ Message is too short. Try recording with more detail.",
        "no_text": "⚠️ Could not recognize speech. Check audio quality and try again.",
        "no_tasks": "⚠️ No tasks found in the message. Describe what needs to be done.",
        "add_calendar": "✅ Add to Calendar",
        "skip": "❌ Skip",
        "adding": "⏳ Adding to Calendar...",
        "added": "✅ Added to Calendar",
        "added_btn": "📅 Open in Calendar",
        "skipped": "⏭ Skipped: ",
        "calendar_error": "Calendar error: ",
        "error": "Error: ",
        "offer_calendar": "📅 Want to add tasks to Google Calendar and get reminders?",
        "connect_calendar": "🔗 Connect Calendar",
        "skip_calendar": "➡️ Skip",
        "connect_link": "🔗 Connect Google Calendar:",
        "calendar_connected": "✅ Google Calendar connected! I'll remind you about your tasks.",
        "calendar_not_connected": "❌ Calendar not connected. Use /connect to connect.",
        "reminder": "🔔 Reminder: *{title}*\n📅 {time}",
        "conflict_found": "⚠️ There's already an event at this time: *{event}*.\n\nWrite or say a new time for *{title}*:",
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
            "• Add tasks to Google Calendar\n"
            "• Remind you about events 30 minutes before\n\n"
            "⚙️ *Commands:*\n"
            "/start — restart\n"
            "/connect — connect Google Calendar\n"
            "/tasks — my tasks (last 10)\n"
            "/timezone — change timezone\n"
            "/help — this help"
        ),
        "tasks_header": "📋 *Recent tasks:*\n\n",
        "tasks_empty": "You have no saved tasks yet.",
        "tasks_item": "{emoji} *{title}* — {date}\n",
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
        "btn_archive": "🗂 Task archive",
        "archive_header": "🗂 *Completed tasks archive:*\n\n",
        "archive_empty": "Archive is empty — no past tasks.",
        "btn_reminder_before": "⏰ Remind {min} min before",
        "reminder_before_settings": "⏰ *Task reminders*\nNow: {min} min before start",
        "reminder_before_set": "✅ Will remind {min} min before task.",
        "task_reminder": "⏰ Reminder: *{title}* starts at {time}",
        "menu_hint": "Dictate or describe a task:",
    },
    "uk": {
        "choose_lang": "Привет! Выбери язык / Choose language / Оберіть мову:",
        "lang_set": "Мову встановлено: Українська 🇺🇦\n\nПросто напиши або надиктуй голосове — я витягну задачі та розставлю їх по матриці Ейзенхауера.",
        "processing": "Обробляю...",
        "transcribing": "Транскрибую голосове...",
        "recognized": "Розпізнав: ",
        "too_long": "⚠️ Голосове занадто довге (більше 60 сек). Запиши кілька коротких повідомлень.",
        "too_short": "⚠️ Повідомлення занадто коротке. Спробуй записати детальніше.",
        "no_text": "⚠️ Не вдалося розпізнати мову. Перевір якість запису і спробуй знову.",
        "no_tasks": "⚠️ Не знайшов задач у повідомленні. Опиши що потрібно зробити.",
        "add_calendar": "✅ Додати до Calendar",
        "skip": "❌ Пропустити",
        "adding": "⏳ Додаю до Calendar...",
        "added": "✅ Додано до Calendar",
        "added_btn": "📅 Відкрити в Calendar",
        "skipped": "⏭ Пропустили: ",
        "calendar_error": "Помилка Calendar: ",
        "error": "Помилка: ",
        "offer_calendar": "📅 Хочеш додавати задачі до Google Calendar і отримувати нагадування?",
        "connect_calendar": "🔗 Підключити Calendar",
        "skip_calendar": "➡️ Пропустити",
        "connect_link": "🔗 Підключи Google Calendar:",
        "calendar_connected": "✅ Google Calendar підключено! Тепер я нагадуватиму тобі про задачі.",
        "calendar_not_connected": "❌ Календар не підключено. Використай /connect щоб підключити.",
        "reminder": "🔔 Нагадування: *{title}*\n📅 {time}",
        "conflict_found": "⚠️ На цей час вже є подія: *{event}*.\n\nНапиши або надиктуй інший час для задачі *{title}*:",
        "correction_unclear": "⚠️ Не зрозумів новий час. Спробуй написати, наприклад: «об 11 ранку» або «завтра о 15:00»",
        "rescheduled": "✅ Час оновлено: {date} о {time}",
        "timezone_current": "🕐 Твій поточний часовий пояс: *{tz}*\n\nОбери зі списку або введи вручну:",
        "timezone_set": "✅ Часовий пояс встановлено: *{tz}*",
        "timezone_manual": "✍️ Ввести вручну",
        "timezone_prompt": "Введи назву часового поясу, наприклад:\n`Europe/Kyiv`, `Asia/Almaty`, `America/New_York`",
        "timezone_invalid": "❌ Не вдалося розпізнати часовий пояс. Спробуй формат: `Europe/Kyiv`",
        "help": (
            "📋 *Що я вмію:*\n\n"
            "• Напиши або надиктуй голосове — витягну задачі та розставлю по матриці Ейзенхауера\n"
            "• Запропоную дату і час для кожної задачі\n"
            "• Додам задачі до Google Calendar\n"
            "• Нагадаю про події за 30 хвилин\n\n"
            "⚙️ *Команди:*\n"
            "/start — почати заново\n"
            "/connect — підключити Google Calendar\n"
            "/tasks — мої задачі (останні 10)\n"
            "/timezone — змінити часовий пояс\n"
            "/help — ця довідка"
        ),
        "tasks_header": "📋 *Останні задачі:*\n\n",
        "tasks_empty": "У тебе поки немає збережених задач.",
        "tasks_item": "{emoji} *{title}* — {date}\n",
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
        "morning_digest": "☀️ *Доброго ранку!* Ось твої задачі на сьогодні:\n\n{tasks}",
        "morning_digest_future": "☀️ *Доброго ранку!* Задач на сьогодні немає.\n\nНайближчі справи:\n\n{tasks}",
        "morning_digest_empty": "☀️ *Доброго ранку!* У тебе немає запланованих задач.",
        "morning_first_offer": "\n\n_Нагадування приходить о {time}. Бажаєш змінити час?_",
        "btn_reminder_change": "🕐 Змінити час",
        "btn_reminder_disable": "🔕 Вимкнути",
        "btn_archive": "🗂 Архів задач",
        "archive_header": "🗂 *Архів виконаних задач:*\n\n",
        "archive_empty": "Архів порожній — немає минулих задач.",
        "btn_reminder_before": "⏰ Нагадати за {min} хв",
        "reminder_before_settings": "⏰ *Нагадування про задачі*\nЗараз: за {min} хв до початку",
        "reminder_before_set": "✅ Нагадуватиму за {min} хв до задачі.",
        "task_reminder": "⏰ Нагадування: *{title}* починається о {time}",
        "menu_hint": "Надиктуй або опиши задачу:",
    },
}

def get_active_task_count(chat_id):
    conn = sqlite3.connect("users.db")
    user = get_user(chat_id)
    tz_name = user["timezone"] if user else "Europe/Moscow"
    now = datetime.now(ZoneInfo(tz_name))
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    count = conn.execute(
        """SELECT COUNT(*) FROM tasks WHERE chat_id=?
           AND (suggested_date > ? OR (suggested_date = ? AND (suggested_time IS NULL OR suggested_time >= ?)))""",
        (chat_id, today, today, current_time)
    ).fetchone()[0]
    conn.close()
    return count

def main_menu_keyboard(lang: str, calendar_connected: bool, task_count: int = 0) -> ReplyKeyboardMarkup:
    t = TEXTS[lang]
    tasks_label = t["btn_my_tasks"] + (f" ({task_count})" if task_count > 0 else "")
    cal_btn = KeyboardButton(t["btn_view_calendar"]) if calendar_connected else KeyboardButton(t["btn_connect"])
    row1 = [KeyboardButton(tasks_label), KeyboardButton(t["btn_settings"])]
    row2 = [cal_btn]
    return ReplyKeyboardMarkup([row1, row2], resize_keyboard=True)

def get_system_prompt(lang: str, tz_name: str = "Europe/Moscow") -> str:
    now = datetime.now(ZoneInfo(tz_name))
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    prompts = {
        "ru": f"""Ты — ассистент по управлению задачами. Сейчас {today} {current_time} (часовой пояс {tz_name}). Из текста извлеки все задачи и классифицируй по матрице Эйзенхауэра.
Для каждой задачи верни JSON с полями: title, description, quadrant (Q1/Q2/Q3/Q4), quadrant_name (на русском), suggested_date (YYYY-MM-DD), suggested_time (HH:MM если пользователь указал время или относительное время вроде "через 15 минут" — считай от {current_time}, иначе null), reason (на русском).
Правила для времени: "через N минут/часов" — прибавь к {current_time}; "завтра", "послезавтра" и т.д. — только дата, время null если не указано явно.
Верни ТОЛЬКО валидный JSON массив. Без пояснений.""",
        "en": f"""You are a task management assistant. Current time is {today} {current_time} (timezone {tz_name}). Extract all tasks from the text and classify them using the Eisenhower Matrix.
For each task return JSON with fields: title, description, quadrant (Q1/Q2/Q3/Q4), quadrant_name (in English), suggested_date (YYYY-MM-DD), suggested_time (HH:MM if user specified a time or relative time like "in 15 minutes" — calculate from {current_time}, otherwise null), reason (in English).
Time rules: "in N minutes/hours" — add to {current_time}; "tomorrow", "next week" etc — date only, time null unless explicitly stated.
Return ONLY a valid JSON array. No explanations.""",
        "uk": f"""Ти — асистент з управління задачами. Зараз {today} {current_time} (часовий пояс {tz_name}). З тексту витягни всі задачі та класифікуй за матрицею Ейзенхауера.
Для кожної задачі поверни JSON з полями: title, description, quadrant (Q1/Q2/Q3/Q4), quadrant_name (українською), suggested_date (YYYY-MM-DD), suggested_time (HH:MM якщо користувач вказав час або відносний час на кшталт "через 15 хвилин" — рахуй від {current_time}, інакше null), reason (українською).
Правила часу: "через N хвилин/годин" — додай до {current_time}; "завтра", "післязавтра" тощо — лише дата, час null якщо не вказано явно.
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
        creds.refresh(Request())
        save_user(chat_id, calendar_token=creds.to_json())
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
    date = task.get("suggested_date", datetime.now().strftime("%Y-%m-%d"))
    time = task.get("suggested_time")
    if time:
        from datetime import date as _date, timedelta as _td
        start_dt = datetime.strptime(f"{date}T{time}", "%Y-%m-%dT%H:%M")
        end_dt = start_dt + _td(minutes=30)
        end_date = end_dt.strftime("%Y-%m-%d")
        start = {"dateTime": f"{date}T{time}:00", "timeZone": tz_name}
        end = {"dateTime": f"{end_date}T{end_dt.strftime('%H:%M')}:00", "timeZone": tz_name}
    else:
        from datetime import date as _date, timedelta as _td
        next_day = (_date.fromisoformat(date) + _td(days=1)).isoformat()
        start = {"date": date}
        end = {"date": next_day}
    event = {
        "summary": task["title"],
        "description": f"{task['description']}\n\n{task['quadrant']} — {task['quadrant_name']}\n{task['reason']}",
        "start": start,
        "end": end,
    }
    result = service.events().insert(calendarId="primary", body=event).execute()
    conn = sqlite3.connect("users.db")
    conn.execute(
        "INSERT INTO tasks (chat_id, title, quadrant, suggested_date, suggested_time) VALUES (?,?,?,?,?)",
        (chat_id, task["title"], task.get("quadrant",""), date, time)
    )
    conn.commit()
    conn.close()
    return result.get("htmlLink")

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
    return json.loads(raw.strip())

# ─── OAuth ────────────────────────────────────────────────────────────────────

pending_oauth = {}

def get_auth_url(chat_id):
    flow = Flow.from_client_secrets_file(
        "credentials.json",
        scopes=SCOPES,
        redirect_uri=f"{BASE_URL}/oauth/callback"
    )
    auth_url, state = flow.authorization_url(access_type="offline", include_granted_scopes="true")
    pending_oauth[state] = {"chat_id": chat_id, "flow": flow}
    return auth_url


# ─── Reminders ────────────────────────────────────────────────────────────────

bot_app = None

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
                except:
                    continue
                reminders = event.get("reminders", {})
                overrides = reminders.get("overrides", [])
                if not overrides and reminders.get("useDefault", True):
                    overrides = [{"method": "popup", "minutes": 30}]
                for reminder in overrides:
                    minutes_before = reminder.get("minutes", 30)
                    remind_at = start_dt - timedelta(minutes=minutes_before)
                    remind_at_utc = remind_at.astimezone(_utc).replace(tzinfo=None)
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
                            await bot_app.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
                            mark_reminder_sent(chat_id, event_id, remind_key)
        except Exception as e:
            logger.error(f"Reminder error for {chat_id}: {e}")

async def check_task_reminders():
    conn = sqlite3.connect("users.db")
    users = conn.execute("SELECT chat_id, lang, timezone, reminder_before FROM users WHERE reminder_before > 0 AND lang IS NOT NULL").fetchall()
    conn.close()
    for chat_id, lang, tz_name, reminder_before in users:
        try:
            tz = ZoneInfo(tz_name or "Europe/Moscow")
            now = datetime.now(tz)
            remind_at = now + timedelta(minutes=reminder_before)
            target_date = remind_at.strftime("%Y-%m-%d")
            target_time = remind_at.strftime("%H:%M")
            db = sqlite3.connect("users.db")
            tasks = db.execute(
                "SELECT id, title, suggested_date, suggested_time FROM tasks WHERE chat_id=? AND suggested_date=? AND suggested_time=?",
                (chat_id, target_date, target_time)
            ).fetchall()
            db.close()
            lang = lang or "ru"
            for task_id, title, date, time in tasks:
                remind_key = f"task_{task_id}"
                if reminder_already_sent(chat_id, remind_key, target_time):
                    continue
                await bot_app.bot.send_message(
                    chat_id=chat_id,
                    text=TEXTS[lang]["task_reminder"].format(title=title, time=time),
                    parse_mode="Markdown"
                )
                mark_reminder_sent(chat_id, remind_key, target_time)
        except Exception as e:
            logger.error(f"Task reminder error for {chat_id}: {e}")

_morning_sent_today = {}  # chat_id -> date string

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
            if _morning_sent_today.get(chat_id) == today:
                continue
            _morning_sent_today[chat_id] = today
            lang = lang or "ru"
            t = TEXTS[lang]
            # Digest: only tasks WITHOUT time (timed tasks get their own reminder)
            db = sqlite3.connect("users.db")
            today_rows = db.execute(
                "SELECT title FROM tasks WHERE chat_id=? AND suggested_date=? AND (suggested_time IS NULL OR suggested_time='') ORDER BY id ASC",
                (chat_id, today)
            ).fetchall()
            future_rows = db.execute(
                "SELECT title, suggested_date FROM tasks WHERE chat_id=? AND suggested_date>? AND (suggested_time IS NULL OR suggested_time='') ORDER BY suggested_date ASC LIMIT 5",
                (chat_id, today)
            ).fetchall() if not today_rows else []
            db.close()
            if today_rows:
                task_lines = "".join(f"• *{title}*\n" for (title,) in today_rows)
                text = t["morning_digest"].format(tasks=task_lines)
            elif future_rows:
                task_lines = "".join(f"• *{title}* — {format_date(date, lang)}\n" for title, date in future_rows)
                text = t["morning_digest_future"].format(tasks=task_lines)
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

# ─── Helpers ──────────────────────────────────────────────────────────────────

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
    return json.loads(raw.strip())

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
        from datetime import date as _date
        d = _date.fromisoformat(date_str)
        months = _MONTHS.get(lang, _MONTHS["en"])
        if lang == "en":
            return f"{months[d.month - 1]} {d.day}, {d.year}"
        return f"{d.day} {months[d.month - 1]} {d.year}"
    except Exception:
        return date_str

async def show_tasks(update, chat_id, tasks, lang):
    user = get_user(chat_id)
    for i, task in enumerate(tasks):
        emoji = QUADRANT_EMOJI.get(task["quadrant"], "⚪")
        date_display = format_date(task["suggested_date"], lang)
        time_sep = _TIME_SEP.get(lang, " ")
        text = (
            f"{emoji} *{task['title']}*\n"
            f"{task['quadrant']} — {task['quadrant_name']}\n"
            f"📅 {date_display}"
            + (f"{time_sep}{task['suggested_time']}" if task.get("suggested_time") else "") + "\n"
            f"_{task['reason']}_"
        )
        if user and user["calendar_connected"]:
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(TEXTS[lang]["add_calendar"], callback_data=f"add_{i}"),
                InlineKeyboardButton(TEXTS[lang]["skip"], callback_data=f"skip_{i}")
            ]])
        else:
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(TEXTS[lang]["skip"], callback_data=f"skip_{i}")
            ]])
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def offer_calendar(update, chat_id, lang):
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(TEXTS[lang]["connect_calendar"], callback_data="connect_calendar"),
        InlineKeyboardButton(TEXTS[lang]["skip_calendar"], callback_data="skip_calendar"),
    ]])
    await update.message.reply_text(TEXTS[lang]["offer_calendar"], reply_markup=keyboard)

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
        link = add_to_calendar(chat_id, task)
        added_markup = InlineKeyboardMarkup([[InlineKeyboardButton(TEXTS[lang]["added_btn"], url=link)]]) if link else None
        await msg.edit_text(TEXTS[lang]["added"], reply_markup=added_markup)
        user = get_user(chat_id)
        await update.message.reply_text(
            TEXTS[lang]["menu_hint"],
            reply_markup=main_menu_keyboard(lang, user["calendar_connected"], get_active_task_count(chat_id))
        )
    except Exception as e:
        await update.message.reply_text(TEXTS[lang]["error"] + str(e))

async def process_and_show(update, context, text, chat_id, lang):
    user = get_user(chat_id)
    tz_name = user["timezone"] if user else "Europe/Moscow"
    tasks = await process_text(text, lang, tz_name)
    if not tasks:
        await update.message.reply_text(TEXTS[lang]["no_tasks"])
        return
    context.user_data["tasks"] = tasks
    await show_tasks(update, chat_id, tasks, lang)
    user = get_user(chat_id)
    if not user["first_task_done"]:
        save_user(chat_id, first_task_done=1)
        if not user["calendar_connected"]:
            await offer_calendar(update, chat_id, lang)

# ─── Handlers ─────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    save_user(chat_id)
    user = get_user(chat_id)
    if user and user["lang"]:
        lang = user["lang"]
        await update.message.reply_text(
            TEXTS[lang]["menu_hint"],
            reply_markup=main_menu_keyboard(lang, user["calendar_connected"], get_active_task_count(chat_id))
        )
        return
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk"),
    ]])
    await update.message.reply_text(TEXTS["ru"]["choose_lang"], reply_markup=keyboard)

async def connect_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    lang = user["lang"] if user else "ru"
    auth_url = get_auth_url(chat_id)
    await update.message.reply_text(
        TEXTS[lang]["connect_link"],
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Google Calendar", url=auth_url)]])
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    if not user or not user["lang"]:
        await start(update, context)
        return
    lang = user["lang"]
    user_text = update.message.text.strip()
    if context.user_data.get("awaiting_timezone"):
        context.user_data.pop("awaiting_timezone")
        try:
            ZoneInfo(user_text)
            save_user(chat_id, timezone=user_text)
            await update.message.reply_text(
                TEXTS[lang]["timezone_set"].format(tz=user_text), parse_mode="Markdown"
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
        reminder_time = user["reminder_time"] if user else "08:00"
        reminder_enabled = user["reminder_enabled"] if user else 1
        reminder_label = t["btn_reminder"] + f" ({reminder_time})" if reminder_enabled else t["btn_reminder"] + f" ({t['reminder_disabled_text']})"
        reminder_before = user["reminder_before"] if user else 30
        before_label = t["btn_reminder_before"].format(min=reminder_before)
        keyboard_rows = [
            [InlineKeyboardButton(t["btn_help"], callback_data="settings_help"),
             InlineKeyboardButton(t["btn_timezone"], callback_data="settings_timezone")],
            [InlineKeyboardButton(reminder_label, callback_data="settings_reminder")],
            [InlineKeyboardButton(before_label, callback_data="settings_reminder_before")],
            [InlineKeyboardButton(t["btn_archive"], callback_data="settings_archive")],
        ]
        if user and user["calendar_connected"]:
            keyboard_rows.append([InlineKeyboardButton(t["btn_disconnect_calendar"], callback_data="disconnect_calendar")])
        else:
            keyboard_rows.append([InlineKeyboardButton(t["btn_connect"], callback_data="connect_calendar")])
        await update.message.reply_text(t["btn_settings"], reply_markup=InlineKeyboardMarkup(keyboard_rows))
        return
    if user_text == t["btn_help"]:
        await help_command(update, context)
        return
    if user_text == t["btn_connect"]:
        await connect_command(update, context)
        return
    if user_text == t["btn_view_calendar"]:
        await update.message.reply_text(
            t["btn_view_calendar"],
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📅 Google Calendar", url="https://calendar.google.com/calendar/r")
            ]])
        )
        return
    if "pending_task" in context.user_data:
        if len(user_text) < 3:
            await update.message.reply_text(t["correction_unclear"])
            return
        await handle_reschedule(update, context, user_text, chat_id, lang)
        return
    if len(user_text) < 3:
        await update.message.reply_text(t["too_short"])
        return
    await update.message.reply_text(t["processing"])
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
    voice = update.message.voice
    if voice.duration > 60:
        await update.message.reply_text(TEXTS[lang]["too_long"])
        return
    if voice.duration < 1:
        await update.message.reply_text(TEXTS[lang]["too_short"])
        return
    await update.message.reply_text(TEXTS[lang]["transcribing"])
    try:
        file = await context.bot.get_file(voice.file_id)
        await file.download_to_drive("voice.ogg")
        with open("voice.ogg", "rb") as f:
            transcription = groq_client.audio.transcriptions.create(
                model="whisper-large-v3", file=f)
        text = transcription.text.strip()
        if not text or len(text) < 5:
            await update.message.reply_text(TEXTS[lang]["no_text"])
            return
        await update.message.reply_text(TEXTS[lang]["recognized"] + text)
        if "pending_task" in context.user_data:
            await handle_reschedule(update, context, text, chat_id, lang)
            return
        await process_and_show(update, context, text, chat_id, lang)
    except Exception as e:
        await update.message.reply_text(TEXTS[lang]["error"] + str(e))

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
        await query.edit_message_reply_markup(reply_markup=None)
        updated_user = get_user(chat_id)
        await query.message.reply_text(
            TEXTS[lang]["lang_set"],
            reply_markup=main_menu_keyboard(lang, updated_user["calendar_connected"], get_active_task_count(chat_id))
        )
        return
    if data == "connect_calendar":
        await query.edit_message_reply_markup(reply_markup=None)
        auth_url = get_auth_url(chat_id)
        await query.message.reply_text(
            TEXTS[lang]["connect_link"],
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Google Calendar", url=auth_url)]])
        )
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
        minutes = user["reminder_before"] if user else 30
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
        save_user(chat_id, reminder_before=mins)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(TEXTS[lang]["reminder_before_set"].format(min=mins))
        return
    if data == "reminder_before_off":
        save_user(chat_id, reminder_before=0)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(TEXTS[lang]["reminder_off"])
        return
    if data == "settings_archive":
        await query.edit_message_reply_markup(reply_markup=None)
        user = get_user(chat_id)
        tz_name = user["timezone"] if user else "Europe/Moscow"
        now = datetime.now(ZoneInfo(tz_name))
        today = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        conn = sqlite3.connect("users.db")
        rows = conn.execute(
            """SELECT title, quadrant, suggested_date, suggested_time FROM tasks
               WHERE chat_id=?
                 AND (suggested_date < ? OR (suggested_date = ? AND suggested_time IS NOT NULL AND suggested_time < ?))
               ORDER BY suggested_date DESC, suggested_time DESC LIMIT 20""",
            (chat_id, today, today, current_time)
        ).fetchall()
        conn.close()
        t = TEXTS[lang]
        if not rows:
            await query.message.reply_text(t["archive_empty"])
            return
        text = t["archive_header"]
        for title, quadrant, date, time in rows:
            emoji = QUADRANT_EMOJI.get(quadrant, "⚪")
            date_display = format_date(date, lang) if date else "—"
            if time:
                date_display += _TIME_SEP.get(lang, " ") + time
            text += TEXTS[lang]["tasks_item"].format(emoji=emoji, title=title, date=date_display)
        await query.message.reply_text(text, parse_mode="Markdown")
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
        if data == "tz_manual":
            context.user_data["awaiting_timezone"] = True
            await query.message.reply_text(TEXTS[lang]["timezone_prompt"], parse_mode="Markdown")
        else:
            idx_tz = int(data[3:])
            tz_name = POPULAR_TIMEZONES[idx_tz][1]
            save_user(chat_id, timezone=tz_name)
            await query.message.reply_text(
                TEXTS[lang]["timezone_set"].format(tz=tz_name), parse_mode="Markdown"
            )
        return
    action, idx = data.split("_")
    tasks = context.user_data.get("tasks", [])
    task = tasks[int(idx)]
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
            link = add_to_calendar(chat_id, task)
            added_markup = InlineKeyboardMarkup([[InlineKeyboardButton(TEXTS[lang]["added_btn"], url=link)]]) if link else None
            await msg.edit_text(TEXTS[lang]["added"], reply_markup=added_markup)
            user = get_user(chat_id)
            await query.message.reply_text(
                TEXTS[lang]["menu_hint"],
                reply_markup=main_menu_keyboard(lang, user["calendar_connected"], get_active_task_count(chat_id))
            )
        except Exception as e:
            await msg.edit_text(TEXTS[lang]["calendar_error"] + str(e))
    elif action == "skip":
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(TEXTS[lang]["skipped"] + task["title"])

async def show_timezone_menu(message, chat_id, lang):
    user = get_user(chat_id)
    current_tz = user["timezone"] if user else "Europe/Moscow"
    rows = []
    for i in range(0, len(POPULAR_TIMEZONES), 2):
        row = [InlineKeyboardButton(POPULAR_TIMEZONES[i][0], callback_data=f"tz_{i}")]
        if i + 1 < len(POPULAR_TIMEZONES):
            row.append(InlineKeyboardButton(POPULAR_TIMEZONES[i + 1][0], callback_data=f"tz_{i+1}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(TEXTS[lang]["timezone_manual"], callback_data="tz_manual")])
    await message.reply_text(
        TEXTS[lang]["timezone_current"].format(tz=current_tz),
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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    lang = user["lang"] if user else "ru"
    await update.message.reply_text(TEXTS[lang]["help"], parse_mode="Markdown")

async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_user(chat_id)
    lang = user["lang"] if user else "ru"
    conn = sqlite3.connect("users.db")
    user_tz = get_user(chat_id)["timezone"] if get_user(chat_id) else "Europe/Moscow"
    now = datetime.now(ZoneInfo(user_tz))
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    rows = conn.execute(
        """SELECT title, quadrant, suggested_date, suggested_time FROM tasks
           WHERE chat_id=?
             AND (suggested_date > ? OR (suggested_date = ? AND (suggested_time IS NULL OR suggested_time >= ?)))
           ORDER BY suggested_date ASC, suggested_time ASC LIMIT 10""",
        (chat_id, today, today, current_time)
    ).fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text(TEXTS[lang]["tasks_empty"])
        return
    text = TEXTS[lang]["tasks_header"]
    for title, quadrant, date, time in rows:
        emoji = QUADRANT_EMOJI.get(quadrant, "⚪")
        date_display = format_date(date, lang) if date else "—"
        if time:
            date_display += _TIME_SEP.get(lang, " ") + time
        text += TEXTS[lang]["tasks_item"].format(emoji=emoji, title=title, date=date_display)
    await update.message.reply_text(text, parse_mode="Markdown")

# ─── OAuth Web Server ─────────────────────────────────────────────────────────

async def oauth_callback(request):
    state = request.rel_url.query.get("state")
    code = request.rel_url.query.get("code")
    if not state or state not in pending_oauth:
        return web.Response(text="Invalid state", status=400)
    entry = pending_oauth.pop(state)
    chat_id = entry["chat_id"]
    flow = entry["flow"]
    flow.fetch_token(code=code)
    creds = flow.credentials
    save_user(chat_id, calendar_token=creds.to_json(), calendar_connected=1)
    user = get_user(chat_id)
    lang = user["lang"] if user else "ru"
    await bot_app.bot.send_message(
        chat_id=chat_id,
        text=TEXTS[lang]["calendar_connected"],
        reply_markup=main_menu_keyboard(lang, calendar_connected=True, task_count=get_active_task_count(chat_id))
    )
    return web.Response(text="✅ Calendar connected! You can close this tab.")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/oauth/callback", oauth_callback)
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
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    bot_app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    bot_app.add_handler(CallbackQueryHandler(handle_callback))
    async def log_all(update, context):
        msg = update.message
        if msg:
            logger.info(f"INCOMING: voice={bool(msg.voice)}, audio={bool(msg.audio)}, text={repr(msg.text)}, video_note={bool(msg.video_note)}, attachment={msg.effective_attachment}")
    bot_app.add_handler(MessageHandler(filters.ALL, log_all), group=-1)
    async def error_handler(update, context):
        logger.error(f"Update {update} caused error: {context.error}", exc_info=context.error)
    bot_app.add_error_handler(error_handler)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_reminders, "interval", minutes=5)
    scheduler.add_job(check_task_reminders, "interval", minutes=1)
    scheduler.add_job(send_morning_digests, "interval", minutes=1)
    scheduler.start()
    await start_web_server()
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.bot.set_my_commands([
        BotCommand("start", "🏠 Главное меню"),
        BotCommand("tasks", "📋 Мои задачи"),
        BotCommand("timezone", "🕐 Таймзона"),
        BotCommand("connect", "📅 Подключить Calendar"),
        BotCommand("help", "❓ Помощь"),
    ])
    await bot_app.updater.start_polling(allowed_updates=["message", "callback_query"])
    print("Бот запущен...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())