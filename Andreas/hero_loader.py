import os
import json

# ----------------------------------------------------------
# 🔹 Alle gespeicherten Helden laden
# ----------------------------------------------------------
def load_all_heroes(base_path):
    """
    Lädt alle Heldennamen aus dem save/heroes Verzeichnis.
    Gibt ein Dict {heldenname: dateipfad} zurück.
    """
    heroes_dir = os.path.join(base_path, "save", "heroes")

    if not os.path.exists(heroes_dir):
        print(f"⚠️ Kein Helden-Ordner gefunden unter: {heroes_dir}")
        return {}

    hero_files = [f for f in os.listdir(heroes_dir) if f.endswith(".json")]
    if not hero_files:
        return {}

    heroes = {}
    for file_name in hero_files:
        hero_name = os.path.splitext(file_name)[0]
        heroes[hero_name] = os.path.join(heroes_dir, file_name)
    return heroes


# ----------------------------------------------------------
# 🔹 Einzelnen Helden laden
# ----------------------------------------------------------
def load_hero(hero_name, base_path):
    """
    Lädt einen einzelnen Helden aus der save/heroes/<name>.json Datei.
    Gibt den Helden als Dictionary zurück.
    """
    hero_file = os.path.join(base_path, "save", "heroes", f"{hero_name}.json")

    if not os.path.exists(hero_file):
        raise FileNotFoundError(f"❌ Heldendatei nicht gefunden: {hero_file}")

    with open(hero_file, "r", encoding="utf-8") as f:
        try:
            hero = json.load(f)
        except json.JSONDecodeError:
            raise ValueError(f"❌ Fehler beim Laden von {hero_file} – Datei beschädigt oder leer")

    print(f"✅ Held '{hero_name}' erfolgreich geladen.")
    return hero


# ----------------------------------------------------------
# 🔹 Helden speichern (optional, wird oft gebraucht)
# ----------------------------------------------------------
def save_hero(hero, base_path):
    """
    Speichert den Helden im save/heroes Verzeichnis.
    """
    heroes_dir = os.path.join(base_path, "save", "heroes")
    os.makedirs(heroes_dir, exist_ok=True)

    hero_name = hero.get("name", "unbekannt")
    hero_file = os.path.join(heroes_dir, f"{hero_name}.json")

    with open(hero_file, "w", encoding="utf-8") as f:
        json.dump(hero, f, indent=4, ensure_ascii=False)

    print(f"💾 Held '{hero_name}' gespeichert unter {hero_file}")
