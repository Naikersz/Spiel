"""
Player Manager - центральный класс управления игроком
Интегрирует все системы управления персонажем
"""
from typing import Optional, Dict, Any
from .player_loader import PlayerLoader
from .player_initializer import PlayerInitializer
from .player_data_validator import PlayerDataValidator
from ..setup.progression_manager import ProgressionManager


class PlayerManager:
    """Централизованное управление персонажем"""
    
    def __init__(self, base_path: str):
        """
        Инициализация менеджера персонажа
        
        Args:
            base_path: Базовый путь к проекту
        """
        self.base_path = base_path
        self.loader = PlayerLoader(base_path)
        self.initializer = PlayerInitializer(base_path)
        self.progression = ProgressionManager()
        
        # Текущий активный персонаж
        self.current_hero: Optional[Dict[str, Any]] = None
    
    def create_character(self, class_id: str, name: str) -> Optional[Dict[str, Any]]:
        """
        Создает нового персонажа
        
        Args:
            class_id: ID класса
            name: Имя персонажа
            
        Returns:
            Dict: Данные созданного персонажа или None
        """
        hero = self.initializer.create_hero(class_id, name)
        if hero:
            self.current_hero = hero
        return hero
    
    def load_character(self, hero_name: str) -> Optional[Dict[str, Any]]:
        """
        Загружает персонажа
        
        Args:
            hero_name: Имя персонажа
            
        Returns:
            Dict: Данные персонажа или None
        """
        hero = self.loader.load_hero(hero_name)
        if hero:
            self.current_hero = hero
        return hero
    
    def save_current_character(self) -> bool:
        """
        Сохраняет текущего персонажа
        
        Returns:
            bool: Успешно ли сохранено
        """
        if not self.current_hero:
            return False
        
        return self.loader.save_hero(self.current_hero)
    
    def get_current_character(self) -> Optional[Dict[str, Any]]:
        """Возвращает текущего персонажа"""
        return self.current_hero
    
    def set_current_character(self, hero_data: Dict[str, Any]) -> None:
        """Устанавливает текущего персонажа"""
        self.current_hero = hero_data
    
    def get_all_characters(self) -> Dict[str, str]:
        """Возвращает список всех персонажей"""
        return self.loader.load_all_heroes()
    
    def delete_character(self, hero_name: str) -> bool:
        """
        Удаляет персонажа
        
        Args:
            hero_name: Имя персонажа
            
        Returns:
            bool: Успешно ли удалено
        """
        if self.current_hero and self.current_hero.get("name") == hero_name:
            self.current_hero = None
        
        return self.loader.delete_hero(hero_name)
    
    def add_experience(self, amount: int) -> bool:
        """
        Добавляет опыт текущему персонажу
        
        Args:
            amount: Количество опыта
            
        Returns:
            bool: Был ли получен новый уровень
        """
        if not self.current_hero:
            return False
        
        old_level = self.current_hero["stats"]["level"]
        self.current_hero = self.progression.add_experience(self.current_hero, amount)
        new_level = self.current_hero["stats"]["level"]
        
        return new_level > old_level
    
    def level_up(self) -> bool:
        """
        Повышает уровень текущего персонажа
        
        Returns:
            bool: Успешно ли повышен уровень
        """
        if not self.current_hero:
            return False
        
        self.current_hero = self.progression.level_up(self.current_hero)
        return True
    
    def calculate_stats(self) -> None:
        """Пересчитывает характеристики текущего персонажа"""
        if self.current_hero:
            self.current_hero = self.progression.calculate_total_stats(self.current_hero)

