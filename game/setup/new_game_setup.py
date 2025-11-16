"""
New Game Setup - настройка новой игры (квесты, мир, NPC)
Интегрируется с существующими системами
"""
import os
from typing import Dict, Any, Optional
from ..player.player_manager import PlayerManager
from .starter_gear_distributor import StarterGearDistributor
from .progression_manager import ProgressionManager


class NewGameSetup:
    """Настройка новой игры"""
    
    def __init__(self, base_path: str):
        """
        Инициализация настройки новой игры
        
        Args:
            base_path: Базовый путь к проекту
        """
        self.base_path = base_path
        self.player_manager = PlayerManager(base_path)
        self.gear_distributor = StarterGearDistributor(base_path)
        self.progression = ProgressionManager()
    
    def setup_new_game(self, class_id: str, character_name: str) -> Optional[Dict[str, Any]]:
        """
        Настраивает новую игру
        
        Args:
            class_id: ID класса персонажа
            character_name: Имя персонажа
            
        Returns:
            Dict: Данные созданного персонажа или None
        """
        # Создаем персонажа
        hero = self.player_manager.create_character(class_id, character_name)
        if not hero:
            return None
        
        # Инициализируем квесты
        hero = self._initialize_quests(hero)
        
        # Инициализируем состояние мира
        hero = self._initialize_world_state(hero)
        
        # Сохраняем персонажа
        self.player_manager.save_current_character()
        
        return hero
    
    def _initialize_quests(self, hero_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Инициализирует систему квестов для персонажа
        
        Args:
            hero_data: Данные персонажа
            
        Returns:
            Dict: Данные персонажа с квестами
        """
        hero = hero_data.copy()
        
        if "quests" not in hero:
            hero["quests"] = {
                "active": [],
                "completed": [],
                "failed": []
            }
        
        # Добавляем стартовый квест (если нужно)
        # TODO: Интеграция с системой квестов
        
        return hero
    
    def _initialize_world_state(self, hero_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Инициализирует состояние мира для персонажа
        
        Args:
            hero_data: Данные персонажа
            
        Returns:
            Dict: Данные персонажа с состоянием мира
        """
        hero = hero_data.copy()
        
        if "world_state" not in hero:
            hero["world_state"] = {
                "current_location": "starting_town",
                "discovered_locations": ["starting_town"],
                "npcs_met": [],
                "events_completed": []
            }
        
        return hero
    
    def get_starting_location(self) -> str:
        """Возвращает стартовую локацию"""
        return "starting_town"
    
    def get_initial_quests(self) -> list:
        """Возвращает список начальных квестов"""
        # TODO: Загрузка из JSON или конфигурации
        return []

