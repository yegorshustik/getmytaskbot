"""
landing.py — Get My Task landing page.

Kept separate from bot.py so it survives refactors.
Imported by bot.py: from landing import get_home_html, FAVICON_ICO, FAVICON_PNG, LLMS_TXT, ROBOTS_TXT, SITEMAP_XML
"""
import base64 as _b64

# favicon.ico — generated with Pillow (purple bg + yellow bot face, 16/32/48/64px)
FAVICON_ICO: bytes = _b64.b64decode(
    "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"
)

# favicon.png — 192px PNG, works in Safari and all browsers
FAVICON_PNG: bytes = _b64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAMAAAADACAIAAADdvvtQAAAFi0lEQVR42u2d0VHsMAxFg8efdEEJ"
    "1LM/UBcl0Q0FvA9m3jAMm00cSdaVz/1kdoMsH8u24pWfbi9vG0KjargAARACIARACIAQAiAEQAiA"
    "0BLqhdv28fmcx5j31y8iEPTUsQeA9HqrJEMNerANgJR6qBhD7MIQACEAQgCEAEhf+fN1xTKKBSNQ"
    "5h6ql4+uOYXl7KeSbzPKroGy9VbVd2GVX6aO9dnDRF9VFIhACIAQACEAQgiAEAAhAEIAhBAAIQBC"
    "AIQACCEAQgCEAAgBEAIghAAIARACIARACAEQAiAEQAiAENoq/DI1VVm4SGPy/wq2Q4zQyEnIU4cb"
    "RZ7ykNRBR5ekDBh10AEjVYBApwBGDXqosK4HEPSU8WoHHaYzmQgEPfX83CVatWxZwmGnfXw+xzjt"
    "6fbyltYRlLPM78AIgM42Hm6EnOkO0KkGg46cVxuluDfKqKeNQAcHCujoerhBzwqhyG9j36AHhlTX"
    "QNBTwJNtVviBnniGPIJQI/YQh7ZUrzLCXsTs/KO0gE632fwVR5cbKEcAzXZ2OMzm99ev4DfWxnkg"
    "19vahl0zEaMpNkfembfE78KmHPpUtDn7ItrpDsqEp2Tm2hyJXc+8fHZ6oKt/JWw2XEp36WnrTy88"
    "/KLfYStFmxMtove9cKr9Jo8ytEfR5pjm98K5su8PTz+IrWizNkD33PerJw4m5e6lRmwnhYM2X0zn"
    "JJzIzKYwq4D553POrhuOf96kP9I+OWAWo8AUKgSQ31Ae3v6UtHmhEne2U37MAkLR5goAzRpYV/6v"
    "n837T84ThNpqB1y8B7Th2jlhPTIW0ZvWm+OPz+fkOSGBEncDHjyblRnLr3h07b30T9qcUFvwgKbc"
    "k99fv9LOYkxhq2QxAAh6AAiVK70FQPP5sH0RC0A16blHiTQ9ABRN0i9c1OlJDdCstwS2T975yyl6"
    "0i6Sep6sz0D2zyofY3vs66GFOznA45YkiVJMYXNyoaKbdjGAwt4VuN7wdRCLs7QBUJbxd/G36FOa"
    "lidWtaUybDFDeWB6Eg0/6QBy3YA4LTtOHeD/88PSSyUW0XMGyX+Y1GttNYmdy8VzVfe+7n30/WFi"
    "Yj/2SOzUes4xeuQI1cUfC5sffTc89iWUoe6F78NKsvxUtFkeoP0k7/5p81k1YhVtrhyBjpT7y1Z/"
    "SdHmylOYeamKgG5QtLn4Nt51r4TNSyyiLw7rKd2gaHPxXdhAl0zvBkWbK2/jf/pXqFK9os1lAZL2"
    "eL1LQngXhgAIARACIARACAEQAiAEQAiAEAIgBEAIgBAAIQRACIAQACEAQgiAEAAhAEIAhAAIIQBC"
    "AIQACAEQQgCEAAhtFFfYhuu91StFUM9RRCDEbT1cyVsAoP0oWuBux02t5lDMrNcrVRYn9qw4hR2B"
    "4+JdGTVu6M0ZwpvQYFoEI5NmhjmqyVUOLIzR2aZlmNl7cKF/q+/+/LD0CmlKIWlDj/VgZ+2YPsyf"
    "HEzXI+jYnrd+md8rMeye76YjZd6dqQbJ0+3lLdhfB7ddWlWb8xhs4v/UEejIJX7XQ1G9THeegee7"
    "CzO8qIY8tbkrzF3aki8LFsfoVPOnBFT7NZDfHY5LJaM9nOMxFPvc7cmpJh2582Y1bqY7xCsCHW/V"
    "lWFRhqQAJzitBBwBCm6bHEyRrfZbR/oCdHa9XH5/PqWNrruQnirB77RZnciTU+flGSHuEWigtZH7"
    "dpOeyGywt20RAA33E4nE/A4MAujiWOdIa1qnxQHEryxK3u7buLMYepR2Yd9tIxSVGaKN69OhR/JQ"
    "PQzV8Gef3mamM+mh2JO0H4xEo3hP5QswklsA9Jx+gSSVhWOX8NSyPOXfanT8iKhQhgAIARACIIQA"
    "CAEQAiAEQAgBEAIgBEAIgBACIARACIAQACG0bdv2D3SnRZPhIeecAAAAAElFTkSuQmCC"
)

