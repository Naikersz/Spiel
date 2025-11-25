import os
import json
from core.constants import BASE_PATH

DATA_DIR = os.path.join(BASE_PATH, "data")
LEVEL_DATA_FILE = os.path.join(DATA_DIR, "level_data.json")

# Default-Konfiguration pro Level/Feld
DEFAULT_LEVEL_SETTINGS = {
    "enemy_count": 5,
    "enchantment_min": 0,
    "enchantment_max": 0,
    "monster_level_min": 1,
    "monster_level_max": 10,
}


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _load_all_level_data():
    _ensure_dir()
    if not os.path.exists(LEVEL_DATA_FILE):
        return {}
    try:
        with open(LEVEL_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Fehler beim Laden von level_data.json: {e}")
        return {}


def _save_all_level_data(data: dict):
    _ensure_dir()
    with open(LEVEL_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_level_settings(level_key: str) -> dict:
    """
    Lädt Settings für ein bestimmtes Level (z.B. 'Feld_1').
    Falls keine existieren, werden Defaults angelegt.
    """
    all_data = _load_all_level_data()
    settings = all_data.get(level_key)

    if settings is None:
        settings = DEFAULT_LEVEL_SETTINGS.copy()
        all_data[level_key] = settings
        _save_all_level_data(all_data)

    # Fehlende Keys auffüllen (falls du später etwas ergänzt)
    changed = False
    for k, v in DEFAULT_LEVEL_SETTINGS.items():
        if k not in settings:
            settings[k] = v
            changed = True
    if changed:
        all_data[level_key] = settings
        _save_all_level_data(all_data)

    return settings


def save_level_settings(level_key: str, settings: dict):
    """
    Speichert Settings für ein bestimmtes Level.
    """
    all_data = _load_all_level_data()
    all_data[level_key] = settings
    _save_all_level_data(all_data)
