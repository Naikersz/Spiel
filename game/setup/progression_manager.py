"""
Progression Manager - система уровней, опыта и прокачки
"""
from typing import Dict, Any


class ProgressionManager:
    """Управление прогрессом персонажа"""
    
    # Формула опыта для следующего уровня: base_exp * (level ^ exp_multiplier)
    BASE_EXP = 100
    EXP_MULTIPLIER = 1.5
    
    # Бонусы за уровень
    STATS_PER_LEVEL = {
        "health": 10,
        "strength": 2,
        "intelligence": 2,
        "dexterity": 1,
        "speed": 1
    }
    
    def calculate_exp_for_level(self, level: int) -> int:
        """
        Рассчитывает необходимое количество опыта для уровня
        
        Args:
            level: Уровень
            
        Returns:
            int: Необходимый опыт
        """
        return int(self.BASE_EXP * (level ** self.EXP_MULTIPLIER))
    
    def add_experience(self, hero_data: Dict[str, Any], amount: int) -> Dict[str, Any]:
        """
        Добавляет опыт персонажу и повышает уровень при необходимости
        
        Args:
            hero_data: Данные персонажа
            amount: Количество опыта
            
        Returns:
            Dict: Обновленные данные персонажа
        """
        hero = hero_data.copy()
        stats = hero.get("stats", {})
        
        current_exp = stats.get("experience", 0)
        current_level = stats.get("level", 1)
        
        new_exp = current_exp + amount
        
        # Проверяем повышение уровня
        while True:
            exp_needed = self.calculate_exp_for_level(current_level)
            if new_exp >= exp_needed:
                new_exp -= exp_needed
                current_level += 1
                # Применяем бонусы за уровень
                self._apply_level_bonuses(hero, current_level)
            else:
                break
        
        stats["experience"] = new_exp
        stats["level"] = current_level
        hero["stats"] = stats
        
        # Пересчитываем итоговые характеристики
        hero = self.calculate_total_stats(hero)
        
        return hero
    
    def _apply_level_bonuses(self, hero_data: Dict[str, Any], level: int) -> None:
        """
        Применяет бонусы за уровень к базовым характеристикам
        
        Args:
            hero_data: Данные персонажа
            level: Уровень
        """
        stats = hero_data.get("stats", {})
        
        # Бонусы применяются только к базовым характеристикам
        # (не к итоговым, которые включают экипировку)
        for stat_name, bonus_per_level in self.STATS_PER_LEVEL.items():
            if stat_name in stats:
                # Базовое значение берется из класса, бонусы добавляются
                # Здесь мы просто увеличиваем базовое значение
                base_value = stats.get(f"base_{stat_name}", stats.get(stat_name, 0))
                if f"base_{stat_name}" not in stats:
                    stats[f"base_{stat_name}"] = base_value
                stats[f"base_{stat_name}"] += bonus_per_level
    
    def level_up(self, hero_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Принудительно повышает уровень персонажа
        
        Args:
            hero_data: Данные персонажа
            
        Returns:
            Dict: Обновленные данные персонажа
        """
        hero = hero_data.copy()
        stats = hero.get("stats", {})
        
        current_level = stats.get("level", 1)
        new_level = current_level + 1
        
        # Применяем бонусы за уровень
        self._apply_level_bonuses(hero, new_level)
        
        stats["level"] = new_level
        hero["stats"] = stats
        
        # Пересчитываем итоговые характеристики
        hero = self.calculate_total_stats(hero)
        
        return hero
    
    def calculate_total_stats(self, hero_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Рассчитывает итоговые характеристики с учетом экипировки
        
        Args:
            hero_data: Данные персонажа
            
        Returns:
            Dict: Данные персонажа с итоговыми характеристиками
        """
        hero = hero_data.copy()
        stats = hero.get("stats", {}).copy()
        equipped = hero.get("equipped", {})
        
        # Базовые характеристики
        total_stats = {
            "health": stats.get("health", 100),
            "strength": stats.get("strength", 10),
            "intelligence": stats.get("intelligence", 10),
            "dexterity": stats.get("dexterity", 10),
            "speed": stats.get("speed", 10),
            "armour": 0,
            "evasion": 0,
            "damage": 0
        }
        
        # Добавляем бонусы от экипировки
        for slot, item in equipped.items():
            if item and isinstance(item, dict):
                item_stats = item.get("base_stats", {})
                
                # Суммируем характеристики
                for stat_name in ["health", "strength", "intelligence", "dexterity", "speed"]:
                    if stat_name in item_stats:
                        total_stats[stat_name] = total_stats.get(stat_name, 0) + item_stats[stat_name]
                
                # Специальные характеристики
                if "armour" in item_stats:
                    total_stats["armour"] = total_stats.get("armour", 0) + item_stats["armour"]
                if "evasion" in item_stats:
                    total_stats["evasion"] = total_stats.get("evasion", 0) + item_stats["evasion"]
                if "damage" in item_stats:
                    total_stats["damage"] = total_stats.get("damage", 0) + item_stats["damage"]
        
        # Сохраняем итоговые характеристики
        hero["total_stats"] = total_stats
        
        return hero

