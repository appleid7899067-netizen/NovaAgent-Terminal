"""NovaAgent Branding Module"""
import os
import json
from pathlib import Path

_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parent.parent.parent


def _find_brand_config():
    candidates = [
        _PROJECT_ROOT / "branding" / "brand_config.json",
        Path("branding/brand_config.json"),
        Path("../branding/brand_config.json"),
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _load():
    p = _find_brand_config()
    if p:
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def get_brand_name():
    return os.getenv("BRAND_NAME") or _load().get("brand_name", "boss.slilelo")

def get_brand_display():
    return os.getenv("BRAND_DISPLAY") or _load().get("display_name", "boss.slilelo")

def get_brand_short():
    return _load().get("short_name", get_brand_name())

def get_brand_tagline():
    return _load().get("tagline", "AI Agent")

def get_brand_logo():
    return _load().get("logo_text", "🤖")

def get_brand_primary_color():
    return _load().get("primary_color", "#00D4FF")

def get_brand_secondary_color():
    return _load().get("secondary_color", "#7B61FF")

def get_brand_copyright():
    return _load().get("copyright", "")

def get_brand_powered_by():
    return _load().get("powered_by", "NovaAgent")


BRAND_NAME = get_brand_name()
BRAND_DISPLAY = get_brand_display()
BRAND_SHORT = get_brand_short()
BRAND_TAGLINE = get_brand_tagline()
BRAND_LOGO = get_brand_logo()
BRAND_COLOR_PRIMARY = get_brand_primary_color()
BRAND_COLOR_SECONDARY = get_brand_secondary_color()
BRAND_COPYRIGHT = get_brand_copyright()
BRAND_POWERED_BY = get_brand_powered_by()


def as_dict():
    return {
        "name": BRAND_NAME,
        "display": BRAND_DISPLAY,
        "short": BRAND_SHORT,
        "tagline": BRAND_TAGLINE,
        "logo": BRAND_LOGO,
        "color_primary": BRAND_COLOR_PRIMARY,
        "color_secondary": BRAND_COLOR_SECONDARY,
        "copyright": BRAND_COPYRIGHT,
        "powered_by": BRAND_POWERED_BY,
    }
