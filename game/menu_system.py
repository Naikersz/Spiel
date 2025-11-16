import pygame
import sys
import json
import os
from typing import List, Tuple, Callable, Optional, Dict
from enum import Enum


class GameState(Enum):
    """Состояния игры"""
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    SETTINGS = "settings"
    INVENTORY = "inventory"
    LOADING = "loading"
    CHARACTER_CREATION = "character_creation"
    TOWN = "town"  # Состояние города


class MenuButton:
    """Кнопка меню"""
    def __init__(self, text: str, action: str, y_pos: int, font: pygame.font.Font):
        self.text = text
        self.action = action
        self.y_pos = y_pos
        self.font = font
        self.hovered = False
        self.active = False
        self.rect = None
        self.alpha = 255
        
    def update_rect(self, x: int, width: int, height: int = 0):
        """Обновляет прямоугольник кнопки"""
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(x + width // 2, self.y_pos))
        padding = 20
        self.rect = pygame.Rect(
            text_rect.x - padding,
            text_rect.y - padding // 2,
            text_rect.width + padding * 2,
            text_rect.height + padding
        )
    
    def check_hover(self, mouse_pos: Tuple[int, int]) -> bool:
        """Проверяет наведение мыши"""
        was_hovered = self.hovered
        self.hovered = self.rect and self.rect.collidepoint(mouse_pos)
        return self.hovered and not was_hovered
    
    def check_click(self, mouse_pos: Tuple[int, int]) -> bool:
        """Проверяет клик по кнопке"""
        if self.rect and self.rect.collidepoint(mouse_pos):
            self.active = True
            return True
        return False


class BaseMenu:
    """Базовый класс для всех меню"""
    def __init__(self, screen: pygame.Surface, font_path: str = "game/fonts/Merri.ttf"):
        self.screen = screen
        self.screen_width, self.screen_height = screen.get_size()
        self.font_path = font_path
        
        # Цветовая схема
        self.colors = {
            "bg": (26, 26, 26),  # #1a1a1a
            "button_normal": (51, 51, 51),  # #333333
            "button_hover": (85, 85, 85),  # #555555
            "button_active": (119, 119, 119),  # #777777
            "text_normal": (224, 224, 224),  # #e0e0e0
            "text_hover": (255, 255, 255),  # #ffffff
            "accent": (139, 0, 0),  # #8b0000
        }
        
        # Загрузка шрифтов
        try:
            self.title_font = pygame.font.Font(font_path, 48)
            self.button_font = pygame.font.Font(font_path, 32)
            self.small_font = pygame.font.Font(font_path, 24)
        except:
            # Fallback на системный шрифт
            self.title_font = pygame.font.Font(None, 48)
            self.button_font = pygame.font.Font(None, 32)
            self.small_font = pygame.font.Font(None, 24)
        
        self.buttons: List[MenuButton] = []
        self.animation_time = 0.0
        self.particles = []  # Для будущих эффектов
        
    def add_button(self, text: str, action: str, y_offset: int = 0):
        """Добавляет кнопку в меню"""
        button_y = self.screen_height // 2 + y_offset
        button = MenuButton(text, action, button_y, self.button_font)
        self.buttons.append(button)
        return button
    
    def update_buttons(self):
        """Обновляет позиции кнопок"""
        button_spacing = 80
        start_y = self.screen_height // 2 - (len(self.buttons) - 1) * button_spacing // 2
        
        for i, button in enumerate(self.buttons):
            button.y_pos = start_y + i * button_spacing
            button.update_rect(0, self.screen_width, 0)
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Обрабатывает события"""
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            for button in self.buttons:
                if button.check_hover(mouse_pos):
                    self.hover_sound()
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Левая кнопка мыши
                mouse_pos = pygame.mouse.get_pos()
                for button in self.buttons:
                    if button.check_click(mouse_pos):
                        self.click_sound()
                        return button.action
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "back"
            # Навигация стрелками
            elif event.key == pygame.K_UP:
                self.navigate_up()
            elif event.key == pygame.K_DOWN:
                self.navigate_down()
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                for button in self.buttons:
                    if button.hovered:
                        self.click_sound()
                        return button.action
        
        return None
    
    def navigate_up(self):
        """Навигация вверх"""
        for i, button in enumerate(self.buttons):
            if button.hovered:
                button.hovered = False
                if i > 0:
                    self.buttons[i - 1].hovered = True
                else:
                    self.buttons[-1].hovered = True
                self.hover_sound()
                return
        if self.buttons:
            self.buttons[-1].hovered = True
            self.hover_sound()
    
    def navigate_down(self):
        """Навигация вниз"""
        for i, button in enumerate(self.buttons):
            if button.hovered:
                button.hovered = False
                if i < len(self.buttons) - 1:
                    self.buttons[i + 1].hovered = True
                else:
                    self.buttons[0].hovered = True
                self.hover_sound()
                return
        if self.buttons:
            self.buttons[0].hovered = True
            self.hover_sound()
    
    def update(self, dt: float):
        """Обновляет меню"""
        self.animation_time += dt
        
        # Обновление частиц (заготовка)
        self.update_particles(dt)
        
        # Сброс активного состояния кнопок
        for button in self.buttons:
            if button.active:
                button.active = False
    
    def update_particles(self, dt: float):
        """Обновляет частицы на фоне (заготовка)"""
        # Здесь можно добавить эффекты частиц
        pass
    
    def draw(self):
        """Отрисовывает меню"""
        # Фон
        self.screen.fill(self.colors["bg"])
        
        # Частицы/эффекты (заготовка)
        self.draw_particles()
        
        # Кнопки
        self.draw_buttons()
    
    def draw_buttons(self):
        """Отрисовывает кнопки"""
        for button in self.buttons:
            if not button.rect:
                continue
            
            # Цвет кнопки
            if button.active:
                color = self.colors["button_active"]
            elif button.hovered:
                color = self.colors["button_hover"]
            else:
                color = self.colors["button_normal"]
            
            # Рисуем кнопку
            pygame.draw.rect(self.screen, color, button.rect, border_radius=5)
            
            # Подсветка при наведении
            if button.hovered:
                pygame.draw.rect(self.screen, self.colors["accent"], button.rect, 2, border_radius=5)
            
            # Текст
            text_color = self.colors["text_hover"] if button.hovered else self.colors["text_normal"]
            text_surf = button.font.render(button.text, True, text_color)
            text_rect = text_surf.get_rect(center=button.rect.center)
            self.screen.blit(text_surf, text_rect)
    
    def draw_particles(self):
        """Отрисовывает частицы (заготовка)"""
        # Здесь можно добавить эффекты частиц
        pass
    
    def hover_sound(self):
        """Звук при наведении (заготовка)"""
        # TODO: Добавить звук наведения
        pass
    
    def click_sound(self):
        """Звук при клике (заготовка)"""
        # TODO: Добавить звук клика
        pass
    
    def open_sound(self):
        """Звук при открытии меню (заготовка)"""
        # TODO: Добавить звук открытия
        pass


class MainMenu(BaseMenu):
    """Главное меню"""
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self.setup_buttons()
        self.open_sound()
    
    def setup_buttons(self):
        """Настройка кнопок главного меню"""
        self.buttons = []
        self.add_button("New Game", "new_game")
        
        # Проверяем наличие сохранений для кнопки "Continue"
        has_saves = self._check_saves_exist()
        if has_saves:
            self.add_button("Continue", "continue_game")
        
        self.add_button("Create Character", "character_creation")
        self.add_button("Quit Game", "quit_game")
        self.update_buttons()
    
    def _check_saves_exist(self) -> bool:
        """Проверяет наличие сохранений"""
        try:
            import os
            base_path = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from game.player.player_manager import PlayerManager
            player_manager = PlayerManager(base_path)
            all_characters = player_manager.get_all_characters()
            return len(all_characters) > 0
        except Exception:
            return False
    
    def refresh_buttons(self):
        """Обновляет кнопки (например, после создания персонажа)"""
        self.setup_buttons()
    
    def draw(self):
        """Отрисовывает главное меню"""
        super().draw()
        
        # Заголовок
        title_text = "SPIEL"
        title_surf = self.title_font.render(title_text, True, self.colors["accent"])
        title_rect = title_surf.get_rect(center=(self.screen_width // 2, 150))
        self.screen.blit(title_surf, title_rect)
        
        # Подзаголовок
        subtitle_text = "Roguelike Adventure"
        subtitle_surf = self.small_font.render(subtitle_text, True, self.colors["text_normal"])
        subtitle_rect = subtitle_surf.get_rect(center=(self.screen_width // 2, 220))
        self.screen.blit(subtitle_surf, subtitle_rect)


class PauseMenu(BaseMenu):
    """Меню паузы"""
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self.setup_buttons()
        self.open_sound()
    
    def setup_buttons(self):
        """Настройка кнопок меню паузы"""
        self.buttons = []
        self.add_button("Resume Game", "resume_game")
        self.add_button("Save Game", "save_game")
        self.add_button("Settings", "open_settings")
        self.add_button("Main Menu", "main_menu")
        self.add_button("Quit Game", "quit_game")
        self.update_buttons()
    
    def draw(self):
        """Отрисовывает меню паузы"""
        # Полупрозрачный фон поверх игры
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(200)
        overlay.fill(self.colors["bg"])
        self.screen.blit(overlay, (0, 0))
        
        # Остальная отрисовка
        super().draw()
        
        # Заголовок
        title_text = "PAUSED"
        title_surf = self.title_font.render(title_text, True, self.colors["accent"])
        title_rect = title_surf.get_rect(center=(self.screen_width // 2, 150))
        self.screen.blit(title_surf, title_rect)


class SettingsMenu(BaseMenu):
    """Меню настроек (заготовка)"""
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self.setup_buttons()
        self.open_sound()
    
    def setup_buttons(self):
        """Настройка кнопок меню настроек"""
        self.buttons = []
        self.add_button("Volume", "volume_settings")
        self.add_button("Music", "music_settings")
        self.add_button("SFX", "sfx_settings")
        self.add_button("Fullscreen", "fullscreen_settings")
        self.add_button("Resolution", "resolution_settings")
        self.add_button("Language", "language_settings")
        self.add_button("Apply", "apply_settings")
        self.add_button("Back", "back")
        self.update_buttons()
    
    def draw(self):
        """Отрисовывает меню настроек"""
        super().draw()
        
        # Заголовок
        title_text = "SETTINGS"
        title_surf = self.title_font.render(title_text, True, self.colors["accent"])
        title_rect = title_surf.get_rect(center=(self.screen_width // 2, 150))
        self.screen.blit(title_surf, title_rect)


class InventoryMenu(BaseMenu):
    """Меню инвентаря (заготовка)"""
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self.setup_buttons()
        self.open_sound()
    
    def setup_buttons(self):
        """Настройка кнопок меню инвентаря"""
        self.buttons = []
        self.add_button("Items", "items_tab")
        self.add_button("Equipment", "equipment_tab")
        self.add_button("Armor", "armor_tab")
        self.add_button("Weapons", "weapons_tab")
        self.add_button("Potions", "potions_tab")
        self.add_button("Resources", "resources_tab")
        self.add_button("Use", "use_item")
        self.add_button("Drop", "drop_item")
        self.add_button("Close", "back")
        self.update_buttons()
    
    def draw(self):
        """Отрисовывает меню инвентаря"""
        super().draw()
        
        # Заголовок
        title_text = "INVENTORY"
        title_surf = self.title_font.render(title_text, True, self.colors["accent"])
        title_rect = title_surf.get_rect(center=(self.screen_width // 2, 150))
        self.screen.blit(title_surf, title_rect)
        
        # TODO: Добавить отображение предметов инвентаря


class CharacterCreationMenu(BaseMenu):
    """Меню создания персонажа"""
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self.selected_class = None
        self.character_name = ""
        self.name_input_active = False
        self.classes_data = []
        self.class_images = {}
        self._is_new_game = False  # Флаг: новая игра или просто создание персонажа
        self.load_classes_data()
        self.load_class_images()
        self.setup_ui()
        self.open_sound()
    
    def load_classes_data(self):
        """Загружает данные классов из JSON"""
        try:
            json_path = "game/data/hero_classes.json"
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    self.classes_data = json.load(f)
            else:
                print(f"Warning: {json_path} not found")
                self.classes_data = []
        except Exception as e:
            print(f"Error loading classes data: {e}")
            self.classes_data = []
    
    def load_class_images(self):
        """Загружает изображения классов"""
        class_ids = ["warrior", "mage", "rogue", "healer"]
        for class_id in class_ids:
            try:
                image_path = f"game/images/{class_id}.png"
                if os.path.exists(image_path):
                    img = pygame.image.load(image_path).convert_alpha()
                    # Масштабируем до нужного размера для карточек
                    self.class_images[class_id] = pygame.transform.scale(img, (200, 200))
                else:
                    # Создаем placeholder
                    placeholder = pygame.Surface((200, 200))
                    placeholder.fill((50, 50, 50))
                    self.class_images[class_id] = placeholder
            except Exception as e:
                print(f"Error loading image for {class_id}: {e}")
                placeholder = pygame.Surface((200, 200))
                placeholder.fill((50, 50, 50))
                self.class_images[class_id] = placeholder
    
    def setup_ui(self):
        """Настраивает элементы интерфейса"""
        self.class_cards = []  # Список карточек классов
        self.info_panel_rect = None
        self.name_input_rect = None
        self.create_button_rect = None
        self.back_button_rect = None
    
    def get_class_by_id(self, class_id: str) -> Optional[Dict]:
        """Получает данные класса по ID"""
        for class_data in self.classes_data:
            if class_data.get("id") == class_id:
                return class_data
        return None
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Обрабатывает события"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Левая кнопка мыши
                mouse_pos = pygame.mouse.get_pos()
                
                # Проверка клика по карточкам классов
                for i, card_rect in enumerate(self.class_cards):
                    if card_rect and card_rect.collidepoint(mouse_pos):
                        if i < len(self.classes_data):
                            self.selected_class = self.classes_data[i]
                            self.click_sound()
                            return None
                
                # Проверка клика по полю ввода имени
                if self.name_input_rect and self.name_input_rect.collidepoint(mouse_pos):
                    self.name_input_active = True
                    return None
                else:
                    self.name_input_active = False
                
                # Проверка клика по кнопке создания
                if self.create_button_rect and self.create_button_rect.collidepoint(mouse_pos):
                    if self.can_create_character():
                        self.click_sound()
                        return "create_character"
                
                # Проверка клика по кнопке назад
                if self.back_button_rect and self.back_button_rect.collidepoint(mouse_pos):
                    self.click_sound()
                    return "back"
        
        elif event.type == pygame.KEYDOWN:
            if self.name_input_active:
                if event.key == pygame.K_BACKSPACE:
                    self.character_name = self.character_name[:-1]
                elif event.key == pygame.K_RETURN or event.key == pygame.K_TAB:
                    self.name_input_active = False
                elif event.unicode.isprintable() and len(self.character_name) < 20:
                    self.character_name += event.unicode
            elif event.key == pygame.K_ESCAPE:
                return "back"
        
        return None
    
    def can_create_character(self) -> bool:
        """Проверяет, можно ли создать персонажа"""
        return self.selected_class is not None and len(self.character_name.strip()) > 0
    
    def update(self, dt: float):
        """Обновляет меню"""
        super().update(dt)
    
    def draw(self):
        """Отрисовывает меню создания персонажа"""
        super().draw()
        
        # Заголовок
        title_text = "CHARACTER CREATION"
        title_surf = self.title_font.render(title_text, True, self.colors["accent"])
        title_rect = title_surf.get_rect(center=(self.screen_width // 2, 60))
        self.screen.blit(title_surf, title_rect)
        
        # Рисуем карточки классов
        self.draw_class_cards()
        
        # Рисуем панель информации
        self.draw_info_panel()
        
        # Рисуем поле ввода имени
        self.draw_name_input()
        
        # Рисуем кнопки
        self.draw_buttons()
    
    def draw_class_cards(self):
        """Отрисовывает карточки классов"""
        if not self.classes_data:
            return
        
        card_width = 220
        card_height = 280
        card_spacing = 30
        total_width = len(self.classes_data) * card_width + (len(self.classes_data) - 1) * card_spacing
        start_x = (self.screen_width - total_width) // 2
        start_y = 120
        
        self.class_cards = []
        
        for i, class_data in enumerate(self.classes_data):
            class_id = class_data.get("id", "")
            class_name = class_data.get("name", "Unknown")
            
            card_x = start_x + i * (card_width + card_spacing)
            card_y = start_y
            card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
            self.class_cards.append(card_rect)
            
            # Проверка выбора
            is_selected = self.selected_class and self.selected_class.get("id") == class_id
            is_hovered = card_rect.collidepoint(pygame.mouse.get_pos())
            
            # Цвет карточки
            if is_selected:
                border_color = self.colors["accent"]
                bg_color = (60, 60, 60)
            elif is_hovered:
                border_color = (100, 100, 100)
                bg_color = (45, 45, 45)
            else:
                border_color = (40, 40, 40)
                bg_color = (35, 35, 35)
            
            # Рисуем карточку
            pygame.draw.rect(self.screen, bg_color, card_rect, border_radius=10)
            pygame.draw.rect(self.screen, border_color, card_rect, 3, border_radius=10)
            
            # Рисуем изображение класса
            if class_id in self.class_images:
                img = self.class_images[class_id]
                img_rect = img.get_rect(center=(card_x + card_width // 2, card_y + 100))
                self.screen.blit(img, img_rect)
            
            # Рисуем название класса
            name_surf = self.button_font.render(class_name, True, self.colors["text_normal"])
            name_rect = name_surf.get_rect(center=(card_x + card_width // 2, card_y + card_height - 30))
            self.screen.blit(name_surf, name_rect)
    
    def draw_info_panel(self):
        """Отрисовывает панель информации о выбранном классе"""
        panel_width = 400
        panel_height = 400
        panel_x = self.screen_width - panel_width - 50
        panel_y = 120
        
        self.info_panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        
        # Фон панели
        pygame.draw.rect(self.screen, (30, 30, 30), self.info_panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, self.colors["accent"], self.info_panel_rect, 2, border_radius=10)
        
        if not self.selected_class:
            # Сообщение о выборе класса
            text = "Select a class to view details"
            text_surf = self.small_font.render(text, True, self.colors["text_normal"])
            text_rect = text_surf.get_rect(center=self.info_panel_rect.center)
            self.screen.blit(text_surf, text_rect)
            return
        
        # Заголовок панели
        class_name = self.selected_class.get("name", "Unknown")
        title_surf = self.button_font.render(class_name, True, self.colors["accent"])
        title_rect = title_surf.get_rect(center=(panel_x + panel_width // 2, panel_y + 30))
        self.screen.blit(title_surf, title_rect)
        
        # Статистика
        y_offset = 80
        line_height = 35
        
        stats = [
            ("Health", self.selected_class.get("base_health", 0)),
            ("Strength", self.selected_class.get("base_strength", 0)),
            ("Intelligence", self.selected_class.get("base_intelligence", 0)),
            ("Dexterity", self.selected_class.get("base_dexterity", 0)),
            ("Speed", self.selected_class.get("base_speed", 0)),
        ]
        
        for stat_name, stat_value in stats:
            stat_text = f"{stat_name}: {stat_value}"
            stat_surf = self.small_font.render(stat_text, True, self.colors["text_normal"])
            self.screen.blit(stat_surf, (panel_x + 20, panel_y + y_offset))
            y_offset += line_height
        
        # Стартовая экипировка
        y_offset += 20
        equipment_title = "Starter Equipment:"
        title_surf = self.small_font.render(equipment_title, True, self.colors["text_hover"])
        self.screen.blit(title_surf, (panel_x + 20, panel_y + y_offset))
        y_offset += line_height
        
        starter_items = self.selected_class.get("starter_items", [])
        for item in starter_items:
            item_text = f"• {item.replace('_', ' ').title()}"
            item_surf = self.small_font.render(item_text, True, self.colors["text_normal"])
            self.screen.blit(item_surf, (panel_x + 30, panel_y + y_offset))
            y_offset += line_height - 5
    
    def draw_name_input(self):
        """Отрисовывает поле ввода имени"""
        input_width = 400
        input_height = 50
        input_x = (self.screen_width - input_width) // 2
        input_y = 450
        
        self.name_input_rect = pygame.Rect(input_x, input_y, input_width, input_height)
        
        # Фон поля ввода
        bg_color = (40, 40, 40) if not self.name_input_active else (50, 50, 50)
        border_color = self.colors["accent"] if self.name_input_active else (60, 60, 60)
        
        pygame.draw.rect(self.screen, bg_color, self.name_input_rect, border_radius=5)
        pygame.draw.rect(self.screen, border_color, self.name_input_rect, 2, border_radius=5)
        
        # Текст подсказки или введенное имя
        if not self.character_name and not self.name_input_active:
            hint_text = "Enter character name..."
            hint_surf = self.small_font.render(hint_text, True, (100, 100, 100))
            hint_rect = hint_surf.get_rect(center=self.name_input_rect.center)
            self.screen.blit(hint_surf, hint_rect)
        else:
            display_text = self.character_name
            if self.name_input_active:
                # Добавляем мигающий курсор
                if int(self.animation_time * 2) % 2:
                    display_text += "|"
            
            name_surf = self.button_font.render(display_text, True, self.colors["text_normal"])
            name_rect = name_surf.get_rect(midleft=(input_x + 10, input_y + input_height // 2))
            self.screen.blit(name_surf, name_rect)
    
    def draw_buttons(self):
        """Отрисовывает кнопки"""
        button_width = 250
        button_height = 50
        button_spacing = 20
        total_width = button_width * 2 + button_spacing
        start_x = (self.screen_width - total_width) // 2
        button_y = 530
        
        # Кнопка "Create Character"
        create_x = start_x
        self.create_button_rect = pygame.Rect(create_x, button_y, button_width, button_height)
        
        can_create = self.can_create_character()
        create_color = self.colors["button_hover"] if can_create else self.colors["button_normal"]
        create_text_color = self.colors["text_hover"] if can_create else (100, 100, 100)
        
        pygame.draw.rect(self.screen, create_color, self.create_button_rect, border_radius=5)
        if can_create:
            pygame.draw.rect(self.screen, self.colors["accent"], self.create_button_rect, 2, border_radius=5)
        
        create_text = "Create Character"
        create_surf = self.button_font.render(create_text, True, create_text_color)
        create_text_rect = create_surf.get_rect(center=self.create_button_rect.center)
        self.screen.blit(create_surf, create_text_rect)
        
        # Кнопка "Back"
        back_x = start_x + button_width + button_spacing
        self.back_button_rect = pygame.Rect(back_x, button_y, button_width, button_height)
        
        is_hovered = self.back_button_rect.collidepoint(pygame.mouse.get_pos())
        back_color = self.colors["button_hover"] if is_hovered else self.colors["button_normal"]
        
        pygame.draw.rect(self.screen, back_color, self.back_button_rect, border_radius=5)
        
        back_text = "Back"
        back_surf = self.button_font.render(back_text, True, self.colors["text_normal"])
        back_text_rect = back_surf.get_rect(center=self.back_button_rect.center)
        self.screen.blit(back_surf, back_text_rect)


class MenuManager:
    """Менеджер меню и состояний игры"""
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.current_state = GameState.MENU
        self.previous_state = None
        
        # Создание меню
        self.menus = {
            GameState.MENU: MainMenu(screen),
            GameState.PAUSED: PauseMenu(screen),
            GameState.SETTINGS: SettingsMenu(screen),
            GameState.INVENTORY: InventoryMenu(screen),
            GameState.CHARACTER_CREATION: CharacterCreationMenu(screen),
        }
        
        self.current_menu = self.menus[GameState.MENU]
    
    def change_state(self, new_state: GameState):
        """Изменяет состояние игры"""
        self.previous_state = self.current_state
        self.current_state = new_state
        
        if new_state in self.menus:
            self.current_menu = self.menus[new_state]
            # Обновляем кнопки главного меню при возврате (может появиться "Continue")
            if new_state == GameState.MENU and isinstance(self.current_menu, MainMenu):
                self.current_menu.refresh_buttons()
            self.current_menu.open_sound()
    
    def handle_action(self, action: str) -> bool:
        """Обрабатывает действие из меню"""
        if action == "new_game":
            # Новая игра - переход к созданию персонажа
            # Помечаем, что это новая игра
            if GameState.CHARACTER_CREATION in self.menus:
                self.menus[GameState.CHARACTER_CREATION]._is_new_game = True
            self.change_state(GameState.CHARACTER_CREATION)
            return True
        
        elif action == "continue_game":
            # Продолжить - загрузка сохранения
            try:
                from game.player.player_manager import PlayerManager
            except ImportError:
                import sys
                import os
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                from game.player.player_manager import PlayerManager
            
            import os
            base_path = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            player_manager = PlayerManager(base_path)
            
            # Получаем список всех персонажей
            all_characters = player_manager.get_all_characters()
            if all_characters:
                # Загружаем первого доступного персонажа
                first_char_name = list(all_characters.keys())[0]
                hero = player_manager.load_character(first_char_name)
                if hero:
                    print(f"Character loaded: {first_char_name}")
                    self.change_state(GameState.TOWN)
                    return True
            else:
                print("No saved characters found")
                # Если нет сохранений, возвращаемся в главное меню
                self.change_state(GameState.MENU)
                return False
        
        elif action == "start_game":
            self.change_state(GameState.TOWN)
            return True
        
        elif action == "resume_game":
            self.change_state(GameState.TOWN)
            return True
        
        elif action == "save_game":
            # TODO: Реализовать сохранение
            print("Saving game...")
            return False
        
        elif action == "load_game":
            # TODO: Реализовать загрузку
            self.change_state(GameState.LOADING)
            return True
        
        elif action == "open_settings":
            self.change_state(GameState.SETTINGS)
            return True
        
        elif action == "open_inventory":
            self.change_state(GameState.INVENTORY)
            return True
        
        elif action == "character_creation":
            # Создать персонажа - переход к созданию (не новая игра)
            # Помечаем, что это НЕ новая игра
            if GameState.CHARACTER_CREATION in self.menus:
                self.menus[GameState.CHARACTER_CREATION]._is_new_game = False
            self.change_state(GameState.CHARACTER_CREATION)
            return True
        
        elif action == "create_character":
            # Создание персонажа - для "Новая игра" переходит в TOWN, для "Создать персонажа" возвращает в меню
            is_new_game = getattr(self.current_menu, '_is_new_game', False)
            
            if hasattr(self.current_menu, 'selected_class') and self.current_menu.selected_class:
                try:
                    from game.player.player_manager import PlayerManager
                    from game.setup.new_game_setup import NewGameSetup
                except ImportError:
                    # Fallback для разных структур проекта
                    import sys
                    import os
                    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                    from game.player.player_manager import PlayerManager
                    from game.setup.new_game_setup import NewGameSetup
                
                import os
                base_path = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                player_manager = PlayerManager(base_path)
                
                class_id = self.current_menu.selected_class.get('id', 'warrior')
                char_name = getattr(self.current_menu, 'character_name', '').strip()
                
                if char_name:
                    # Упрощенное создание персонажа как в Andreas
                    try:
                        # Используем PlayerInitializer для создания
                        hero = player_manager.create_character(class_id, char_name)
                        
                        if not hero:
                            # Если создание не удалось, создаем минимального персонажа
                            hero = {
                                "name": char_name,
                                "class_id": class_id,
                                "class_name": self.current_menu.selected_class.get('name', 'Unknown'),
                                "level": 1,
                                "experience": 0,
                                "x": 100,
                                "y": 100,
                                "stats": {
                                    "health": self.current_menu.selected_class.get("base_health", 100),
                                    "max_health": self.current_menu.selected_class.get("base_health", 100),
                                    "strength": self.current_menu.selected_class.get("base_strength", 10),
                                    "intelligence": self.current_menu.selected_class.get("base_intelligence", 10),
                                    "dexterity": self.current_menu.selected_class.get("base_dexterity", 10),
                                    "speed": self.current_menu.selected_class.get("base_speed", 10)
                                },
                                "equipped": {}
                            }
                            # Сохраняем персонажа
                            player_manager.set_current_character(hero)
                            player_manager.save_current_character()
                    except Exception as e:
                        print(f"Error creating character, using fallback: {e}")
                        import traceback
                        traceback.print_exc()
                        # Создаем минимального персонажа для тестирования
                        hero = {
                            "name": char_name,
                            "class_id": class_id,
                            "class_name": self.current_menu.selected_class.get('name', 'Unknown'),
                            "level": 1,
                            "experience": 0,
                            "x": 100,
                            "y": 100,
                            "stats": {
                                "health": self.current_menu.selected_class.get("base_health", 100),
                                "max_health": self.current_menu.selected_class.get("base_health", 100),
                                "strength": self.current_menu.selected_class.get("base_strength", 10),
                                "intelligence": self.current_menu.selected_class.get("base_intelligence", 10),
                                "dexterity": self.current_menu.selected_class.get("base_dexterity", 10),
                                "speed": self.current_menu.selected_class.get("base_speed", 10)
                            },
                            "equipped": {}
                        }
                        player_manager.set_current_character(hero)
                        player_manager.save_current_character()
                    
                    if hero:
                        print(f"Character created: {char_name} as {self.current_menu.selected_class.get('name', 'Unknown')}")
                        if is_new_game:
                            # Новая игра - переходим в TOWN
                            self.change_state(GameState.TOWN)
                        else:
                            # Создать персонажа - возвращаемся в главное меню
                            self.change_state(GameState.MENU)
                        return True
                    else:
                        print(f"Failed to create character: {char_name}")
            return False
        
        elif action == "main_menu":
            self.change_state(GameState.MENU)
            return True
        
        elif action == "back":
            if self.previous_state:
                self.change_state(self.previous_state)
            else:
                self.change_state(GameState.MENU)
            return True
        
        elif action == "quit_game":
            return False  # Сигнал для выхода
        
        # Обработка новых действий из SettingsMenu
        elif action in ["volume_settings", "music_settings", "sfx_settings", 
                       "fullscreen_settings", "resolution_settings", "language_settings"]:
            # TODO: Реализовать настройки
            print(f"Settings action: {action}")
            return False
        
        elif action == "apply_settings":
            # TODO: Применить настройки
            print("Applying settings...")
            return False
        
        # Обработка новых действий из InventoryMenu
        elif action in ["items_tab", "equipment_tab", "armor_tab", 
                       "weapons_tab", "potions_tab", "resources_tab"]:
            # TODO: Переключение вкладок инвентаря
            print(f"Inventory tab: {action}")
            return False
        
        elif action == "use_item":
            # TODO: Использовать предмет
            print("Using item...")
            return False
        
        elif action == "drop_item":
            # TODO: Выбросить предмет
            print("Dropping item...")
            return False
        
        return False
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Обрабатывает события"""
        if self.current_state in [GameState.MENU, GameState.PAUSED, GameState.SETTINGS, 
                                  GameState.INVENTORY, GameState.CHARACTER_CREATION]:
            action = self.current_menu.handle_event(event)
            if action:
                return action
        return None
    
    def update(self, dt: float):
        """Обновляет меню"""
        if self.current_menu:
            self.current_menu.update(dt)
    
    def draw(self):
        """Отрисовывает текущее меню"""
        if self.current_menu:
            self.current_menu.draw()