_ICON_SVG = """<svg id="hero-icon" viewBox="0 0 501.5 500.3" xmlns="http://www.w3.org/2000/svg">
<rect fill="#5D2362" width="501.5" height="500.3"/>
<rect x="239.3" y="81.1" fill="#FAF06E" width="22" height="44"/>
<rect x="217.1" y="81.1" fill="#FAF06E" width="66" height="22"/>
<circle fill="#FAF06E" cx="218.1" cy="92.1" r="11"/>
<circle fill="#FAF06E" cx="283.4" cy="92.1" r="11"/>
<path fill-rule="evenodd" clip-rule="evenodd" fill="#FAF06E" d="M406.7,250.7c-0.1-0.8-0.2-1.6-0.5-2.3l-33-87.9
  c-7.9-21.3-28.3-35.4-51-35.4L179.3,125c-22.7,0-43,14.1-51,35.4l-33,87.9c-0.3,0.7-0.5,1.5-0.6,2.3
  c0,0.5-0.1,1-0.1,1.5v72.7c0,30,24.3,54.4,54.4,54.4h203.5c30,0,54.4-24.3,54.4-54.4v-72.6
  C406.9,251.7,406.8,251.2,406.7,250.7z M148.6,168.1c4.8-12.7,17-21.2,30.6-21.2h143.1
  c13.6,0,25.8,8.4,30.6,21.2l27.2,73.3h-73.3c-5,0-9.3,3.4-10.5,8.2c-6.5,25.2-32.3,40.4-57.5,33.9
  c-16.6-4.3-29.6-17.3-33.9-33.9c-1.2-4.8-5.5-8.2-10.5-8.2h-73.3L148.6,168.1z M385,324.8
  c0,16.8-12.6,30.8-29.3,32.5l-3.4,0.2H149c-18,0-32.7-14.7-32.7-32.7V263h70.2
  c14.1,35.5,54.2,52.8,89.7,38.7c17.7-7,31.7-21,38.7-38.7H385V324.8z"/>
<!-- Right eye: default=checkmark, alt=plus -->
<circle fill="#FAF06E" cx="291.6" cy="195.1" r="31.7"/>
<polygon id="eye-right-check" fill="#5D2362" points="303.6,179.1 287.7,195.1 279.6,187 271.6,195 279.7,203.1 279.6,203.1 287.6,211.1 311.6,187.1"/>
<polygon id="eye-right-plus" fill="#5D2362" style="display:none" points="310.2,189.4 297.2,189.4 297.2,176.5 286.0,176.5 286.0,189.4 273.0,189.4 273.0,200.7 286.0,200.7 286.0,213.7 297.2,213.7 297.2,200.7 310.2,200.7"/>
<!-- Left eye: default=plus, alt=checkmark -->
<circle fill="#FAF06E" cx="209.9" cy="195.1" r="31.7"/>
<polygon id="eye-left-plus" fill="#5D2362" points="228.5,189.4 215.5,189.4 215.5,176.5 204.3,176.5 204.3,189.4 191.3,189.4
  191.3,200.7 204.3,200.7 204.3,213.7 215.5,213.7 215.5,200.7 228.5,200.7"/>
<polygon id="eye-left-check" fill="#5D2362" style="display:none" points="221.9,179.1 206.0,195.1 197.9,187 189.9,195 198.0,203.1 197.9,203.1 205.9,211.1 229.9,187.1"/>
</svg>"""

# ── Copy ─────────────────────────────────────────────────────────────────────

