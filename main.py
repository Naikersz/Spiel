import pygame
import os
import sys
from typing import Dict, List, Optional, Tuple

pygame.init()

# 🔥 НОВЫЙ КЛАСС: Управление движением (общий для всех)
class MovementController:
    """Управляет движением с коллизиями"""
    def __init__(self, speed: float = 3.0):
        self.speed = speed
    
    def move(self, entity, dx: int, dy: int, tilemap=None):
        """Двигает entity с учётом коллизий"""
        new_x = entity.x + dx
        new_y = entity.y + dy
        
        if tilemap:
            # Коллизия по X
            if not tilemap.is_blocked(new_x, entity.y):
                entity.x = new_x
            # Коллизия по Y
            if not tilemap.is_blocked(entity.x, new_y):
                entity.y = new_y
        else:
            entity.x = new_x
            entity.y = new_y
        
        # Направление (приоритет: диагональ → горизонталь → вертикаль)
        if dx != 0 and dy != 0:
            if abs(dx) > abs(dy):
                entity.current_direction = "left" if dx < 0 else "right"
            else:
                entity.current_direction = "up" if dy < 0 else "down"
        elif dy != 0:
            entity.current_direction = "up" if dy < 0 else "down"
        elif dx != 0:
            entity.current_direction = "left" if dx < 0 else "right"
        
        # Анимация
        entity.current_animation = "walk" if dx != 0 or dy != 0 else "idle"

class CharacterLayer:
    WALK_DIRECTIONS = {"up": 8, "left": 9, "down": 10, "right": 11}
    ATTACK_DIRECTIONS = {"up": 1, "left": 2, "down": 3, "right": 4}

    def __init__(self, sprite_path: str, layer_name: str, z_pos: int = 0):
        self.sprite_path = sprite_path
        self.name = layer_name
        self.z_pos = z_pos
        self.sprite_sheet = self.load_image(sprite_path)
        
        if self.sprite_sheet:
            self.sheet_width = self.sprite_sheet.get_width()
            self.sheet_height = self.sprite_sheet.get_height()
            self.frame_width, self.frame_height = self.detect_frame_size()
        else:
            self.sheet_width = self.sheet_height = self.frame_width = self.frame_height = 64
        
        self.rows = self.sheet_height // self.frame_height
        self.cols = self.sheet_width // self.frame_width

    def load_image(self, path: str) -> Optional[pygame.Surface]:
        possible_paths = [
            path, f"game/assets/sprites/{os.path.basename(path)}",
            f"assets/sprites/{os.path.basename(path)}", os.path.basename(path)
        ]
        for p in possible_paths:
            if os.path.exists(p):
                try:
                    return pygame.image.load(p).convert_alpha()
                except:
                    continue
        print(f"Не найден: {path}")
        return None

    def detect_frame_size(self) -> Tuple[int, int]:
        if self.sheet_width % 64 == 0 and self.sheet_height % 64 == 0:
            return 64, 64
        for size in [32, 48, 96]:
            if self.sheet_width % size == 0 and self.sheet_height % size == 0:
                return size, size
        return 64, 64

    def get_frame_rect(self, direction: str, animation_type: str, frame: int) -> pygame.Rect:
        if self.name in ["scimitar", "scimitar_attack"]:
            row = self.ATTACK_DIRECTIONS.get(direction, 3) if "attack" in self.name else self.WALK_DIRECTIONS.get(direction, 10)
            max_frames = 6 if "attack" in self.name else 9
        elif animation_type == "walk":
            row, max_frames = self.WALK_DIRECTIONS.get(direction, 10), 9
        elif animation_type == "attack":
            row, max_frames = self.ATTACK_DIRECTIONS.get(direction, 3), 6
        else:
            row, max_frames = self.WALK_DIRECTIONS.get(direction, 10), 1

        frame = frame % max_frames
        x, y = frame * self.frame_width, row * self.frame_height
        
        if x + self.frame_width > self.sheet_width or y + self.frame_height > self.sheet_height:
            return pygame.Rect(0, 10 * self.frame_height, self.frame_width, self.frame_height)
        return pygame.Rect(x, y, self.frame_width, self.frame_height)

