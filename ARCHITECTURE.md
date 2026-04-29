# Get My Task — Architecture

## Текущая структура модулей

```
getmytaskbot/
├── bot.py              # Telegram-хендлеры, веб-сервер, main()       ~3620 строк
├── db.py               # SQLite-слой, все операции с БД               ~415 строк
├── calendar_utils.py   # Google Calendar API, OAuth/PKCE, iCal        ~240 строк
├── texts.py            # Все локализованные строки (ru/en/uk)         ~695 строк
├── landing.py          # HTML лендинга (get_home_html + assets)       ~1775 строк
├── tests/
│   ├── conftest.py     # Моки тяжёлых зависимостей
│   ├── test_logic.py   # 38 unit-тестов на чистую логику
│   └── test_texts.py   # Проверка консистентности TEXTS
├── Makefile            # deploy / test / logs / status / hooks
└── .githooks/
    └── pre-commit      # Запускает pytest перед каждым коммитом
```

---

## Слои и зависимости

```
texts.py          ← нет зависимостей на наш код
    ↑
db.py             ← stdlib только (sqlite3, datetime, logging)
    ↑
calendar_utils.py ← db + texts + google-libs
    ↑
bot.py            ← всё вышеперечисленное + telegram + groq + aiohttp
```

Правило: **зависимости только вниз по стреле**. `db.py` никогда не импортирует из `bot.py`. `calendar_utils.py` никогда не импортирует из `bot.py`.

---

## Модули подробно

### `db.py` — данные
Единственное место, где открывается `sqlite3.connect("users.db")`.

| Группа | Функции |
|--------|---------|
| Схема | `init_db()` |
| Пользователи | `get_user`, `save_user`, `log_event` |
| Задачи | `save_task_to_db`, `link_task_to_goal`, `get_active_task_count` |
| Повторяющиеся | `save_recurring_task_to_db` |
| Цели | `save_goal_to_db`, `get_active_goals`, `delete_goal_from_db`, `get_goal_progress` |
| Напоминания | `reminder_already_sent`, `mark_reminder_sent` |
| OAuth | `save_oauth_state`, `pop_oauth_state` |

**Поля таблицы `users` (актуально на апрель 2026):**
`chat_id`, `lang`, `calendar_token`, `first_task_done`, `calendar_connected`, `timezone`, `reminder_time`, `reminder_enabled`, `reminder_before`, `reminder_minutes`, `pending_task_json`, `last_active`, `ical_token`, `last_reengagement`, `reengagement_count`, `first_name`, `username`, `registered_at`

`registered_at` — проставляется автоматически в `save_user()` при первом INSERT (если NULL). Используется для подсчёта реально новых пользователей в `/admin`.

### `calendar_utils.py` — интеграция с Google
Зависит от `db` и `texts`. Нет Telegram-импортов.

| Группа | Функции |
|--------|---------|
| Сервис | `get_calendar_service_for_user`, `get_tz_offset_str` |
| Создание событий | `add_to_calendar`, `add_recurring_to_calendar` |
| Конфликты | `check_conflicts` |
| Повторяемость | `describe_recurrence` |
| iCal | `generate_ics` |
| OAuth/PKCE | `get_auth_url`, `_pkce_pair`, `SCOPES` |

Инициализация BASE_URL вызывается один раз из `main()`:
```python
import calendar_utils as _cu
_cu.init(BASE_URL)
```

### `texts.py` — локализация
Один словарь `TEXTS = {"ru": {...}, "en": {...}, "uk": {...}}` с ~140 ключами на язык. Тест `test_texts.py` гарантирует, что все три языка имеют одинаковый набор ключей.

### `bot.py` — точка входа
Содержит:
- Telegram-хендлеры (`handle_text`, `handle_voice`, `handle_callback` и его 11 sub-handlers)
- Фоновые задачи APScheduler (`check_reminders`, `sync_calendar_events`, `send_morning_digests`, `check_reengagement`, `check_task_reminders`)
- aiohttp веб-сервер (`/oauth/callback`, `/stats`, `/ical/{token}`, `/privacy`)
- Вспомогательная логика (`format_date`, `build_tasks_by_day`, `adjust_task_to_future`, `process_and_show`)
- `main()` — сборка и запуск

---

## Структура `handle_callback`

`handle_callback` — чистый диспетчер (~20 строк). Логика живёт в sub-handlers:

| Функция | Префикс callback_data |
|---------|-----------------------|
| `_cb_lang` | `lang_` |
| `_cb_goal` | `goal_confirm_*`, `goal_link_*` |
| `_cb_goal_delete` | `gdel_*` |
| `_cb_announce` | `announce_*` |
| `_cb_calendar_connect` | `connect_calendar`, `disconnect_calendar`, `skip_calendar` |
| `_cb_settings` | `settings_*`, `reminder_*`, `archive_page_*`, `set_remind_min_*` |
| `_cb_tz` | `tz_*` |
| `_cb_ics` | `ics_*` |
| `_cb_recur` | `recur_*` |
| `_cb_conflict` | `force_save_*`, `cancel_save_*` |
| `_cb_task_action` | `save_*`, `skip_*`, `add_*` |

