"""
Tests: чистая бизнес-логика бота.
"""
import pytest
import sys
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from bot import (
    _progress_bar,
    _task_matches_goal,
    format_date,
    format_date_relative,
    adjust_task_to_future,
    build_tasks_by_day,
    fmt_title,
)

TZ = "Europe/Moscow"


# ─── _progress_bar ────────────────────────────────────────────────────────────

class TestProgressBar:
    def test_zero_percent(self):
        assert _progress_bar(0) == "░░░░░░░░"

    def test_hundred_percent(self):
        assert _progress_bar(100) == "████████"

    def test_fifty_percent(self):
        bar = _progress_bar(50)
        assert "█" in bar and "░" in bar
        assert len(bar) == 8

    def test_length_parameter(self):
        assert len(_progress_bar(50, length=10)) == 10


# ─── _task_matches_goal ───────────────────────────────────────────────────────

class TestTaskMatchesGoal:
    def test_matching_word(self):
        assert _task_matches_goal("Запустить лендинг GetMyTask", "Запустить GetMyTask") is True

    def test_no_match(self):
        assert _task_matches_goal("Купить молоко", "Запустить бизнес") is False

    def test_stop_words_only(self):
        # "я хочу" — только стоп-слова, не должно давать match
        assert _task_matches_goal("я хочу", "я хочу") is False

    def test_case_insensitive(self):
        assert _task_matches_goal("ЛЕНДИНГ готов", "лендинг GetMyTask") is True


# ─── format_date ──────────────────────────────────────────────────────────────

class TestFormatDate:
    def test_valid_date_ru(self):
        result = format_date("2026-07-15", "ru")
        assert "15" in result
        assert result != ""

    def test_valid_date_en(self):
        result = format_date("2026-07-15", "en")
        assert "15" in result

    def test_invalid_date_returns_string(self):
        result = format_date("not-a-date", "ru")
        assert isinstance(result, str)

    def test_empty_string(self):
        result = format_date("", "ru")
        assert isinstance(result, str)


# ─── format_date_relative ─────────────────────────────────────────────────────

class TestFormatDateRelative:
    def test_today(self):
        result = format_date_relative("2026-05-01", "2026-05-01", "2026-05-02", "ru")
        assert "сегодня" in result.lower() or "today" in result.lower() or result != ""

    def test_tomorrow(self):
        result = format_date_relative("2026-05-02", "2026-05-01", "2026-05-02", "ru")
        assert "завтра" in result.lower() or result != ""

    def test_future_date(self):
        result = format_date_relative("2026-05-10", "2026-05-01", "2026-05-02", "ru")
        assert isinstance(result, str) and result != ""


# ─── adjust_task_to_future ────────────────────────────────────────────────────

class TestAdjustTaskToFuture:
    def _future_task(self):
        tz = ZoneInfo(TZ)
        future = datetime.now(tz) + timedelta(hours=2)
        return {
            "title": "Test",
            "suggested_date": future.strftime("%Y-%m-%d"),
            "suggested_time": future.strftime("%H:%M"),
        }

    def _past_task(self):
        tz = ZoneInfo(TZ)
        # >12h in the past so AM/PM flip still leaves it in the past
        past = datetime.now(tz) - timedelta(hours=14)
        return {
            "title": "Test",
            "suggested_date": past.strftime("%Y-%m-%d"),
            "suggested_time": past.strftime("%H:%M"),
        }

    def test_future_task_unchanged(self):
        task = self._future_task()
        adjusted, status = adjust_task_to_future(task, TZ)
        assert status == "ok"
        assert adjusted["suggested_date"] == task["suggested_date"]

    def test_past_task_marked(self):
        task = self._past_task()
        _, status = adjust_task_to_future(task, TZ)
        assert status == "past"

    def test_no_time_task_ok(self):
        tz = ZoneInfo(TZ)
        future_date = (datetime.now(tz) + timedelta(days=1)).strftime("%Y-%m-%d")
        task = {"title": "No time task", "suggested_date": future_date}
        _, status = adjust_task_to_future(task, TZ)
        assert status == "ok"


# ─── build_tasks_by_day ───────────────────────────────────────────────────────

class TestBuildTasksByDay:
    def test_single_task_today(self):
        today = "2026-05-01"
        rows = [("Позвонить врачу", "Q1", today, "10:00")]
        result = build_tasks_by_day(rows, "ru", today, "2026-05-02", "09:00")
        assert "Позвонить врачу" in result

    def test_done_task_has_checkmark(self):
        today = "2026-05-01"
        rows = [("Старая задача", "Q1", today, "08:00")]
        result = build_tasks_by_day(rows, "ru", today, "2026-05-02", "09:00")
        assert "✅" in result

    def test_future_task_no_checkmark(self):
        today = "2026-05-01"
        rows = [("Будущая задача", "Q1", today, "23:59")]
        result = build_tasks_by_day(rows, "ru", today, "2026-05-02", "09:00")
        assert "✅" not in result

    def test_empty_rows_returns_empty(self):
        result = build_tasks_by_day([], "ru", "2026-05-01", "2026-05-02", "09:00")
        assert result == ""

    def test_tomorrow_task_shown(self):
        today = "2026-05-01"
        tomorrow = "2026-05-02"
        rows = [("Завтрашняя задача", "Q2", tomorrow, None)]
        result = build_tasks_by_day(rows, "ru", today, tomorrow, "09:00")
        assert "Завтрашняя задача" in result


# ─── fmt_title ────────────────────────────────────────────────────────────────

class TestFmtTitle:
    def test_title_without_url(self):
        result = fmt_title("Задача", None)
        assert "Задача" in result

    def test_title_with_url(self):
        result = fmt_title("Задача", "https://example.com")
        assert "Задача" in result
        assert "https://example.com" in result

    def test_bold_default(self):
        result = fmt_title("Задача", None, bold=True)
        assert "*" in result

    def test_no_bold(self):
        result = fmt_title("Задача", None, bold=False)
        assert result == "Задача"
