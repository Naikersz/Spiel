import pygame
import os
import sys
from typing import Dict, List, Optional, Tuple

# Инициализация Pygame
pygame.init()

class CharacterLayer:
    """Класс для одного слоя персонажа"""
    
    # Правильные направления и их строки для WALK анимации
    WALK_DIRECTIONS = {
        "up": 8,     
        "left": 9,   
        "down": 10,   
        "right": 11   
    }
    
    IDLE_DIRECTIONS = {
    "up": 8,      # Вместо 22 — используем ту же строку, что и walk up
    "left": 9,    # Вместо 23
    "down": 10,   # Вместо 24
    "right": 11   # Вместо 25
}
    
    def __init__(self, sprite_path: str, layer_name: str, z_pos: int = 0, 
             walk_directions=None, idle_directions=None):
        self.sprite_path = sprite_path
        self.name = layer_name
        self.z_pos = z_pos
        
        # Загружаем спрайт
        self.sprite_sheet = self.load_image(sprite_path)
        if self.sprite_sheet:
            self.sheet_width = self.sprite_sheet.get_width()
            self.sheet_height = self.sprite_sheet.get_height()
            
            # Автоматически определяем размер кадра
            self.frame_width, self.frame_height = self.detect_frame_size()
            self.rows = self.sheet_height // self.frame_height
            self.cols = self.sheet_width // self.frame_width
            
            print(f"Загружен {layer_name}: {self.sheet_width}x{self.sheet_height}, "
                  f"кадры: {self.frame_width}x{self.frame_height}, "
                  f"сетка: {self.cols}x{self.rows}")
        else:
            self.frame_width = 64
            self.frame_height = 64
            self.rows = 13
            self.cols = 9  # 9 кадров для ходьбы!
    
        
    def detect_frame_size(self) -> Tuple[int, int]:
        """Автоматически определяет размер кадра"""
        for frame_size in [64, 32, 48, 96]:
            if (self.sheet_width % frame_size == 0 and 
                self.sheet_height % frame_size == 0):
                return frame_size, frame_size
        
        return self.sheet_width, self.sheet_height
    
    def load_image(self, path: str) -> Optional[pygame.Surface]:
        """Загрузка изображения"""
        possible_paths = [
            path,
            f"game/assets/sprites/{os.path.basename(path)}",
            f"assets/sprites/{os.path.basename(path)}",
            os.path.basename(path)
        ]
        
        for try_path in possible_paths:
            try:
                if os.path.exists(try_path):
                    image = pygame.image.load(try_path).convert_alpha()
                    print(f"Успешно загружен: {try_path}")
                    return image
            except Exception as e:
                continue
        
        print(f"Не удалось загрузить: {path}")
        return None
    
    def get_frame_rect(self, direction: str, animation_type: str, frame: int) -> pygame.Rect:
        """Получает прямоугольник кадра с учётом направления и анимации"""
        if animation_type == "walk":
            row = self.WALK_DIRECTIONS.get(direction, 10)
            max_frames = 9
        else:  # idle
            row = self.WALK_DIRECTIONS.get(direction, 10)  # Используем WALK строки!
            max_frames = 1  # Только первый кадр

        frame = frame % max_frames
        frame_x = frame * self.frame_width
        frame_y = row * self.frame_height

        # Проверка на выход за границы
        if (frame_x + self.frame_width > self.sheet_width or 
            frame_y + self.frame_height > self.sheet_height):
            # Fallback: первый кадр down
            return pygame.Rect(0, 10 * self.frame_height, self.frame_width, self.frame_height)

        return pygame.Rect(frame_x, frame_y, self.frame_width, self.frame_height)



