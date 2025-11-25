import json
import os
import random
from typing import Any, Dict, List, Optional

from core.constants import BASE_PATH


ITEM_FILES = [
    "weapons.json",
    "helmets.json",
    "chests.json",
    "gloves.json",
    "pants.json",
    "boots.json",
    "shields.json",
]


class LootGenerator:
    """
    Erzeugt Item-Drops auf Basis der Item-JSON-Dateien und Enchantments.
    """

    DROP_CHANCE = 0.5
    ENCHANT_ROLL_CHANCE = 0.05

    def __init__(self):
        self.data_path = os.path.join(BASE_PATH, "data")
        self.item_pool: List[Dict[str, Any]] = self._load_all_items()
        self.enchantments: List[Dict[str, Any]] = self._load_enchantments()

    # ------------------------------------------------------------------ #
    def _load_json_file(self, filename: str) -> List[Dict[str, Any]]:
        path = os.path.join(self.data_path, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[LootGenerator] Datei fehlt: {path}")
        except json.JSONDecodeError:
            print(f"[LootGenerator] Ungültiges JSON: {path}")
        return []

    def _load_all_items(self) -> List[Dict[str, Any]]:
        pool: List[Dict[str, Any]] = []
        for filename in ITEM_FILES:
            pool.extend(self._load_json_file(filename))
        return pool

    def _load_enchantments(self) -> List[Dict[str, Any]]:
        return self._load_json_file("enchantments.json")

    # ------------------------------------------------------------------ #
    def generate_loot(self, monster_level: int) -> Optional[Dict[str, Any]]:
        """
        Generiert ein Item, das zu einem Gegnerlevel passt. Kann None zurückgeben,
        wenn kein Drop gerollt wurde oder keine passenden Items existieren.
        """
        if random.random() > self.DROP_CHANCE:
            return None

        candidate = self._pick_item_for_level(monster_level)
        if not candidate:
            return None

        rolled_item = self._build_item(candidate)
        rolled_item["enchantments"] = self._roll_enchantments(
            rolled_item.get("item_level", monster_level),
            rolled_item.get("enchant_slots", 0),
            candidate.get("possible_enchantments", []),
        )

        return rolled_item

    def _pick_item_for_level(self, monster_level: int) -> Optional[Dict[str, Any]]:
        if monster_level <= 0:
            monster_level = 1

        allowed_diff = max(1, int(monster_level * 0.05))
        min_level = max(1, monster_level - allowed_diff)
        max_level = monster_level

        candidates = [
            item for item in self.item_pool
            if min_level <= item.get("item_level", 1) <= max_level
        ]

        if not candidates:
            return None

        return random.choice(candidates)

    def _build_item(self, template: Dict[str, Any]) -> Dict[str, Any]:
        item = {
            "id": template.get("id"),
            "name": template.get("name"),
            "item_type": template.get("item_type"),
            "item_level": template.get("item_level", 1),
            "min_player_level": template.get("min_player_level", 1),
            "material": template.get("material", {}),
            "enchant_slots": template.get("enchant_slots", 0),
            "requirements": self._roll_range_block(template.get("requirements", {})),
            "stats": self._roll_range_block(template.get("base_stats", {})),
        }
        return item

    def _roll_range_block(self, block: Dict[str, Any]) -> Dict[str, Any]:
        """
        Erwartet Keys im Format xyz_min/xyz_max und erzeugt fertige Werte.
        """
        rolled: Dict[str, Any] = {}

        for key, value in block.items():
            if not key.endswith("_min"):
                continue

            base_key = key[:-4]  # Entfernt "_min"
            min_val = value
            max_val = block.get(f"{base_key}_max", min_val)

            if isinstance(min_val, float) or isinstance(max_val, float):
                rolled_value = random.uniform(float(min_val), float(max_val))
            else:
                rolled_value = random.randint(int(min_val), int(max_val))

            rolled[base_key] = rolled_value

        return rolled

    def _roll_enchantments(
        self,
        item_level: int,
        max_slots: int,
        allowed_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        if max_slots <= 0:
            return []

        candidates = [
            e for e in self.enchantments
            if e.get("item_level_min", 1) <= item_level <= e.get("item_level_max", 999)
        ]

        if allowed_ids:
            allowed_set = set(allowed_ids)
            candidates = [e for e in candidates if e.get("id") in allowed_set]

        random.shuffle(candidates)

        results: List[Dict[str, Any]] = []
        tier_cap = self._max_tier_for_level(item_level)

        for enchant in candidates:
            if len(results) >= max_slots:
                break
            if random.random() > self.ENCHANT_ROLL_CHANCE:
                continue

            value_min = enchant.get("value_min", 0)
            value_max = enchant.get("value_max", value_min)
            base_value = random.randint(value_min, value_max) if value_max > value_min else value_min

            rolled_tier = random.randint(1, tier_cap)
            final_value = base_value * rolled_tier

            results.append({
                "id": enchant.get("id"),
                "name": enchant.get("name"),
                "type": enchant.get("type"),
                "value": final_value,
                "rolled_tier": rolled_tier,
            })

        return results

    @staticmethod
    def _max_tier_for_level(level: int) -> int:
        if level <= 0:
            return 1
        return 1 + ((level - 1) // 20)

