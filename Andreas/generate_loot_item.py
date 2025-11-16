import json
import os
import random


def generate_loot_item(enemy_level: int,
                       item_type: str,
                       data_dir: str,
                       enchant_find_bonus: float = 0.0):
    """
    Generiert ein zufälliges Item basierend auf Gegner-Level und Item-Typ.
    """

    # --- Pfadaufbau relativ zu main.py ---
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_path, "data") if not os.path.isabs(data_dir) else data_dir

    if not os.path.exists(data_path):
        print(f"❌ Datenpfad nicht gefunden: {data_path}")
        return None
    else:
        print(f"✅ Datenpfad erkannt: {data_path}")

    # --- Sicherheitscheck: Gegnerlevel ---
    enemy_level = max(1, enemy_level)
    min_level = max(1, int(enemy_level * 0.9))
    item_level = random.randint(min_level, enemy_level)

    # --- Dateien laden ---
    item_file = os.path.join(data_path, f"{item_type}s.json")  # z. B. weapon → weapons.json
    enchant_file = os.path.join(data_path, "enchantments.json")

    if not os.path.exists(item_file):
        raise FileNotFoundError(f"Itemdatei nicht gefunden: {item_file}")
    if not os.path.exists(enchant_file):
        raise FileNotFoundError(f"Verzauberungsdatei nicht gefunden: {enchant_file}")

    with open(item_file, "r", encoding="utf-8") as f:
        item_data = json.load(f)

    with open(enchant_file, "r", encoding="utf-8") as f:
        enchant_data = json.load(f)

    # --- Zufälliges Basisitem auswählen ---
    base_item = random.choice(item_data)
    item = {
        "name": base_item["name"],
        "item_type": item_type,
        "item_level": item_level,
        "base_stats": base_item.get("base_stats", {}),
        "enchantments": []
    }

    # --- Verzauberungen bestimmen ---
    roll_chance = min(100, 20 + enchant_find_bonus)  # z. B. 20 % Basis + Bonus
    num_rolls = random.randint(0, 3)  # Maximal 3 Enchantments

    possible_enchants = [
        e for e in enchant_data
        if e["item_level_min"] <= item_level <= e["item_level_max"]
    ]

    rolled_types = set()

    for _ in range(num_rolls):
        if random.randint(1, 100) > roll_chance or not possible_enchants:
            continue

        enchant = random.choice(possible_enchants)
        # gleiche Basisverzauberung nur einmal pro Item
        if enchant["type"] in rolled_types:
            continue

        rolled_types.add(enchant["type"])
        value = random.randint(enchant["value_min"], enchant["value_max"])
        item["enchantments"].append({
            "name": enchant["name"],
            "type": enchant["type"],
            "value": value
        })

    return item
