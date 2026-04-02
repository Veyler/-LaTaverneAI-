"""
Configuration centrale de l'application.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 COMMENT AJOUTER UN NOUVEAU PROVIDER/MODÈLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. AJOUTER LE PROVIDER dans PROVIDERS :
   {
       "id":       "mon_provider",
       "label":    "Mon Provider",
       "base_url": "https://api.exemple.com/v1",
       "api_key":  "sk-ma-cle-api-ici",
   }

2. AJOUTER LE MODÈLE dans AVAILABLE_MODELS :
   {
       "label":              "Mon Modèle",
       "id":                 "model-id-api",
       "provider_id":        "mon_provider",   # doit correspondre à l'id du provider
       "description":        "Description",
       "max_tokens":         4096,
       "supports_reasoning": False,
   }
"""

import os
import sys
from pathlib import Path

APP_NAME = "[LaTaverneAI]"
APP_VERSION = "1.1.0"

def _get_db_path() -> str:
    home = Path.home()
    if sys.platform == "win32":
        app_dir = home / "AppData" / "Roaming" / "LaTaverneAI"
    elif sys.platform == "darwin":
        app_dir = home / "Library" / "Application Support" / "LaTaverneAI"
    else:
        app_dir = home / ".local" / "share" / "LaTaverneAI"
    app_dir.mkdir(parents=True, exist_ok=True)
    return str(app_dir / "chatapp.db")

DB_PATH = _get_db_path()

# ─── Providers ───────────────────────────────────────────────────────────────
PROVIDERS = [
    {
        "id":       "nvidia",
        "label":    "NVIDIA NIM",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "api_key":  "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",
    }
]

# ─── Modèles disponibles ─────────────────────────────────────────────────────
AVAILABLE_MODELS = [
    {
        "label":              "GPT-OSS 120B",
        "id":                 "openai/gpt-oss-120b",
        "provider_id":        "nvidia",
        "description":        "Modèle principal open-source 120B",
        "max_tokens":         4096,
        "supports_reasoning": True,
    }
]

DEFAULT_MODEL_ID = AVAILABLE_MODELS[0]["id"]

# ─── Paramètres de génération ────────────────────────────────────────────────
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 1.0
DEFAULT_MAX_TOKENS = 4096

# ─── UI ─────────────────────────────────────────────────────────────────────
WINDOW_MIN_WIDTH  = 1000
WINDOW_MIN_HEIGHT = 650
WINDOW_START_WIDTH  = 1000
WINDOW_START_HEIGHT = 650

THEME = "green"
COLOR_THEME = "blue"
DEFAULT_FONT = "Inter"

FONTS = {
    "title":   (DEFAULT_FONT, 22, "bold"),
    "heading": (DEFAULT_FONT, 13, "bold"),
    "body":    (DEFAULT_FONT, 12),
    "small":   (DEFAULT_FONT, 10),
    "mono":    ("Consolas", 11),
    "code":    ("Consolas", 11),
}

COLORS = {
    "accent":           "#00FF88",
    "accent_dim":       "#00CC66",
    "bg_dark":          "#0A0E1A",
    "bg_mid":           "#111827",
    "bg_panel":         "#1A2235",
    "bg_card":          "#1E2D40",
    "text_primary":     "#E8F4FD",
    "text_secondary":   "#B0C4DE",
    "text_dim":         "#6B8CAE",
    "user_bubble":      "#0D3B66",
    "ai_bubble":        "#131C2E",
    "border":           "#2A3F5F",
    "danger":           "#FF4466",
    "warning":          "#FFB300",
    "code_bg":          "#0D1117",
    "code_border":      "#1E3048",
    "h1":               "#00FF88",
    "h2":               "#00DDAA",
    "h3":               "#00BBCC",
    "bold_text":        "#FFFFFF",
    "italic_text":      "#B8D4E8",
    "inline_code_bg":   "#162030",
    "inline_code_fg":   "#7FDBCA",
    "quote_border":     "#2A5F4F",
    "quote_bg":         "#0F1A1A",
    "quote_text":       "#8FAAAA",
    "separator":        "#1E3048",
    "list_bullet":      "#00CC66",
}
