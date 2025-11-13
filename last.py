import pygame
import os
import sys
from typing import Dict, List, Optional, Tuple

# Инициализация Pygame
pygame.init()

class CharacterLayer:
    """Класс для одного слоя персонажа"""
    
    WALK_DIRECTIONS = {
        "up": 8,     
        "left": 9,   
        "down": 10,   
        "right": 11   
    }
    
    IDLE_DIRECTIONS = {
        "up": 8, "left": 9, "down": 10, "right": 11
    }
    
    # 🔥 НОВОЕ: Анимация атаки (LPC строки 1-4)
    ATTACK_DIRECTIONS = {
        "up": 1,    # Удар вверх
        "left": 2,  # Удар влево
        "down": 3,  # Удар вниз  
        "right": 4  # Удар вправо
    }
    
    def __init__(self, sprite_path: str, layer_name: str, z_pos: int = 0):
        self.sprite_path = sprite_path
        self.name = layer_name
        self.z_pos = z_pos
        
        # Загружаем изображение
        self.sprite_sheet = self.load_image(sprite_path)
        # ВСЕГДА устанавливаем размеры (даже если нет изображения)
        if self.sprite_sheet:
            self.sheet_width = self.sprite_sheet.get_width()
            self.sheet_height = self.sprite_sheet.get_height()
            self.frame_width, self.frame_height = self.detect_frame_size()
        else:
            # Fallback размеры
            self.sheet_width = 64
            self.sheet_height = 64
            self.frame_width = 64
            self.frame_height = 64
    
        self.rows = self.sheet_height // self.frame_height
        self.cols = self.sheet_width // self.frame_width
        
    # ДОБАВЬ ЭТОТ МЕТОД!
    def load_image(self, path: str) -> Optional[pygame.Surface]:
        """Безопасная загрузка изображения с fallback-путями"""
        possible_paths = [
            path,
            f"game/assets/sprites/{os.path.basename(path)}",
            f"assets/sprites/{os.path.basename(path)}",
            os.path.basename(path)
        ]
        
        for p in possible_paths:
            if os.path.exists(p):
                try:
                    img = pygame.image.load(p).convert_alpha()
                    print(f"Загружен: {p}")
                    return img
                except Exception as e:
                    print(f"Ошибка загрузки {p}: {e}")
                    continue
        
        print(f"Не найден спрайт: {path}")
        return None

    # ДОБАВЬ ЭТОТ МЕТОД!
    def detect_frame_size(self) -> Tuple[int, int]:
        """Определяет размер кадра по делителям"""
        for size in [64, 32, 48, 96]:
            if (self.sheet_width % size == 0 and 
                self.sheet_height % size == 0):
                return size, size
        return self.sheet_width, self.sheet_height

    def get_frame_rect(self, direction: str, animation_type: str, frame: int) -> pygame.Rect:
        if self.name in ["scimitar", "scimitar_attack"]:
            if self.name == "scimitar_attack":
                row = self.ATTACK_DIRECTIONS.get(direction, 3)
                max_frames = 6
            else:
                row = self.WALK_DIRECTIONS.get(direction, 10)
                max_frames = 9
        elif animation_type == "walk":
            row = self.WALK_DIRECTIONS.get(direction, 10)
            max_frames = 9
        elif animation_type == "attack":
            row = self.ATTACK_DIRECTIONS.get(direction, 3)
            max_frames = 6
        else:
            row = self.WALK_DIRECTIONS.get(direction, 10)
            max_frames = 1

        frame = frame % max_frames
        frame_x = frame * self.frame_width
        frame_y = row * self.frame_height

        if (frame_x + self.frame_width > self.sheet_width or 
            frame_y + self.frame_height > self.sheet_height):
            return pygame.Rect(0, 10 * self.frame_height, self.frame_width, self.frame_height)

        return pygame.Rect(frame_x, frame_y, self.frame_width, self.frame_height)