_C = {
    "ru": {
        "lang_html": "ru",
        "tagline": "AI-менеджер задач и целей",
        "desc": "Голосовые сообщения и текст → задачи, цели и синхронизация с Google Calendar",
        "cta": "Попробовать бесплатно →",
        "social_proof": "Уже {n} пользователей управляют задачами",

        "for_whom_title": "Для кого",
        "personas": [
            ("🚀", "Предприниматели", "Фиксируй идеи голосом за рулём — бот сразу превратит их в задачи с датами"),
            ("📋", "Менеджеры", "Управляй проектами и целями прямо в Telegram без переключения между приложениями"),
            ("💻", "Фрилансеры", "Планируй дедлайны и синхронизируй задачи с Google Calendar одним нажатием"),
            ("🎯", "Все, кто ставит цели", "Создавай SMART-цели, декомпозируй на задачи и отслеживай прогресс"),
        ],

        "problems_title": "Какие проблемы решает",
        "problems": [
            ("😤", "Идеи теряются", "Пришла мысль — надиктовал голосовое. Бот сам выделит задачи, расставит приоритеты и предложит дату."),
            ("😵", "Задачи разбросаны по мессенджерам", "Всё в одном месте: задачи, цели, напоминания и Google Calendar — прямо в Telegram."),
            ("😓", "Нет системы приоритетов", "Матрица Эйзенхауэра автоматически делит задачи на важные/срочные — ты видишь, что делать сейчас, а что подождёт."),
        ],

        "features_title": "Возможности",
        "features": [
            ("🎙", "Голосовой ввод", "Надиктуй список дел — Whisper AI транскрибирует и выделит каждую задачу отдельно"),
            ("📊", "Матрица Эйзенхауэра", "Q1–Q4 автоматически: важно/срочно, важно/не срочно, не важно/срочно, остальное"),
            ("📅", "Google Calendar", "Добавляй задачи в календарь одним нажатием, с временем и напоминанием"),
            ("🔔", "Умные напоминания", "Утренний дайджест задач на день + уведомление за N минут до начала"),
            ("🎯", "Цели (SMART)", "Ставь цели с дедлайном и критериями, связывай с задачами, отслеживай прогресс"),
            ("🔁", "Повторяющиеся задачи", "Ежедневные и еженедельные задачи из Google Calendar в утреннем дайджесте"),
            ("📅", "Перенос задач", "Перенеси задачу голосом или текстом — бот найдёт её и обновит в Calendar"),
            ("🌐", "Три языка", "Русский, английский, украинский — бот отвечает на твоём языке"),
        ],

        "facts_title": "В цифрах",
        "facts": [
            ("3", "языка интерфейса"),
            ("4", "квадранта приоритетов"),
            ("1", "нажатие до Google Calendar"),
            ("0", "лишних приложений"),
        ],

        "faq_title": "Частые вопросы",
        "faq": [
            ("Что такое Get My Task и чем он отличается от обычных планировщиков?",
             "Get My Task — AI-менеджер задач и целей прямо в Telegram. В отличие от отдельных приложений, тебе не нужно переключаться между сервисами: пишешь или диктуешь боту, он сам разбирает задачи, расставляет приоритеты по матрице Эйзенхауэра и синхронизирует с Google Calendar."),
            ("Как добавить задачу голосом в Telegram через Get My Task?",
             "Отправь голосовое сообщение боту @getmytask_bot — например: «Позвонить Максиму в пятницу в 11:00 и сдать отчёт до понедельника». Бот распознает речь через Whisper AI, разберёт каждую задачу отдельно, определит дату и присвоит приоритет. Никакой ручной работы."),
            ("Как Get My Task помогает не забывать о важных делах?",
             "Каждое утро бот присылает дайджест — список всех задач на сегодня с временем и приоритетами. За 30 минут до начала задачи приходит напоминание прямо в Telegram. Можно отметить выполненным или перенести одним нажатием — не выходя из чата."),
            ("Можно ли поставить цель и разбить её на задачи в боте?",
             "Да. В Get My Task есть отдельный режим целей: задаёшь цель с дедлайном и критерием успеха — например «Запустить сайт до 1 июня». Затем добавляешь связанные задачи. Бот показывает прогресс и уведомляет, когда все задачи по цели выполнены."),
            ("Get My Task синхронизируется с Google Calendar?",
             "Да. Подключи Google Calendar в настройках бота за 30 секунд — и любую задачу с датой и временем можно добавить в календарь одним нажатием. Если перенести задачу командой боту, дата в Google Calendar тоже обновится автоматически."),
            ("Как работает приоритизация задач по матрице Эйзенхауэра?",
             "Каждая задача автоматически попадает в один из 4 квадрантов: Q1 (важно и срочно — делай сейчас), Q2 (важно, не срочно — запланируй), Q3 (срочно, не важно — делегируй), Q4 (не важно и не срочно — удали). AI определяет квадрант по контексту задачи — тебе ничего не нужно настраивать вручную."),
            ("Можно ли перенести задачу голосом или текстом?",
             "Да. Напиши или надиктуй: «Перенеси встречу с Андреем на следующую среду в 14:00». Бот найдёт задачу, обновит дату в своей базе и синхронизирует изменение с Google Calendar, если задача там есть."),
            ("Get My Task бесплатный?",
             "Да, полностью бесплатный. Голосовой ввод, матрица Эйзенхауэра, цели, Google Calendar, напоминания и утренний дайджест — всё доступно без подписок и скрытых платежей."),
            ("Get My Task работает на iPhone и Android?",
             "Да. Бот работает через Telegram — он есть на iOS, Android, macOS, Windows и в браузере. Отдельное приложение устанавливать не нужно: всё управление происходит прямо в чате с ботом."),
            ("Насколько безопасно хранить задачи в Get My Task?",
             "Задачи хранятся на защищённом сервере и не передаются третьим лицам. Токен Google OAuth хранится в зашифрованном виде и удаляется сразу при отключении календаря. Бот не читает содержимое твоих событий Google Calendar — только добавляет и обновляет задачи, которые ты сам создал."),
        ],

        "footer_privacy": "Политика конфиденциальности",
        "footer_contact": "Написать нам",
        "schema_desc": "Get My Task — AI-бот для Telegram, который превращает голосовые сообщения и текст в структурированные задачи с приоритетами, датами и синхронизацией с Google Calendar.",
    },

    "en": {
        "lang_html": "en",
        "tagline": "AI Task & Goal Manager",
        "desc": "Voice notes and texts → tasks, goals & Google Calendar sync",
        "cta": "Try for free →",
        "social_proof": "Join {n} people managing their tasks",

        "for_whom_title": "Who it's for",
        "personas": [
            ("🚀", "Entrepreneurs", "Capture ideas by voice while driving — the bot instantly turns them into dated tasks"),
            ("📋", "Managers", "Manage projects and goals right inside Telegram without switching apps"),
            ("💻", "Freelancers", "Plan deadlines and sync tasks with Google Calendar in one tap"),
            ("🎯", "Goal setters", "Create SMART goals, break them into tasks, and track progress automatically"),
        ],

        "problems_title": "Problems it solves",
        "problems": [
            ("😤", "Ideas get lost", "Had a thought? Dictate a voice note. The bot extracts tasks, sets priorities and suggests a date."),
            ("😵", "Tasks scattered across apps", "Everything in one place: tasks, goals, reminders and Google Calendar — right inside Telegram."),
            ("😓", "No priority system", "The Eisenhower Matrix automatically sorts tasks by importance and urgency — you always know what to do next."),
        ],

        "features_title": "Features",
        "features": [
            ("🎙", "Voice input", "Dictate a to-do list — Whisper AI transcribes and extracts each task separately"),
            ("📊", "Eisenhower Matrix", "Q1–Q4 automatically: urgent/important, not urgent/important, urgent/not important, the rest"),
            ("📅", "Google Calendar", "Add tasks to your calendar in one tap, with time and reminder"),
            ("🔔", "Smart reminders", "Morning digest of today's tasks + notification N minutes before each task starts"),
            ("🎯", "SMART Goals", "Set goals with deadlines and criteria, link tasks to them, track progress"),
            ("🔁", "Recurring tasks", "Daily and weekly tasks from Google Calendar appear in your morning digest"),
            ("📅", "Reschedule tasks", "Move a task by voice or text — the bot finds it and updates it in Calendar"),
            ("🌐", "Three languages", "Russian, English, Ukrainian — the bot replies in your language"),
        ],

        "facts_title": "By the numbers",
        "facts": [
            ("3", "interface languages"),
            ("4", "priority quadrants"),
            ("1", "tap to Google Calendar"),
            ("0", "extra apps needed"),
        ],

        "faq_title": "FAQ",
        "faq": [
            ("What is Get My Task and how is it different from other task managers?",
             "Get My Task is an AI task and goal manager built directly inside Telegram. Unlike standalone apps, there's nothing to install — you write or dictate to the bot, it extracts tasks, prioritises them using the Eisenhower Matrix, and syncs with Google Calendar automatically."),
            ("How do I add a task by voice in Telegram with Get My Task?",
             "Send a voice message to @getmytask_bot — for example: 'Call Max on Friday at 11am and submit the report by Monday.' Whisper AI transcribes your message, splits it into individual tasks, detects dates, and assigns a priority quadrant. No manual input needed."),
            ("How does Get My Task help me remember important things?",
             "Every morning the bot sends a digest — all of today's tasks with times and priorities. Before each task starts, you get a reminder right in Telegram. You can mark it done or reschedule with one tap, without leaving the chat."),
            ("Can I set a goal and break it down into tasks?",
             "Yes. Get My Task has a dedicated goals mode: set a goal with a deadline and success criteria — e.g. 'Launch the website by June 1.' Then add linked tasks. The bot tracks progress and notifies you when all tasks under a goal are completed."),
            ("Does Get My Task sync with Google Calendar?",
             "Yes. Connect Google Calendar in bot settings in 30 seconds — then any task with a date and time can be added to your calendar in one tap. If you reschedule a task via the bot, the Google Calendar event updates automatically too."),
            ("How does the Eisenhower Matrix prioritisation work?",
             "Every task is automatically placed in one of 4 quadrants: Q1 (urgent & important — do now), Q2 (important, not urgent — schedule), Q3 (urgent, not important — delegate), Q4 (neither — drop). The AI infers the quadrant from the task context — you don't configure anything manually."),
            ("Can I reschedule a task by voice or text?",
             "Yes. Write or dictate: 'Move the meeting with Anna to next Wednesday at 2pm.' The bot finds the task, updates the date in its database, and syncs the change to Google Calendar if the task is linked there."),
            ("Is Get My Task free?",
             "Yes, completely free. Voice input, Eisenhower Matrix, goals, Google Calendar sync, reminders, and the morning digest — all features are available with no subscription or hidden fees."),
            ("Does Get My Task work on iPhone and Android?",
             "Yes. The bot runs inside Telegram, which is available on iOS, Android, macOS, Windows, and the web. No separate app to install — everything happens in a chat with the bot."),
            ("How safe is it to store tasks in Get My Task?",
             "Tasks are stored on a secure server and never shared with third parties or used for advertising. Your Google OAuth token is stored encrypted and deleted immediately when you disconnect the calendar. The bot only adds and updates tasks you explicitly created — it does not read your other Calendar events."),
        ],

        "footer_privacy": "Privacy Policy",
        "footer_contact": "Contact us",
        "schema_desc": "Get My Task is an AI Telegram bot that turns voice messages and text into structured tasks with priorities, dates and Google Calendar sync.",
    },

    "uk": {
        "lang_html": "uk",
        "tagline": "AI-менеджер задач і цілей",
        "desc": "Голосові повідомлення і текст → задачі, цілі та синхронізація з Google Calendar",
        "cta": "Спробувати безкоштовно →",
        "social_proof": "Вже {n} користувачів керують завданнями",

        "for_whom_title": "Для кого",
        "personas": [
            ("🚀", "Підприємці", "Фіксуй ідеї голосом за кермом — бот одразу перетворить їх на задачі з датами"),
            ("📋", "Менеджери", "Керуй проектами і цілями прямо в Telegram без перемикання між застосунками"),
            ("💻", "Фрілансери", "Плануй дедлайни і синхронізуй задачі з Google Calendar одним натисканням"),
            ("🎯", "Всі, хто ставить цілі", "Створюй SMART-цілі, розбивай на задачі та відстежуй прогрес"),
        ],

        "problems_title": "Які проблеми вирішує",
        "problems": [
            ("😤", "Ідеї губляться", "Прийшла думка — надиктував голосове. Бот сам виділить задачі, розставить пріоритети і запропонує дату."),
            ("😵", "Задачі розкидані по месенджерах", "Все в одному місці: задачі, цілі, нагадування і Google Calendar — прямо в Telegram."),
            ("😓", "Немає системи пріоритетів", "Матриця Ейзенхауера автоматично ділить задачі на важливі/термінові — ти бачиш, що робити зараз, а що зачекає."),
        ],

        "features_title": "Можливості",
        "features": [
            ("🎙", "Голосове введення", "Надиктуй список справ — Whisper AI транскрибує і виділить кожну задачу окремо"),
            ("📊", "Матриця Ейзенхауера", "Q1–Q4 автоматично: важливо/терміново, важливо/не терміново, не важливо/терміново, решта"),
            ("📅", "Google Calendar", "Додавай задачі в календар одним натисканням, з часом і нагадуванням"),
            ("🔔", "Розумні нагадування", "Ранковий дайджест задач на день + сповіщення за N хвилин до початку"),
            ("🎯", "Цілі (SMART)", "Став цілі з дедлайном і критеріями, пов'язуй із задачами, відстежуй прогрес"),
            ("🔁", "Повторювані задачі", "Щоденні та щотижневі задачі з Google Calendar у ранковому дайджесті"),
            ("📅", "Перенесення задач", "Перенеси задачу голосом або текстом — бот знайде її й оновить у Calendar"),
            ("🌐", "Три мови", "Російська, англійська, українська — бот відповідає твоєю мовою"),
        ],

        "facts_title": "У цифрах",
        "facts": [
            ("3", "мови інтерфейсу"),
            ("4", "квадранти пріоритетів"),
            ("1", "натискання до Google Calendar"),
            ("0", "зайвих застосунків"),
        ],

        "faq_title": "Часті запитання",
        "faq": [
            ("Що таке Get My Task і чим він відрізняється від звичайних планувальників?",
             "Get My Task — AI-менеджер задач і цілей прямо в Telegram. На відміну від окремих застосунків, нічого встановлювати не потрібно: пишеш або диктуєш боту, він розбирає задачі, розставляє пріоритети за матрицею Ейзенхауера і синхронізує з Google Calendar."),
            ("Як додати задачу голосом у Telegram через Get My Task?",
             "Відправ голосове повідомлення боту @getmytask_bot — наприклад: «Зателефонувати Максиму в п'ятницю о 11:00 і здати звіт до понеділка». Whisper AI розпізнає мовлення, розбере кожну задачу окремо, визначить дати й призначить пріоритетний квадрант. Жодної ручної роботи."),
            ("Як Get My Task допомагає не забувати про важливі справи?",
             "Щоранку бот надсилає дайджест — список усіх задач на сьогодні з часом і пріоритетами. За 30 хвилин до початку задачі приходить нагадування прямо в Telegram. Можна відмітити виконаним або перенести одним натисканням, не виходячи з чату."),
            ("Чи можна поставити ціль і розбити її на задачі у боті?",
             "Так. У Get My Task є окремий режим цілей: задаєш ціль із дедлайном і критерієм успіху — наприклад «Запустити сайт до 1 червня». Потім додаєш пов'язані задачі. Бот показує прогрес і сповіщає, коли всі задачі по цілі виконані."),
            ("Get My Task синхронізується з Google Calendar?",
             "Так. Підключи Google Calendar у налаштуваннях бота за 30 секунд — і будь-яку задачу з датою і часом можна додати в календар одним натисканням. Якщо перенести задачу командою боту, дата в Google Calendar теж оновиться автоматично."),
            ("Як працює пріоритизація задач за матрицею Ейзенхауера?",
             "Кожна задача автоматично потрапляє в один із 4 квадрантів: Q1 (важливо і терміново — роби зараз), Q2 (важливо, не терміново — сплануй), Q3 (терміново, не важливо — делегуй), Q4 (не важливо і не терміново — видали). AI визначає квадрант за контекстом задачі — нічого налаштовувати вручну не потрібно."),
            ("Чи можна перенести задачу голосом або текстом?",
             "Так. Напиши або надиктуй: «Перенеси зустріч з Оленою на наступну середу о 14:00». Бот знайде задачу, оновить дату у своїй базі й синхронізує зміну з Google Calendar, якщо задача там є."),
            ("Get My Task безкоштовний?",
             "Так, повністю безкоштовний. Голосове введення, матриця Ейзенхауера, цілі, Google Calendar, нагадування і ранковий дайджест — всі функції доступні без підписок і прихованих платежів."),
            ("Get My Task працює на iPhone та Android?",
             "Так. Бот працює через Telegram — він є на iOS, Android, macOS, Windows і в браузері. Окремий застосунок встановлювати не потрібно: все управління відбувається прямо в чаті з ботом."),
            ("Наскільки безпечно зберігати задачі в Get My Task?",
             "Задачі зберігаються на захищеному сервері і не передаються третім особам. Токен Google OAuth зберігається в зашифрованому вигляді і видаляється одразу при відключенні календаря. Бот не читає вміст твоїх подій Google Calendar — лише додає й оновлює задачі, які ти сам створив."),
        ],

        "footer_privacy": "Політика конфіденційності",
        "footer_contact": "Написати нам",
        "schema_desc": "Get My Task — AI-бот для Telegram, який перетворює голосові повідомлення і текст на структуровані задачі з пріоритетами, датами та синхронізацією з Google Calendar.",
    },
}

