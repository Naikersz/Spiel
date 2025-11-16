"""
Starter Gear Distributor - умная выдача стартовой экипировки
Использует существующую JSON базу предметов
"""
import os
import json
from typing import Dict, Optional, Any


class StarterGearDistributor:
    """Распределение стартовой экипировки"""
    
    def __init__(self, base_path: str):
        """
        Инициализация распределителя экипировки
        
        Args:
            base_path: Базовый путь к проекту
        """
        self.base_path = base_path
        self.data_dir = os.path.join(base_path, "game", "data")
    
    def load_item_data(self, item_name: str) -> Optional[Dict[str, Any]]:
        """
        Загружает данные предмета
        
        Args:
            item_name: Имя предмета
            
        Returns:
            Dict: Данные предмета или None
        """
        items_dir = os.path.join(self.data_dir, "items")
        
        # Проверяем оружие
        weapons_file = os.path.join(items_dir, "weapons.json")
        if os.path.exists(weapons_file):
            try:
                with open(weapons_file, "r", encoding="utf-8") as f:
                    weapons = json.load(f)
                    for weapon in weapons:
                        if weapon.get("id") == item_name or weapon.get("name", "").lower().replace(" ", "_") == item_name.lower():
                            return self._get_minimal_item(weapon)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Проверяем броню
        armor_dir = os.path.join(items_dir, "armor")
        armor_files = {
            "helmets": "helmets.json",
            "pants": "pants.json",
            "gloves": "gloves.json",
            "boots": "boots.json",
            "shields": "shields.json"
        }
        
        for armor_type, filename in armor_files.items():
            armor_file = os.path.join(armor_dir, filename)
            if os.path.exists(armor_file):
                try:
                    with open(armor_file, "r", encoding="utf-8") as f:
                        armor_items = json.load(f)
                        for item in armor_items:
                            if item.get("id") == item_name or item.get("name", "").lower().replace(" ", "_") == item_name.lower():
                                return self._get_minimal_item(item)
                except (json.JSONDecodeError, IOError):
                    pass
        
        # Проверяем chest (может быть в разных файлах)
        # Для chest ищем в разных местах
        chest_patterns = ["chest", "armor", "robe", "tunic", "jerkin"]
        for pattern in chest_patterns:
            if pattern in item_name.lower():
                # Ищем в разных файлах брони
                for armor_type, filename in armor_files.items():
                    armor_file = os.path.join(armor_dir, filename)
                    if os.path.exists(armor_file):
                        try:
                            with open(armor_file, "r", encoding="utf-8") as f:
                                armor_items = json.load(f)
                                for item in armor_items:
                                    item_id = item.get("id", "").lower()
                                    item_name_lower = item_name.lower()
                                    if pattern in item_id or pattern in item_name_lower:
                                        return self._get_minimal_item(item)
                        except (json.JSONDecodeError, IOError):
                            pass
        
        return None
    
    def _get_minimal_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создает копию предмета с минимальными значениями
        
        Args:
            item_data: Данные предмета
            
        Returns:
            Dict: Предмет с минимальными значениями
        """
        item_copy = item_data.copy()
        
        # Заменяем диапазоны на минимальные значения
        for key, value in item_copy.items():
            if isinstance(value, dict):
                if "min" in value and "max" in value:
                    item_copy[key] = value["min"]
                else:
                    # Рекурсивно обрабатываем вложенные словари
                    item_copy[key] = self._process_dict(value)
        
        return item_copy
    
    def _process_dict(self, d: Dict[str, Any]) -> Any:
        """Рекурсивно обрабатывает словарь"""
        result = {}
        for key, value in d.items():
            if isinstance(value, dict):
                if "min" in value and "max" in value:
                    result[key] = value["min"]
                else:
                    result[key] = self._process_dict(value)
            else:
                result[key] = value
        return result
    
    def _detect_slot(self, item_name: str) -> Optional[str]:
        """
        Определяет слот экипировки по имени предмета
        
        Args:
            item_name: Имя предмета
            
        Returns:
            str: Название слота или None
        """
        name = item_name.lower()
        
        if any(word in name for word in ["sword", "staff", "dagger", "weapon"]):
            return "weapon"
        if any(word in name for word in ["helm", "hat", "helmet"]):
            return "helmet"
        if any(word in name for word in ["chest", "armor", "robe", "tunic", "jerkin"]):
            return "chest"
        if any(word in name for word in ["pants", "legs", "hose"]):
            return "pants"
        if any(word in name for word in ["glove", "gloves"]):
            return "gloves"
        if any(word in name for word in ["boots", "shoe", "boot"]):
            return "boots"
        if "shield" in name:
            return "shield"
        
        return None
    
    def distribute_starter_gear(self, hero_class: Dict[str, Any]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Распределяет стартовую экипировку для класса
        
        Args:
            hero_class: Данные класса персонажа
            
        Returns:
            Dict: Словарь слотов экипировки
        """
        equipped = {
            "weapon": None,
            "helmet": None,
            "chest": None,
            "pants": None,
            "gloves": None,
            "boots": None,
            "shield": None
        }
        
        starter_items = hero_class.get("starter_items", [])
        
        for item_name in starter_items:
            item_data = self.load_item_data(item_name)
            if not item_data:
                print(f"Warning: Starter item not found: {item_name}")
                continue
            
            # Определяем слот
            slot = self._detect_slot(item_name)
            if slot:
                equipped[slot] = item_data
            else:
                # Пытаемся определить по item_type
                item_type = item_data.get("item_type", "").lower()
                if item_type in equipped:
                    equipped[item_type] = item_data
        
        return equipped

