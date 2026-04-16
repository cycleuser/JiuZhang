"""Font and language configuration for JiuZhang visualizations.

Automatically detects and configures appropriate fonts for different languages
to ensure proper text rendering in matplotlib plots.
"""

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import warnings
import platform
import os


# Detect OS for font paths
SYSTEM = platform.system()

# Font configuration by language
LANGUAGE_FONTS = {
    "zh": {
        "name": "Chinese",
        "fonts": [
            "PingFang SC",  # macOS
            "Heiti SC",  # macOS
            "STHeiti",  # macOS
            "Microsoft YaHei",  # Windows
            "SimHei",  # Windows
            "WenQuanYi Micro Hei",  # Linux
            "Noto Sans CJK SC",  # Linux
            "Source Han Sans SC",  # Cross-platform
            "Arial Unicode MS",  # Fallback
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


def get_system_fonts():
    """Get list of all available system fonts."""
    return [f.name for f in fm.fontManager.ttflist]


def find_best_font(language: str = "zh") -> str:
    """Find the best available font for a given language.

    Args:
        language: Language code (zh, ja, ko, ru, etc.)

    Returns:
        Font family name
    """
    system_fonts = get_system_fonts()
    font_config = LANGUAGE_FONTS.get(language, LANGUAGE_FONTS["default"])

    # Try each font in order
    for font_name in font_config["fonts"]:
        if font_name in system_fonts:
            return font_name

    # If no CJK font found, try to find any font that supports CJK
    # by checking font files directly
    cjk_font_paths = _find_cjk_fonts()
    if cjk_font_paths:
        return cjk_font_paths[0]

    # Ultimate fallback
    return "DejaVu Sans"


def _find_cjk_fonts():
    """Find CJK fonts by scanning font directories."""
    cjk_paths = []

    # Common font directories
    font_dirs = []
    if SYSTEM == "Darwin":  # macOS
        font_dirs = [
            "/System/Library/Fonts",
            "/Library/Fonts",
            os.path.expanduser("~/Library/Fonts"),
        ]
    elif SYSTEM == "Windows":
        font_dirs = [
            os.environ.get("WINDIR", "C:\\Windows") + "\\Fonts",
        ]
    else:  # Linux
        font_dirs = [
            "/usr/share/fonts",
            "/usr/local/share/fonts",
            os.path.expanduser("~/.fonts"),
            os.path.expanduser("~/.local/share/fonts"),
        ]

    # CJK font file patterns
    cjk_patterns = [
        "NotoSansCJK",
        "SourceHanSans",
        "WenQuanYi",
        "AR",
        "uming",
        "ukai",
    ]

    for font_dir in font_dirs:
        if not os.path.exists(font_dir):
            continue
        for root, dirs, files in os.walk(font_dir):
            for f in files:
                if f.endswith((".ttf", ".otf", ".ttc")):
                    for pattern in cjk_patterns:
                        if pattern.lower() in f.lower():
                            cjk_paths.append(os.path.join(root, f))
                            break

    return cjk_paths


def configure_matplotlib(language: str = "zh", style: str = "default"):
    """Configure matplotlib for proper text rendering in specified language.

    Args:
        language: Language code
        style: Matplotlib style to use

    Returns:
        Font family name that was configured
    """
    # Set style first
    try:
        plt.style.use(style)
    except Exception:
        pass

    # Find best font
    font_family = find_best_font(language)

    # Configure matplotlib rcParams
    matplotlib.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [font_family],
            "axes.unicode_minus": False,  # Fix minus sign display
            "figure.dpi": 100,
            "savefig.dpi": 150,
            "savefig.bbox": "tight",
            "savefig.facecolor": "white",
            "axes.labelsize": 12,
            "axes.titlesize": 14,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            "figure.titlesize": 16,
            "font.size": 12,
        }
    )

    # Clear font cache to ensure new fonts are picked up
    fm._load_fontmanager(try_read_cache=False)

    # Suppress font warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")
    warnings.filterwarnings(
        "ignore", category=UserWarning, module="matplotlib.font_manager"
    )

    return font_family


def get_font_info(language: str = "zh") -> dict:
    """Get information about font configuration for a language.

    Args:
        language: Language code

    Returns:
        Dictionary with font information
    """
    system_fonts = get_system_fonts()
    font_config = LANGUAGE_FONTS.get(language, LANGUAGE_FONTS["default"])

    available = []
    unavailable = []

    for font_name in font_config["fonts"]:
        if font_name in system_fonts:
            available.append(font_name)
        else:
            unavailable.append(font_name)

    # Also check for CJK fonts
    cjk_fonts = _find_cjk_fonts()

    return {
        "language": language,
        "language_name": font_config["name"],
        "best_font": available[0]
        if available
        else (cjk_fonts[0] if cjk_fonts else "DejaVu Sans"),
        "available_fonts": available,
        "unavailable_fonts": unavailable,
        "cjk_fonts_found": cjk_fonts,
        "total_system_fonts": len(system_fonts),
    }


# Auto-configure on module import for Chinese by default
_default_font = configure_matplotlib("zh")