_BASE_URL = "https://getmytask.synergize.digital"

# ── Builders ─────────────────────────────────────────────────────────────────

def _personas_html(c):
    parts = []
    for icon, title, text in c["personas"]:
        parts.append(
            f'<div class="card persona">'
            f'<div class="card-icon">{icon}</div>'
            f'<strong>{title}</strong>'
            f'<p>{text}</p>'
            f'</div>'
        )
    return "".join(parts)


def _problems_html(c):
    parts = []
    for icon, title, text in c["problems"]:
        parts.append(
            f'<div class="problem">'
            f'<div class="prob-icon">{icon}</div>'
            f'<div><strong>{title}</strong><p>{text}</p></div>'
            f'</div>'
        )
    return "".join(parts)


def _features_html(c):
    parts = []
    for icon, title, text in c["features"]:
        parts.append(
            f'<div class="card feat">'
            f'<div class="card-icon">{icon}</div>'
            f'<strong>{title}</strong>'
            f'<p>{text}</p>'
            f'</div>'
        )
    return "".join(parts)


def _facts_html(c):
    parts = []
    for num, label in c["facts"]:
        parts.append(
            f'<div class="fact">'
            f'<span class="fact-num">{num}</span>'
            f'<span class="fact-label">{label}</span>'
            f'</div>'
        )
    return "".join(parts)


