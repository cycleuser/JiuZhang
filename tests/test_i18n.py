"""Tests for i18n module."""

import pytest
from jiuzhang.i18n import I18n, SUPPORTED_LANGUAGES


class TestI18n:
    @pytest.fixture
    def i18n(self):
        return I18n()

    def test_default_language(self, i18n):
        assert i18n.get_language() == "zh"

    def test_set_language(self, i18n):
        i18n.set_language("en")
        assert i18n.get_language() == "en"

    def test_set_unsupported_language(self, i18n):
        with pytest.raises(ValueError):
            i18n.set_language("unsupported")

    def test_translate_chinese(self, i18n):
        assert i18n.t("app_name") == "九章"
        assert i18n.t("welcome") == "欢迎使用九章"

    def test_translate_english(self, i18n):
        i18n.set_language("en")
        assert i18n.t("app_name") == "JiuZhang"
        assert i18n.t("welcome") == "Welcome to JiuZhang"

    def test_translate_japanese(self, i18n):
        i18n.set_language("ja")
        assert i18n.t("app_name") == "九章"
        assert i18n.t("welcome") == "九章へようこそ"

    def test_translate_french(self, i18n):
        i18n.set_language("fr")
        assert i18n.t("app_name") == "JiuZhang"
        assert i18n.t("welcome") == "Bienvenue sur JiuZhang"

    def test_translate_russian(self, i18n):
        i18n.set_language("ru")
        assert i18n.t("app_name") == "Цзючжан"
        assert i18n.t("welcome") == "Добро пожаловать в Цзючжан"

    def test_translate_german(self, i18n):
        i18n.set_language("de")
        assert i18n.t("app_name") == "JiuZhang"
        assert i18n.t("welcome") == "Willkommen bei JiuZhang"

    def test_translate_italian(self, i18n):
        i18n.set_language("it")
        assert i18n.t("app_name") == "JiuZhang"
        assert i18n.t("welcome") == "Benvenuto su JiuZhang"

    def test_translate_spanish(self, i18n):
        i18n.set_language("es")
        assert i18n.t("app_name") == "JiuZhang"
        assert i18n.t("welcome") == "Bienvenido a JiuZhang"

    def test_translate_portuguese(self, i18n):
        i18n.set_language("pt")
        assert i18n.t("app_name") == "JiuZhang"
        assert i18n.t("welcome") == "Bem-vindo ao JiuZhang"

    def test_translate_korean(self, i18n):
        i18n.set_language("ko")
        assert i18n.t("app_name") == "구장"
        assert i18n.t("welcome") == "구장에 오신 것을 환영합니다"

    def test_get_supported_languages(self, i18n):
        langs = i18n.get_supported_languages()
        assert len(langs) == 10
        assert "zh" in langs
        assert "en" in langs
        assert "ja" in langs
        assert "fr" in langs
        assert "ru" in langs
        assert "de" in langs
        assert "it" in langs
        assert "es" in langs
        assert "pt" in langs
        assert "ko" in langs

    def test_get_language_name(self, i18n):
        assert i18n.get_language_name("zh") == "中文"
        assert i18n.get_language_name("en") == "English"
        assert i18n.get_language_name("ja") == "日本語"
        assert i18n.get_language_name("fr") == "Français"
        assert i18n.get_language_name("ru") == "Русский"
        assert i18n.get_language_name("de") == "Deutsch"
        assert i18n.get_language_name("it") == "Italiano"
        assert i18n.get_language_name("es") == "Español"
        assert i18n.get_language_name("pt") == "Português"
        assert i18n.get_language_name("ko") == "한국어"

    def test_get_all_translations(self, i18n):
        translations = i18n.get_all_translations("app_name")
        assert len(translations) == 10
        assert translations["zh"] == "九章"
        assert translations["en"] == "JiuZhang"
        assert translations["ko"] == "구장"

    def test_translate_unknown_key(self, i18n):
        assert i18n.t("unknown_key") == "unknown_key"

    def test_translate_with_default(self, i18n):
        assert i18n.t("unknown_key", default="fallback") == "fallback"

    def test_all_languages_have_common_keys(self, i18n):
        common_keys = ["app_name", "welcome", "learn", "exercise", "courses", "stats"]
        for lang in SUPPORTED_LANGUAGES:
            i18n.set_language(lang)
            for key in common_keys:
                assert i18n.t(key) != key, f"Key '{key}' not translated for {lang}"
