import os
import sys

def setup_imports():
    """
    Stellt sicher, dass der Projekt-Hauptordner im Python-Importpfad liegt.
    Dadurch funktionieren relative Imports wie 'from hero_system.hero_loader import ...'
    auch beim Start aus Unterordnern oder der IDE.
    """
    base_path = os.path.dirname(os.path.abspath(__file__))
    if base_path not in sys.path:
        sys.path.insert(0, base_path)
    return base_path


"""
Wenn du später mehrere Subsysteme hast (z. B. ui, battle_system, world),
kannst du das in setup_paths.py erweitern:


def setup_imports():
    base_path = os.path.dirname(os.path.abspath(__file__))
    subdirs = ["hero_system", "ui", "battle_system", "world"]
    for sub in subdirs:
        full = os.path.join(base_path, sub)
        if os.path.isdir(full) and full not in sys.path:
            sys.path.insert(0, full)
    return base_path


Dann brauchst du dich nie wieder um Pfade kümmern.
Einmal aufgerufen – alles sauber verfügbar ✅
"""