---

## Тесты

```bash
make test     # запустить вручную
make hooks    # активировать pre-commit хук
```

- **38 unit-тестов** в `tests/test_logic.py` — чистые функции без сайд-эффектов
- **`conftest.py`** мокирует все тяжёлые зависимости: telegram, groq, dotenv, google.*, apscheduler, aiohttp — тесты работают без credentials
- **Pre-commit хук** блокирует коммит при падении тестов

Что тестируется: `_progress_bar`, `_task_matches_goal`, `is_goal_rename_intent`, `format_date`, `format_date_relative`, `adjust_task_to_future`, `build_tasks_by_day`, `fmt_title`, консистентность TEXTS.

---

## История рефакторинга

| Шаг | Что сделано | Результат |
|-----|-------------|-----------|
| 1 | Извлечён `texts.py` из bot.py | −627 строк |
| 2 | `handle_callback` разбит на 11 sub-handlers | −~600 строк логики в одной функции |
| 3 | Извлечён `db.py` | −~260 строк |
| 4 | Извлечён `calendar_utils.py` | −~220 строк |
| **Итого** | bot.py: 4251 → 3158 строк | **−1093 строки** |

### Изменения апрель 2026
- `registered_at` добавлен в схему `users` и `_ALLOWED_USER_COLS`
- `/admin` (= `/stats`): исправлена метрика `new_users` (теперь по `registered_at`), убрано дублирование уведомлений
- Меню команд: порядок start→tasks→goals→settings, `/timezone` убрана из меню (доступна из `/settings`)
- Кнопки "Перенести задачу": заменены на +1ч / +3ч / завтра
- После удаления последней цели — автоматический промпт создать новую

---

## Следующие шаги рефакторинга

### Шаг 5 — `utils.py` (~150 строк)
Вынести display-утилиты из bot.py — нужны и bot.py, и будущему jobs.py:
```
format_date, format_date_relative, build_tasks_by_day
adjust_task_to_future, fmt_title, extract_url
get_menu_hint, _days_word
Константы: _TIME_SEP, QUADRANT_EMOJI, _MONTHS, POPULAR_TIMEZONES
```
**Зависимости:** только stdlib + texts.py. Без db и без telegram.

### Шаг 6 — `jobs.py` (~350 строк)
Вынести фоновые задачи APScheduler. Нужен после шага 5 (чтобы не было циклических импортов).
```
check_reminders, sync_calendar_events, check_task_reminders
send_morning_digests, check_reengagement
```
Паттерн инициализации — передача `bot` через `jobs.set_bot(bot_app.bot)` в `main()`.

После шагов 5+6 bot.py уменьшится ещё на ~500 строк и будет содержать только Telegram-хендлеры + веб-сервер + `main()`.

### Шаг 7 — тесты на `db.py`
Добавить `tests/test_db.py` с SQLite in-memory базой:
```python
# conftest добавит фикстуру:
@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("db.sqlite3.connect", lambda _: sqlite3.connect(db_path))
    init_db()
    return db_path
```
Тестировать: `save_user/get_user`, `save_task_to_db`, `get_active_goals`, `delete_goal_from_db`.

---

## Деплой

```bash
make deploy   # git push + git pull на сервере + systemctl restart
make logs     # journalctl -f
make status   # systemctl status taskbot
make ssh      # зайти на сервер
```

**Сервер:** `ubuntu@92.5.42.221` (Oracle Cloud, Always Free)  
**Сервис:** `taskbot` (systemd)  
**Python:** 3.11+

---

## Принципы, которые мы соблюдаем

1. **Зависимости только вниз** — нижние слои не знают о верхних
2. **Один модуль — одна ответственность** — db.py не содержит UI-логики, texts.py не содержит DB-вызовов
3. **TDD-guard** — любая чистая функция покрывается тестом; pre-commit хук не даёт сломать проект
4. **Минимум глобального состояния** — `bot_app` и `_BASE_URL` инициализируются один раз в `main()` и передаются через `init()` функции
5. **Явные импорты** — никаких `import *`; каждый модуль указывает что именно он берёт

---

## Документация проекта

| Файл | Для чего |
|------|----------|
| `CLAUDE.md` | Правила для Claude Code — читается автоматически каждую сессию |
| `PRODUCT.md` | Продуктовая логика: флоу, правила, UX, команды |
| `ARCHITECTURE.md` | Технический дизайн: модули, слои, roadmap рефакторинга |

**Правило:** при изменении продуктовой логики → обновить `PRODUCT.md`; при изменении структуры кода → обновить `ARCHITECTURE.md`.
