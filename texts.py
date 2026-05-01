from __future__ import annotations

_FEEDBACK_MAX_TEXT_LEN = 1000

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
        "free_dialog": "Я бот для задач — не умею отвечать на вопросы 🙂\n\nЕсли что-то непонятно или что-то пошло не так — напишите нам, разберёмся.",
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
        "btn_apple_cal_connected": "🍎 Apple Calendar — отключить",
        "btn_gcal_connected": "✅ Google Calendar — отключить",
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
        "btn_apple_cal_connect": "🍎 Подключить Apple Calendar",
        "btn_apple_cal_disconnect": "❌ Отключить подписку",
        "apple_cal_disconnected": (
            "✅ Подписка отключена на стороне бота.\n\n"
            "📱 *Чтобы полностью удалить её из приложения:*\n"
            "Настройки → Приложения → Календарь → Учётные записи → "
            "найди «Get My Task» → удали.\n\n"
            "Иначе Apple Calendar будет показывать ошибку при обновлении."
        ),
        "calendar_choose": "📅 Подключи календарь, чтобы задачи синхронизировались автоматически:",
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
        "reschedule_not_found": "⚠️ Не нашёл предстоящих задач по запросу *{query}*.",
        "reschedule_choose": "📋 Нашёл несколько задач. Какую переносим?",
        "reschedule_confirm": "📅 Перенести *{title}* на {date}?",
        "btn_reschedule_yes": "✅ Да, перенести",
        "btn_reschedule_no": "❌ Отмена",
        "reschedule_done": "✅ *{title}* перенесена на {date}",
        "reschedule_done_cal": "✅ *{title}* перенесена на {date} и обновлена в Google Calendar",
        "btn_reminder_done": "✅ Выполнено",
        "btn_reminder_reschedule": "📅 Перенести",
        "reminder_task_done": "✅ *{title}* отмечена как выполненная",
        "reminder_reschedule_prompt": "📅 Когда перенести *{title}*?",
        "reminder_tomorrow": "На завтра",
        "reminder_1h": "Через час",
        "reminder_3h": "Через 3 часа",
        "goal_all_done": "🏆 Все задачи по цели *{goal}* выполнены!\n\nЗакроем цель или добавим новые задачи?",
        "btn_goal_close": "🏁 Закрыть цель",
        "btn_goal_add_tasks": "➕ Добавить задачи",
        "goal_closed_done": "✅ Цель *{goal}* закрыта. Отличная работа!",
        "goal_add_tasks_prompt": "Опишите новые задачи для цели *{goal}* — голосом или текстом.",
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
        "goal_onboarding": (
            "🎯 *Как создать цель*\n\n"
            "Хорошая цель — это три составляющих:\n\n"
            "• *Что:* конкретный результат — _«запустить онлайн-курс»_\n"
            "• *Когда:* реальный дедлайн — _«до 1 сентября»_\n"
            "• *Критерий:* как поймёшь, что достиг — _«первые 10 оплат»_\n\n"
            "_Я задам уточняющие вопросы_ 👇"
        ),
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
        "goal_rename_hint": "✏️ Переименовать цель напрямую нельзя.\n\nУдали её через раздел *Цели* и создай новую с нужным названием.",
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
        "deletedata_warning": "⚠️ Это безвозвратно удалит все ваши данные: задачи, цели, настройки.\n\nВы уверены?",
        "deletedata_confirm": "🗑 Да, удалить всё",
        "deletedata_cancel": "❌ Отмена",
        "deletedata_done": "✅ Все ваши данные удалены. Используйте /start, чтобы зарегистрироваться снова.",
        "deletedata_cancelled": "❌ Удаление отменено.",
        # Weekly digest
        "weekly_intro": "Привет! Вот твоя неделя в цифрах 📊",
        "weekly_days": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
        "weekly_done": "Выполнено",
        "weekly_streak": "Стрик",
        "weekly_streak_days": "дн",
        "weekly_no_tasks": "На этой неделе задач не было. Начни с понедельника! 💪",
        "weekly_motivation": [
            "Новая неделя — новые возможности. Вперёд! 🎯",
            "Каждый шаг вперёд — уже победа. Так держать! 🚀",
            "Ты на верном пути. Продолжай! ⚡",
            "Постоянство — залог успеха! 💪",
            "Результаты приходят к тем, кто не останавливается. 🔥",
        ],
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
        "free_dialog": "I'm a task bot — I can't answer questions 🙂\n\nIf something is unclear or went wrong — write to us and we'll sort it out.",
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
        "btn_apple_cal_connected": "🍎 Apple Calendar — disconnect",
        "btn_gcal_connected": "✅ Google Calendar — disconnect",
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
        "btn_apple_cal_connect": "🍎 Connect Apple Calendar",
        "btn_apple_cal_disconnect": "❌ Disconnect subscription",
        "apple_cal_disconnected": (
            "✅ Subscription disconnected on the bot side.\n\n"
            "📱 *To fully remove it from the app:*\n"
            "Settings → Apps → Calendar → Accounts → "
            "find «Get My Task» → delete.\n\n"
            "Otherwise Apple Calendar will show an error when refreshing."
        ),
        "calendar_choose": "📅 Connect a calendar so tasks sync automatically:",
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
        "reschedule_not_found": "⚠️ No upcoming tasks found for *{query}*.",
        "reschedule_choose": "📋 Found several tasks. Which one to reschedule?",
        "reschedule_confirm": "📅 Move *{title}* to {date}?",
        "btn_reschedule_yes": "✅ Yes, move it",
        "btn_reschedule_no": "❌ Cancel",
        "reschedule_done": "✅ *{title}* moved to {date}",
        "reschedule_done_cal": "✅ *{title}* moved to {date} and updated in Google Calendar",
        "btn_reminder_done": "✅ Done",
        "btn_reminder_reschedule": "📅 Reschedule",
        "reminder_task_done": "✅ *{title}* marked as done",
        "reminder_reschedule_prompt": "📅 When to reschedule *{title}*?",
        "reminder_tomorrow": "Tomorrow",
        "reminder_1h": "In 1 hour",
        "reminder_3h": "In 3 hours",
        "goal_all_done": "🏆 All tasks for goal *{goal}* are done!\n\nClose the goal or add new tasks?",
        "btn_goal_close": "🏁 Close goal",
        "btn_goal_add_tasks": "➕ Add tasks",
        "goal_closed_done": "✅ Goal *{goal}* closed. Great work!",
        "goal_add_tasks_prompt": "Describe new tasks for goal *{goal}* — by text or voice.",
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
        "goal_onboarding": (
            "🎯 *How to create a goal*\n\n"
            "A good goal has three parts:\n\n"
            "• *What:* a specific result — _'launch an online course'_\n"
            "• *When:* a real deadline — _'by September 1st'_\n"
            "• *Criterion:* how you'll know you made it — _'first 10 payments'_\n\n"
            "_I'll ask you a couple of questions_ 👇"
        ),
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
        "goal_rename_hint": "✏️ Renaming a goal directly isn't supported.\n\nDelete it via *Goals* and create a new one with the desired name.",
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
        "deletedata_warning": "⚠️ This will permanently delete all your data: tasks, goals, and settings.\n\nAre you sure?",
        "deletedata_confirm": "🗑 Yes, delete everything",
        "deletedata_cancel": "❌ Cancel",
        "deletedata_done": "✅ All your data has been deleted. Use /start to register again.",
        "deletedata_cancelled": "❌ Deletion cancelled.",
        # Weekly digest
        "weekly_intro": "Hey! Here's your week in numbers 📊",
        "weekly_days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "weekly_done": "Done",
        "weekly_streak": "Streak",
        "weekly_streak_days": "d",
        "weekly_no_tasks": "No tasks this week. Start fresh on Monday! 💪",
        "weekly_motivation": [
            "New week — new opportunities. Let's go! 🎯",
            "Every step forward is already a win. Keep it up! 🚀",
            "You're on the right track. Keep going! ⚡",
            "Consistency is the key to success! 💪",
            "Results come to those who never stop. 🔥",
        ],
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
        "free_dialog": "Я бот для задач — не вмію відповідати на запитання 🙂\n\nЯкщо щось незрозуміло або пішло не так — напишіть нам, розберемось.",
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
        "btn_apple_cal_connected": "🍎 Apple Calendar — відключити",
        "btn_gcal_connected": "✅ Google Calendar — відключити",
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
        "btn_apple_cal_connect": "🍎 Підключити Apple Calendar",
        "btn_apple_cal_disconnect": "❌ Відключити підписку",
        "apple_cal_disconnected": (
            "✅ Підписку відключено на стороні бота.\n\n"
            "📱 *Щоб повністю видалити її з додатку:*\n"
            "Налаштування → Програми → Календар → Облікові записи → "
            "знайди «Get My Task» → видали.\n\n"
            "Інакше Apple Calendar показуватиме помилку при оновленні."
        ),
        "calendar_choose": "📅 Підключи календар, щоб задачі синхронізувалися автоматично:",
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
        "reschedule_not_found": "⚠️ Не знайшов майбутніх задач за запитом *{query}*.",
        "reschedule_choose": "📋 Знайшов кілька задач. Яку переносимо?",
        "reschedule_confirm": "📅 Перенести *{title}* на {date}?",
        "btn_reschedule_yes": "✅ Так, перенести",
        "btn_reschedule_no": "❌ Скасувати",
        "reschedule_done": "✅ *{title}* перенесено на {date}",
        "reschedule_done_cal": "✅ *{title}* перенесено на {date} і оновлено в Google Calendar",
        "btn_reminder_done": "✅ Виконано",
        "btn_reminder_reschedule": "📅 Перенести",
        "reminder_task_done": "✅ *{title}* позначено як виконану",
        "reminder_reschedule_prompt": "📅 Коли перенести *{title}*?",
        "reminder_tomorrow": "На завтра",
        "reminder_1h": "Через годину",
        "reminder_3h": "Через 3 години",
        "goal_all_done": "🏆 Усі задачі по цілі *{goal}* виконані!\n\nЗакрити ціль або додати нові задачі?",
        "btn_goal_close": "🏁 Закрити ціль",
        "btn_goal_add_tasks": "➕ Додати задачі",
        "goal_closed_done": "✅ Ціль *{goal}* закрита. Чудова робота!",
        "goal_add_tasks_prompt": "Опишіть нові задачі для цілі *{goal}* — голосом або текстом.",
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
        "goal_onboarding": (
            "🎯 *Як створити ціль*\n\n"
            "Хороша ціль — це три складові:\n\n"
            "• *Що:* конкретний результат — _«запустити онлайн-курс»_\n"
            "• *Коли:* реальний дедлайн — _«до 1 вересня»_\n"
            "• *Критерій:* як зрозумієш, що досяг — _«перші 10 оплат»_\n\n"
            "_Я поставлю уточнюючі запитання_ 👇"
        ),
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
        "goal_rename_hint": "✏️ Перейменувати ціль напряму не можна.\n\nВидали її через розділ *Цілі* і створи нову з потрібною назвою.",
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
        "deletedata_warning": "⚠️ Це безповоротно видалить усі ваші дані: задачі, цілі, налаштування.\n\nВи впевнені?",
        "deletedata_confirm": "🗑 Так, видалити все",
        "deletedata_cancel": "❌ Скасувати",
        "deletedata_done": "✅ Усі ваші дані видалені. Використайте /start для повторної реєстрації.",
        "deletedata_cancelled": "❌ Видалення скасовано.",
        # Weekly digest
        "weekly_intro": "Привіт! Ось твій тиждень у цифрах 📊",
        "weekly_days": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"],
        "weekly_done": "Виконано",
        "weekly_streak": "Стрік",
        "weekly_streak_days": "дн",
        "weekly_no_tasks": "Цього тижня задач не було. Починай з понеділка! 💪",
        "weekly_motivation": [
            "Новий тиждень — нові можливості. Вперед! 🎯",
            "Кожен крок вперед — вже перемога. Так тримати! 🚀",
            "Ти на правильному шляху. Продовжуй! ⚡",
            "Постійність — запорука успіху! 💪",
            "Результати приходять до тих, хто не зупиняється. 🔥",
        ],
    },
}

