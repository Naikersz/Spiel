"""Global Dev-Settings (nur In-Memory, keine Dateien)"""
# Dieses Modul stellt einen einfachen globalen Dev-Flag bereit,
# ohne irgendetwas auf die Festplatte zu schreiben.

DEFAULT_DEV_SETTINGS = {
    "dev_mode": False,
    # Rest aktuell ungenutzt, kann später wiederverwendet werden
    "enemy_count": 5,
    "enchantment_min": 0,
    "enchantment_max": 0,
    "monster_level_min": 1,
    "monster_level_max": 10,
}

# Interner, veränderbarer Zustand (gilt global im Prozess)
_DEV_STATE = DEFAULT_DEV_SETTINGS.copy()


def load_dev_settings() -> dict:
    """Gibt eine Kopie des aktuellen Dev-States zurück."""
    return _DEV_STATE.copy()


def save_dev_settings(settings: dict):
    """Aktualisiert den globalen Dev-State (nur im Speicher)."""
    if not isinstance(settings, dict):
        return
    _DEV_STATE.update(settings)


def set_dev_mode(enabled: bool):
    """Schaltet den Dev-Modus global an/aus (nur im Speicher)."""
    _DEV_STATE["dev_mode"] = bool(enabled)
