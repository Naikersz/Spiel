"""
Game State Manager - управление глобальным состоянием игры
Интегрируется с существующими системами сохранений и настроек
"""
import os
import json
from typing import Dict, Optional, Any
from datetime import datetime


class GameStateManager:
    """Централизованное управление состоянием игры"""
    
    def __init__(self, base_path: str):
        """
        Инициализация менеджера состояния
        
        Args:
            base_path: Базовый путь к проекту
        """
        self.base_path = base_path
        self.save_root = os.path.join(base_path, "save")
        self.settings_path = os.path.join(self.save_root, "settings.json")
        self.game_state_path = os.path.join(self.save_root, "game_state.json")
        
        # Создаем директории если их нет
        os.makedirs(self.save_root, exist_ok=True)
        os.makedirs(os.path.join(self.save_root, "heroes"), exist_ok=True)
        
        # Загружаем настройки и состояние
        self.settings = self._load_settings()
        self.game_state = self._load_game_state()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Загружает настройки игры"""
        default_settings = {
            "volume": 1.0,
            "music": 1.0,
            "sfx": 1.0,
            "fullscreen": True,
            "resolution": {"width": 1920, "height": 1080},
            "language": "en"
        }
        
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    # Объединяем с дефолтными настройками
                    default_settings.update(loaded)
            except (json.JSONDecodeError, IOError):
                pass
        
        return default_settings
    
    def _load_game_state(self) -> Dict[str, Any]:
        """Загружает глобальное состояние игры"""
        default_state = {
            "last_played": None,
            "total_playtime": 0,
            "characters_created": 0,
            "last_character": None,
            "quests_completed": 0,
            "world_state": {}
        }
        
        if os.path.exists(self.game_state_path):
            try:
                with open(self.game_state_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    default_state.update(loaded)
            except (json.JSONDecodeError, IOError):
                pass
        
        return default_state
    
    def save_settings(self) -> bool:
        """Сохраняет настройки игры"""
        try:
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            return True
        except IOError:
            return False
    
    def save_game_state(self) -> bool:
        """Сохраняет глобальное состояние игры"""
        try:
            # Обновляем время последней игры
            self.game_state["last_played"] = datetime.now().isoformat()
            
            with open(self.game_state_path, "w", encoding="utf-8") as f:
                json.dump(self.game_state, f, indent=4, ensure_ascii=False)
            return True
        except IOError:
            return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Получает значение настройки"""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """Устанавливает значение настройки"""
        self.settings[key] = value
    
    def update_game_state(self, updates: Dict[str, Any]) -> None:
        """Обновляет состояние игры"""
        self.game_state.update(updates)
    
    def get_game_state(self, key: str, default: Any = None) -> Any:
        """Получает значение состояния игры"""
        return self.game_state.get(key, default)
    
    def get_save_slots(self) -> list:
        """Получает список слотов сохранений (интеграция с существующей системой)"""
        # Используем существующую структуру из constants.py
        save_slots = ["save1", "save2", "save3"]
        return save_slots
    
    def get_heroes_directory(self) -> str:
        """Получает путь к директории с героями"""
        return os.path.join(self.save_root, "heroes")
    
    def get_global_inventory_path(self) -> str:
        """Получает путь к глобальному инвентарю"""
        return os.path.join(self.save_root, "global_inventory.json")