class ModularCharacter:
    def __init__(self, x: int = 100, y: int = 100):
        self.x, self.y = x, y
        self.hp, self.max_hp = 100, 100
        self.damage_texts = []
        self.layers: Dict[str, CharacterLayer] = {}
        self.current_animation = "idle"
        self.current_direction = "down"
        self.current_frame = 0
        self.animation_speed = 0.1
        self.frame_timer = 0.0
        self.visible_layers = set()
        self.font = pygame.font.Font(None, 28)
        self.movement = MovementController(3.0)  # 🔥 НОВОЕ!
        self.load_default_layers()

    def load_default_layers(self):
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
            self.layers[name] = CharacterLayer(path, name, z_pos=z)
        self.visible_layers = {"body", "head"}

    def toggle_clothing(self, item_name: str, base_layer: str = None) -> bool:
        if item_name not in self.layers:
            print(f"Предмет не найден: {item_name}")
            return False
        if item_name in self.visible_layers:
            self.visible_layers.remove(item_name)
            if base_layer in self.layers:
                self.visible_layers.add(base_layer)
            print(f"Снято: {item_name}")
            return False
        else:
            if base_layer in self.visible_layers:
                self.visible_layers.remove(base_layer)
            self.visible_layers.add(item_name)
            print(f"Надето: {item_name}")
            return True

    def move(self, dx: int, dy: int, tilemap=None):
        """🔥 ПРОСТО! Вызывает MovementController"""
        self.movement.move(self, dx, dy, tilemap)

    def update_animation(self, dt: float):
        self.frame_timer += dt
        if self.current_animation == "attack":
            if self.frame_timer >= 0.08:
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
        self.damage_texts = [t for t in self.damage_texts if t[2] > 0]
        for t in self.damage_texts:
            t[2] -= dt
            t[1] -= 50 * dt

    def draw_damage_texts(self, screen: pygame.Surface, draw_x: int, draw_y: int):
        for text in self.damage_texts:
            # Смещение относительно позиции персонажа
            text_x = draw_x + (text[0] - self.x)
            text_y = draw_y + (text[1] - self.y)
            alpha = int(255 * text[2])
            surf = self.font.render(str(int(text[3])), True, (255, 100, 100))
            surf.set_alpha(alpha)
            screen.blit(surf, (text_x, text_y))

    def take_damage(self, damage: int):
        self.hp = max(0, self.hp - damage)
        self.damage_texts.append([self.x, self.y - 30, 1.0, damage])
        print(f"Получено {damage} урона! HP: {self.hp}")

    def update(self, dt: float):
        self.update_animation(dt)
        self.update_damage_texts(dt)

    def draw(self, screen: pygame.Surface):
        # Используем координаты с камерой, если есть
        draw_x = getattr(self, '_draw_x', self.x)
        draw_y = getattr(self, '_draw_y', self.y)

        if self.layers:
            layers_to_draw = sorted(
                [self.layers[n] for n in self.visible_layers if n in self.layers],
                key=lambda l: l.z_pos
            )
            for layer in layers_to_draw:
                try:
                    rect = layer.get_frame_rect(self.current_direction, self.current_animation, self.current_frame)
                    if (rect.x + rect.width <= layer.sheet_width and 
                        rect.y + rect.height <= layer.sheet_height):
                        sprite = layer.sprite_sheet.subsurface(rect)  # ← sprite создаётся ЗДЕСЬ
                        screen.blit(sprite, (draw_x, draw_y))        # ← используем sprite
                except Exception as e:
                    pass  # Игнорируем ошибки кадра

        # HP бар
        if self.hp < self.max_hp:
            bar_w, bar_h = 60, 8
            hp_ratio = max(0, self.hp / self.max_hp)
            pygame.draw.rect(screen, (150, 0, 0), (draw_x - 30, draw_y - 45, bar_w, bar_h), border_radius=3)
            pygame.draw.rect(screen, (0, 200, 0), (draw_x - 30, draw_y - 45, bar_w * hp_ratio, bar_h), border_radius=3)

        self.draw_damage_texts(screen, draw_x, draw_y)  
    def draw_at(self, screen, x, y):
        self._draw_x = x
        self._draw_y = y
        self.draw(screen)

    def draw_damage_texts_at(self, screen, draw_x, draw_y):
        """Тексты урона с камерой"""
        for text in self.damage_texts:
            text_screen_x = draw_x + text[0] - self.x
            text_screen_y = draw_y + text[1] - self.y
            alpha = int(255 * text[2])
            surf = self.font.render(str(int(text[3])), True, (255, 100, 100))
            surf.set_alpha(alpha)
            screen.blit(surf, (text_screen_x, text_screen_y))