def _faq_html(c):
    parts = []
    for i, (q, a) in enumerate(c["faq"]):
        parts.append(
            f'<details class="faq-item">'
            f'<summary>{q}</summary>'
            f'<p>{a}</p>'
            f'</details>'
        )
    return "".join(parts)


def _schema_json(c, lang):
    import json as _json
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "SoftwareApplication",
                "name": "Get My Task",
                "applicationCategory": "ProductivityApplication",
                "operatingSystem": "Telegram",
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
                "url": _BASE_URL,
                "description": c["schema_desc"],
                "inLanguage": ["ru", "en", "uk"],
                "featureList": [feat[1] for feat in c["features"]],
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a},
                    }
                    for q, a in c["faq"]
                ],
            },
        ],
    }
    return _json.dumps(schema, ensure_ascii=False, separators=(",", ":"))


# ── CSS (shared) ─────────────────────────────────────────────────────────────

_CSS = """
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg:       #0e0b14;
      --surface:  #17112a;
      --border:   #2a1f45;
      --purple:   #5D2362;
      --purple-l: #7a2f80;
      --yellow:   #FAF06E;
      --white:    #f0eaff;
      --muted:    #8a7fa8;
      --text:     #c4b8e0;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg);
      color: var(--white);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 40px 20px 80px;
    }
    .wrap { width: 100%; max-width: 680px; }

    /* Lang switcher */
    .lang-bar {
      display: flex; gap: 6px; margin-bottom: 48px;
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 999px; padding: 4px; align-self: center;
    }
    .lang-bar a {
      padding: 6px 18px; border-radius: 999px; font-size: .85rem;
      font-weight: 600; color: var(--muted); text-decoration: none;
      transition: background .15s, color .15s;
    }
    .lang-bar a.active, .lang-bar a:hover {
      background: var(--purple); color: var(--yellow);
    }

    /* Hero */
    .hero { text-align: center; margin-bottom: 64px; }
    .icon-wrap {
      width: 96px; height: 96px; border-radius: 24px; overflow: hidden;
      margin: 0 auto 24px;
      box-shadow: 0 8px 32px rgba(93,35,98,.6);
    }
    .icon-wrap svg { width: 100%; height: 100%; display: block; }
    h1 { font-size: 2.8rem; font-weight: 800; letter-spacing: -.5px; color: #fff; margin-bottom: 8px; }
    .tagline { font-size: 1.1rem; font-weight: 600; color: var(--yellow); margin-bottom: 14px; }
    .desc { font-size: 1rem; color: var(--muted); line-height: 1.65; margin-bottom: 32px; }
    .btn {
      display: inline-block; background: var(--purple); color: var(--yellow);
      font-size: 1rem; font-weight: 700; padding: 14px 36px;
      border-radius: 14px; text-decoration: none; letter-spacing: .3px;
      box-shadow: 0 4px 20px rgba(93,35,98,.5);
      transition: background .15s, transform .1s;
    }
    .btn:hover { background: var(--purple-l); transform: translateY(-1px); }
    .social-proof { margin-top: 14px; font-size: .88rem; color: var(--muted); opacity: .8; }

    /* Section titles */
    .section { margin-bottom: 56px; }
    .section-title {
      font-size: 1.3rem; font-weight: 700; color: #fff;
      margin-bottom: 24px; letter-spacing: -.2px;
    }

    /* Cards grid */
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
    @media (max-width: 560px) {
      .grid-2 { grid-template-columns: 1fr; }
      .grid-4 { grid-template-columns: 1fr 1fr; }
      h1 { font-size: 2rem; }
    }
    .card {
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 16px; padding: 20px 18px;
    }
    .card-icon { font-size: 1.6rem; margin-bottom: 10px; }
    .card strong { display: block; color: var(--white); margin-bottom: 6px; font-size: .95rem; }
    .card p { color: var(--text); font-size: .87rem; line-height: 1.5; }

    /* Problems */
    .problems { display: flex; flex-direction: column; gap: 12px; }
    .problem {
      display: flex; gap: 16px; align-items: flex-start;
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 16px; padding: 20px 18px;
    }
    .prob-icon { font-size: 1.8rem; flex-shrink: 0; }
    .problem strong { display: block; color: var(--white); margin-bottom: 4px; }
    .problem p { color: var(--text); font-size: .9rem; line-height: 1.5; }

    /* Facts strip */
    .facts-strip {
      display: grid; grid-template-columns: repeat(4, 1fr);
      gap: 12px; margin-bottom: 56px;
    }
    @media (max-width: 560px) { .facts-strip { grid-template-columns: 1fr 1fr; } }
    .fact {
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 16px; padding: 20px 12px;
      text-align: center;
    }
    .fact-num { display: block; font-size: 2.4rem; font-weight: 800; color: var(--yellow); line-height: 1; }
    .fact-label { display: block; font-size: .8rem; color: var(--muted); margin-top: 6px; line-height: 1.3; }

    /* FAQ */
    .faq-list { display: flex; flex-direction: column; gap: 8px; }
    .faq-item {
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 14px; overflow: hidden;
    }
    .faq-item summary {
      padding: 16px 20px; cursor: pointer; font-weight: 600;
      color: var(--white); font-size: .95rem; list-style: none;
      display: flex; justify-content: space-between; align-items: center;
      user-select: none;
    }
    .faq-item summary::after { content: "+"; font-size: 1.2rem; color: var(--yellow); flex-shrink: 0; margin-left: 12px; }
    .faq-item[open] summary::after { content: "−"; }
    .faq-item p { padding: 0 20px 16px; color: var(--text); font-size: .9rem; line-height: 1.6; }

    /* Footer */
    footer {
      margin-top: 64px; font-size: .82rem; color: var(--muted); text-align: center;
      border-top: 1px solid var(--border); padding-top: 32px; width: 100%; max-width: 680px;
    }
    .footer-links { display: flex; justify-content: center; gap: 24px; flex-wrap: wrap; margin-bottom: 16px; }
    footer a { color: var(--muted); text-decoration: none; transition: color .15s; }
    footer a:hover { color: var(--yellow); }
    .footer-copy { color: #4a4060; font-size: .78rem; }
"""


