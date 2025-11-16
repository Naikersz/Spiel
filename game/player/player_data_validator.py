"""
Player Data Validator - валидация данных персонажа
Обеспечивает обратную совместимость с существующими сохранениями
"""
from typing import Dict, List, Tuple, Optional, Any


class PlayerDataValidator:
    """Валидация и исправление данных персонажа"""
    
    REQUIRED_FIELDS = ["name", "class_id", "stats"]
    REQUIRED_STATS = ["health", "strength", "intelligence", "dexterity", "speed", "level", "experience"]
    EQUIPMENT_SLOTS = ["weapon", "helmet", "chest", "pants", "gloves", "boots", "shield"]
    
    @staticmethod
    def validate_hero(hero_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Валидирует данные героя
        
        Args:
            hero_data: Данные героя для валидации
            
        Returns:
            Tuple[bool, List[str]]: (валидно ли, список ошибок)
        """
        errors = []
        
        # Проверка обязательных полей
        for field in PlayerDataValidator.REQUIRED_FIELDS:
            if field not in hero_data:
                errors.append(f"Missing required field: {field}")
        
        # Проверка stats
        if "stats" in hero_data:
            stats = hero_data["stats"]
            for stat in PlayerDataValidator.REQUIRED_STATS:
                if stat not in stats:
                    errors.append(f"Missing required stat: {stat}")
                elif not isinstance(stats[stat], (int, float)):
                    errors.append(f"Invalid stat type for {stat}: expected number")
        
        # Проверка equipped
        if "equipped" not in hero_data:
            errors.append("Missing 'equipped' field")
        else:
            equipped = hero_data["equipped"]
            if not isinstance(equipped, dict):
                errors.append("'equipped' must be a dictionary")
            else:
                # Проверяем наличие всех слотов
                for slot in PlayerDataValidator.EQUIPMENT_SLOTS:
                    if slot not in equipped:
                        errors.append(f"Missing equipment slot: {slot}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def fix_hero_data(hero_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Исправляет и дополняет данные героя для обратной совместимости
        
        Args:
            hero_data: Данные героя для исправления
            
        Returns:
            Dict: Исправленные данные героя
        """
        fixed = hero_data.copy()
        
        # Добавляем недостающие обязательные поля
        if "name" not in fixed:
            fixed["name"] = "Unknown"
        
        if "class_id" not in fixed:
            fixed["class_id"] = "warrior"
        
        if "class_name" not in fixed:
            fixed["class_name"] = "Warrior"
        
        # Исправляем stats
        if "stats" not in fixed:
            fixed["stats"] = {}
        
        stats = fixed["stats"]
        default_stats = {
            "health": 100,
            "strength": 10,
            "intelligence": 10,
            "dexterity": 10,
            "speed": 10,
            "level": 1,
            "experience": 0
        }
        
        for stat, default_value in default_stats.items():
            if stat not in stats:
                stats[stat] = default_value
            elif not isinstance(stats[stat], (int, float)):
                stats[stat] = default_value
        
        # Исправляем equipped
        if "equipped" not in fixed:
            fixed["equipped"] = {}
        
        equipped = fixed["equipped"]
        for slot in PlayerDataValidator.EQUIPMENT_SLOTS:
            if slot not in equipped:
                equipped[slot] = None
        
        # Добавляем created_at если его нет
        if "created_at" not in fixed:
            from datetime import datetime
            fixed["created_at"] = datetime.now().isoformat()
        
        return fixed
    
    @staticmethod
    def validate_and_fix(hero_data: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        Валидирует и исправляет данные героя
        
        Args:
            hero_data: Данные героя
            
        Returns:
            Tuple[Dict, bool]: (исправленные данные, были ли исправления)
        """
        is_valid, errors = PlayerDataValidator.validate_hero(hero_data)
        
        if is_valid:
            return hero_data, False
        
        # Исправляем данные
        fixed_data = PlayerDataValidator.fix_hero_data(hero_data)
        return fixed_data, True