# 🔥 ИСПРАВЛЕННЫЙ ModularCharacter
class ModularCharacter:
    def __init__(self, x: int = 100, y: int = 100):
        self.x = x
        self.y = y
        self.hp = 100
        self.max_hp = 100
        self.damage_texts = []
        self.layers: Dict[str, CharacterLayer] = {}
        self.current_animation = "idle"
        self.current_direction = "down"
        self.current_frame = 0
        self.animation_speed = 0.1
        self.frame_timer = 0
        self.visible_layers = set()
        self.font = pygame.font.Font(None, 28)

        # Загружаем слои
        self.load_default_layers()  # Теперь метод есть!
    def toggle_clothing(self, item_name: str, base_layer: str = None) -> bool:
    
        
        if item_name not in self.layers:
            print(f"Предмет не найден: {item_name}")
            return False

        if item_name in self.visible_layers:
            # Снимаем
            self.visible_layers.remove(item_name)
            if base_layer and base_layer in self.layers:
                self.visible_layers.add(base_layer)
            print(f"Снято: {item_name}")
            return False
        else:
            # Надеваем
            if base_layer and base_layer in self.visible_layers:
                self.visible_layers.remove(base_layer)
            self.visible_layers.add(item_name)
            print(f"Надето: {item_name}")
            return True

    # ДОБАВЬ ЭТОТ МЕТОД В ModularCharacter!
    def load_default_layers(self):
        """Загружает базовые слои персонажа"""
        layers = [
            ("body", "game/assets/sprites/body/bodies/male/light.png", 10),
            ("head", "game/assets/sprites/head/heads/human/male/light.png", 50),
            ("leather_armor", "game/assets/sprites/torso/torsoLeather.png", 20),
            ("gloves", "game/assets/sprites/arms/gloves/glovesLeather.png", 30),
            ("pants", "game/assets/sprites/legs/hose/hoseLeather.png", 15),
            ("boots", "game/assets/sprites/feet/boots/bootsBrown.png", 18),
            ("mantal", "game/assets/sprites/arms/shoulders/mantal/mantalLeather.png", 25),
            ("cuffs", "game/assets/sprites/arms/wrists/cuffs/cuffsLeather.png", 35),
            ("hut", "game/assets/sprites/head/heads/human/male/hut.png", 100),
        ]

        for name, path, z in layers:
            layer = CharacterLayer(path, name, z_pos=z)
            self.layers[name] = layer

        # По умолчанию показываем только тело и голову
        self.visible_layers = {"body", "head"}
    def move(self, dx: int, dy: int):
        """Перемещает персонажа и обновляет направление + анимацию"""
        self.x += dx
        self.y += dy
        
        # Обновляем направление
        if dy < 0:
            self.current_direction = "up"
        elif dy > 0:
            self.current_direction = "down"
        elif dx < 0:
            self.current_direction = "left"
        elif dx > 0:
            self.current_direction = "right"
        
        # Обновляем анимацию
        if dx != 0 or dy != 0:
            self.current_animation = "walk"
        else:
            self.current_animation = "idle"    
    
    def update_animation(self, dt: float):
        """ОБНОВЛЁННАЯ анимация (вызывается из update)"""
        self.frame_timer += dt
        
        if self.current_animation == "attack":
            if self.frame_timer >= 0.08:  # Быстрее для атаки
                self.frame_timer = 0
                self.current_frame += 1
                if self.current_frame >= 6:
                    self.current_animation = "idle"
                    self.current_frame = 0
        elif self.current_animation == "walk":
            if self.frame_timer >= self.animation_speed:
                self.frame_timer = 0
                self.current_frame = (self.current_frame + 1) % 9
        else:
            self.current_frame = 0
    
    def update_damage_texts(self, dt: float):
        """Обновляет плавающий урон"""
        self.damage_texts = [t for t in self.damage_texts if t[2] > 0]
        for t in self.damage_texts:
            t[2] -= dt
            t[1] -= 50 * dt  # Поднимается
    
    def draw_damage_texts(self, screen: pygame.Surface):
        """Рисует плавающий урон"""
        for text in self.damage_texts:
            alpha = int(255 * text[2])
            damage_surf = self.font.render(str(int(text[3])), True, (255, 100, 100))
            damage_surf.set_alpha(alpha)
            screen.blit(damage_surf, (text[0], text[1]))
    
    def take_damage(self, damage: int):
        """Получает урон"""
        self.hp = max(0, self.hp - damage)
        self.damage_texts.append([self.x, self.y - 30, 1.0, damage])
        print(f"Получено {damage} урона! HP: {self.hp}")
    
    def update(self, dt: float):
        """УНИВЕРСАЛЬНЫЙ update"""
        self.update_animation(dt)
        self.update_damage_texts(dt)
    
    def draw(self, screen: pygame.Surface):
        """Отрисовка + урон + HP"""
        # Слои
        if self.layers:
            layers_to_draw = [self.layers[name] for name in self.visible_layers if name in self.layers]
            layers_to_draw.sort(key=lambda layer: layer.z_pos)
            
            for layer in layers_to_draw:
                try:
                    frame_rect = layer.get_frame_rect(self.current_direction, self.current_animation, self.current_frame)
                    if (frame_rect.x + frame_rect.width <= layer.sheet_width and 
                        frame_rect.y + frame_rect.height <= layer.sheet_height):
                        sprite = layer.sprite_sheet.subsurface(frame_rect)
                        screen.blit(sprite, (self.x, self.y))
                except:
                    pass
        
        # HP бар (только если HP < max_hp)
        if self.hp < self.max_hp:
            bar_w, bar_h = 60, 8
            hp_ratio = max(0, self.hp / self.max_hp)
            pygame.draw.rect(screen, (150, 0, 0), (self.x-30, self.y-45, bar_w, bar_h), border_radius=3)
            pygame.draw.rect(screen, (0, 200, 0), (self.x-30, self.y-45, bar_w * hp_ratio, bar_h), border_radius=3)
        
        # Плавающий урон
        self.draw_damage_texts(screen)

