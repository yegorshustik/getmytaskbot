"""
landing.py — Get My Task landing page.

Kept separate from bot.py so it survives refactors.
Imported by bot.py: from landing import get_home_html, FAVICON_ICO, FAVICON_PNG, LLMS_TXT, ROBOTS_TXT, SITEMAP_XML
"""
import base64 as _b64

# favicon.ico — real logo, 32x16px sizes
FAVICON_ICO: bytes = _b64.b64decode(
    "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"
    "YII="
)

# favicon.png — 180px PNG from real logo, works in Safari and all browsers
FAVICON_PNG: bytes = _b64.b64decode(
    "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"
    "DZAk/H/NR0zuICP2rwAAAABJRU5ErkJggg=="
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
        "cookie_text": "Мы используем cookies для аналитики, чтобы улучшать сервис.",
        "cookie_accept": "Принять",
        "cookie_decline": "Отклонить",
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
        "cookie_text": "We use cookies for analytics to improve the service.",
        "cookie_accept": "Accept",
        "cookie_decline": "Decline",
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
        "cookie_text": "Ми використовуємо cookies для аналітики, щоб покращувати сервіс.",
        "cookie_accept": "Прийняти",
        "cookie_decline": "Відхилити",
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

    /* Cookie consent banner */
    #cookie-banner {
      position: fixed; bottom: 0; left: 0; right: 0; z-index: 9999;
      background: #1a1230; border-top: 1px solid var(--border);
      padding: 14px 20px; display: flex; align-items: center;
      justify-content: center; gap: 14px; flex-wrap: wrap;
      font-size: .85rem; color: var(--text);
    }
    #cookie-banner p { margin: 0; flex: 1; min-width: 200px; }
    #cookie-banner a { color: var(--muted); }
    .cookie-btn {
      padding: 7px 18px; border-radius: 8px; border: none;
      font-size: .85rem; cursor: pointer; white-space: nowrap;
    }
    .cookie-btn-accept {
      background: var(--purple); color: #fff;
    }
    .cookie-btn-accept:hover { background: var(--purple-l); }
    .cookie-btn-decline {
      background: transparent; color: var(--muted);
      border: 1px solid var(--border);
    }
    .cookie-btn-decline:hover { color: var(--white); border-color: var(--muted); }
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

  <!-- Google Analytics (loaded only after cookie consent) -->
  <script>
    window._GA_ID = 'G-2G3KF54HDS';
    function _loadGA() {{
      if (window._gaLoaded) return; window._gaLoaded = true;
      var s = document.createElement('script');
      s.async = true;
      s.src = 'https://www.googletagmanager.com/gtag/js?id=' + window._GA_ID;
      document.head.appendChild(s);
      window.dataLayer = window.dataLayer || [];
      function gtag(){{ dataLayer.push(arguments); }}
      window.gtag = gtag;
      gtag('js', new Date());
      gtag('config', window._GA_ID, {{anonymize_ip: true}});
    }}
    if (localStorage.getItem('cookie_consent') === 'yes') {{ _loadGA(); }}
  </script>

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
      {f'<p class="social-proof">{c["social_proof"].format(n=user_count)}</p>' if user_count > 0 else ''}
    </div>

  </div>

  <footer>
    <div class="footer-links">
      <a href="/privacy">{c['footer_privacy']}</a>
    </div>
    <div class="footer-copy">© {year} Get My Task. All rights reserved.</div>
  </footer>

<!-- Cookie consent banner -->
<div id="cookie-banner" style="display:none">
  <p>{c['cookie_text']} <a href="/privacy">{c['footer_privacy']}</a></p>
  <button class="cookie-btn cookie-btn-accept" onclick="_cookieConsent(true)">{c['cookie_accept']}</button>
  <button class="cookie-btn cookie-btn-decline" onclick="_cookieConsent(false)">{c['cookie_decline']}</button>
</div>
<script>
(function(){{
  var b = document.getElementById('cookie-banner');
  if (!localStorage.getItem('cookie_consent')) {{ b.style.display = 'flex'; }}
}})();
function _cookieConsent(yes) {{
  localStorage.setItem('cookie_consent', yes ? 'yes' : 'no');
  document.getElementById('cookie-banner').style.display = 'none';
  if (yes) {{ _loadGA(); }}
}}
</script>

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
