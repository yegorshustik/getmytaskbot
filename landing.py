"""
landing.py — HTML for the Get My Task landing page at /.

Kept as a separate file so it survives bot.py refactors.
Imported by bot.py: from landing import HOME_HTML
"""

_ICON_SVG = """<svg viewBox="0 0 501.5 500.3" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<rect fill="#5D2362" width="501.5" height="500.3"/>
<rect x="239.3" y="81.1" fill="#FAF06E" width="22" height="44"/>
<rect x="217.1" y="81.1" fill="#FAF06E" width="66" height="22"/>
<circle fill="#FAF06E" cx="218.1" cy="92.1" r="11"/>
<circle fill="#FAF06E" cx="283.4" cy="92.1" r="11"/>
<path fill-rule="evenodd" clip-rule="evenodd" fill="#FAF06E" d="M406.7,250.7c-0.1-0.8-0.2-1.6-0.5-2.3l-33-87.9c-7.9-21.3-28.3-35.4-51-35.4L179.3,125
  c-22.7,0-43,14.1-51,35.4l-33,87.9c-0.3,0.7-0.5,1.5-0.6,2.3c0,0.5-0.1,1-0.1,1.5v72.7c0,30,24.3,54.4,54.4,54.4l0,0h203.5
  c30,0,54.4-24.3,54.4-54.4l0,0v-72.6C406.9,251.7,406.8,251.2,406.7,250.7z M148.6,168.1c4.8-12.7,17-21.2,30.6-21.2h143.1
  c13.6,0,25.8,8.4,30.6,21.2l27.2,73.3h-73.3c-5,0-9.3,3.4-10.5,8.2c-6.5,25.2-32.3,40.4-57.5,33.9
  c-16.6-4.3-29.6-17.3-33.9-33.9c-1.2-4.8-5.5-8.2-10.5-8.2h-73.3L148.6,168.1z M385,324.8c0,16.8-12.6,30.8-29.3,32.5
  l-3.4,0.2H149c-18,0-32.7-14.7-32.7-32.7V263h70.2c14.1,35.5,54.2,52.8,89.7,38.7c17.7-7,31.7-21,38.7-38.7H385V324.8z"/>
<circle fill="#FAF06E" cx="291.6" cy="195.1" r="31.7"/>
<polygon fill="#5D2362" points="303.6,179.1 287.7,195.1 279.6,187 271.6,195 279.7,203.1 279.6,203.1 287.6,211.1 311.6,187.1"/>
<circle fill="#FAF06E" cx="209.9" cy="195.1" r="31.7"/>
<polygon fill="#5D2362" points="228.5,189.4 215.5,189.4 215.5,176.5 204.3,176.5 204.3,189.4 191.3,189.4 191.3,200.7 204.3,200.7 204.3,213.7 215.5,213.7 215.5,200.7 228.5,200.7"/>
</svg>"""

_COPY = {
    "ru": {
        "tagline": "AI-менеджер задач и целей",
        "desc": "Голосовые сообщения и текст → задачи, цели и синхронизация с календарём",
        "cta": "@getmytask_bot",
        "f1": "Надиктуй задачи голосом — ИИ выделит заголовок, дату и приоритет",
        "f2": "Матрица Эйзенхауэра — задачи сортируются по важности и срочности",
        "f3": "Синхронизация с Google Calendar — добавляй задачи одним нажатием",
        "f4": "Умные напоминания — получай уведомление до начала каждой задачи",
        "f5": "Цели — ставь SMART-цели и связывай с ними задачи",
        "f6": "Три языка — русский, английский, украинский",
        "footer_privacy": "Политика конфиденциальности",
    },
    "en": {
        "tagline": "AI Task & Goal Manager",
        "desc": "Voice notes and texts → tasks, goals & calendar sync",
        "cta": "@getmytask_bot",
        "f1": "Dictate tasks by voice — AI extracts title, date and priority",
        "f2": "Eisenhower Matrix — tasks sorted by importance and urgency",
        "f3": "Google Calendar sync — add tasks as events in one tap",
        "f4": "Smart reminders — get notified before each task starts",
        "f5": "Goals — set SMART goals and link tasks to them",
        "f6": "Three languages — Russian, English, Ukrainian",
        "footer_privacy": "Privacy Policy",
    },
    "uk": {
        "tagline": "AI-менеджер задач і цілей",
        "desc": "Голосові повідомлення і текст → задачі, цілі та синхронізація з календарем",
        "cta": "@getmytask_bot",
        "f1": "Надиктуй задачі голосом — ШІ визначить заголовок, дату та пріоритет",
        "f2": "Матриця Ейзенхауера — задачі сортуються за важливістю та терміновістю",
        "f3": "Синхронізація з Google Calendar — додавай задачі одним натисканням",
        "f4": "Розумні нагадування — отримуй сповіщення до початку кожної задачі",
        "f5": "Цілі — ставте SMART-цілі та пов'язуйте з ними задачі",
        "f6": "Три мови — російська, англійська, українська",
        "footer_privacy": "Політика конфіденційності",
    },
}