# 🔥 ИСПРАВЛЕННЫЙ ENEMY (использует MovementController!)
class Enemy(ModularCharacter):
    def __init__(self, x: int, y: int, player_ref):
        super().__init__(x, y)
        self.player = player_ref
        self.speed = 1.5
        self.attack_range = 80
        self.attack_cooldown = 0
        self.max_cooldown = 1.5
        self.hp = self.max_hp = 50
        self.patrol_points = [(200, 200), (600, 400)]
        self.current_patrol = 0
        self.state = "patrol"
        self.movement = MovementController(self.speed)  # 🔥 Медленнее!
        
        # Слои врага
        self.layers.clear()
        self.visible_layers.clear()
        self.load_default_layers()

    def load_default_layers(self):
        layers = [
            ("body", "game/assets/sprites/body/bodies/male/bodySkeleton.png", 10),
            ("head", "game/assets/sprites/head/heads/enemies/headSkeleton.png", 50),
            ("scimitar", "game/assets/sprites/weapons/scimitarwWalk.png", 40),
            ("scimitar_attack", "game/assets/sprites/weapons/scimitarSlash.png", 41),
        ]
        for name, path, z in layers:
            self.layers[name] = CharacterLayer(path, name, z_pos=z)
        self.visible_layers = {"body", "head", "scimitar"}

    def update(self, dt: float, player, tilemap):
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        dist = ((player.x - self.x)**2 + (player.y - self.y)**2)**0.5

        # ИИ
        self.state = "chase" if dist < 200 else "patrol"
        self.visible_layers = {"body", "head", "scimitar_attack"} if self.current_animation == "attack" else {"body", "head", "scimitar"}

        # АТАКА (🔥 ИСПРАВЛЕНО!)
        if (self.state == "chase" and dist < self.attack_range and 
            self.attack_cooldown <= 0 and self.current_animation != "attack"):
            self.current_animation = "attack"
            self.current_frame = 0  # ← используем current_frame!
            self.attack_cooldown = self.max_cooldown

        # Движение (только не во время атаки)
        if self.current_animation != "attack":
            dx, dy = 0, 0
            if self.state == "chase":
                dx = 1 if player.x > self.x else -1 if player.x < self.x else 0
                dy = 1 if player.y > self.y else -1 if player.y < self.y else 0
                norm = max((dx**2 + dy**2)**0.5, 1)
                dx = int(dx / norm * self.speed)
                dy = int(dy / norm * self.speed)
            elif self.state == "patrol":
                tx, ty = self.patrol_points[self.current_patrol]
                dx, dy = tx - self.x, ty - self.y
                dist_to = max((dx**2 + dy**2)**0.5, 1)
                if dist_to < 20:
                    self.current_patrol = (self.current_patrol + 1) % 2
                else:
                    dx = int(dx / dist_to * self.speed)
                    dy = int(dy / dist_to * self.speed)
            
            self.movement.move(self, dx, dy, tilemap)  # 🔥 ПРОСТО!

        # Урон на 3-м кадре атаки
        if self.current_animation == "attack" and self.current_frame == 3:
            player.take_damage(15)

        super().update(dt)

    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, (255, 0, 0), (self.x-32, self.y-64, 64, 64), 3)
        super().draw(screen)