# ── Page builder ─────────────────────────────────────────────────────────────

def _page(lang: str, user_count: int = 0) -> str:
    from datetime import datetime as _dt
    c = _C[lang]
    year = _dt.now().year
    alt = {"ru": "en", "en": "uk", "uk": "ru"}
    active = {l: ' class="active"' if l == lang else "" for l in ("ru", "en", "uk")}

    hreflang_tags = "\n".join(
        f'  <link rel="alternate" hreflang="{l}" href="{_BASE_URL}/?lang={l}"/>'
        for l in ("ru", "en", "uk")
    )

    return f"""<!DOCTYPE html>
<html lang="{c['lang_html']}">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Get My Task — {c['tagline']}</title>
  <meta name="description" content="{c['schema_desc']}"/>
  <meta name="robots" content="index, follow"/>
  <link rel="canonical" href="{_BASE_URL}/?lang={lang}"/>
{hreflang_tags}

  <!-- Open Graph -->
  <meta property="og:type" content="website"/>
  <meta property="og:url" content="{_BASE_URL}/?lang={lang}"/>
  <meta property="og:title" content="Get My Task — {c['tagline']}"/>
  <meta property="og:description" content="{c['desc']}"/>
  <meta property="og:site_name" content="Get My Task"/>

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary"/>
  <meta name="twitter:title" content="Get My Task — {c['tagline']}"/>
  <meta name="twitter:description" content="{c['desc']}"/>
  <link rel="icon" type="image/png" href="/favicon.png"/>
  <link rel="icon" type="image/x-icon" href="/favicon.ico"/>

  <!-- Schema.org JSON-LD -->
  <script type="application/ld+json">{_schema_json(c, lang)}</script>

  <style>{_CSS}</style>
</head>
<body>

  <nav class="lang-bar">
    <a href="/?lang=ru"{active['ru']}>RU</a>
    <a href="/?lang=en"{active['en']}>EN</a>
    <a href="/?lang=uk"{active['uk']}>UK</a>
  </nav>

  <div class="wrap">

    <!-- Hero -->
    <section class="hero">
      <div class="icon-wrap">{_ICON_SVG}</div>
      <h1>Get My Task</h1>
      <p class="tagline">{c['tagline']}</p>
      <p class="desc">{c['desc']}</p>
      <a class="btn" href="https://t.me/getmytask_bot" rel="noopener">{c['cta']}</a>
      {f'<p class="social-proof">{c["social_proof"].format(n=user_count)}</p>' if user_count > 0 else ''}
    </section>

    <!-- For whom -->
    <section class="section" aria-labelledby="for-whom">
      <h2 class="section-title" id="for-whom">{c['for_whom_title']}</h2>
      <div class="grid-2">{_personas_html(c)}</div>
    </section>

    <!-- Problems -->
    <section class="section" aria-labelledby="problems">
      <h2 class="section-title" id="problems">{c['problems_title']}</h2>
      <div class="problems">{_problems_html(c)}</div>
    </section>

    <!-- Features -->
    <section class="section" aria-labelledby="features">
      <h2 class="section-title" id="features">{c['features_title']}</h2>
      <div class="grid-2">{_features_html(c)}</div>
    </section>

    <!-- FAQ -->
    <section class="section" aria-labelledby="faq">
      <h2 class="section-title" id="faq">{c['faq_title']}</h2>
      <div class="faq-list">{_faq_html(c)}</div>
    </section>

    <!-- CTA repeat -->
    <div style="text-align:center;margin-bottom:8px;">
      <a class="btn" href="https://t.me/getmytask_bot" rel="noopener">{c['cta']}</a>
    </div>

  </div>

  <footer>
    <div class="footer-links">
      <a href="/privacy">{c['footer_privacy']}</a>
    </div>
    <div class="footer-copy">© {year} Get My Task. All rights reserved.</div>
  </footer>

<script>
(function(){{
  var lp=document.getElementById('eye-left-plus'),
      lc=document.getElementById('eye-left-check'),
      rp=document.getElementById('eye-right-plus'),
      rc=document.getElementById('eye-right-check');
  if(!lp||!lc||!rp||!rc) return;

  var phase=0, tid=null, stopTid=null, curMs=200, running=false;

  function show(p){{
    phase=p;
    if(p===0){{ lp.style.display=''; lc.style.display='none'; rp.style.display='none'; rc.style.display=''; }}
    else      {{ lp.style.display='none'; lc.style.display=''; rp.style.display=''; rc.style.display='none'; }}
  }}

  function tick(){{
    show(phase===0?1:0);
    tid=setTimeout(tick, curMs);
  }}

  function stop(){{
    clearTimeout(tid); tid=null; running=false; show(0);
  }}

  function onV(v){{
    if(v < 50) return;
    // map velocity px/s → delay ms: 50→350ms, 3000+→60ms
    curMs=Math.round(Math.max(60, 350 - Math.min(v,3000)/3000*290));
    clearTimeout(stopTid);
    stopTid=setTimeout(stop, 1200);
    if(!running){{ running=true; tick(); }}
  }}

  // Desktop: mouse speed
  var mx=0,my=0,mt=0;
  document.addEventListener('mousemove',function(e){{
    var now=Date.now(),dx=e.clientX-mx,dy=e.clientY-my,dt=now-mt;
    if(dt>0&&dt<150) onV(Math.sqrt(dx*dx+dy*dy)/dt*1000);
    mx=e.clientX; my=e.clientY; mt=now;
  }});

  // Mobile: scroll speed
  var sy=0,st=0;
  window.addEventListener('scroll',function(){{
    var now=Date.now(),ds=Math.abs(window.scrollY-sy),dt=now-st;
    if(dt>0&&dt<150) onV(ds/dt*1000);
    sy=window.scrollY; st=now;
  }},{{passive:true}});
}})();
</script>

</body>
</html>"""


