"""
landing.py — Get My Task landing page.

Kept separate from bot.py so it survives refactors.
Imported by bot.py: from landing import get_home_html, LLMS_TXT, ROBOTS_TXT, SITEMAP_XML
"""

_ICON_SVG = """<svg viewBox="0 0 501.5 500.3" xmlns="http://www.w3.org/2000/svg">
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
<circle fill="#FAF06E" cx="291.6" cy="195.1" r="31.7"/>
<polygon fill="#5D2362" points="303.6,179.1 287.7,195.1 279.6,187 271.6,195 279.7,203.1 279.6,203.1 287.6,211.1 311.6,187.1"/>
<circle fill="#FAF06E" cx="209.9" cy="195.1" r="31.7"/>
<polygon fill="#5D2362" points="228.5,189.4 215.5,189.4 215.5,176.5 204.3,176.5 204.3,189.4 191.3,189.4
  191.3,200.7 204.3,200.7 204.3,213.7 215.5,213.7 215.5,200.7 228.5,200.7"/>
</svg>"""

# ── Copy ─────────────────────────────────────────────────────────────────────

_C = {
    "ru": {
        "lang_html": "ru",
        "tagline": "AI-менеджер задач и целей",
        "desc": "Голосовые сообщения и текст → задачи, цели и синхронизация с Google Calendar",
        "cta": "Попробовать бесплатно →",

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
            ("Нужно ли устанавливать что-то отдельно?",
             "Нет. Get My Task работает прямо в Telegram — просто открой бота @getmytask_bot и начни писать или диктовать. Никаких приложений, регистраций и паролей."),
            ("Как добавить задачу голосом?",
             "Просто запиши голосовое сообщение в боте — например: «Позвонить клиенту в пятницу в 15:00 и подготовить презентацию к понедельнику». Бот сам разберёт несколько задач, определит даты и расставит приоритеты по матрице Эйзенхауэра."),
            ("Что такое матрица Эйзенхауэра и зачем она нужна?",
             "Это система приоритетов из 4 квадрантов: Q1 — важно и срочно (делай сейчас), Q2 — важно, но не срочно (запланируй), Q3 — срочно, но не важно (делегируй), Q4 — не важно и не срочно (удали). Бот автоматически определяет квадрант для каждой задачи."),
            ("Как работает утренний дайджест?",
             "Каждое утро в выбранное тобой время бот присылает список задач на сегодня — с временем, приоритетами и повторяющимися делами. Так ты начинаешь день с чётким планом, а не со списком непрочитанных сообщений."),
            ("Как подключить Google Calendar?",
             "Зайди в настройки бота (кнопка «Настройки»), нажми «Подключить Google Calendar» и пройди стандартную авторизацию Google. Занимает 30 секунд. После этого все задачи с датой и временем можно добавлять в календарь одним нажатием."),
            ("В чём разница между задачей и целью?",
             "Задача — конкретное действие с датой: «Отправить отчёт до пятницы». Цель — результат, который ты хочешь достичь: «Запустить продукт до конца квартала». В боте можно создать цель, связать с ней задачи и отслеживать прогресс — сколько уже выполнено из запланированного."),
            ("Можно ли перенести задачу на другой день?",
             "Да. Напиши или надиктуй боту: «Перенеси встречу с клиентом на следующую среду» — бот найдёт задачу и обновит дату. Если задача есть в Google Calendar, она тоже обновится автоматически."),
            ("Бот платный?",
             "Сейчас бот полностью бесплатный. Все функции — голосовой ввод, Google Calendar, цели, напоминания — доступны без ограничений."),
            ("Работает ли бот на iPhone и Android?",
             "Да. Get My Task работает через Telegram, который есть на всех платформах: iOS, Android, macOS, Windows и в браузере. Устанавливать ничего дополнительно не нужно."),
            ("Мои данные в безопасности?",
             "Да. Задачи хранятся на нашем сервере и не передаются третьим лицам и не используются для рекламы. OAuth-токен Google хранится в зашифрованном виде и удаляется сразу при отключении календаря."),
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
            ("Do I need to install anything?",
             "No. Get My Task works directly inside Telegram — just open @getmytask_bot and start typing or dictating. No sign-up, no passwords, no extra apps."),
            ("How do I add a task by voice?",
             "Just send a voice message to the bot — for example: 'Call the client on Friday at 3pm and prepare the presentation by Monday.' The bot extracts each task separately, detects dates, and classifies them using the Eisenhower Matrix."),
            ("What is the Eisenhower Matrix and why does it matter?",
             "It's a 4-quadrant priority system: Q1 — urgent & important (do now), Q2 — important, not urgent (schedule), Q3 — urgent, not important (delegate), Q4 — neither (drop). The bot automatically places each task in the right quadrant so you always know what to focus on."),
            ("How does the morning digest work?",
             "Every morning at your chosen time the bot sends a list of today's tasks — with times, priorities, and recurring items. You start the day with a clear plan instead of a pile of unread messages."),
            ("How do I connect Google Calendar?",
             "Go to bot settings, tap 'Connect Google Calendar' and complete the standard Google OAuth flow. Takes about 30 seconds. After that, any task with a date and time can be added to your calendar in one tap."),
            ("What's the difference between a task and a goal?",
             "A task is a specific action with a date: 'Send the report by Friday.' A goal is the outcome you want: 'Launch the product by end of quarter.' In the bot you can create a goal, link tasks to it, and track progress — how many are done out of the total."),
            ("Can I reschedule a task?",
             "Yes. Just write or dictate: 'Move the client meeting to next Wednesday' — the bot finds the task and updates the date. If the task is in Google Calendar, it updates there too automatically."),
            ("Is the bot free?",
             "Yes, the bot is completely free. All features — voice input, Google Calendar, goals, reminders — are available with no limitations."),
            ("Does it work on iPhone and Android?",
             "Yes. Get My Task runs inside Telegram, which is available on iOS, Android, macOS, Windows and in the browser. Nothing extra to install."),
            ("Is my data safe?",
             "Yes. Tasks are stored on our server and are never shared with third parties or used for advertising. Your Google OAuth token is stored encrypted and deleted immediately when you disconnect the calendar."),
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
            ("Чи потрібно щось встановлювати?",
             "Ні. Get My Task працює прямо в Telegram — просто відкрий бота @getmytask_bot і починай писати або диктувати. Жодних реєстрацій, паролів і додаткових застосунків."),
            ("Як додати задачу голосом?",
             "Просто запиши голосове повідомлення — наприклад: «Зателефонувати клієнту в п'ятницю о 15:00 і підготувати презентацію до понеділка». Бот сам розбере кілька задач, визначить дати й розставить пріоритети за матрицею Ейзенхауера."),
            ("Що таке матриця Ейзенхауера і навіщо вона потрібна?",
             "Це система пріоритетів із 4 квадрантів: Q1 — важливо і терміново (роби зараз), Q2 — важливо, але не терміново (сплануй), Q3 — терміново, але не важливо (делегуй), Q4 — не важливо і не терміново (видали). Бот автоматично визначає квадрант для кожної задачі."),
            ("Як працює ранковий дайджест?",
             "Щоранку в обраний тобою час бот надсилає список задач на сьогодні — з часом, пріоритетами і повторюваними справами. Починаєш день із чітким планом, а не зі списком непрочитаних повідомлень."),
            ("Як підключити Google Calendar?",
             "Зайди в налаштування бота, натисни «Підключити Google Calendar» і пройди стандартну авторизацію Google. Займає 30 секунд. Після цього будь-яку задачу з датою і часом можна додати в календар одним натисканням."),
            ("У чому різниця між задачею і ціллю?",
             "Задача — конкретна дія з датою: «Надіслати звіт до п'ятниці». Ціль — результат, якого ти хочеш досягти: «Запустити продукт до кінця кварталу». У боті можна створити ціль, прив'язати до неї задачі й відстежувати прогрес."),
            ("Чи можна перенести задачу на інший день?",
             "Так. Напиши або надиктуй боту: «Перенеси зустріч із клієнтом на наступну середу» — бот знайде задачу й оновить дату. Якщо задача є в Google Calendar, вона теж оновиться автоматично."),
            ("Бот платний?",
             "Зараз бот повністю безкоштовний. Всі функції — голосове введення, Google Calendar, цілі, нагадування — доступні без обмежень."),
            ("Чи працює бот на iPhone та Android?",
             "Так. Get My Task працює через Telegram, який є на всіх платформах: iOS, Android, macOS, Windows і в браузері. Нічого додатково встановлювати не потрібно."),
            ("Мої дані в безпеці?",
             "Так. Задачі зберігаються на нашому сервері і не передаються третім особам та не використовуються для реклами. OAuth-токен Google зберігається в зашифрованому вигляді і видаляється одразу при відключенні календаря."),
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

def _page(lang: str) -> str:
    c = _C[lang]
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
      <a href="mailto:hello.egour@gmail.com">{c['footer_contact']}</a>
      <a href="https://t.me/getmytask_bot" rel="noopener">Telegram</a>
    </div>
    <div class="footer-copy">© 2025 Get My Task. All rights reserved.</div>
  </footer>

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


def get_home_html(lang: str = "en") -> str:
    if lang not in _C:
        lang = "en"
    return _page(lang)