# 🔥 ИСПРАВЛЕННЫЙ Enemy
class Enemy(ModularCharacter):
    def __init__(self, x: int, y: int, player_ref):
        super().__init__(x, y)
        self.player = player_ref
        self.speed = 1.5
        self.attack_range = 80
        self.attack_cooldown = 0
        self.max_cooldown = 1.5
        self.hp = 50
        self.max_hp = 50
        self.patrol_points = [(200, 200), (600, 400)]
        self.current_patrol = 0
        self.state = "patrol"

        # Перезагружаем слои врага
        self.layers.clear()
        self.visible_layers.clear()
        self.load_default_layers()  # Теперь вызовет ПЕРЕОПРЕДЕЛЁННЫЙ метод

    # ПЕРЕОПРЕДЕЛЯЕМ для врага
    def load_default_layers(self):
        layers = [
            ("body", "game/assets/sprites/body/bodies/male/bodySkeleton.png", 10),
            ("head", "game/assets/sprites/head/heads/enemies/headSkeleton.png", 50),
            ("scimitar", "game/assets/sprites/weapons/scimitarwWalk.png", 40),
            ("scimitar_attack", "game/assets/sprites/weapons/scimitarSlash.png", 41),
        ]
        for name, path, z in layers:
            layer = CharacterLayer(path, name, z_pos=z)
            self.layers[name] = layer
        self.visible_layers = {"body", "head", "scimitar"}
    
    def update(self, dt: float, player):
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        
        # Логика ИИ
        dist = ((player.x - self.x)**2 + (player.y - self.y)**2)**0.5
        
        if dist < 200:
            self.state = "chase"
        else:
            self.state = "patrol"
        if self.current_animation == "attack":
            self.visible_layers = {"body", "head", "scimitar_attack"}
        else:
            self.visible_layers = {"body", "head", "scimitar"}
        
        # 🔥 АТАКА исправлена
        if (self.state == "chase" and dist < self.attack_range and 
            self.attack_cooldown == 0 and self.current_animation != "attack"):
            
            self.state = "attack"
            self.current_animation = "attack"
            self.attack_frame = 0
            self.attack_cooldown = self.max_cooldown
        
        # Движение
        dx, dy = 0, 0
        if self.state == "chase" and self.current_animation != "attack":
            dx = 1 if player.x > self.x else -1 if player.x < self.x else 0
            dy = 1 if player.y > self.y else -1 if player.y < self.y else 0
            norm = (dx**2 + dy**2)**0.5 or 1
            dx = dx / norm * self.speed
            dy = dy / norm * self.speed
            self.move(int(dx), int(dy))
        elif self.state == "patrol" and self.current_animation != "attack":
            target = self.patrol_points[self.current_patrol]
            dx = target[0] - self.x
            dy = target[1] - self.y
            dist_to_target = (dx**2 + dy**2)**0.5
            if dist_to_target < 20:
                self.current_patrol = (self.current_patrol + 1) % 2
            else:
                norm = dist_to_target or 1
                self.move(int(dx / norm * self.speed), int(dy / norm * self.speed))
        
        # 🔥 АНИМАЦИЯ атаки (урон на 3-м кадре)
        if self.current_animation == "attack":
            if self.attack_frame == 3:  # Урон именно здесь!
                player.take_damage(15)
            self.attack_frame += 1
            if self.attack_frame >= 6:
                self.current_animation = "idle"
                self.state = "chase"
        
        # Базовый update
        super().update(dt)
    
    def draw(self, screen: pygame.Surface):
        # Красный контур для врага
        pygame.draw.rect(screen, (255, 0, 0), (self.x-32, self.y-64, 64, 64), 3)
        print(f"Scimitar sheet: {self.layers['scimitar'].sheet_width}x{self.layers['scimitar'].sheet_height}")
        super().draw(screen)

