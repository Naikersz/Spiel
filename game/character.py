# game/character.py
import pygame
import os
from typing import Dict, Optional, Tuple

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
        print(f"Не найден спрайт: {path}")
        return None

    def detect_frame_size(self) -> Tuple[int, int]:
        if (self.sheet_width % 64 == 0 and self.sheet_height % 64 == 0):
            return 64, 64
        for size in [32, 48, 96]:
            if (self.sheet_width % size == 0 and self.sheet_height % size == 0):
                return size, size
        return 64, 64

    def get_frame_rect(self, direction: str, animation_type: str, frame: int) -> pygame.Rect:
        if self.name in ["scimitar", "scimitar_attack"]:
            row = self.ATTACK_DIRECTIONS.get(direction, 3) if "attack" in self.name else self.WALK_DIRECTIONS.get(direction, 10)
            max_frames = 6 if "attack" in self.name else 9
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
        self.frame_timer = 0.0
        self.visible_layers = set()
        self.font = pygame.font.Font(None, 28)
        self.load_default_layers()

    def load_default_layers(self):
        # Пытаемся загрузить из player_layers.json
        layers_config = self._load_layers_config()
        
        if layers_config:
            # Загружаем из конфига
            for layer_data in layers_config.get("layers", []):
                name = layer_data.get("name")
                file_path = layer_data.get("file")
                z = layer_data.get("z", 0)
                if name and file_path:
                    self.layers[name] = CharacterLayer(file_path, name, z_pos=z)
            # Создаем синоним "hut" для "hat" для совместимости
            if "hat" in self.layers and "hut" not in self.layers:
                self.layers["hut"] = self.layers["hat"]
            # Видимые слои по умолчанию (body и head)
            self.visible_layers = {"body", "head"}
        else:
            # Fallback к старым слоям
            layers = [
                ("body", "game/assets/sprites/body/bodies/male/bodyMale.png", 10),
                ("head", "game/assets/sprites/head/heads/human/male/headMale.png", 50),
                ("leather_armor", "game/assets/sprites/torso/torsoLeather.png", 20),
                ("gloves", "game/assets/sprites/arms/gloves/glovesLeather.png", 30),
                ("pants", "game/assets/sprites/legs/hose/hoseLeather.png", 15),
                ("boots", "game/assets/sprites/feet/boots/bootsBrown.png", 18),
                ("mantal", "game/assets/sprites/arms/shoulders/mantal/mantalLeather.png", 25),
                ("cuffs", "game/assets/sprites/arms/wrists/cuffs/cuffsLeather.png", 35),
                ("hut", "game/assets/sprites/head/heads/human/male/hut.png", 100),
                ("hat", "game/assets/sprites/head/heads/human/male/hut.png", 100),  # Синоним для hut
            ]
            for name, path, z in layers:
                self.layers[name] = CharacterLayer(path, name, z_pos=z)
            self.visible_layers = {"body", "head"}
    
    def _load_layers_config(self):
        """Загружает конфигурацию слоев из player_layers.json"""
        import json
        possible_paths = [
            "game/assets/configs/player_layers.json",
            "assets/configs/player_layers.json",
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "configs", "player_layers.json")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception as e:
                    print(f"Error loading player_layers.json from {path}: {e}")
        
        return None

    def toggle_clothing(self, item_name: str, base_layer: str = None) -> bool:
        """
        Переключает видимость предмета одежды.
        
        Args:
            item_name: Имя предмета одежды
            base_layer: Базовый слой (для совместимости, не используется для большинства предметов)
        
        Returns:
            bool: True если надето, False если снято
        """
        if item_name not in self.layers:
            print(f"Предмет не найден: {item_name}")
            return False
        
        # Определяем, какие слои должны оставаться видимыми
        # Базовые слои, которые никогда не должны скрываться
        base_layers = {"body", "head"}
        
        # Предметы, которые являются дополнительными слоями (не заменяют базовые)
        additional_layers = {"leather_armor", "hut", "hat", "gloves", "pants", "boots", "mantal", "cuffs"}
        
        if item_name in self.visible_layers:
            # Снимаем предмет
            self.visible_layers.remove(item_name)
            # Убеждаемся, что базовые слои остаются видимыми
            if item_name in additional_layers:
                # Для дополнительных слоев базовые остаются
                if base_layer and base_layer in self.layers and base_layer not in self.visible_layers:
                    self.visible_layers.add(base_layer)
            print(f"Снято: {item_name}")
            return False
        else:
            # Надеваем предмет
            # Для дополнительных слоев базовые остаются видимыми
            if item_name in additional_layers:
                # Не удаляем базовый слой - дополнительные слои идут поверх
                if base_layer and base_layer not in self.visible_layers:
                    self.visible_layers.add(base_layer)
            else:
                # Для предметов, которые заменяют базовый слой (если такие есть)
                if base_layer and base_layer in self.visible_layers:
                    self.visible_layers.remove(base_layer)
            
            self.visible_layers.add(item_name)
            
            # Убеждаемся, что базовые слои всегда видимы
            for base in base_layers:
                if base in self.layers and base not in self.visible_layers:
                    self.visible_layers.add(base)
            
            print(f"Надето: {item_name}")
            return True

    def move(self, dx: int, dy: int):
        self.x += dx
        self.y += dy
        if dy < 0: self.current_direction = "up"
        elif dy > 0: self.current_direction = "down"
        elif dx < 0: self.current_direction = "left"
        elif dx > 0: self.current_direction = "right"
        self.current_animation = "walk" if dx != 0 or dy != 0 else "idle"

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

    def draw_damage_texts(self, screen: pygame.Surface):
        for text in self.damage_texts:
            alpha = int(255 * text[2])
            surf = self.font.render(str(int(text[3])), True, (255, 100, 100))
            surf.set_alpha(alpha)
            screen.blit(surf, (text[0], text[1]))

    def take_damage(self, damage: int):
        self.hp = max(0, self.hp - damage)
        self.damage_texts.append([self.x, self.y - 30, 1.0, damage])
        print(f"Получено {damage} урона! HP: {self.hp}")

    def update(self, dt: float):
        self.update_animation(dt)
        self.update_damage_texts(dt)

    def draw(self, screen: pygame.Surface):
        if self.layers:
            layers_to_draw = [self.layers[n] for n in self.visible_layers if n in self.layers]
            layers_to_draw.sort(key=lambda l: l.z_pos)
            for layer in layers_to_draw:
                try:
                    rect = layer.get_frame_rect(self.current_direction, self.current_animation, self.current_frame)
                    if (rect.x + rect.width <= layer.sheet_width and rect.y + rect.height <= layer.sheet_height):
                        sprite = layer.sprite_sheet.subsurface(rect)
                        screen.blit(sprite, (self.x, self.y))
                except: pass

        if self.hp < self.max_hp:
            bar_w, bar_h = 60, 8
            hp_ratio = max(0, self.hp / self.max_hp)
            pygame.draw.rect(screen, (150, 0, 0), (self.x-30, self.y-45, bar_w, bar_h), border_radius=3)
            pygame.draw.rect(screen, (0, 200, 0), (self.x-30, self.y-45, bar_w * hp_ratio, bar_h), border_radius=3)

        self.draw_damage_texts(screen)