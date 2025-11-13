import pygame
import os
import sys
from typing import Dict, List, Optional

# Инициализация Pygame
pygame.init()

class CharacterLayer:
    """Класс для одного слоя персонажа (тело, одежда и т.д.)"""
    
    def __init__(self, sprite_path: str, layer_name: str, z_pos: int = 0):
        self.sprite_path = sprite_path
        self.name = layer_name
        self.z_pos = z_pos
        
        # Загружаем спрайт
        self.sprite_sheet = self.load_image(sprite_path)
        self.frame_width = 64  # Стандартный размер для LPC
        self.frame_height = 64
        
    def load_image(self, path: str) -> pygame.Surface:
        """Загрузка изображения с обработкой ошибок"""
        try:
            # Пытаемся найти файл в разных местах
            if os.path.exists(path):
                image = pygame.image.load(path).convert_alpha()
            elif os.path.exists(f"game/assets/sprites/{os.path.basename(path)}"):
                image = pygame.image.load(f"game/assets/sprites/{os.path.basename(path)}").convert_alpha()
            else:
                print(f"Файл не найден: {path}")
                # Создаём временную поверхность (красный квадрат для отладки)
                image = pygame.Surface((512, 832), pygame.SRCALPHA)
                image.fill((255, 0, 0, 128))  # Полупрозрачный красный
        except Exception as e:
            print(f"Ошибка загрузки {path}: {e}")
            image = pygame.Surface((512, 832), pygame.SRCALPHA)
            image.fill((255, 255, 0, 128))  # Полупрозрачный жёлтый для ошибок
            
        return image
    
    def get_frame_rect(self, frame_index: int) -> pygame.Rect:
        """Получает прямоугольник кадра в спрайт-листе"""
        frame_x = (frame_index % 8) * self.frame_width
        frame_y = (frame_index // 8) * self.frame_height
        return pygame.Rect(frame_x, frame_y, self.frame_width, self.frame_height)


class ModularCharacter:
    """Персонаж с модульной системой одежды"""
    
    # Стандартные анимации LPC и их номера строк
    ANIMATION_ROWS = {
        "spellcast": 0, "thrust": 1, "walk": 2, "slash": 3,
        "shoot": 4, "hurt": 5, "idle": 6, "jump": 7, "run": 8,
        "sit": 9, "emote": 10, "climb": 11, "combat": 12,
        "1h_slash": 13, "1h_backslash": 14, "1h_halfslash": 15,
        "watering": 16
    }
    
    def __init__(self, x: int = 100, y: int = 100):
        self.x = x
        self.y = y
        
        # Слои персонажа
        self.layers: Dict[str, CharacterLayer] = {}
        
        # Анимация
        self.current_animation = "idle"
        self.current_frame = 0
        self.animation_speed = 0.15
        self.frame_timer = 0
        self.facing_right = True
        
        # Загружаем базовые слои
        self.load_default_layers()
    
    def load_default_layers(self):
        """Загружает базовые слои персонажа"""
    # Основное тело персонажа
        body_layer = CharacterLayer(
            "game/assets/sprites/body/bodies/male/light.png", 
            "body", 
            z_pos=10
        )
        self.layers["body"] = body_layer
    
        # Голова персонажа
        head_layer = CharacterLayer(
            "game/assets/sprites/head/heads/human/male/light.png",  # Укажите ваш правильный путь к голове
            "head", 
            z_pos=50  # z_pos между телом и волосами/шляпой
        )
        self.layers["head"] = head_layer
    
        # Шляпа (изначально не надета)
        hat_layer = CharacterLayer(
            "game/assets/sprites/hut.png",
            "hat",
            z_pos=100  # Высокий z_pos чтобы была поверх всего
        )
        self.layers["hat"] = hat_layer
    
        # Автоматически делаем видимыми тело и голову
        self.visible_layers = {"body", "head"}
    
        print("Загружены слои: body, head, hat")
    
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
        else:
            print(f"✗ Предмет '{item_name}' не найден")
            return False
    
    def set_animation(self, animation_name: str):
        """Устанавливает текущую анимацию"""
        if animation_name in self.ANIMATION_ROWS:
            if self.current_animation != animation_name:
                self.current_animation = animation_name
                self.current_frame = 0
                self.frame_timer = 0
                print(f"Анимация: {animation_name}")
        else:
            print(f"Анимация '{animation_name}' не найдена")
    
    def update(self, dt: float):
        """Обновляет анимацию персонажа"""
        self.frame_timer += dt
        
        if self.frame_timer >= self.animation_speed:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1) % 8
    
    def get_frame_index(self) -> int:
        """Получает индекс кадра в спрайт-листе"""
        row = self.ANIMATION_ROWS.get(self.current_animation, 6)  # idle по умолчанию
        return row * 8 + self.current_frame
    
    def draw(self, screen: pygame.Surface):
        """Отрисовывает персонажа со всеми видимыми слоями"""
        frame_index = self.get_frame_index()
        
        # Определяем какие слои рисовать
        layers_to_draw = []
        for layer_name, layer in self.layers.items():
            if hasattr(self, 'visible_layers'):
                if layer_name in self.visible_layers:
                    layers_to_draw.append(layer)
            else:
                # Если visible_layers не определен, рисуем все слои
                layers_to_draw.append(layer)
        
        # Сортируем по z_pos
        layers_to_draw.sort(key=lambda layer: layer.z_pos)
        
        # Отрисовываем каждый слой
        for layer in layers_to_draw:
            frame_rect = layer.get_frame_rect(frame_index)
            sprite_to_draw = layer.sprite_sheet.subsurface(frame_rect)
            
            # Отражаем спрайт если смотрит влево
            if not self.facing_right:
                sprite_to_draw = pygame.transform.flip(sprite_to_draw, True, False)
            
            screen.blit(sprite_to_draw, (self.x, self.y))
    
    def move(self, dx: int, dy: int):
        """Перемещает персонажа"""
        self.x += dx
        self.y += dy
        
        # Автоматически устанавливаем направление взгляда
        if dx > 0:
            self.facing_right = True
        elif dx < 0:
            self.facing_right = False
        
        # Автоматически переключаем анимацию при движении
        if dx != 0 or dy != 0:
            self.set_animation("walk")
        else:
            self.set_animation("idle")


