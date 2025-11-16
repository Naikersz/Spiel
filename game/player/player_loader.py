"""
Player Loader - загрузка сохранений персонажей
Интегрируется с существующей системой hero_loader из Andreas
"""
import os
import json
from typing import Dict, List, Optional, Any
from .player_data_validator import PlayerDataValidator


class PlayerLoader:
    """Загрузка и управление сохранениями персонажей"""
    
    def __init__(self, base_path: str):
        """
        Инициализация загрузчика
        
        Args:
            base_path: Базовый путь к проекту
        """
        self.base_path = base_path
        self.heroes_dir = os.path.join(base_path, "save", "heroes")
        os.makedirs(self.heroes_dir, exist_ok=True)
    
    def load_all_heroes(self) -> Dict[str, str]:
        """
        Загружает все сохраненные персонажи
        
        Returns:
            Dict[str, str]: Словарь {имя_персонажа: путь_к_файлу}
        """
        if not os.path.exists(self.heroes_dir):
            return {}
        
        hero_files = [f for f in os.listdir(self.heroes_dir) if f.endswith(".json")]
        if not hero_files:
            return {}
        
        heroes = {}
        for file_name in hero_files:
            hero_name = os.path.splitext(file_name)[0]
            heroes[hero_name] = os.path.join(self.heroes_dir, file_name)
        
        return heroes
    
    def load_hero(self, hero_name: str, validate: bool = True) -> Optional[Dict[str, Any]]:
        """
        Загружает персонажа по имени
        
        Args:
            hero_name: Имя персонажа
            validate: Валидировать и исправлять данные
            
        Returns:
            Dict: Данные персонажа или None если не найден
        """
        hero_file = os.path.join(self.heroes_dir, f"{hero_name}.json")
        
        if not os.path.exists(hero_file):
            return None
        
        try:
            with open(hero_file, "r", encoding="utf-8") as f:
                hero_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading hero {hero_name}: {e}")
            return None
        
        # Валидация и исправление
        if validate:
            hero_data, was_fixed = PlayerDataValidator.validate_and_fix(hero_data)
            if was_fixed:
                # Сохраняем исправленные данные
                self.save_hero(hero_data)
        
        return hero_data
    
    def save_hero(self, hero_data: Dict[str, Any]) -> bool:
        """
        Сохраняет персонажа
        
        Args:
            hero_data: Данные персонажа
            
        Returns:
            bool: Успешно ли сохранено
        """
        hero_name = hero_data.get("name", "unknown")
        hero_file = os.path.join(self.heroes_dir, f"{hero_name}.json")
        
        try:
            with open(hero_file, "w", encoding="utf-8") as f:
                json.dump(hero_data, f, indent=4, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error saving hero {hero_name}: {e}")
            return False
    
    def delete_hero(self, hero_name: str) -> bool:
        """
        Удаляет сохранение персонажа
        
        Args:
            hero_name: Имя персонажа
            
        Returns:
            bool: Успешно ли удалено
        """
        hero_file = os.path.join(self.heroes_dir, f"{hero_name}.json")
        
        if os.path.exists(hero_file):
            try:
                os.remove(hero_file)
                return True
            except IOError:
                return False
        
        return False
    
    def hero_exists(self, hero_name: str) -> bool:
        """
        Проверяет существование персонажа
        
        Args:
            hero_name: Имя персонажа
            
        Returns:
            bool: Существует ли персонаж
        """
        hero_file = os.path.join(self.heroes_dir, f"{hero_name}.json")
        return os.path.exists(hero_file)
    
    def get_hero_list(self) -> List[str]:
        """
        Получает список всех персонажей
        
        Returns:
            List[str]: Список имен персонажей
        """
        heroes = self.load_all_heroes()
        return list(heroes.keys())