def _build_features(c):
    icons = ["🎙", "📊", "📅", "🔔", "🎯", "🌐"]
    keys  = ["f1", "f2", "f3", "f4", "f5", "f6"]
    return "".join(
        f'<div class="feat"><span class="feat-icon">{icons[i]}</span><span>{c[keys[i]]}</span></div>'
        for i in range(6)
    )

def _page(lang: str) -> str:
    c = _COPY[lang]
    feats = _build_features(c)
    active = {l: ' class="active"' if l == lang else "" for l in ("ru", "en", "uk")}
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Get My Task — {c['tagline']}</title>
  <meta name="description" content="{c['desc']}"/>
  <meta property="og:title" content="Get My Task"/>
  <meta property="og:description" content="{c['desc']}"/>
  <meta property="og:type" content="website"/>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg:      #0e0b14;
      --surface: #17112a;
      --border:  #2a1f45;
      --purple:  #5D2362;
      --purple-l:#7a2f80;
      --yellow:  #FAF06E;
      --white:   #f0eaff;
      --muted:   #8a7fa8;
    }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg);
      color: var(--white);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 48px 20px 64px;
    }}

    /* ── Language switcher ── */
    .lang-bar {{
      display: flex;
      gap: 6px;
      margin-bottom: 48px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 4px;
    }}
    .lang-bar a {{
      padding: 6px 18px;
      border-radius: 999px;
      font-size: .85rem;
      font-weight: 600;
      color: var(--muted);
      text-decoration: none;
      transition: background .15s, color .15s;
    }}
    .lang-bar a.active,
    .lang-bar a:hover {{
      background: var(--purple);
      color: var(--yellow);
    }}

    /* ── Hero ── */
    .hero {{ text-align: center; max-width: 560px; width: 100%; }}

    .icon-wrap {{
      width: 96px;
      height: 96px;
      border-radius: 24px;
      overflow: hidden;
      margin: 0 auto 24px;
      box-shadow: 0 8px 32px rgba(93,35,98,.6);
    }}
    .icon-wrap svg {{ width: 100%; height: 100%; display: block; }}

    h1 {{
      font-size: 2.6rem;
      font-weight: 800;
      letter-spacing: -.5px;
      color: #fff;
      margin-bottom: 8px;
    }}
    .tagline {{
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--yellow);
      margin-bottom: 16px;
    }}
    .desc {{
      font-size: 1rem;
      color: var(--muted);
      line-height: 1.65;
      margin-bottom: 36px;
    }}

    /* ── CTA button ── */
    .btn {{
      display: inline-block;
      background: var(--purple);
      color: var(--yellow);
      font-size: 1rem;
      font-weight: 700;
      padding: 14px 36px;
      border-radius: 14px;
      text-decoration: none;
      letter-spacing: .3px;
      box-shadow: 0 4px 20px rgba(93,35,98,.5);
      transition: background .15s, transform .1s;
    }}
    .btn:hover {{ background: var(--purple-l); transform: translateY(-1px); }}
    .btn:active {{ transform: translateY(0); }}

    /* ── Features grid ── */
    .features {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-top: 48px;
      width: 100%;
      max-width: 560px;
    }}
    @media (max-width: 480px) {{
      .features {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 2rem; }}
    }}
    .feat {{
      display: flex;
      align-items: flex-start;
      gap: 12px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 16px;
      font-size: .9rem;
      color: #c4b8e0;
      line-height: 1.4;
    }}
    .feat-icon {{
      font-size: 1.3rem;
      flex-shrink: 0;
      margin-top: 1px;
    }}

    /* ── Footer ── */
    footer {{
      margin-top: 56px;
      font-size: .8rem;
      color: var(--muted);
      text-align: center;
    }}
    footer a {{
      color: var(--muted);
      text-decoration: none;
      border-bottom: 1px solid transparent;
      transition: color .15s, border-color .15s;
    }}
    footer a:hover {{ color: var(--yellow); border-color: var(--yellow); }}
  </style>
</head>
<body>

  <nav class="lang-bar">
    <a href="/?lang=ru"{active['ru']}>RU</a>
    <a href="/?lang=en"{active['en']}>EN</a>
    <a href="/?lang=uk"{active['uk']}>UK</a>
  </nav>

  <div class="hero">
    <div class="icon-wrap">{_ICON_SVG}</div>
    <h1>Get My Task</h1>
    <p class="tagline">{c['tagline']}</p>
    <p class="desc">{c['desc']}</p>
    <a class="btn" href="https://t.me/getmytask_bot">{c['cta']}</a>
  </div>

  <div class="features">
    {feats}
  </div>

  <footer>
    <a href="/privacy">{c['footer_privacy']}</a>
  </footer>

</body>
</html>"""


def get_home_html(lang: str = "en") -> str:
    if lang not in _COPY:
        lang = "en"
    return _page(lang)


# Pre-render all three so import is cheap
HOME_HTML_RU = _page("ru")
HOME_HTML_EN = _page("en")
HOME_HTML_UK = _page("uk")
