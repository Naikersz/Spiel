"""
Tilemap - генерация подземелья с использованием BSP + случайные комнаты
Стиль "The Greedy Cave"
"""
import pygame
import random
import json
import os
from typing import List, Tuple, Optional, Dict, Any


class BSPNode:
    """Узел BSP дерева"""
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.left = None
        self.right = None
        self.room = None  # Комната в этом узле


class Tilemap:
    """Генератор карты подземелья"""
    
    def __init__(self, width: int = 100, height: int = 100, tile_size: int = 32):
        """
        Инициализация Tilemap
        
        Args:
            width: Ширина карты в тайлах
            height: Высота карты в тайлах
            tile_size: Размер тайла в пикселях
        """
        self.width = width
        self.height = height
        self.tile_size = tile_size
        
        # Инициализация карты (0 = стена, 1 = пол)
        self.map_data = [[0 for _ in range(width)] for _ in range(height)]
        
        # Загрузка конфигурации тайлов
        self.tiles_config = self._load_tiles_config()
        
        # Загрузка изображений тайлов
        self.tile_images = {}
        self._load_tile_images()
        
        # Генерация карты
        self.rooms = []
        self.corridors = []
        self.bsp_root = None
        
    def _load_tiles_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию тайлов"""
        config_path = "game/assets/configs/tiles_config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading tiles config: {e}")
        
        # Дефолтная конфигурация
        return {
            "tile_size": 32,
            "room_settings": {
                "min_room_width": 6,
                "max_room_width": 12,
                "min_room_height": 6,
                "max_room_height": 12,
            },
            "tiles": {
                "floor_primary": {
                    "images": [
                        "game/assets/tiles/cobble_blood1.png",
                        "game/assets/tiles/cobble_blood2.png",
                    ]
                },
                "wall": {
                    "images": [
                        "game/assets/tiles/brick_dark0.png",
                        "game/assets/tiles/brick_dark1.png",
                    ]
                }
            }
        }
    
    def _load_tile_images(self):
        """Загружает изображения тайлов"""
        # Загружаем пол
        floor_images = self.tiles_config.get("tiles", {}).get("floor_primary", {}).get("images", [])
        self.tile_images["floor"] = []
        for img_path in floor_images[:2]:  # Используем только первые 2
            if os.path.exists(img_path):
                try:
                    img = pygame.image.load(img_path).convert_alpha()
                    img = pygame.transform.scale(img, (self.tile_size, self.tile_size))
                    self.tile_images["floor"].append(img)
                except Exception as e:
                    print(f"Error loading floor image {img_path}: {e}")
        
        # Загружаем стены
        wall_images = self.tiles_config.get("tiles", {}).get("wall", {}).get("images", [])
        self.tile_images["wall"] = []
        for img_path in wall_images[:2]:  # Используем только первые 2
            if os.path.exists(img_path):
                try:
                    img = pygame.image.load(img_path).convert_alpha()
                    img = pygame.transform.scale(img, (self.tile_size, self.tile_size))
                    self.tile_images["wall"].append(img)
                except Exception as e:
                    print(f"Error loading wall image {img_path}: {e}")
        
        # Если изображения не загружены, создаем placeholder
        if not self.tile_images.get("floor"):
            placeholder = pygame.Surface((self.tile_size, self.tile_size))
            placeholder.fill((100, 50, 50))
            self.tile_images["floor"] = [placeholder]
        
        if not self.tile_images.get("wall"):
            placeholder = pygame.Surface((self.tile_size, self.tile_size))
            placeholder.fill((80, 80, 80))
            self.tile_images["wall"] = [placeholder]
    
    def generate(self):
        """Генерирует карту подземелья"""
        # Очищаем карту
        self.map_data = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.rooms = []
        self.corridors = []
        
        # Создаем BSP дерево (3-4 итерации)
        self.bsp_root = self._create_bsp_tree(0, 0, self.width, self.height, depth=0, max_depth=4)
        
        # Создаем комнаты в листьях BSP
        self._create_rooms(self.bsp_root)
        
        # Соединяем комнаты коридорами
        self._connect_rooms(self.bsp_root)
        
        # Отрисовываем стены вокруг комнат
        self._create_walls()
    
    def _create_bsp_tree(self, x: int, y: int, width: int, height: int, depth: int, max_depth: int) -> Optional[BSPNode]:
        """Создает BSP дерево"""
        if depth >= max_depth or width < 12 or height < 12:
            return None
        
        node = BSPNode(x, y, width, height)
        
        # Случайный выбор оси разделения
        split_horizontal = random.random() < 0.5
        
        if split_horizontal:
            # Горизонтальное разделение
            if height < 20:
                return None
            split_pos = random.randint(height // 3, 2 * height // 3)
            node.left = self._create_bsp_tree(x, y, width, split_pos, depth + 1, max_depth)
            node.right = self._create_bsp_tree(x, y + split_pos, width, height - split_pos, depth + 1, max_depth)
        else:
            # Вертикальное разделение
            if width < 20:
                return None
            split_pos = random.randint(width // 3, 2 * width // 3)
            node.left = self._create_bsp_tree(x, y, split_pos, height, depth + 1, max_depth)
            node.right = self._create_bsp_tree(x + split_pos, y, width - split_pos, height, depth + 1, max_depth)
        
        return node
    
    def _create_rooms(self, node: Optional[BSPNode]):
        """Создает комнаты в листьях BSP дерева"""
        if node is None:
            return
        
        if node.left is None and node.right is None:
            # Лист - создаем комнату
            room_settings = self.tiles_config.get("room_settings", {})
            min_w = room_settings.get("min_room_width", 6)
            max_w = room_settings.get("max_room_width", 12)
            min_h = room_settings.get("min_room_height", 6)
            max_h = room_settings.get("max_room_height", 12)
            
            # Сжатие: комната на 2-4 тайла меньше области
            margin = random.randint(2, 4)
            room_width = min(random.randint(min_w, max_w), node.width - margin * 2)
            room_height = min(random.randint(min_h, max_h), node.height - margin * 2)
            
            # Гарантируем минимум 4x4
            room_width = max(4, room_width)
            room_height = max(4, room_height)
            
            # Позиция комнаты с отступом
            room_x = node.x + random.randint(margin, max(margin, node.width - room_width - margin))
            room_y = node.y + random.randint(margin, max(margin, node.height - room_height - margin))
            
            node.room = (room_x, room_y, room_width, room_height)
            self.rooms.append(node.room)
            
            # Заполняем пол
            for ry in range(room_y, room_y + room_height):
                for rx in range(room_x, room_x + room_width):
                    if 0 <= ry < self.height and 0 <= rx < self.width:
                        self.map_data[ry][rx] = 1
        else:
            # Рекурсивно обрабатываем дочерние узлы
            self._create_rooms(node.left)
            self._create_rooms(node.right)
    
    def _connect_rooms(self, node: Optional[BSPNode]):
        """Соединяет комнаты коридорами"""
        if node is None or (node.left is None and node.right is None):
            return
        
        # Рекурсивно соединяем дочерние узлы
        self._connect_rooms(node.left)
        self._connect_rooms(node.right)
        
        # Соединяем комнаты из левого и правого поддеревьев
        left_room = self._get_room_from_node(node.left)
        right_room = self._get_room_from_node(node.right)
        
        if left_room and right_room:
            # Центры комнат
            lx, ly, lw, lh = left_room
            rx, ry, rw, rh = right_room
            left_center = (lx + lw // 2, ly + lh // 2)
            right_center = (rx + rw // 2, ry + rh // 2)
            
            # L-образный коридор (ширина 2 тайла)
            # Сначала горизонтально, затем вертикально (или наоборот)
            if random.random() < 0.5:
                # Горизонтально, затем вертикально
                self._create_corridor_horizontal(left_center[0], left_center[1], right_center[0], left_center[1], 2)
                self._create_corridor_vertical(right_center[0], left_center[1], right_center[0], right_center[1], 2)
            else:
                # Вертикально, затем горизонтально
                self._create_corridor_vertical(left_center[0], left_center[1], left_center[0], right_center[1], 2)
                self._create_corridor_horizontal(left_center[0], right_center[1], right_center[0], right_center[1], 2)
    
    def _get_room_from_node(self, node: Optional[BSPNode]) -> Optional[Tuple[int, int, int, int]]:
        """Получает комнату из узла (или из дочерних)"""
        if node is None:
            return None
        
        if node.room:
            return node.room
        
        # Ищем в дочерних узлах
        left_room = self._get_room_from_node(node.left)
        if left_room:
            return left_room
        
        return self._get_room_from_node(node.right)
    
    def _create_corridor_horizontal(self, x1: int, y: int, x2: int, y2: int, width: int):
        """Создает горизонтальный коридор"""
        start_x = min(x1, x2)
        end_x = max(x1, x2)
        start_y = y - width // 2
        
        for ry in range(start_y, start_y + width):
            for rx in range(start_x, end_x + 1):
                if 0 <= ry < self.height and 0 <= rx < self.width:
                    self.map_data[ry][rx] = 1
    
    def _create_corridor_vertical(self, x: int, y1: int, x2: int, y2: int, width: int):
        """Создает вертикальный коридор"""
        start_y = min(y1, y2)
        end_y = max(y1, y2)
        start_x = x - width // 2
        
        for ry in range(start_y, end_y + 1):
            for rx in range(start_x, start_x + width):
                if 0 <= ry < self.height and 0 <= rx < self.width:
                    self.map_data[ry][rx] = 1
    
    def _create_walls(self):
        """Создает стены вокруг пола"""
        new_map = [row[:] for row in self.map_data]
        
        for y in range(self.height):
            for x in range(self.width):
                if self.map_data[y][x] == 1:  # Пол
                    # Проверяем соседей
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = x + dx, y + dy
                            if 0 <= ny < self.height and 0 <= nx < self.width:
                                if self.map_data[ny][nx] == 0:  # Сосед - стена
                                    # Оставляем как есть (стена уже есть)
                                    pass
    
    def draw(self, screen: pygame.Surface, camera_x: int = 0, camera_y: int = 0):
        """Отрисовывает карту"""
        screen_width, screen_height = screen.get_size()
        
        # Вычисляем видимую область
        start_tile_x = max(0, camera_x // self.tile_size - 1)
        end_tile_x = min(self.width, (camera_x + screen_width) // self.tile_size + 1)
        start_tile_y = max(0, camera_y // self.tile_size - 1)
        end_tile_y = min(self.height, (camera_y + screen_height) // self.tile_size + 1)
        
        for y in range(start_tile_y, end_tile_y):
            for x in range(start_tile_x, end_tile_x):
                screen_x = x * self.tile_size - camera_x
                screen_y = y * self.tile_size - camera_y
                
                if self.map_data[y][x] == 1:  # Пол
                    # Шахматный порядок для пола
                    floor_index = (x + y) % len(self.tile_images["floor"])
                    screen.blit(self.tile_images["floor"][floor_index], (screen_x, screen_y))
                else:  # Стена
                    # Случайный выбор стены
                    wall_index = (x + y * 7) % len(self.tile_images["wall"])
                    screen.blit(self.tile_images["wall"][wall_index], (screen_x, screen_y))
    
    def get_tile_at(self, x: int, y: int) -> int:
        """Возвращает тип тайла в позиции (в пикселях)"""
        tile_x = x // self.tile_size
        tile_y = y // self.tile_size
        
        if 0 <= tile_y < self.height and 0 <= tile_x < self.width:
            return self.map_data[tile_y][tile_x]
        return 0  # Стена за пределами карты
    
    def is_walkable(self, x: int, y: int) -> bool:
        """Проверяет, можно ли ходить по тайлу"""
        return self.get_tile_at(x, y) == 1