class ModularCharacter:
    """Персонаж с правильной системой анимаций"""
    
    def __init__(self, x: int = 100, y: int = 100):
        self.x = x
        self.y = y
        
        # Слои персонажа
        self.layers: Dict[str, CharacterLayer] = {}
        
        # Анимация и движение
        self.current_animation = "idle"
        self.current_direction = "down"
        self.current_frame = 0
        self.animation_speed = 0.1  # Немного быстрее для плавности
        self.frame_timer = 0
        
        # Видимые слои
        self.visible_layers = set()
        
        # Загружаем базовые слои
        self.load_default_layers()
    
    def load_default_layers(self):
        """Загружает базовые слои персонажа"""
        # Основное тело персонажа
        body_layer = CharacterLayer(
            "game/assets/sprites/body/bodies/male/bodyMale.png", 
            "body", 
            z_pos=10
        )
        self.layers["body"] = body_layer
        
        # Кожаная броня 
        leather_armor_layer = CharacterLayer(
        "game/assets/sprites/torso/torsoLeather.png",
        "leather_armor",
        z_pos=20  # ТОТ ЖЕ z_pos что у базового торса!
        )
        self.layers["leather_armor"] = leather_armor_layer

        # Кожаные перчатки
        gloves_layer = CharacterLayer(
            "game/assets/sprites/arms/gloves/glovesLeather.png",
            "gloves",
            z_pos=30
        )
        self.layers["gloves"] = gloves_layer

        # Кожаные штаны
        pants_layer = CharacterLayer(
            "game/assets/sprites/legs/hose/hoseLeather.png",
            "pants",
            z_pos=15
        )
        self.layers["pants"] = pants_layer

        # Кожаные ботинки
        boots_layer = CharacterLayer(
            "game/assets/sprites/feet/boots/bootsBrown.png",
            "boots",
            z_pos=18
        )
        self.layers["boots"] = boots_layer

        # Кожаный шинель
        mantal_layer = CharacterLayer(
            "game/assets/sprites/arms/shoulders/mantal/mantalLeather.png",
            "mantel",
            z_pos=25
        )
        self.layers["mantal"] = mantal_layer

        # Манжеты
        cuffs_layer = CharacterLayer(
            "game/assets/sprites/arms/wrists/cuffs/cuffsLeather.png",
            "cuffs",
            z_pos=35
        )
        self.layers["cuffs"] = cuffs_layer


        # Голова персонажа
        head_layer = CharacterLayer(
            "game/assets/sprites/head/heads/human/male/headMale.png",
            "head", 
            z_pos=50
        )
        self.layers["head"] = head_layer
        
        # Шляпа Кожаная
        hat_layer = CharacterLayer(
            "game/assets/sprites/head/heads/human/male/hut.png",
            "hat",
            z_pos=100
        )
        self.layers["hat"] = hat_layer

        self.visible_layers = {"body", "head"}

    def toggle_leather_armor(self) -> bool:
        """Переключение кожаной брони"""
        if "leather_armor" in self.visible_layers:
            # Снимаем броню - показываем базовый торс
            self.visible_layers.remove("leather_armor")
            self.visible_layers.add("body")
            print("✗ Снята кожаная броня")
            return False
        else:
            # Надеваем броню - скрываем базовый торс
            self.visible_layers.remove("body")
            self.visible_layers.add("leather_armor")
            print("✓ Надета кожаная броня")
            return True
        
    
    def update_direction(self, dx: int, dy: int):
        """Обновляет направление персонажа на основе движения"""
        # Приоритет вертикального движения
        if dy < 0:  # Вверх
            self.current_direction = "up"
        elif dy > 0:  # Вниз
            self.current_direction = "down"
        elif dx < 0:  # Влево
            self.current_direction = "left"
        elif dx > 0:  # Вправо
            self.current_direction = "right"
    
    def update_animation_state(self, dx: int, dy: int):
        """Обновляет состояние анимации на основе движения"""
        is_moving = (dx != 0 or dy != 0)
        self.current_animation = "walk" if is_moving else "idle"
    
    def get_max_frames(self) -> int:
        """Возвращает максимальное количество кадров для текущей анимации"""
        if self.current_animation == "walk":
            return 9  # 9 кадров ходьбы!
        else:
            return 1   # 1 кадр для idle
    
    def move(self, dx: int, dy: int):
        """Перемещает персонажа и обновляет анимацию"""
        self.x += dx
        self.y += dy
        
        self.update_direction(dx, dy)
        self.update_animation_state(dx, dy)
    
    def update(self, dt: float):
        """Обновляет анимацию персонажа"""
        self.frame_timer += dt
        
        if self.frame_timer >= self.animation_speed:
            self.frame_timer = 0
            
            max_frames = self.get_max_frames()
            if self.current_animation == "walk":
                self.current_frame = (self.current_frame + 1) % max_frames
            else:
                self.current_frame = 0
    
    def draw(self, screen: pygame.Surface):
        """Отрисовывает персонажа со всеми видимыми слоями"""
        if not self.layers:
            return
        
        # Сортируем слои по z_pos
        layers_to_draw = []
        for layer_name in self.visible_layers:
            if layer_name in self.layers:
                layers_to_draw.append(self.layers[layer_name])
        
        layers_to_draw.sort(key=lambda layer: layer.z_pos)
        
        # Отрисовываем каждый слой
        for layer in layers_to_draw:
            try:
                frame_rect = layer.get_frame_rect(
                    self.current_direction, 
                    self.current_animation,
                    self.current_frame
                )
                
                # Проверяем что кадр в пределах спрайт-листа
                if (frame_rect.x + frame_rect.width <= layer.sheet_width and 
                    frame_rect.y + frame_rect.height <= layer.sheet_height):
                    
                    sprite_to_draw = layer.sprite_sheet.subsurface(frame_rect)
                    
                    # Для направления "right" можно отразить "left" если нужно
                    # но в LPC обычно есть отдельные спрайты для всех направлений
                    screen.blit(sprite_to_draw, (self.x, self.y))
                    
            except (ValueError, pygame.error) as e:
                # Fallback на первый кадр idle анимации
                try:
                    fallback_rect = pygame.Rect(0, 7 * layer.frame_height, layer.frame_width, layer.frame_height)
                    sprite_to_draw = layer.sprite_sheet.subsurface(fallback_rect)
                    screen.blit(sprite_to_draw, (self.x, self.y))
                except:
                    print(f"Ошибка отрисовки слоя {layer.name}")
    
    def toggle_clothing(self, item_name: str) -> bool:
        """Включает/выключает элемент одежды"""
        if item_name in self.layers:
            if item_name in self.visible_layers:
                self.visible_layers.remove(item_name)
                print(f"✗ Снято: {item_name}")
                return False
            else:
                self.visible_layers.add(item_name)
                print(f"✓ Надето: {item_name}")
                return True
        return False
    
    def print_debug_info(self):
        """Выводит отладочную информацию"""
        return (f"Направление: {self.current_direction} | "
                f"Анимация: {self.current_animation} | "
                f"Кадр: {self.current_frame}/8")


