import pygame
from game.create_character import create_character, Player
class CharacterCreationScene:
    MIN_STAT = 1
    MAX_STAT = 4
    def __init__(self, screen):
        self.screen = screen
        self.name_input = ""
        self.strength = 1
        self.intelligence = 1
        self.charisma = 1
        self.points_total = 7
        self.selected_stat = None
        self.points_left = self.points_total - (self.strength + self.intelligence + self.charisma)
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 32)
       
        

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self.selected_stat = "strength"
                elif event.key == pygame.K_2:
                 self.selected_stat = "intelligence"
                elif event.key == pygame.K_3:
                    self.selected_stat = "charisma"
                elif event.key == pygame.K_TAB:
                    self.selected_stat = None
                elif event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    self._modify_selected_stat(event)
                else:
                    self._handle_keydown(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mousebuttondown(event)
            
    def _handle_mousebuttondown(self, event):
    # Получаем координаты клика мыши
        x, y = event.pos
    
    # Проверяем клик по характеристикам
        if 200 <= x <= 400:  # Примерная ширина области характеристик
            if 320 <= y <= 380:  # Область силы
                self.selected_stat = "strength"
            elif 380 <= y <= 440:  # Область интеллекта
                self.selected_stat = "intelligence"
            elif 440 <= y <= 500:  # Область харизмы
                self.selected_stat = "charisma"
            else:
                self.selected_stat = None            
            
    
    def _handle_keydown(self, event):
        if event.key == pygame.K_RETURN:
            # тут потом будем вызывать create_character()
            pass
        elif event.key == pygame.K_BACKSPACE:
            self.name_input = self.name_input[:-1]
        elif self._can_modify_stats(event):
            self._modify_selected_stat(event)
        else:
            self.name_input += event.unicode
    
    def _can_modify_stats(self, event):
        return self.selected_stat is not None and (event.key in [pygame.K_UP, pygame.K_DOWN])
    
    def _modify_selected_stat(self, event):
        current_value = getattr(self, self.selected_stat)
        if event.key == pygame.K_UP and current_value < self.MAX_STAT and self.points_left > 0:
            setattr(self, self.selected_stat, current_value + 1)
            self.points_left -= 1
        elif event.key == pygame.K_DOWN and current_value > self.MIN_STAT:
            setattr(self, self.selected_stat, current_value - 1)
            self.points_left += 1
        self.points_left = self.points_total - (self.strength + self.intelligence + self.charisma)
        
    def _update_stats(self, strength, intelligence, charisma):
        self.strength = strength
        self.intelligence = intelligence
        self.charisma = charisma
        self.points_left = self.points_total - (self.strength + self.intelligence + self.charisma)
    
    def _clamp_stats(self):
        self.strength = self._clamp_value(self.strength)
        self.intelligence = self._clamp_value(self.intelligence)
        self.charisma = self._clamp_value(self.charisma)
    
    def _clamp_value(self, value):
        return max(self.MIN_STAT, min(self.MAX_STAT, value))

    def render(self):
        self.screen.fill((30, 30, 30))
        font = pygame.font.Font(None, 48)
        if self.name_input: 
            text_surface = font.render(self.name_input, True, (255, 255, 255))
        else:  # если строка пустая, показываем подсказку
            text_surface = font.render("Введите имя персонажа...", True, (150, 150, 150))
        self.screen.blit(text_surface, (200, 250))
        # отрисовать остальные элементы интерфейса (характеристики, кнопки и т.д.)
        stats = [("Strength", self.strength), ("Intelligence", self.intelligence), ("Charisma", self.charisma)]
        for i, (stat_name, stat_value) in enumerate(stats):
            stat_text = f"{stat_name}: {stat_value}"
            color = (255, 255, 0) if self.selected_stat == stat_name.lower() else (255, 255, 255)
            stat_surface = font.render(stat_text, True, color)
            self.screen.blit(stat_surface, (200, 320 + i * 60))
        points_text = f"Points left: {self.points_left}"
        points_surface = font.render(points_text, True, (255, 255, 255))
        self.screen.blit(points_surface, (200, 500))
        