# ── /llms.txt — for AI agents (Claude, GPT, Perplexity, Gemini) ──────────────

LLMS_TXT = f"""# Get My Task

> AI-powered task and goal manager for Telegram.
> URL: {_BASE_URL}
> Bot: https://t.me/getmytask_bot

## What it does

Get My Task is a Telegram bot that converts voice messages and text into structured tasks.
It classifies tasks using the Eisenhower Matrix (Q1–Q4), suggests dates and times,
syncs with Google Calendar, and helps users set and track SMART goals.

## Key features

- Voice-to-task: Whisper AI transcribes voice messages and extracts individual tasks
- Eisenhower Matrix: automatic priority classification (urgent/important quadrants)
- Google Calendar sync: one-tap event creation with reminders
- SMART Goals: goal creation with deadline and success criteria, linked to tasks
- Recurring tasks: daily and weekly tasks from Google Calendar in morning digest
- Task rescheduling: move tasks by voice or text command
- Morning digest: daily summary of tasks sent at user-configured time
- Three languages: Russian (ru), English (en), Ukrainian (uk)

## Audience

Entrepreneurs, managers, freelancers, students — anyone who needs a fast,
voice-first task management system inside Telegram.

## Tech stack

- Python (python-telegram-bot, aiohttp)
- Groq API (Whisper for voice, LLaMA for intent classification)
- Google Calendar API (OAuth 2.0)
- SQLite

## Pages

- {_BASE_URL}/ — landing page (supports ?lang=ru|en|uk)
- {_BASE_URL}/privacy — privacy policy
- {_BASE_URL}/stats — analytics dashboard (private)

## Contact

hello.egour@gmail.com
"""

# ── /robots.txt ───────────────────────────────────────────────────────────────

ROBOTS_TXT = f"""User-agent: *
Allow: /
Disallow: /stats
Disallow: /oauth/

Sitemap: {_BASE_URL}/sitemap.xml
"""

# ── /sitemap.xml ──────────────────────────────────────────────────────────────

SITEMAP_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <url>
    <loc>{_BASE_URL}/</loc>
    <xhtml:link rel="alternate" hreflang="en" href="{_BASE_URL}/?lang=en"/>
    <xhtml:link rel="alternate" hreflang="ru" href="{_BASE_URL}/?lang=ru"/>
    <xhtml:link rel="alternate" hreflang="uk" href="{_BASE_URL}/?lang=uk"/>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{_BASE_URL}/privacy</loc>
    <changefreq>monthly</changefreq>
    <priority>0.4</priority>
  </url>
</urlset>
"""


def get_home_html(lang: str = "en", user_count: int = 0) -> str:
    if lang not in _C:
        lang = "en"
    return _page(lang, user_count)
