import os
import json
from hero_system.hero_loader import save_hero

# ----------------------------------------------------------
# 🔹 Globales Inventar laden / speichern
# ----------------------------------------------------------
def load_global_inventory(base_path):
    save_path = os.path.join(base_path, "save")
    os.makedirs(save_path, exist_ok=True)

    inv_path = os.path.join(save_path, "global_inventory.json")

    if not os.path.exists(inv_path) or os.path.getsize(inv_path) == 0:
        with open(inv_path, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []

    with open(inv_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ global_inventory.json beschädigt, wird neu erstellt.")
            with open(inv_path, "w", encoding="utf-8") as fw:
                json.dump([], fw)
            return []


def save_global_inventory(base_path, inventory):
    save_path = os.path.join(base_path, "save")
    os.makedirs(save_path, exist_ok=True)
    inv_path = os.path.join(save_path, "global_inventory.json")

    with open(inv_path, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=4, ensure_ascii=False)


# ----------------------------------------------------------
# 🔹 Item aus globalem Inventar an Held anlegen
# ----------------------------------------------------------
def equip_item_from_global(hero, base_path):
    """
    Zeigt alle Items im globalen Inventar an,
    fragt welches angelegt werden soll und aktualisiert Held + Inventar.
    """
    inventory = load_global_inventory(base_path)
    if not inventory:
        print("📦 Globales Inventar ist leer.")
        return hero

    print("\n🎒 Globales Inventar:")
    for i, item in enumerate(inventory, start=1):
        print(f"{i}. {item.get('name')} (Typ: {item.get('item_type')}, Level: {item.get('item_level')})")

    try:
        choice = int(input("\nWelches Item soll angelegt werden? (Zahl eingeben, 0 = abbrechen): "))
    except ValueError:
        print("❌ Ungültige Eingabe.")
        return hero

    if choice == 0 or choice > len(inventory):
        print("🔙 Abgebrochen.")
        return hero

    selected_item = inventory.pop(choice - 1)
    item_type = selected_item.get("item_type")

    # Stelle sicher, dass Held 'equipped' Slot hat
    if "equipped" not in hero:
        hero["equipped"] = {}

    # Falls schon ein Item im Slot liegt → ins Inventar zurück
    if item_type in hero["equipped"] and hero["equipped"][item_type]:
        old_item = hero["equipped"][item_type]
        print(f"↩️ {old_item['name']} wurde abgelegt und ins Inventar verschoben.")
        inventory.append(old_item)

    # Neues Item anlegen
    hero["equipped"][item_type] = selected_item
    print(f"✅ {selected_item['name']} wurde angelegt!")

    # Änderungen speichern
    save_hero(hero, base_path)
    save_global_inventory(base_path, inventory)

    return hero


# ----------------------------------------------------------
# 🔹 Item vom Helden ins globale Inventar verschieben
# ----------------------------------------------------------
def transfer_equipment_to_global(hero, base_path):
    """
    Zeigt angelegte Items an und fragt, welche ins globale Inventar verschoben werden sollen.
    """
    if "equipped" not in hero or not hero["equipped"]:
        print("⚠️ Held hat keine ausgerüsteten Gegenstände.")
        return

    equipped_items = hero["equipped"]
    print("\n🧙‍♂️ Ausgerüstete Gegenstände:")
    slots = list(equipped_items.keys())
    for i, slot in enumerate(slots, start=1):
        item = equipped_items[slot]
        if item:
            print(f"{i}. {item['name']} (Typ: {slot})")
        else:
            print(f"{i}. [leer] ({slot})")

    try:
        choice = int(input("\nWelchen Gegenstand willst du ablegen? (Zahl, 0 = abbrechen): "))
    except ValueError:
        print("❌ Ungültige Eingabe.")
        return

    if choice == 0 or choice > len(slots):
        print("🔙 Abgebrochen.")
        return

    slot = slots[choice - 1]
    item = equipped_items.get(slot)
    if not item:
        print("⚠️ Kein Gegenstand in diesem Slot.")
        return

    inventory = load_global_inventory(base_path)
    inventory.append(item)
    equipped_items[slot] = None

    print(f"📦 {item['name']} wurde ins globale Inventar verschoben!")

    save_hero(hero, base_path)
    save_global_inventory(base_path, inventory)
