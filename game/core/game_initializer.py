"""
Game Initializer - основная точка входа инициализации всех систем
Интегрируется с MenuManager и существующими системами
"""
import os
import math
import pygame
from typing import Optional
from .game_state_manager import GameStateManager
from ..menu_system import MenuManager, GameState


class GameInitializer:
    """Инициализирует все системы игры"""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Инициализация игры
        
        Args:
            base_path: Базовый путь к проекту (если None, определяется автоматически)
        """
        if base_path is None:
            base_path = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        self.base_path = base_path
        self.state_manager = GameStateManager(base_path)
        
        # Инициализация pygame
        pygame.init()
        
        # Настройки экрана из сохраненных настроек
        self.screen = None
        self.clock = None
        self.menu_manager = None
        self.game_instance = None  # Игровой процесс
        self.tilemap = None  # Карта подземелья
        self.camera_x = 0
        self.camera_y = 0
        
        # Кнопка поворота карты
        self.rotate_button_rect = None
        self.rotate_button_size = 40
        
        self._initialize_display()
        self._initialize_menu_system()
        self._initialize_game()
    
    def _initialize_display(self):
        """Инициализирует дисплей"""
        fullscreen = self.state_manager.get_setting("fullscreen", False)  # По умолчанию не полноэкранный
        resolution = self.state_manager.get_setting("resolution", {"width": 1280, "height": 720})
        
        if fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            width = resolution.get("width", 1280)
            height = resolution.get("height", 720)
            self.screen = pygame.display.set_mode((width, height))
        
        pygame.display.set_caption("Spiel - Roguelike Adventure")
        self.clock = pygame.time.Clock()
    
    def _initialize_menu_system(self):
        """Инициализирует систему меню"""
        if self.screen:
            self.menu_manager = MenuManager(self.screen)
    
    def _initialize_game(self):
        """Инициализирует игровой процесс"""
        # Игровой экземпляр будет создан при переходе в TOWN или PLAYING
        self.game_instance = None
    
    def get_menu_manager(self) -> Optional[MenuManager]:
        """Возвращает менеджер меню"""
        return self.menu_manager
    
    def get_state_manager(self) -> GameStateManager:
        """Возвращает менеджер состояния"""
        return self.state_manager
    
    def get_screen(self) -> Optional[pygame.Surface]:
        """Возвращает экран"""
        return self.screen
    
    def get_clock(self) -> Optional[pygame.time.Clock]:
        """Возвращает часы"""
        return self.clock
    
    def update(self, dt: float):
        """Обновляет системы игры"""
        if not self.menu_manager:
            return
        
        current_state = self.menu_manager.current_state
        
        # Обновляем меню
        self.menu_manager.update(dt)
        
        # Обновляем игровой процесс если игра активна
        if current_state == GameState.TOWN or current_state == GameState.PLAYING:
            if self.game_instance is None:
                # Проверяем, есть ли загруженный персонаж
                load_char = False
                try:
                    from ..player.player_manager import PlayerManager
                    player_manager = PlayerManager(self.base_path)
                    if player_manager.get_current_character():
                        load_char = True
                except Exception:
                    pass
                self._start_town(load_character=load_char)
            if self.game_instance:
                # Обновляем игровой процесс
                keys = pygame.key.get_pressed()
                dx = (keys[pygame.K_d] - keys[pygame.K_a]) * 3
                dy = (keys[pygame.K_s] - keys[pygame.K_w]) * 3
                
                if hasattr(self.game_instance, 'player') and self.game_instance.player:
                    # Проверка коллизий с картой
                    player = self.game_instance.player
                    new_x = player.x + dx
                    new_y = player.y + dy
                    
                    # Размер спрайта игрока (64x64 согласно player_layers.json)
                    sprite_width = 64
                    sprite_height = 64
                    
                    if self.tilemap:
                        # Проверяем движение (игрок = 1 тайл, центр спрайта)
                        # Используем абсолютные координаты (мировое пространство)
                        if self.tilemap.is_walkable_rect(new_x, new_y, sprite_width, sprite_height):
                            player.move(dx, dy)
                        # Если коллизия, не двигаем
                    else:
                        # Если карты нет, просто двигаем
                        player.move(dx, dy)
                    
                    # Сохраняем позицию игрока для сохранения
                    # TODO: Реализовать периодическое сохранение позиции
                    
                    # Обновляем камеру
                    if self.screen:
                        screen_width, screen_height = self.screen.get_size()
                        self.camera_x = max(0, min(self.game_instance.player.x - screen_width // 2, 
                                                  (self.tilemap.width * self.tilemap.tile_size - screen_width) if self.tilemap else 0))
                        self.camera_y = max(0, min(self.game_instance.player.y - screen_height // 2,
                                                  (self.tilemap.height * self.tilemap.tile_size - screen_height) if self.tilemap else 0))
                
                if hasattr(self.game_instance, 'enemies'):
                    for enemy in self.game_instance.enemies:
                        if hasattr(enemy, 'update'):
                            enemy.update(dt, self.game_instance.player if hasattr(self.game_instance, 'player') else None)
                if hasattr(self.game_instance, 'player') and hasattr(self.game_instance.player, 'update'):
                    self.game_instance.player.update(dt)
    
    def _start_town(self, load_character: bool = False):
        """Запускает игровой процесс в городе с генерацией Tilemap"""
        try:
            from ..character import ModularCharacter
            from ..enemy import Enemy
            from ..tilemap import Tilemap
            
            # Генерируем карту подземелья
            self.tilemap = Tilemap(width=100, height=100, tile_size=64)
            self.tilemap.generate()
            
            # Определяем позицию спавна
            spawn_x, spawn_y = 100, 100  # Дефолтная позиция
            
            # Если загружаем персонажа, используем его позицию из сохранения
            if load_character:
                try:
                    from ..player.player_manager import PlayerManager
                    player_manager = PlayerManager(self.base_path)
                    current_hero = player_manager.get_current_character()
                    if current_hero:
                        # Используем сохраненную позицию если есть
                        spawn_x = current_hero.get("x", spawn_x)
                        spawn_y = current_hero.get("y", spawn_y)
                except Exception:
                    pass
            
            # Если позиция не задана, находим первую комнату
            if spawn_x == 100 and spawn_y == 100 and self.tilemap.rooms:
                first_room = self.tilemap.rooms[0]
                room_x, room_y, room_w, room_h = first_room
                # Позиция спавна: центр комнаты минус половина спрайта (64x64)
                # Чтобы игрок был точно в центре тайла пола
                spawn_x = (room_x + room_w // 2) * self.tilemap.tile_size - 32
                spawn_y = (room_y + room_h // 2) * self.tilemap.tile_size - 32
                
                # Гарантируем, что спавн на проходимом тайле
                if not self.tilemap.is_walkable_rect(spawn_x, spawn_y, 64, 64):
                    # Ищем первую проходимую позицию в комнате
                    found_spawn = False
                    for ry in range(room_y + 1, room_y + room_h - 1):
                        for rx in range(room_x + 1, room_x + room_w - 1):
                            test_x = rx * self.tilemap.tile_size - 32
                            test_y = ry * self.tilemap.tile_size - 32
                            if self.tilemap.is_walkable_rect(test_x, test_y, 64, 64):
                                spawn_x = test_x
                                spawn_y = test_y
                                found_spawn = True
                                break
                        if found_spawn:
                            break
            
            # Создаем простой объект для хранения игрового состояния
            class GameState:
                def __init__(self, screen, player, enemies):
                    self.screen = screen
                    self.player = player
                    self.enemies = enemies
                    self.screen_width, self.screen_height = screen.get_size() if screen else (1920, 1080)
            
            player = ModularCharacter(spawn_x, spawn_y)
            
            # Загружаем HP из сохранения если есть
            if load_character:
                try:
                    from ..player.player_manager import PlayerManager
                    player_manager = PlayerManager(self.base_path)
                    current_hero = player_manager.get_current_character()
                    if current_hero and "stats" in current_hero:
                        stats = current_hero["stats"]
                        player.hp = stats.get("health", player.hp)
                        player.max_hp = stats.get("max_health", stats.get("health", player.max_hp))
                except Exception:
                    pass
            
            enemies = []  # Пока без врагов в городе
            
            self.game_instance = GameState(self.screen, player, enemies)
            
            # Устанавливаем камеру на игрока
            if self.screen:
                screen_width, screen_height = self.screen.get_size()
                self.camera_x = max(0, spawn_x - screen_width // 2)
                self.camera_y = max(0, spawn_y - screen_height // 2)
        except Exception as e:
            print(f"Error initializing town: {e}")
            import traceback
            traceback.print_exc()
            self.game_instance = None
            self.tilemap = None
    
    def _start_game(self):
        """Запускает игровой процесс (legacy, используйте _start_town)"""
        self._start_town()
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Обрабатывает события"""
        if not self.menu_manager:
            return None
        
        current_state = self.menu_manager.current_state
        
        # Обрабатываем события меню
        action = self.menu_manager.handle_event(event)
        
        # Обрабатываем игровые события если игра активна
        if current_state == GameState.TOWN or current_state == GameState.PLAYING:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Пауза
                    self.menu_manager.change_state(GameState.PAUSED)
                    return None
                elif event.key == pygame.K_r:
                    # Регенерация карты
                    if self.tilemap:
                        import random
                        seed = random.randint(0, 1000000)
                        self.tilemap.regenerate(seed=seed)
                        print(f"Карта регенерирована с seed: {seed}")
                elif event.key == pygame.K_g:
                    # Поворот карты на 90°
                    if self.tilemap and self.game_instance and hasattr(self.game_instance, 'player') and self.game_instance.player:
                        screen_width, screen_height = self.screen.get_size() if self.screen else (1280, 720)
                        new_px, new_py, new_cx, new_cy = self.tilemap.rotate_map(
                            player_x=self.game_instance.player.x,
                            player_y=self.game_instance.player.y,
                            camera_x=self.camera_x,
                            camera_y=self.camera_y,
                            screen_width=screen_width,
                            screen_height=screen_height
                        )
                        if new_px is not None and new_py is not None:
                            self.game_instance.player.x = new_px
                            self.game_instance.player.y = new_py
                        if new_cx is not None and new_cy is not None:
                            self.camera_x = new_cx
                            self.camera_y = new_cy
                        print(f"Карта повернута на {self.tilemap.camera_angle * 90}°")
            
            # Обработка клика по кнопке поворота
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.rotate_button_rect and self.rotate_button_rect.collidepoint(event.pos):
                    if self.tilemap and self.game_instance and hasattr(self.game_instance, 'player') and self.game_instance.player:
                        screen_width, screen_height = self.screen.get_size() if self.screen else (1280, 720)
                        new_px, new_py, new_cx, new_cy = self.tilemap.rotate_map(
                            player_x=self.game_instance.player.x,
                            player_y=self.game_instance.player.y,
                            camera_x=self.camera_x,
                            camera_y=self.camera_y,
                            screen_width=screen_width,
                            screen_height=screen_height
                        )
                        if new_px is not None and new_py is not None:
                            self.game_instance.player.x = new_px
                            self.game_instance.player.y = new_py
                        if new_cx is not None and new_cy is not None:
                            self.camera_x = new_cx
                            self.camera_y = new_cy
                        print(f"Карта повернута на {self.tilemap.camera_angle * 90}°")
            
            # Отладочные кнопки для переключения одежды (1-7)
            if event.type == pygame.KEYDOWN:
                if self.game_instance and hasattr(self.game_instance, 'player') and self.game_instance.player:
                    if event.key == pygame.K_1:
                        # Шляпа - дополнительный слой, голова остается видимой
                        self.game_instance.player.toggle_clothing("hut")
                    elif event.key == pygame.K_2:
                        # Броня - дополнительный слой, тело остается видимым
                        self.game_instance.player.toggle_clothing("leather_armor")
                    elif event.key == pygame.K_3:
                        self.game_instance.player.toggle_clothing("gloves")
                    elif event.key == pygame.K_4:
                        self.game_instance.player.toggle_clothing("pants")
                    elif event.key == pygame.K_5:
                        self.game_instance.player.toggle_clothing("boots")
                    elif event.key == pygame.K_6:
                        self.game_instance.player.toggle_clothing("mantal")
                    elif event.key == pygame.K_7:
                        self.game_instance.player.toggle_clothing("cuffs")
                # Обработка игровых событий
                # События обрабатываются напрямую здесь
        
        return action
    
    def draw(self):
        """Отрисовывает игру"""
        if not self.menu_manager:
            return
        
        current_state = self.menu_manager.current_state
        
        # Отрисовываем игровой процесс если игра активна
        if current_state == GameState.TOWN or current_state == GameState.PLAYING:
            if self.game_instance is None:
                # Проверяем, есть ли загруженный персонаж
                load_char = False
                try:
                    from ..player.player_manager import PlayerManager
                    player_manager = PlayerManager(self.base_path)
                    if player_manager.get_current_character():
                        load_char = True
                except Exception:
                    pass
                self._start_town(load_character=load_char)
            if self.game_instance and self.screen:
                # Отрисовываем карту
                if self.tilemap:
                    self.tilemap.draw(self.screen, self.camera_x, self.camera_y)
                else:
                    self.screen.fill((30, 50, 40))
                
                # Рисуем игровые объекты (с учетом камеры)
                if hasattr(self.game_instance, 'player') and self.game_instance.player:
                    if hasattr(self.game_instance.player, 'draw'):
                        # Временно сохраняем позицию для отрисовки с камерой
                        original_x = self.game_instance.player.x
                        original_y = self.game_instance.player.y
                        
                        # Устанавливаем позицию относительно камеры для отрисовки
                        self.game_instance.player.x = original_x - self.camera_x
                        self.game_instance.player.y = original_y - self.camera_y
                        
                        # Отрисовываем игрока
                        self.game_instance.player.draw(self.screen)
                        
                        # Восстанавливаем абсолютные координаты
                        self.game_instance.player.x = original_x
                        self.game_instance.player.y = original_y
                
                if hasattr(self.game_instance, 'enemies'):
                    for enemy in self.game_instance.enemies:
                        if hasattr(enemy, 'draw'):
                            enemy.draw(self.screen)
                
                # Рисуем HP
                if hasattr(self.game_instance, 'player') and self.game_instance.player:
                    hp_ratio = self.game_instance.player.hp / self.game_instance.player.max_hp
                    pygame.draw.rect(self.screen, (100, 0, 0), (10, 10, 200, 20))
                    pygame.draw.rect(self.screen, (0, 200, 0), (10, 10, 200 * hp_ratio, 20))
                
                # Рисуем кнопку поворота карты (правый верхний угол)
                if self.screen:
                    screen_width = self.screen.get_width()
                    button_x = screen_width - self.rotate_button_size - 10
                    button_y = 10
                    self.rotate_button_rect = pygame.Rect(button_x, button_y, self.rotate_button_size, self.rotate_button_size)
                    
                    # Рисуем круглую кнопку
                    pygame.draw.circle(self.screen, (60, 60, 80), 
                                     (button_x + self.rotate_button_size // 2, 
                                      button_y + self.rotate_button_size // 2),
                                     self.rotate_button_size // 2)
                    pygame.draw.circle(self.screen, (100, 100, 120), 
                                     (button_x + self.rotate_button_size // 2, 
                                      button_y + self.rotate_button_size // 2),
                                     self.rotate_button_size // 2, 2)
                    
                    # Рисуем стрелку поворота ↻
                    center_x = button_x + self.rotate_button_size // 2
                    center_y = button_y + self.rotate_button_size // 2
                    # Простая стрелка в виде дуги со стрелкой
                    radius = self.rotate_button_size // 3
                    for i in range(8):
                        angle = i * math.pi / 4
                        x = int(center_x + radius * math.cos(angle))
                        y = int(center_y + radius * math.sin(angle))
                        pygame.draw.circle(self.screen, (200, 200, 200), (x, y), 2)
                    
                    # Стрелка в конце дуги
                    arrow_angle = math.pi / 4
                    arrow_x = int(center_x + radius * math.cos(arrow_angle))
                    arrow_y = int(center_y + radius * math.sin(arrow_angle))
                    pygame.draw.polygon(self.screen, (200, 200, 200), [
                        (arrow_x, arrow_y),
                        (arrow_x - 3, arrow_y - 3),
                        (arrow_x + 3, arrow_y - 3)
                    ])
        else:
            # Отрисовываем меню
            self.menu_manager.draw()
    
    def cleanup(self):
        """Очистка ресурсов"""
        self.state_manager.save_settings()
        self.state_manager.save_game_state()
        pygame.quit()

