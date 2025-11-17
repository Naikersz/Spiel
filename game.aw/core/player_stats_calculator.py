"""
Player Stats Calculator - Berechnet Spieler-Stats inklusive ausgerüsteter Items
"""
import json
import os
from typing import Dict, Any, Optional
from core.constants import SAVE_ROOT, SAVE_SLOTS


class PlayerStatsCalculator:
    """Berechnet Spieler-Stats aus Basis-Stats und ausgerüsteten Items"""
    
    def __init__(self):
        pass
    
    def load_player_data(self, slot_index: int) -> Optional[Dict[str, Any]]:
        """
        Lädt Spielerdaten aus einem Save-Slot
        
        Args:
            slot_index: Index des Save-Slots (0-2)
            
        Returns:
            Dictionary mit Spielerdaten oder None
        """
        if slot_index < 0 or slot_index >= len(SAVE_SLOTS):
            return None
        
        slot_name = SAVE_SLOTS[slot_index]
        player_path = os.path.join(SAVE_ROOT, slot_name, "player.json")
        
        if not os.path.exists(player_path):
            return None
        
        try:
            with open(player_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Fehler beim Laden von Spielerdaten: {e}")
            return None
    
    def _extract_item_stats(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrahiert Stats aus einem Item
        Items können verschiedene Strukturen haben:
        - base_stats: {damage, armour, evasion, etc.}
        - direkte Stats: defense, magic_defense, attack_speed, etc.
        
        Args:
            item: Item-Dictionary
            
        Returns:
            Dictionary mit allen Stats des Items
        """
        if not item:
            return {}
        
        stats = {}
        
        # Prüfe base_stats (moderne Struktur)
        if "base_stats" in item:
            base_stats = item["base_stats"]
            for key, value in base_stats.items():
                stats[key] = stats.get(key, 0) + value
        
        # Prüfe direkte Stats (alte Struktur)
        stat_keys = [
            "defense", "defence", "magic_defense", "magic_defence",
            "damage", "attack_speed", "movement_speed",
            "armour", "armor", "evasion", "energy_shield",
            "block_chance", "health", "strength", "intelligence",
            "dexterity", "speed"
        ]
        
        for key in stat_keys:
            if key in item:
                # Normalisiere Schlüsselnamen
                normalized_key = key
                if key == "defence":
                    normalized_key = "defense"
                elif key == "magic_defence":
                    normalized_key = "magic_defense"
                elif key == "armor":
                    normalized_key = "armour"
                
                stats[normalized_key] = stats.get(normalized_key, 0) + item[key]
        
        return stats
    
    def calculate_total_stats(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Berechnet Gesamt-Stats des Spielers
        
        Args:
            player_data: Spielerdaten aus player.json
            
        Returns:
            Dictionary mit berechneten Gesamt-Stats
        """
        if not player_data:
            return {}
        
        # Starte mit Basis-Stats
        base_stats = player_data.get("stats", {})
        total_stats = {
            "health": base_stats.get("health", 100),
            "max_health": base_stats.get("health", 100),
            "strength": base_stats.get("strength", 0),
            "intelligence": base_stats.get("intelligence", 0),
            "dexterity": base_stats.get("dexterity", 0),
            "speed": base_stats.get("speed", 0),
            "damage": 0,
            "defense": 0,
            "magic_defense": 0,
            "armour": 0,
            "evasion": 0,
            "energy_shield": 0,
            "block_chance": 0,
            "attack_speed": 1.0,
            "movement_speed": 0
        }
        
        # Füge Stats aus ausgerüsteten Items hinzu
        equipped = player_data.get("equipped", {})
        
        # Liste aller Equipment-Slots
        equipment_slots = [
            "weapon", "helmet", "chest", "pants", "gloves", 
            "boots", "shield", "glove"  # glove für Kompatibilität
        ]
        
        for slot in equipment_slots:
            item = equipped.get(slot)
            if item:
                item_stats = self._extract_item_stats(item)
                
                # Addiere alle Item-Stats zu den Gesamt-Stats
                for stat_name, stat_value in item_stats.items():
                    if isinstance(stat_value, (int, float)):
                        # Für bestimmte Stats verwenden wir spezielle Logik
                        if stat_name in ["attack_speed"]:
                            # Attack Speed: Multipliziere mit dem Wert (Werte > 1 sind Multiplikatoren)
                            if stat_name in total_stats and stat_value > 0:
                                if stat_value >= 1.0:
                                    # Wert ist ein Multiplikator
                                    total_stats[stat_name] *= stat_value
                                else:
                                    # Wert ist ein Bonus (z.B. 0.1 = +10%)
                                    total_stats[stat_name] *= (1.0 + stat_value)
                        else:
                            # Normale Stats werden addiert
                            if stat_name in total_stats:
                                total_stats[stat_name] += stat_value
                            else:
                                total_stats[stat_name] = stat_value
        
        # Stelle sicher, dass min/max Werte eingehalten werden
        if total_stats["health"] <= 0:
            total_stats["health"] = 1
        if total_stats["max_health"] <= 0:
            total_stats["max_health"] = 1
        if total_stats["attack_speed"] <= 0:
            total_stats["attack_speed"] = 1.0
        
        return total_stats
    
    def get_player_stats(self, slot_index: int) -> Optional[Dict[str, Any]]:
        """
        Lädt Spielerdaten und berechnet Gesamt-Stats
        
        Args:
            slot_index: Index des Save-Slots
            
        Returns:
            Dictionary mit berechneten Stats oder None
        """
        player_data = self.load_player_data(slot_index)
        if not player_data:
            return None
        
        stats = self.calculate_total_stats(player_data)
        
        # Füge zusätzliche Informationen hinzu
        result = {
            "stats": stats,
            "name": player_data.get("name", "Unbekannt"),
            "class_name": player_data.get("class_name", "Unbekannt"),
            "level": player_data.get("level", 1)
        }
        
        return result

