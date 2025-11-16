"""
Player Initializer - создание нового персонажа
Интегрируется с hero_creator и CharacterCreationMenu
"""
import os
import json
from datetime import datetime
from typing import Dict, Optional, Any
from .player_loader import PlayerLoader
from .player_data_validator import PlayerDataValidator


class PlayerInitializer:
    """Создание нового персонажа"""
    
    def __init__(self, base_path: str):
        """
        Инициализация создателя персонажей
        
        Args:
            base_path: Базовый путь к проекту
        """
        self.base_path = base_path
        self.data_dir = os.path.join(base_path, "game", "data")
        self.loader = PlayerLoader(base_path)
    
    def load_hero_class(self, class_id: str) -> Optional[Dict[str, Any]]:
        """
        Загружает данные класса персонажа
        
        Args:
            class_id: ID класса
            
        Returns:
            Dict: Данные класса или None
        """
        # Пробуем несколько путей к файлу
        possible_paths = [
            os.path.join(self.data_dir, "hero_classes.json"),
            os.path.join(self.base_path, "game", "data", "hero_classes.json"),
            "game/data/hero_classes.json",
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "hero_classes.json")
        ]
        
        classes_file = None
        for path in possible_paths:
            if os.path.exists(path):
                classes_file = path
                break
        
        if not classes_file:
            print(f"Error: hero_classes.json not found. Tried paths: {possible_paths}")
            return None
        
        try:
            with open(classes_file, "r", encoding="utf-8") as f:
                classes = json.load(f)
            
            # Если classes - это список
            if isinstance(classes, list):
                for hero_class in classes:
                    if hero_class.get("id") == class_id:
                        return hero_class
            # Если classes - это dict с ключами-классами
            elif isinstance(classes, dict):
                if class_id in classes:
                    return classes[class_id]
            
            print(f"Class '{class_id}' not found in {classes_file}. Available classes: {[c.get('id', 'unknown') if isinstance(c, dict) else c for c in (classes if isinstance(classes, list) else list(classes.keys()))]}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading hero classes from {classes_file}: {e}")
        
        return None
    
    def load_item_data(self, item_name: str) -> Optional[Dict[str, Any]]:
        """
        Загружает данные предмета
        
        Args:
            item_name: Имя предмета
            
        Returns:
            Dict: Данные предмета или None
        """
        items_dir = os.path.join(self.data_dir, "items")
        
        # Проверяем все типы предметов
        item_types = ["weapons", "armor"]
        armor_subdirs = ["helmets", "pants", "gloves", "boots", "shields"]
        
        # Проверяем оружие
        weapons_file = os.path.join(items_dir, "weapons.json")
        if os.path.exists(weapons_file):
            try:
                with open(weapons_file, "r", encoding="utf-8") as f:
                    weapons = json.load(f)
                    for weapon in weapons:
                        if weapon.get("id") == item_name or weapon.get("name", "").lower().replace(" ", "_") == item_name.lower():
                            return weapon
            except (json.JSONDecodeError, IOError):
                pass
        
        # Проверяем броню
        armor_dir = os.path.join(items_dir, "armor")
        for subdir in armor_subdirs:
            armor_file = os.path.join(armor_dir, f"{subdir}.json")
            if os.path.exists(armor_file):
                try:
                    with open(armor_file, "r", encoding="utf-8") as f:
                        armor_items = json.load(f)
                        for item in armor_items:
                            if item.get("id") == item_name or item.get("name", "").lower().replace(" ", "_") == item_name.lower():
                                return item
                except (json.JSONDecodeError, IOError):
                    pass
        
        return None
    
    def create_hero(self, class_id: str, name: str) -> Optional[Dict[str, Any]]:
        """
        Создает нового персонажа
        
        Args:
            class_id: ID класса
            name: Имя персонажа
            
        Returns:
            Dict: Данные созданного персонажа или None при ошибке
        """
        # Проверяем существование персонажа с таким именем
        if self.loader.hero_exists(name):
            print(f"Hero with name '{name}' already exists")
            return None
        
        # Загружаем класс
        hero_class = self.load_hero_class(class_id)
        if not hero_class:
            print(f"Unknown class: {class_id}")
            return None
        
        # Создаем базовые характеристики
        base_stats = {
            "health": hero_class.get("base_health", 100),
            "strength": hero_class.get("base_strength", 10),
            "intelligence": hero_class.get("base_intelligence", 10),
            "dexterity": hero_class.get("base_dexterity", 10),
            "speed": hero_class.get("base_speed", 10),
            "level": 1,
            "experience": 0
        }
        
        # Создаем структуру персонажа
        hero = {
            "name": name,
            "class_id": class_id,
            "class_name": hero_class.get("name", "Unknown"),
            "created_at": datetime.now().isoformat(),
            "stats": base_stats,
            "equipped": {
                "weapon": None,
                "helmet": None,
                "chest": None,
                "pants": None,
                "gloves": None,
                "boots": None,
                "shield": None
            }
        }
        
        # Выдаем стартовую экипировку
        from ..setup.starter_gear_distributor import StarterGearDistributor
        distributor = StarterGearDistributor(self.base_path)
        hero["equipped"] = distributor.distribute_starter_gear(hero_class)
        
        # Рассчитываем итоговые характеристики
        from ..setup.progression_manager import ProgressionManager
        progression = ProgressionManager()
        hero = progression.calculate_total_stats(hero)
        
        # Сохраняем персонажа
        if self.loader.save_hero(hero):
            return hero
        
        return None

