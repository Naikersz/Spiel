import os
from hero_system.hero_loader import load_all_heroes, load_hero
from hero_system.inventory_manager import (
    transfer_equipment_to_global,
    equip_item_from_global,
    load_global_inventory
)

# ----------------------------------------------------------
# 🧭 Basis-Setup
# ----------------------------------------------------------
base_path = os.path.abspath(os.path.dirname(__file__))
save_path = os.path.join(base_path, "save")
hero_path = os.path.join(save_path, "heroes")

print(f"📂 base_path: {base_path}")
print(f"📂 save_path: {save_path}")
print(f"📂 hero_path: {hero_path}")

# Falls der Helden-Ordner fehlt, erstellen
if not os.path.exists(hero_path):
    print("⚠️ Kein Helden-Ordner gefunden. Erstelle neuen...")
    os.makedirs(hero_path, exist_ok=True)

# ----------------------------------------------------------
# 🧙 Helden laden und auswählen
# ----------------------------------------------------------
heroes = load_all_heroes(base_path)

if not heroes:
    print("⚠️ Keine gespeicherten Helden gefunden.")
    print("Bitte zuerst über hero_creator.py einen Helden erstellen.")
    exit()

print("\n🎭 Verfügbare Helden:")
for i, hero_name in enumerate(heroes.keys(), start=1):
    print(f"{i}. {hero_name}")

try:
    choice = int(input("\n➡️ Welchen Helden willst du laden? (Nummer): "))
    hero_name = list(heroes.keys())[choice - 1]
except (ValueError, IndexError):
    print("❌ Ungültige Auswahl!")
    exit()

hero = load_hero(hero_name, base_path)
print(f"\n🧙 Held '{hero_name}' erfolgreich geladen!\n")

# ----------------------------------------------------------
# 🎒 Inventaroptionen
# ----------------------------------------------------------
while True:
    print("\n=== 🧭 INVENTAR-MANAGER ===")
    print("1️⃣  Ausrüstung ins globale Inventar verschieben")
    print("2️⃣  Gegenstand aus globalem Inventar anlegen")
    print("3️⃣  Globales Inventar anzeigen")
    print("4️⃣  Spiel beenden")

    choice = input("\n➡️ Auswahl: ")

    if choice == "1":
        transfer_equipment_to_global(hero, base_path)

    elif choice == "2":
        equip_item_from_global(hero, base_path)

    elif choice == "3":
        inventory = load_global_inventory(base_path)
        print("\n🎒 Globales Inventar:")

        if not inventory:
            print("📦 Das globale Inventar ist leer.")
        else:
            for i, item in enumerate(inventory, start=1):
                name = item.get("name", "Unbekanntes Item")
                item_type = item.get("item_type", "unbekannt")
                level = item.get("item_level", "?")
                print(f"{i}. {name} (Typ: {item_type}, Level: {level})")

    elif choice == "4":
        print("💾 Spiel beendet. Änderungen gespeichert.")
        break

    else:
        print("❌ Ungültige Eingabe, bitte wähle 1-4.")
