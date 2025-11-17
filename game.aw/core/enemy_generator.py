"""
Gegnergenerator für Kämpfe
Generiert Gegner-Kopien aus monster.json mit zufälligen Verzauberungen
"""
import json
import random
import os
from typing import List, Dict, Any


class EnemyGenerator:
    def __init__(self, data_path: str = None):
        """
        Initialisiert den Gegnergenerator
        
        Args:
            data_path: Pfad zum data Ordner (default: game.aw/data)
        """
        if data_path is None:
            base_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
            data_path = os.path.join(base_path, "data")
        
        self.data_path = data_path
        self.monsters = self._load_monsters()
        self.enchantments = self._load_enchantments()
    
    def _load_monsters(self) -> List[Dict[str, Any]]:
        """Lädt die Monster-Daten aus monster.json"""
        monster_file = os.path.join(self.data_path, "monster.json")
        try:
            with open(monster_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Fehler beim Laden von monster.json: {e}")
            return []
    
    def _load_enchantments(self) -> List[Dict[str, Any]]:
        """Lädt die Verzauberungen aus monster_enchantments.json"""
        enchantment_file = os.path.join(self.data_path, "monster_enchantments.json")
        try:
            with open(enchantment_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Fehler beim Laden von monster_enchantments.json: {e}")
            return []
    
    def _get_available_enchantments(self, monster_level: int) -> List[Dict[str, Any]]:
        """
        Gibt verfügbare Verzauberungen für das Monster-Level zurück
        
        Args:
            monster_level: Level des Monsters
            
        Returns:
            Liste der verfügbaren Verzauberungen
        """
        available = []
        for enchant in self.enchantments:
            min_level = enchant.get("min_level", 1)
            if monster_level >= min_level:
                available.append(enchant)
        return available
    
    def _select_random_enchantments(self, available_enchantments: List[Dict], count: int, max_slots: int = 6) -> List[Dict[str, Any]]:
        """
        Wählt zufällige Verzauberungen aus
        
        Args:
            available_enchantments: Liste verfügbarer Verzauberungen
            count: Anzahl der Verzauberungen
            max_slots: Maximale Anzahl an Slots (Standard: 6)
            
        Returns:
            Liste der ausgewählten Verzauberungen mit generierten Werten
        """
        if not available_enchantments or count <= 0:
            return []
        
        # Begrenze die Anzahl auf die verfügbaren Slots
        count = min(count, max_slots, len(available_enchantments))
        
        selected = random.sample(available_enchantments, count)
        result = []
        
        for enchant in selected:
            # Generiere einen zufälligen Wert basierend auf value_min und value_max
            value_min = enchant.get("value_min", 0)
            value_max = enchant.get("value_max", 0)
            value = random.randint(value_min, value_max) if value_max > value_min else value_min
            
            # Erstelle eine Kopie der Verzauberung mit generiertem Wert
            enchant_copy = enchant.copy()
            enchant_copy["value"] = value
            result.append(enchant_copy)
        
        return result
    
    def _randomize_stats(self, monster_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generiert zufällige Stats für ein Monster basierend auf min/max Werten
        
        Args:
            monster_data: Monster-Daten aus JSON
            
        Returns:
            Dictionary mit generierten Stats
        """
        stats_data = monster_data.get("stats", {})
        stats = {}
        
        # HP
        hp_min = stats_data.get("hp_min", 10)
        hp_max = stats_data.get("hp_max", 20)
        stats["hp"] = random.randint(hp_min, hp_max)
        stats["max_hp"] = stats["hp"]
        
        # Schaden
        dmg_min = stats_data.get("damage_min", 1)
        dmg_max = stats_data.get("damage_max", 5)
        stats["damage"] = random.randint(dmg_min, dmg_max)
        
        # Verteidigung
        def_min = stats_data.get("defense_min", 0)
        def_max = stats_data.get("defense_max", 5)
        stats["defense"] = random.randint(def_min, def_max)
        
        # Angriffsgeschwindigkeit
        atk_spd_min = stats_data.get("attack_speed_min", 1)
        atk_spd_max = stats_data.get("attack_speed_max", 2)
        stats["attack_speed"] = random.uniform(atk_spd_min, atk_spd_max)
        
        # Ausweichen
        eva_min = stats_data.get("evasion_min", 0)
        eva_max = stats_data.get("evasion_max", 10)
        stats["evasion"] = random.randint(eva_min, eva_max)
        
        return stats
    
    def generate_enemy(self, monster_id: str = None, enchantment_count: int = 0) -> Dict[str, Any]:
        """
        Generiert einen einzelnen Gegner
        
        Args:
            monster_id: ID des Monsters (wenn None, wird zufällig ausgewählt)
            enchantment_count: Anzahl der Verzauberungen (0 = keine)
            
        Returns:
            Dictionary mit Gegnerdaten
        """
        # Wähle Monster aus
        if monster_id:
            monster = next((m for m in self.monsters if m.get("id") == monster_id), None)
            if not monster:
                print(f"Monster '{monster_id}' nicht gefunden, verwende zufälliges Monster")
                monster = random.choice(self.monsters) if self.monsters else None
        else:
            monster = random.choice(self.monsters) if self.monsters else None
        
        if not monster:
            raise ValueError("Keine Monster verfügbar")
        
        # Erstelle eine Kopie des Monsters
        enemy = monster.copy()
        
        # Generiere Stats
        stats = self._randomize_stats(monster)
        enemy["generated_stats"] = stats
        
        # Generiere Verzauberungen wenn gewünscht
        enchantments = []
        if enchantment_count > 0:
            available = self._get_available_enchantments(monster.get("level", 1))
            max_slots = monster.get("enchant_slots", 6)
            enchantments = self._select_random_enchantments(available, enchantment_count, max_slots)
        
        enemy["enchantments"] = enchantments
        
        # Berechne finale Stats mit Verzauberungen
        final_stats, enchantment_bonuses = self._apply_enchantments_to_stats(stats, enchantments)
        enemy["final_stats"] = final_stats
        enemy["enchantment_bonuses"] = enchantment_bonuses
        
        return enemy
    
    def _apply_enchantments_to_stats(self, base_stats: Dict[str, Any], enchantments: List[Dict[str, Any]]) -> tuple:
        """
        Wendet Verzauberungen auf Basis-Stats an
        
        Args:
            base_stats: Basis-Stats des Gegners
            enchantments: Liste von Verzauberungen
            
        Returns:
            Tuple: (finale_stats, enchantment_bonuses)
        """
        # Kopiere Basis-Stats
        final_stats = base_stats.copy()
        enchantment_bonuses = {
            "hp": 0,
            "max_hp": 0,
            "damage": 0,
            "defense": 0,
            "attack_speed": 0.0,
            "evasion": 0
        }
        
        # Speichere Basis-Werte für Prozent-Berechnungen
        base_max_hp = base_stats.get("max_hp", base_stats.get("hp", 100))
        base_attack_speed = base_stats.get("attack_speed", 1.0)
        
        # Sammle zuerst alle Prozent-Boni (für korrekte Berechnung)
        total_hp_percent = 0
        total_attack_speed_percent = 0
        
        for enchant in enchantments:
            enchant_type = enchant.get("type", "")
            value = enchant.get("value", 0)
            
            if enchant_type == "hp_percent":
                # Sammle HP-Prozent-Boni (werden zusammen auf Basis-HP angewendet)
                total_hp_percent += value
            elif enchant_type == "attack_speed":
                # Sammle Attack Speed Prozent-Boni
                total_attack_speed_percent += value
        
        # Wende Prozent-Boni auf Basis-Werte an
        if total_hp_percent > 0:
            hp_bonus = int(base_max_hp * (total_hp_percent / 100.0))
            final_stats["max_hp"] = base_max_hp + hp_bonus
            final_stats["hp"] = final_stats.get("hp", base_max_hp) + hp_bonus
            enchantment_bonuses["max_hp"] = hp_bonus
            enchantment_bonuses["hp"] = hp_bonus
        
        if total_attack_speed_percent > 0:
            attack_speed_bonus = base_attack_speed * (total_attack_speed_percent / 100.0)
            final_stats["attack_speed"] = base_attack_speed + attack_speed_bonus
            enchantment_bonuses["attack_speed"] = attack_speed_bonus
        
        # Wende direkte Boni an
        for enchant in enchantments:
            enchant_type = enchant.get("type", "")
            value = enchant.get("value", 0)
            
            if enchant_type == "damage":
                # Direkter Schadensbonus
                final_stats["damage"] = final_stats.get("damage", 0) + value
                enchantment_bonuses["damage"] += value
            
            elif enchant_type == "res_physical":
                # Physische Resistenz (addiert zu Verteidigung)
                final_stats["defense"] = final_stats.get("defense", 0) + value
                enchantment_bonuses["defense"] += value
            
            # Weitere Verzauberungstypen können hier hinzugefügt werden
            # Für jetzt ignorieren wir element_damage, status effects, etc.
            # da diese in den Kampfmechaniken behandelt werden sollten
        
        return final_stats, enchantment_bonuses
    
    def generate_field_enemies(self, field_number: int) -> List[Dict[str, Any]]:
        """
        Generiert Gegner für ein Feld
        
        Args:
            field_number: Nummer des Feldes (1, 2, 3, ...)
            
        Returns:
            Liste von Gegnern
        """
        enemies = []
        
        # Feld 1: 3 normale Gegner, 1 mit 1-3 Verzauberungen, 1 mit 4-6 Verzauberungen
        if field_number == 1:
            # 3 normale Gegner (ohne Verzauberungen)
            for _ in range(3):
                enemies.append(self.generate_enemy(enchantment_count=0))
            
            # 1 Gegner mit 1-3 Verzauberungen
            enchant_count = random.randint(1, 3)
            enemies.append(self.generate_enemy(enchantment_count=enchant_count))
            
            # 1 Gegner mit 4-6 Verzauberungen
            enchant_count = random.randint(4, 6)
            enemies.append(self.generate_enemy(enchantment_count=enchant_count))
        
        # TODO: Weitere Felder können hier konfiguriert werden
        else:
            # Standard: 5 normale Gegner für andere Felder
            for _ in range(5):
                enemies.append(self.generate_enemy(enchantment_count=0))
        
        return enemies


def generate_enemies_for_field(field_number: int) -> List[Dict[str, Any]]:
    """
    Hilfsfunktion zum Generieren von Gegnern für ein Feld
    
    Args:
        field_number: Nummer des Feldes
        
    Returns:
        Liste von Gegnern
    """
    generator = EnemyGenerator()
    return generator.generate_field_enemies(field_number)

