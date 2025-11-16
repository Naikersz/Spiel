"""
Game Launcher - управление процессом запуска игры
Интегрируется с GameInitializer и MenuManager
"""
import pygame
from typing import Optional
from .game_initializer import GameInitializer


class GameLauncher:
    """Управляет запуском и основным циклом игры"""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Инициализация лаунчера
        
        Args:
            base_path: Базовый путь к проекту
        """
        self.initializer = GameInitializer(base_path)
        self.running = False
    
    def run(self):
        """Запускает основной цикл игры"""
        self.running = True
        
        while self.running:
            dt = self.initializer.get_clock().tick(60) / 1000.0
            
            # Обработка событий
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                
                # Обработка событий через менеджер меню
                action = self.initializer.handle_event(event)
                if action:
                    menu_manager = self.initializer.get_menu_manager()
                    if menu_manager:
                        if action == "quit_game":
                            self.running = False
                            break
                        else:
                            result = menu_manager.handle_action(action)
                            # Отладка: выводим действие и результат
                            if result:
                                print(f"Action '{action}' handled successfully")
                            else:
                                print(f"Action '{action}' returned False")
            
            # Обновление
            self.initializer.update(dt)
            
            # Отрисовка
            self.initializer.draw()
            
            pygame.display.flip()
        
        # Очистка
        self.initializer.cleanup()
    
    def stop(self):
        """Останавливает игру"""
        self.running = False
    
    def get_initializer(self) -> GameInitializer:
        """Возвращает инициализатор игры"""
        return self.initializer

