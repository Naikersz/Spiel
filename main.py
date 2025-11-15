import pygame
import sys
import random
import json
from typing import Dict
import os

pygame.init()

# -----------------------------
# КЛАССЫ
# -----------------------------

class MovementController:
    """Управляет движением с коллизиями"""
    def __init__(self, speed: float = 3.0):
        self.speed = speed

    def move(self, entity, dx: int, dy: int, tilemap=None):
        new_x = entity.x + dx
        new_y = entity.y + dy

        if tilemap:
            # X
            if not tilemap.is_blocked(new_x, entity.y):
                entity.x = new_x
            # Y
            if not tilemap.is_blocked(entity.x, new_y):
                entity.y = new_y
        else:
            entity.x = new_x
            entity.y = new_y

        # Направление
        if dx != 0 and dy != 0:
            if abs(dx) > abs(dy):
                entity.current_direction = "left" if dx < 0 else "right"
            else:
                entity.current_direction = "up" if dy < 0 else "down"
        elif dx != 0:
            entity.current_direction = "left" if dx < 0 else "right"
        elif dy != 0:
            entity.current_direction = "up" if dy < 0 else "down"

        # Анимация
        entity.current_animation = "walk" if dx != 0 or dy != 0 else "idle"

# -----------------------------
class CharacterLayer:
    def __init__(self, owner, cfg):
        self.owner = owner
        self.name = cfg["name"]
        self.z_pos = cfg.get("z", 0)
        self.offset_x = cfg.get("offset_x", 0)
        self.offset_y = cfg.get("offset_y", 0)
        self.file_path = cfg["file"]
        
        # Проверяем существование файла
        if not os.path.exists(self.file_path):
            print(f"Warning: File {self.file_path} not found. Creating placeholder.")
            self.create_placeholder_sprite()
        else:
            self.sprite_sheet = pygame.image.load(self.file_path).convert_alpha()
        
        self.frame_w = owner.sprite_w
        self.frame_h = owner.sprite_h
        self.cols = self.sprite_sheet.get_width() // self.frame_w
        self.rows = self.sprite_sheet.get_height() // self.frame_h

    def create_placeholder_sprite(self):
        """Создает placeholder спрайт если файл не найден"""
        colors = {
            "body": (255, 0, 0),
            "head": (0, 255, 0),
            "hut": (0, 0, 255),
            "leather_armor": (255, 165, 0)
        }
        color = colors.get(self.name, (128, 128, 128))
        
        self.sprite_sheet = pygame.Surface((self.owner.sprite_w * 4, self.owner.sprite_h * 4), pygame.SRCALPHA)
        for row in range(4):
            for col in range(4):
                rect = pygame.Rect(col * self.owner.sprite_w, row * self.owner.sprite_h, 
                                 self.owner.sprite_w, self.owner.sprite_h)
                pygame.draw.rect(self.sprite_sheet, color, rect)
                pygame.draw.rect(self.sprite_sheet, (255, 255, 255), rect, 2)

    def get_frame(self, direction, anim_name, frame_index):
        anim_cfg = self.owner.animations.get(anim_name, {"frames": 1, "rows": {"down": 0}})
        row = anim_cfg["rows"].get(direction, 0)
        frames_count = anim_cfg.get("frames", 1)
        frame_index %= frames_count
        rect = pygame.Rect(frame_index * self.frame_w, row * self.frame_h, self.frame_w, self.frame_h)
        surf = pygame.Surface((self.frame_w, self.frame_h), pygame.SRCALPHA)
        surf.blit(self.sprite_sheet, (0, 0), rect)
        return surf

