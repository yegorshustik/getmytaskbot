"""
calendar_utils.py — Google Calendar API + OAuth + iCal for Get My Task bot.

Depends on: db.py, texts.py
No Telegram imports.
"""
from __future__ import annotations
import base64
import hashlib
import json
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone as _utc
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from db import get_user, save_user, save_task_to_db, save_recurring_task_to_db
from texts import TEXTS

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Set at startup via init(base_url) from bot.py
_BASE_URL = "http://localhost:8080"


def init(base_url: str):
    global _BASE_URL
    _BASE_URL = base_url


# ─── Timezone helper ──────────────────────────────────────────────────────────

def get_tz_offset_str(tz_name: str) -> str:
    tz = ZoneInfo(tz_name)
    offset = datetime.now(tz).utcoffset()
    total = int(offset.total_seconds())
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    h, m = divmod(total // 60, 60)
    return f"{sign}{h:02d}:{m:02d}"


# ─── Calendar service ─────────────────────────────────────────────────────────

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
        return [e for e in result.get("items", []) if "dateTime" in e.get("start", {})]
    except Exception as e:
        logger.error(f"Conflict check error: {e}")
        return []


def add_to_calendar(chat_id, task):
    service = get_calendar_service_for_user(chat_id)
    if not service:
        return None, None
    user = get_user(chat_id)
    tz_name = user["timezone"] if user else "Europe/Moscow"
    reminder_mins = user.get("reminder_minutes", 30) if user else 30
    date = task.get("suggested_date", datetime.now().strftime("%Y-%m-%d"))
    time = task.get("suggested_time")
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
        "description": f"{task.get('description', '')}\n\n{task.get('quadrant', '')} — {task.get('quadrant_name', '')}\n{task.get('reason', '')}",
        "start": start,
        "end": end,
        "reminders": {
            "useDefault": False,
            "overrides": [{"method": "popup", "minutes": reminder_mins}],
        },
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
            "overrides": [{"method": "popup", "minutes": reminder_mins}],
        },
    }
    result = service.events().insert(calendarId="primary", body=event).execute()
    event_id = result.get("id")
    save_recurring_task_to_db(chat_id, task["title"], event_id, rrule, time)
    save_task_to_db(chat_id, task, synced_to_calendar=1, google_event_id=event_id)
    return event_id, result.get("htmlLink")


# ─── iCal feed ────────────────────────────────────────────────────────────────

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


# ─── OAuth / PKCE ─────────────────────────────────────────────────────────────

def _pkce_pair():
    """Generate a PKCE code_verifier and corresponding S256 code_challenge."""
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(96)).rstrip(b"=").decode()
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def get_auth_url(chat_id):
    from db import save_oauth_state  # already imported at top but explicit for clarity
    flow = Flow.from_client_secrets_file(
        "credentials.json",
        scopes=SCOPES,
        redirect_uri=f"{_BASE_URL}/oauth/callback",
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
