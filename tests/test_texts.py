"""
Tests: все языки в TEXTS имеют одинаковый набор ключей.
TDD-ценность: ловит случай когда добавили ключ в ru, но забыли в en/uk.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from bot import TEXTS

LANGS = ["ru", "en", "uk"]


def test_all_languages_present():
    for lang in LANGS:
        assert lang in TEXTS, f"Язык '{lang}' отсутствует в TEXTS"


def test_all_langs_have_same_keys():
    keys_by_lang = {lang: set(TEXTS[lang].keys()) for lang in LANGS}
    reference = keys_by_lang["ru"]

    for lang in ["en", "uk"]:
        missing = reference - keys_by_lang[lang]
        extra   = keys_by_lang[lang] - reference

        assert not missing, (
            f"[{lang}] отсутствуют ключи: {sorted(missing)}"
        )
        assert not extra, (
            f"[{lang}] лишние ключи (нет в ru): {sorted(extra)}"
        )
