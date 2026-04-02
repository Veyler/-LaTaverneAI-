"""
Gestionnaire de paramètres utilisateur.
Charge/sauvegarde depuis un fichier JSON par utilisateur.
"""

import json
import os
import sys
from pathlib import Path

def _get_app_data_dir() -> Path:
    home = Path.home()
    if sys.platform == "win32":
        return home / "AppData" / "Roaming" / "LaTaverneAI"
    elif sys.platform == "darwin":
        return home / "Library" / "Application Support" / "LaTaverneAI"
    else:
        return home / ".local" / "share" / "LaTaverneAI"

SETTINGS_DIR = os.path.join(str(_get_app_data_dir()), "user_settings")

DEFAULT_SETTINGS = {
    "appearance": {
        "accent_color": "#00FF88",
        "font_family": "Inter",
        "font_size": 12,
    },
    "ai": {
        "system_prompt": "",
    },
}


def _settings_path(user_id: int) -> str:
    os.makedirs(SETTINGS_DIR, exist_ok=True)
    return os.path.join(SETTINGS_DIR, f"user_{user_id}.json")


def load_settings(user_id: int) -> dict:
    """Charge les paramètres utilisateur, ou retourne les défauts."""
    path = _settings_path(user_id)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            # Merge avec les défauts pour gérer les nouvelles clés
            merged = _deep_merge(DEFAULT_SETTINGS, saved)
            return merged
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULT_SETTINGS))  # deep copy


def save_settings(user_id: int, settings: dict):
    """Sauvegarde les paramètres utilisateur."""
    path = _settings_path(user_id)
    os.makedirs(SETTINGS_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def get_setting(user_id: int, category: str, key: str, default=None):
    """Récupère une valeur de paramètre spécifique."""
    settings = load_settings(user_id)
    return settings.get(category, {}).get(key, default)


def set_setting(user_id: int, category: str, key: str, value):
    """Met à jour une valeur de paramètre spécifique."""
    settings = load_settings(user_id)
    if category not in settings:
        settings[category] = {}
    settings[category][key] = value
    save_settings(user_id, settings)


def _deep_merge(default: dict, override: dict) -> dict:
    """Fusionne override dans default récursivement."""
    result = default.copy()
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result
