"""Font and language configuration for JiuZhang visualizations.

Automatically detects and configures appropriate fonts for different languages
to ensure proper text rendering in manim scenes.
"""

import platform
import os

SYSTEM = platform.system()

LANGUAGE_FONTS = {
    "zh": {
        "name": "Chinese",
        "fonts": [
            "PingFang SC",
            "Heiti SC",
            "STHeiti",
            "Microsoft YaHei",
            "SimHei",
            "WenQuanYi Micro Hei",
            "Noto Sans CJK SC",
            "Source Han Sans SC",
            "Arial Unicode MS",
        ],
    },
    "ja": {
        "name": "Japanese",
        "fonts": [
            "Hiragino Sans",
            "Hiragino Kaku Gothic Pro",
            "Yu Gothic",
            "Meiryo",
            "MS Gothic",
            "Noto Sans CJK JP",
            "Source Han Sans JP",
            "Arial Unicode MS",
        ],
    },
    "ko": {
        "name": "Korean",
        "fonts": [
            "Apple SD Gothic Neo",
            "Nanum Gothic",
            "Malgun Gothic",
            "Noto Sans CJK KR",
            "Source Han Sans KR",
            "Arial Unicode MS",
        ],
    },
    "ru": {
        "name": "Russian",
        "fonts": [
            "Arial",
            "Helvetica",
            "DejaVu Sans",
            "Liberation Sans",
            "Noto Sans",
        ],
    },
    "default": {
        "name": "Default (Latin)",
        "fonts": [
            "Arial",
            "Helvetica",
            "DejaVu Sans",
            "Liberation Sans",
            "Noto Sans",
        ],
    },
}

_manimmation_config_done = False


def _find_system_font_candidates(language: str = "zh") -> list:
    """Find available system font candidates for a given language.

    Manim uses its own font discovery, so we just return preferred font names
    that manim can resolve.
    """
    config = LANGUAGE_FONTS.get(language, LANGUAGE_FONTS["default"])
    return list(config["fonts"])


def get_manim_font(language: str = "zh") -> str:
    """Get the best manim-compatible font name for a given language.

    Manim resolves fonts differently from matplotlib.  For CJK text we try
    known system font names; fall back to the manim default (Sans).
    """
    candidates = _find_system_font_candidates(language)

    if platform.system() == "Darwin":
        cjk_lookup = {
            "zh": "PingFang SC",
            "ja": "Hiragino Sans",
            "ko": "Apple SD Gothic Neo",
        }
        preferred = cjk_lookup.get(language)
        if preferred and preferred in candidates:
            return preferred
    elif platform.system() == "Windows":
        cjk_lookup = {
            "zh": "Microsoft YaHei",
            "ja": "Yu Gothic",
            "ko": "Malgun Gothic",
        }
        preferred = cjk_lookup.get(language)
        if preferred and preferred in candidates:
            return preferred

    return candidates[0] if candidates else "Sans"


def configure_manim(language: str = "zh") -> str:
    """Configure manim for proper text rendering in the specified language.

    Sets global manim config for output format, frame rate, etc.
    Returns the font family name that should be used.
    """
    global _manimmation_config_done

    try:
        from manim import config as manim_config
    except ImportError:
        return get_manim_font(language)

    if not _manimmation_config_done:
        manim_config.quality = "low_quality"
        manim_config.frame_rate = 30
        manim_config.format = "mp4"
        manim_config.write_to_movie = True
        _manimmation_config_done = True

    return get_manim_font(language)


def get_font_info(language: str = "zh") -> dict:
    """Get information about font configuration for a language.

    Args:
        language: Language code

    Returns:
        Dictionary with font information
    """
    config = LANGUAGE_FONTS.get(language, LANGUAGE_FONTS["default"])
    best_font = get_manim_font(language)

    return {
        "language": language,
        "language_name": config["name"],
        "best_font": best_font,
        "available_fonts": config["fonts"],
        "manim_configured": _manimmation_config_done,
    }


DEFAULT_FONT = configure_manim("zh")