# -----------------------------
class ModularCharacter:
    def __init__(self, x=100, y=100, json_file=None):
        self.x, self.y = x, y
        self.hp, self.max_hp = 100, 100
        self.layers = {}
        self.visible_layers = set()
        self.current_animation = "idle"
        self.current_direction = "down"
        self.current_frame = 0
        self.animation_speed = 0.1
        self.frame_timer = 0.0
        self.sprite_w, self.sprite_h = 64, 64
        self.animations = {}
        self.movement = MovementController(3.0)
        self.damage_texts = []

        if json_file:
            self.load_from_json(json_file)

    def load_from_json(self, path):
        try:
            with open(path, "r") as f:
                cfg = json.load(f)
        
            # Адаптируем под вашу структуру JSON
            if "sprite_size" in cfg:
                self.sprite_w = cfg["sprite_size"]["w"]
                self.sprite_h = cfg["sprite_size"]["h"]
            else:
                self.sprite_w = cfg.get("sprite_w", 64)
                self.sprite_h = cfg.get("sprite_h", 64)
        
            self.animations = cfg.get("animations", {})
        
            # Загружаем слои
            for layer_cfg in cfg.get("layers", []):
                layer = CharacterLayer(self, layer_cfg)
                self.layers[layer.name] = layer
        
            # Устанавливаем видимые слои по умолчанию
            self.visible_layers = {layer.name for layer in self.layers.values()}
        
        except FileNotFoundError:
            print(f"JSON file {path} not found. Using default configuration.")
            self.create_default_layers()
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in {path}: {e}. Using default configuration.")
            self.create_default_layers()
        except KeyError as e:
            print(f"Missing key in JSON {path}: {e}. Using default configuration.")
            self.create_default_layers()
    def create_default_layers(self):
        """Создает слои по умолчанию если JSON не загружен"""
        default_layers = [
            {"name": "body", "file": "body.png", "z": 0},
            {"name": "head", "file": "head.png", "z": 1}
        ]
        for layer_cfg in default_layers:
            layer = CharacterLayer(self, layer_cfg)
            self.layers[layer.name] = layer
        self.visible_layers = {"body", "head"}

    def toggle_clothing(self, layer_name):
        """Переключает видимость слоя одежды"""
        if layer_name in self.visible_layers:
            self.visible_layers.remove(layer_name)
        else:
            self.visible_layers.add(layer_name)

    def move(self, dx, dy, tilemap=None):
        self.movement.move(self, dx, dy, tilemap)

    def update(self, dt):
        self.frame_timer += dt
        speed = 0.08 if self.current_animation == "attack" else self.animation_speed
        if self.frame_timer >= speed:
            self.frame_timer = 0
            self.current_frame += 1
            frames_count = self.animations.get(self.current_animation, {"frames": 1})["frames"]
            if self.current_animation == "attack" and self.current_frame >= frames_count:
                self.current_animation = "idle"
                self.current_frame = 0
            else:
                self.current_frame %= frames_count
        # Обновляем damage_texts
        self.damage_texts = [t for t in self.damage_texts if t[2] > 0]
        for t in self.damage_texts:
            t[2] -= dt
            t[1] -= 50 * dt

    def draw_at(self, screen, x, y):
        # Сортируем слои по z-позиции
        sorted_layers = sorted(self.layers.items(), key=lambda item: item[1].z_pos)
        
        for name, layer in sorted_layers:
            if name not in self.visible_layers:
                continue
            sprite = layer.get_frame(self.current_direction, self.current_animation, self.current_frame)
            screen.blit(sprite, (x - self.sprite_w//2 + layer.offset_x, y - self.sprite_h//2 + layer.offset_y))
        
        # HP бар
        if self.hp < self.max_hp:
            bar_w, bar_h = 60, 8
            hp_ratio = self.hp / self.max_hp
            pygame.draw.rect(screen, (150, 0, 0), (x-30, y-45, bar_w, bar_h), border_radius=3)
            pygame.draw.rect(screen, (0, 200, 0), (x-30, y-45, bar_w * hp_ratio, bar_h), border_radius=3)
        
        # Damage texts
        for t in self.damage_texts:
            alpha = int(255 * t[2])
            font = pygame.font.Font(None, 28)
            text_surf = font.render(str(int(t[3])), True, (255, 100, 100))
            text_surf.set_alpha(alpha)
            screen.blit(text_surf, (x + t[0] - self.x, y + t[1] - self.y))

# -----------------------------
class Enemy(ModularCharacter):
    def __init__(self, x, y, player, json_file=None):
        super().__init__(x, y, json_file=json_file)
        self.player = player
        self.speed = 1.5
        self.attack_range = 80
        self.attack_cooldown = 0
        self.max_cooldown = 1.5
        self.hp = self.max_hp = 50
        self.patrol_points = [(200, 200), (600, 400)]
        self.current_patrol = 0
        self.state = "patrol"
        self.movement = MovementController(self.speed)

    def update(self, dt, player=None, tilemap=None):
        super().update(dt)
        
        if player is None:
            return
            
        # Логика врага
        dist_to_player = ((self.x - player.x)**2 + (self.y - player.y)**2)**0.5
        
        if dist_to_player < self.attack_range:
            self.state = "attack"
            self.current_animation = "attack"
        else:
            self.state = "patrol"
            # Патрулирование
            target_x, target_y = self.patrol_points[self.current_patrol]
            dx = target_x - self.x
            dy = target_y - self.y
            dist_to_target = (dx**2 + dy**2)**0.5
            
            if dist_to_target < 10:
                self.current_patrol = (self.current_patrol + 1) % len(self.patrol_points)
            else:
                dx = (dx / dist_to_target) * self.speed if dist_to_target > 0 else 0
                dy = (dy / dist_to_target) * self.speed if dist_to_target > 0 else 0
                self.move(dx, dy, tilemap)

# -----------------------------
class TileMap:
    def __init__(self, tile_size=64):
        self.tile_size = tile_size
        self.tiles = {}  # {tile_id: [Surface, Surface...]}
        self.collision_tiles = set()
        self.map_data = []
        self.room_settings = {}
        self.load_tiles_config()

    def load_tiles_config(self):
        try:
            with open("game/assets/configs/tiles_config.json", "r") as f:
                config = json.load(f)

            self.tile_size = config.get("tile_size", 64)
            self.room_settings = config.get("room_settings", {})

            for tile_id, tile_cfg in config["tiles"].items():
                surfaces = []

                if "images" in tile_cfg:
                # Загружаем все PNG как поверхности
                    for img_path in tile_cfg["images"]:
                        surf = pygame.image.load(img_path).convert_alpha()
                        surfaces.append(surf)

                if "frames" in tile_cfg:
                # Берём первый PNG как базу для фреймов
                    base_img = pygame.image.load(tile_cfg["images"][0]).convert_alpha()
                    for frame in tile_cfg["frames"]:
                        surf = pygame.Surface((frame["w"], frame["h"]), pygame.SRCALPHA)
                        surf.blit(base_img, (0, 0), (frame["x"], frame["y"], frame["w"], frame["h"]))
                        surfaces.append(surf)

                self.tiles[tile_id] = surfaces

                if tile_cfg.get("collision", False):
                    self.collision_tiles.add(tile_id)


            print("Tiles loaded:", list(self.tiles.keys()))

        except FileNotFoundError:
            print("Tiles config not found!")

    def generate_dungeon(self, screen_w, screen_h):
        cols = screen_w // self.tile_size
        rows = screen_h // self.tile_size
        self.map_data = [["wall" for _ in range(cols)] for _ in range(rows)]
        rooms = []

        settings = self.room_settings
        min_w = settings.get("min_room_width", 10)
        max_w = settings.get("max_room_width", 20)
        min_h = settings.get("min_room_height", 8)
        max_h = settings.get("max_room_height", 16)
        room_count = settings.get("room_count", 7)

        # создаём комнаты
        for _ in range(room_count):
            w = random.randint(min_w * 2, max_w * 2)
            h = random.randint(min_h * 2, max_h * 2)
            x = random.randint(1, max(1, cols - w - 1))
            y = random.randint(1, max(1, rows - h - 1))
            rooms.append((x, y, w, h))

            # заполняем пол конкретным спрайтом
            for i in range(y, y + h):
                for j in range(x, x + w):
                    if 0 <= i < rows and 0 <= j < cols:
                        tile_surf = random.choice(self.tiles["floor_primary"])
                        self.map_data[i][j] = {"type": "floor_primary", "surf": tile_surf}

        # соединяем комнаты коридорами
        for i in range(len(rooms) - 1):
            x1, y1, w1, h1 = rooms[i]
            x2, y2, w2, h2 = rooms[i + 1]
            c1x, c1y = x1 + w1 // 2, y1 + h1 // 2
            c2x, c2y = x2 + w2 // 2, y2 + h2 // 2

            for x in range(min(c1x, c2x), max(c1x, c2x) + 1):
                if 0 <= c1y < rows and 0 <= x < cols:
                    tile_surf = random.choice(self.tiles["floor_primary"])
                    self.map_data[c1y][x] = {"type": "floor_primary", "surf": tile_surf}
            for y in range(min(c1y, c2y), max(c1y, c2y) + 1):
                if 0 <= y < rows and 0 <= c2x < cols:
                    tile_surf = random.choice(self.tiles["floor_primary"])
                    self.map_data[y][c2x] = {"type": "floor_primary", "surf": tile_surf}

        # размещаем объекты
        self.place_objects(rooms, cols, rows)

        # фиксируем стены с рандомным спрайтом
        for y in range(rows):
            for x in range(cols):
                if isinstance(self.map_data[y][x], str) and self.map_data[y][x] == "wall":
                    tile_surf = random.choice(self.tiles["wall"])
                    self.map_data[y][x] = {"type": "wall", "surf": tile_surf}

    def place_objects(self, rooms, cols, rows):
        for room in rooms:
            rx, ry, rw, rh = room

            # сундуки (1-2 шт)
            chest_count = random.randint(1,2)
            chest_positions = []
            for _ in range(chest_count):
                ox = random.randint(rx+1, rx+rw-2)
                oy = random.randint(ry+1, ry+rh-2)
                if 0 <= oy < rows and 0 <= ox < cols:
                    tile_surf = random.choice(self.tiles["chest"])
                    self.map_data[oy][ox] = {"type": "chest", "surf": tile_surf}
                    chest_positions.append((ox, oy))

            # паутина (на стене рядом с сундуком или в углу)
            for _ in range(random.randint(1,2)):
                possible_positions = [
                    (rx+1, ry+1),
                    (rx+rw-2, ry+1),
                    (rx+1, ry+rh-2),
                    (rx+rw-2, ry+rh-2)
                ] + chest_positions
                ox, oy = random.choice(possible_positions)
                if 0 <= oy < rows and 0 <= ox < cols:
                    tile_surf = random.choice(self.tiles["cobweb"])
                    self.map_data[oy][ox] = {"type": "cobweb", "surf": tile_surf}

    def is_blocked(self, x, y):
        tile_x = int(x) // self.tile_size
        tile_y = int(y) // self.tile_size
        if tile_y < 0 or tile_y >= len(self.map_data) or tile_x < 0 or tile_x >= len(self.map_data[0]):
            return True
        tile_info = self.map_data[tile_y][tile_x]
        tile_type = tile_info["type"] if isinstance(tile_info, dict) else tile_info
        return tile_type in self.collision_tiles

    def draw_with_camera(self, screen, cam_x, cam_y):
        tile_size = self.tile_size
        screen_w, screen_h = screen.get_size()
        start_x = max(0, int(cam_x) // tile_size)
        start_y = max(0, int(cam_y) // tile_size)
        end_x = min(len(self.map_data[0]), (int(cam_x) + screen_w) // tile_size + 1)
        end_y = min(len(self.map_data), (int(cam_y) + screen_h) // tile_size + 1)

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile_info = self.map_data[y][x]
                surf = tile_info["surf"] if isinstance(tile_info, dict) else self.tiles[tile_info][0]
                screen.blit(surf, (x * tile_size - int(cam_x), y * tile_size - int(cam_y)))
# -----------------------------
class SimpleGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((800, 600))  # Изменил на оконный режим для отладки
        self.screen_width, self.screen_height = self.screen.get_size()
        pygame.display.set_caption("Spiel - LPC + TileMap + JSON")
        self.clock = pygame.time.Clock()
        self.running = True
        self.camera_x = 0
        self.camera_y = 0
        self.camera_target_x = 0
        self.camera_target_y = 0

        # Карта
        self.tilemap = TileMap()
        self.tilemap.generate_dungeon(self.screen_width, self.screen_height)

        # Игрок с JSON
        try:
            self.player = ModularCharacter(128, 128, json_file="game/assets/configs/player_layers.json")
        except:
            print("Failed to load player JSON, using default")
            self.player = ModularCharacter(128, 128)
        
        self.player.visible_layers = {"body", "head"}

        # Враги
        self.enemies = []
        try:
            enemy = Enemy(384, 128, self.player, json_file="game/assets/configs/enemy_layers.json")
            self.enemies.append(enemy)
        except:
            print("Failed to load enemy JSON, using default enemy")
            enemy = Enemy(384, 128, self.player)
            self.enemies.append(enemy)

    def update_camera(self):
        self.camera_target_x = self.player.x - self.screen_width // 2
        self.camera_target_y = self.player.y - self.screen_height // 2
        map_w = len(self.tilemap.map_data[0]) * self.tilemap.tile_size
        map_h = len(self.tilemap.map_data) * self.tilemap.tile_size
        self.camera_target_x = max(0, min(self.camera_target_x, map_w - self.screen_width))
        self.camera_target_y = max(0, min(self.camera_target_y, map_h - self.screen_height))
        self.camera_x += (self.camera_target_x - self.camera_x) * 0.1
        self.camera_y += (self.camera_target_y - self.camera_y) * 0.1

    def world_to_screen(self, wx, wy):
        return wx - int(self.camera_x), wy - int(self.camera_y)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                # Исправленный вызов toggle_clothing
                elif event.key == pygame.K_1:
                    self.player.toggle_clothing("hat")
                elif event.key == pygame.K_2:
                    self.player.toggle_clothing("leather_armor")
                elif event.key == pygame.K_3:
                    self.player.toggle_clothing("pants")
                elif event.key == pygame.K_4:
                    self.player.toggle_clothing("boots")
                elif event.key == pygame.K_5:
                    self.player.toggle_clothing("gloves")
                elif event.key == pygame.K_6:
                    self.player.toggle_clothing("cuffs")
                elif event.key == pygame.K_7:
                    self.player.toggle_clothing("mantal")

    def update(self):
        dt = self.clock.tick(60) / 1000.0
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] - keys[pygame.K_a]) * 3
        dy = (keys[pygame.K_s] - keys[pygame.K_w]) * 3
        self.player.move(dx, dy, self.tilemap)
        
        for enemy in self.enemies:
            enemy.update(dt, self.player, self.tilemap)
            
        self.player.update(dt)
        self.update_camera()

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.tilemap.draw_with_camera(self.screen, self.camera_x, self.camera_y)
        
        px, py = self.world_to_screen(self.player.x, self.player.y)
        self.player.draw_at(self.screen, px, py)
        
        for e in self.enemies:
            ex, ey = self.world_to_screen(e.x, e.y)
            e.draw_at(self.screen, ex, ey)
        
        # HP игрока
        hp_ratio = self.player.hp / self.player.max_hp
        pygame.draw.rect(self.screen, (100, 0, 0), (10, 10, 200, 20))
        pygame.draw.rect(self.screen, (0, 200, 0), (10, 10, 200 * hp_ratio, 20))
        
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
        pygame.quit()
        sys.exit()

# -----------------------------
if __name__ == "__main__":
    SimpleGame().run()