class SimpleGame:
    """Простая игра для демонстрации системы"""
    
    def __init__(self):
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Spiel - LPC анимации (9 кадров ходьбы)")
        self.clock = pygame.time.Clock()
        self.running = True
        self.player = ModularCharacter(400, 300)
        self.enemies = [Enemy(100, 200, self.player)]
        self.player.hp = 100
        self.player.max_hp = 100
        
        
    
    def handle_events(self):
        """Обрабатывает события"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self.player.toggle_clothing("hut", base_layer="head")
                elif event.key == pygame.K_2:
                    self.player.toggle_clothing("leather_armor", base_layer="body")
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
        dt = self.clock.tick(60) / 1000.0
    
        # Игрок
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_LEFT]: dx = -3
        if keys[pygame.K_RIGHT]: dx = 3
        if keys[pygame.K_UP]: dy = -3
        if keys[pygame.K_DOWN]: dy = 3
        self.player.move(dx, dy)
    
        # Враги
        for enemy in self.enemies:
            enemy.update(dt, self.player)
    
        self.player.update(dt)

    def draw(self):
        self.screen.fill((30, 50, 40))
    
        # Все персонажи
        self.player.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
    
        pygame.display.flip()

        # Сетка
        cell_size = 64
        for x in range(0, self.screen_width, cell_size):
            pygame.draw.line(self.screen, (70, 70, 100), (x, 0), (x, self.screen_height), 1)
        for y in range(0, self.screen_height, cell_size):
            pygame.draw.line(self.screen, (70, 70, 100), (0, y), (self.screen_width, y), 1)

        # Персонаж и враги
        self.player.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)

        # HP игрока
        hp_ratio = self.player.hp / self.player.max_hp
        pygame.draw.rect(self.screen, (100, 0, 0), (10, 70, 100, 10))
        pygame.draw.rect(self.screen, (0, 200, 0), (10, 70, 100 * hp_ratio, 10))

        # Плавающий урон игрока
        self.player.damage_texts = [t for t in self.player.damage_texts if t[2] > 0]
        for t in self.player.damage_texts:
            t[2] -= self.clock.get_time() / 1000
            t[1] -= 50 * (self.clock.get_time() / 1000)
            alpha = int(255 * t[2])
            surf = self.player.font.render(str(t[3]), True, (255, 100, 100))
            surf.set_alpha(alpha)
            self.screen.blit(surf, (t[0], t[1]))

        # Отладка
        pygame.display.flip()
    
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