class SimpleGame:
    """Простая игра для демонстрации системы"""
    
    def __init__(self):
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Spiel - Модульная система персонажа")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Создаём персонажа
        self.player = ModularCharacter(400, 300)
        
        # Шрифт для отладочной информации
        self.font = pygame.font.Font(None, 24)
    
    def handle_events(self):
        """Обрабатывает события"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                # Смена анимаций
                if event.key == pygame.K_1:
                    self.player.set_animation("idle")
                elif event.key == pygame.K_2:
                    self.player.set_animation("walk")
                elif event.key == pygame.K_3:
                    self.player.set_animation("jump")
                elif event.key == pygame.K_4:
                    self.player.set_animation("slash")
                
                # Смена одежды
                elif event.key == pygame.K_h:
                    self.player.toggle_clothing("hat")
                
                # Тестовые анимации
                elif event.key == pygame.K_5:
                    self.player.set_animation("spellcast")
                elif event.key == pygame.K_6:
                    self.player.set_animation("hurt")
    
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
    
    def draw_debug_info(self):
        """Рисует отладочную информацию"""
        # Фон для текста
        debug_bg = pygame.Surface((300, 120), pygame.SRCALPHA)
        debug_bg.fill((0, 0, 0, 128))
        self.screen.blit(debug_bg, (10, 10))
        
        # Текст информации
        anim_text = self.font.render(f"Анимация: {self.player.current_animation}", True, (255, 255, 255))
        frame_text = self.font.render(f"Кадр: {self.player.current_frame}", True, (255, 255, 255))
        pos_text = self.font.render(f"Позиция: ({self.player.x}, {self.player.y})", True, (255, 255, 255))
        
        # Определяем надета ли шляпа
        hat_status = "Надета" if (hasattr(self.player, 'visible_layers') and "hat" in self.player.visible_layers) else "Снята"
        hat_text = self.font.render(f"Шляпа: {hat_status}", True, (255, 255, 255))
        
        # Управление
        controls1 = self.font.render("Управление: Стрелки - движение, 1-4 - анимации", True, (255, 255, 255))
        controls2 = self.font.render("H - шляпа вкл/выкл, 5-6 - доп. анимации", True, (255, 255, 255))
        
        # Отображаем весь текст
        self.screen.blit(anim_text, (20, 20))
        self.screen.blit(frame_text, (20, 45))
        self.screen.blit(pos_text, (20, 70))
        self.screen.blit(hat_text, (20, 95))
        self.screen.blit(controls1, (20, 130))
        self.screen.blit(controls2, (20, 155))
    
    def draw(self):
        """Отрисовывает игру"""
        # Фон
        self.screen.fill((70, 70, 120))
        
        # Рисуем сетку для отладки
        for x in range(0, self.screen_width, 64):
            pygame.draw.line(self.screen, (100, 100, 150), (x, 0), (x, self.screen_height))
        for y in range(0, self.screen_height, 64):
            pygame.draw.line(self.screen, (100, 100, 150), (0, y), (self.screen_width, y))
        
        # Персонаж
        self.player.draw(self.screen)
        
        # Отладочная информация
        self.draw_debug_info()
        
        pygame.display.flip()
    
    def run(self):
        """Запускает главный игровой цикл"""
        print("Запуск игры...")
        print("Управление:")
        print("  Стрелки - движение")
        print("  1-4 - основные анимации")
        print("  5-6 - дополнительные анимации") 
        print("  H - надеть/снять шляпу")
        
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