class SimpleGame:
    """Простая игра для демонстрации системы"""
    
    def __init__(self):
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Spiel - LPC анимации (9 кадров ходьбы)")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Создаём персонажа
        self.player = ModularCharacter(400, 300)
        
        # Шрифт
        self.font = pygame.font.Font(None, 24)
    
    def handle_events(self):
        """Обрабатывает события"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self.player.toggle_clothing("hat")
                elif event.key == pygame.K_2:  
                    self.player.toggle_clothing("leather_armor")
                elif event.key == pygame.K_3:
                    self.player.toggle_clothing("gloves")
                elif event.key == pygame.K_4:
                    self.player.toggle_clothing("pants")
                elif event.key == pygame.K_5:
                    self.player.toggle_clothing("boots")
                elif event.key == pygame.K_6:
                    self.player.toggle_clothing("mantal")
                elif event.key == pygame.K_7:
                    self.player.toggle_clothing("cuffs")
                elif event.key == pygame.K_SPACE:
                    # Покадровый просмотр анимации
                    self.player.current_frame = (self.player.current_frame + 1) % 9
                    print(f"Кадр: {self.player.current_frame}")
    
    def update(self):
        """Обновляет состояние игры"""
        dt = self.clock.tick(60) / 1000.0
        
        # Управление движением
        keys = pygame.key.get_pressed()
        move_x, move_y = 0, 0
        if keys[pygame.K_LEFT]:
            move_x = -3
        if keys[pygame.K_RIGHT]:
            move_x = 3
        if keys[pygame.K_UP]:
            move_y = -3
        if keys[pygame.K_DOWN]:
            move_y = 3
            
        self.player.move(move_x, move_y)
        self.player.update(dt)
    
    def draw(self):
        """Отрисовывает игру"""
        # Фон
        self.screen.fill((50, 50, 80))
        
        # Сетка
        cell_size = 64
        for x in range(0, self.screen_width, cell_size):
            pygame.draw.line(self.screen, (70, 70, 100), (x, 0), (x, self.screen_height), 1)
        for y in range(0, self.screen_height, cell_size):
            pygame.draw.line(self.screen, (70, 70, 100), (0, y), (self.screen_width, y), 1)
        
        # Персонаж
        self.player.draw(self.screen)
        
        # Отладочная информация
        self.draw_debug_info()
        
        pygame.display.flip()
    
    def draw_debug_info(self):
        """Рисует отладочную информацию"""
        debug_info = self.player.print_debug_info()
        
        # Фон
        debug_bg = pygame.Surface((450, 80), pygame.SRCALPHA)
        debug_bg.fill((0, 0, 0, 128))
        self.screen.blit(debug_bg, (10, 10))
        
        # Текст
        lines = [
            debug_info,
            "H - шляпа вкл/выкл, SPACE - след. кадр",
            "СТРЕЛКИ - движение"
        ]
        
        for i, line in enumerate(lines):
            text_surface = self.font.render(line, True, (255, 255, 255))
            self.screen.blit(text_surface, (20, 15 + i * 25))
    
    def run(self):
        """Запускает главный игровой цикл"""
        print("=" * 60)
        print("LPC АНИМАЦИИ ХОДЬБЫ (9 КАДРОВ):")
        print("• Ходьба ВВЕРХ - строка 9")
        print("• Ходьба ВЛЕВО - строка 10") 
        print("• Ходьба ВНИЗ - строка 11")
        print("• Ходьба ВПРАВО - строка 12")
        print("• Каждая анимация имеет 9 кадров")
        print("=" * 60)
        
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
        
        pygame.quit()
        sys.exit()


# Запуск игры
if __name__ == "__main__":
    game = SimpleGame()
    game.run()