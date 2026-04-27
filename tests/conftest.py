"""
Mock all heavy external dependencies before bot.py is imported.
This lets us test pure logic functions without Telegram / Groq / Google creds.
"""
import sys
from unittest.mock import MagicMock

_MOCKED = [
    "telegram",
    "telegram.ext",
    "telegram.ext._utils",
    "groq",
    "dotenv",
    "google",
    "google.auth",
    "google.auth.transport",
    "google.auth.transport.requests",
    "google.oauth2",
    "google.oauth2.credentials",
    "google_auth_oauthlib",
    "google_auth_oauthlib.flow",
    "googleapiclient",
    "googleapiclient.discovery",
    "apscheduler",
    "apscheduler.schedulers",
    "apscheduler.schedulers.asyncio",
    "aiohttp",
]

for mod in _MOCKED:
    sys.modules.setdefault(mod, MagicMock())

# Stub specific symbols that bot.py uses at module level
import os
os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("BOT_OWNER_ID", "114978994")
os.environ.setdefault("GROQ_API_KEY", "test-key")