class TileMap:
    def __init__(self, tile_size=64, tileset_path="game/assets/tiles/tileset.png"):
        self.tile_size = tile_size
        self.tileset_path = tileset_path

        # Временная карта, чтобы было что-то по умолчанию
        self.map_data = [
            "####################",
            "#..................#",
            "#......##......##..#",
            "#..................#",
            "#..##.........##...#",
            "#..................#",
            "####################",
        ]
        self.collision_tiles = {"#"}

        self.tiles = self.load_tileset()

    # 👇 ДОБАВЬ ЭТО:
    def generate_fullscreen_map(self, screen_w, screen_h):
        """Создаёт карту, которая хотя бы покрывает весь экран."""
        import math

        cols = math.ceil(screen_w / self.tile_size)
        rows = math.ceil(screen_h / self.tile_size)

        # Минимум 3×3, чтобы были нормальные стены
        cols = max(cols, 3)
        rows = max(rows, 3)

        # Верхняя стена
        new_map = ["#" * cols]

        # Средние строки: стены по краям, пол внутри
        for _ in range(rows - 2):
            new_map.append("#" + "." * (cols - 2) + "#")

        # Нижняя стена
        new_map.append("#" * cols)

        self.map_data = new_map
    def load_tileset(self):
        """Режет 1536x1024 → 24x16 тайлов по 64x64"""
        try:
            tileset = pygame.image.load(self.tileset_path).convert_alpha()
            w, h = tileset.get_width(), tileset.get_height()
            print(f"Успешно загружен tileset: {w}x{h}")

            tiles = {}
            tile_w, tile_h = 64, 64

            def get_tile(col, row):
                return tileset.subsurface((col * tile_w, row * tile_h, tile_w, tile_h))

            tiles["."] = get_tile(0, 0)   # пол / трава
            tiles["#"] = get_tile(1, 0)   # стена

            return tiles

        except Exception as e:
            print(f"Ошибка загрузки tileset: {e}")
            return self.create_fallback()

    def create_fallback(self):
        """Запасные тайлы"""
        grass = pygame.Surface((64, 64)); grass.fill((40, 120, 40))
        wall  = pygame.Surface((64, 64)); wall.fill((80, 80, 80))
        return {"#": wall, ".": grass}

    def is_blocked(self, x, y):
        """Коллизия по центру персонажа"""
        tile_x = (x + 32) // self.tile_size
        tile_y = (y + 32) // self.tile_size
        
        if (tile_y < 0 or tile_y >= len(self.map_data) or 
            tile_x < 0 or tile_x >= len(self.map_data[0])):
            return True
            
        return self.map_data[tile_y][tile_x] in self.collision_tiles

    def draw_with_camera(self, screen, cam_x, cam_y):
        """Рисует только видимые тайлы, учитывая полностью экран"""
        tile_size = self.tile_size
        screen_w, screen_h = screen.get_size()

        cam_left = max(0, int(cam_x) // tile_size)
        cam_top = max(0, int(cam_y) // tile_size)
        cam_right = min(len(self.map_data[0]), (int(cam_x) + screen_w + tile_size - 1) // tile_size)
        cam_bottom = min(len(self.map_data), (int(cam_y) + screen_h + tile_size - 1) // tile_size)

        for row_i in range(cam_top, cam_bottom):
            for col_i in range(cam_left, cam_right):
                char = self.map_data[row_i][col_i]
                tile = self.tiles.get(char, self.tiles["."])
                screen_x = col_i * tile_size - int(cam_x)
                screen_y = row_i * tile_size - int(cam_y)
                screen.blit(tile, (screen_x, screen_y))
class SimpleGame:
    def __init__(self):
        # FULLSCREEN
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.screen_width, self.screen_height = self.screen.get_size()
        pygame.display.set_caption("Spiel - LPC + TileMap + CAMERA")
        self.clock = pygame.time.Clock()
        self.running = True

        # КАМЕРА
        self.camera_x = 0
        self.camera_y = 0
        self.camera_target_x = 0
        self.camera_target_y = 0

        # Тайлсет и персонажи
        self.tilemap = TileMap(tileset_path="game/assets/tiles/tileset.png")

        # 🔥 ВАЖНО: растягиваем карту под экран
        self.tilemap.generate_fullscreen_map(self.screen_width, self.screen_height)

        self.player = ModularCharacter(128, 128)
        self.enemies = [Enemy(384, 128, self.player)]
        
    def update_camera(self):
        """Плавно следует за игроком"""
        self.camera_target_x = self.player.x - self.screen_width // 2
        self.camera_target_y = self.player.y - self.screen_height // 2
        
        # Границы карты (чтобы камера не уходила за края)
        map_w = len(self.tilemap.map_data[0]) * self.tilemap.tile_size
        map_h = len(self.tilemap.map_data) * self.tilemap.tile_size
        
        self.camera_target_x = max(0, min(self.camera_target_x, map_w - self.screen_width))
        self.camera_target_y = max(0, min(self.camera_target_y, map_h - self.screen_height))
        
        # Плавное движение камеры
        self.camera_x += (self.camera_target_x - self.camera_x) * 0.1
        self.camera_y += (self.camera_target_y - self.camera_y) * 0.1

    def world_to_screen(self, wx, wy):
        return (wx - int(self.camera_x), wy - int(self.camera_y))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                toggles = {
                    pygame.K_1: ("hut", "head"), pygame.K_2: ("leather_armor", "body"),
                    pygame.K_3: ("gloves", None), pygame.K_4: ("pants", None),
                    pygame.K_5: ("boots", None), pygame.K_6: ("mantal", None),
                    pygame.K_7: ("cuffs", None)
                }
                if event.key in toggles:
                    base = toggles[event.key][1]
                    self.player.toggle_clothing(toggles[event.key][0], base)
                elif event.key == pygame.K_SPACE:
                    self.player.current_frame = (self.player.current_frame + 1) % 9

    def update(self):
        dt = self.clock.tick(60) / 1000.0
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] - keys[pygame.K_a]) * 3   # 🔥 A/D вместо стрелок
        dy = (keys[pygame.K_s] - keys[pygame.K_w]) * 3   # 🔥 W/S
        self.player.move(dx, dy, self.tilemap)
        
        for enemy in self.enemies:
            enemy.update(dt, self.player, self.tilemap)
        self.player.update(dt)
        
        self.update_camera()  # 🔥 Обновляем камеру

    def draw(self):
        self.tilemap.draw_with_camera(self.screen, self.camera_x, self.camera_y)
        
        # Персонажи с камерой
        px, py = self.world_to_screen(self.player.x, self.player.y)
        self.player.draw_at(self.screen, px, py)
        
        for enemy in self.enemies:
            ex, ey = self.world_to_screen(enemy.x, enemy.y)
            enemy.draw_at(self.screen, ex, ey)
        
        # HP (всегда в углу экрана)
        hp_ratio = self.player.hp / self.player.max_hp
        pygame.draw.rect(self.screen, (100, 0, 0), (10, 10, 200, 20))
        pygame.draw.rect(self.screen, (0, 200, 0), (10, 10, 200 * hp_ratio, 20))
        
        # 🔥 ИНФО
        font = pygame.font.Font(None, 36)
        text = font.render(f"Камера: {int(self.camera_x)}, {int(self.camera_y)}", True, (255,255,255))
        self.screen.blit(text, (10, 50))
        
        pygame.display.flip()

    def run(self):
        print("=" * 60)
        print("✅ LPC + TILEMAP + AI + КАМЕРА!")
        print("WASD: движение | 1-7: одежда | SPACE: кадр")
        print("Экран: 1280x720 | Карта видна полностью!")
        print("=" * 60)
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    SimpleGame().run()