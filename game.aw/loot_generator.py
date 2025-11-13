import os
import random
from generate_loot_item import generate_loot_item

def generate_enemy_loot(enemy_level: int, player_stats: dict, data_dir: str):
    """
    Generiert Loot, basierend auf Gegner-Level und Spielerwerten.
    """

    # --- Dropchance: Je höher das Gegnerlevel, desto seltener ---
    base_drop_chance = max(5, 50 - int(enemy_level * 0.4))  # z. B. Level 100 → ~10 %
    item_drop_bonus = player_stats.get("item_drop_bonus", 0)
    enchant_find_bonus = player_stats.get("enchant_find_bonus", 0)

    # --- Effektiver Dropwert (Bonus eingerechnet) ---
    effective_chance = base_drop_chance + item_drop_bonus
    if random.randint(1, 100) > effective_chance:
        return []  # Kein Loot gedroppt

    # --- 1 bis 3 Items droppen ---
    loot = []
    drop_count = random.randint(1, 3)

    # --- Itemtypen im Singular (Pluralisierung passiert automatisch) ---
    possible_items = ["helmet", "glove", "chest", "pant", "boot", "shield", "weapon"]

    for _ in range(drop_count):
        item_type = random.choice(possible_items)
        item = generate_loot_item(
            enemy_level=enemy_level,
            item_type=item_type,
            data_dir=data_dir,
            enchant_find_bonus=enchant_find_bonus
        )
        loot.append(item)

    return loot
