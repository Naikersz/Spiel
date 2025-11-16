"""
Tilemap - генерация подземелья с использованием BSP + случайные комнаты
"""
import pygame
import random
import json
import os
import logging
from typing import List, Tuple, Optional, Dict, Any

# Настройка логирования
logger = logging.getLogger(__name__)


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
    
    def __init__(self, width: int = 100, height: int = 100, tile_size: int = 64):
        """
        Инициализация Tilemap
        
        Args:
            width: Ширина карты в тайлах
            height: Высота карты в тайлах
            tile_size: Размер тайла в пикселях (по умолчанию 64 для изометрических тайлов)
        """
        self.width = width
        self.height = height
        self.tile_size = tile_size  # НЕ МЕНЯТЬ после генерации!
        
        logger.debug(f"Tilemap.__init__: width={width}, height={height}, tile_size={tile_size}")
        
        # Параметры BSP генерации
        self.min_leaf_size = 14
        self.max_depth = 7
        self.void_value = -1
        self.corridor_width = 2  # GUARANTEED: ширина коридора в тайлах (для игрока 64x64)
        
        # Инициализация карты (-1 = пустота, 0 = стена, 1 = пол)
        self.map_data = [[self.void_value for _ in range(width)] for _ in range(height)]
        
        # Загрузка конфигурации тайлов
        self.tiles_config = self._load_tiles_config()
        
        # Загрузка изображений тайлов
        self.tile_images = {}
        self.catacomb_tiles = None  # Все тайлы из catacomb.png
        self.wall_autotile = False  # Автоподбор тайлов стен
        self.wall_indices = []  # Индексы тайлов стен
        self._load_tile_images()
        
        # Генерация карты
        self.rooms = []
        self.corridors = []
        self.bsp_root = None
        
        # Карта индексов тайлов стен (для автоподбора и фильтрации)
        self.wall_index_map = [[-1 for _ in range(width)] for _ in range(height)]  # -1 = нет стены
        
        # Фон для пустоты (темный градиент + шум)
        self.void_background = None
        self._generate_void_background()
        
        # Отладка: счетчик вызовов draw()
        self._draw_call_count = 0
        
        # ГАРАНТИРОВАННАЯ ГЕНЕРАЦИЯ: вызываем generate() в __init__
        self.generate()
        
    def _load_tiles_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию тайлов"""
        config_path = "game/assets/configs/tiles_config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading tiles config: {e}")
        
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
        """Загружает изображения тайлов: dirt3 для пола, wall (боковые стены), wall1 (верх/низ стены), dirtstone для декораций (64x64 тайлы)"""
        # Загружаем тайлы для ортогонального рендеринга
        self._load_orthogonal_tiles()
    
    def _load_orthogonal_tiles(self):
        """Загружает тайлы для ортогонального рендеринга: dirt3 (пол), wall (боковые стены), wall1 (верх/низ стены), dirtstone (декорации)"""
        tile_size = 64  # Фиксированный размер тайла: 64x64
        
        # Загружаем пол только из dirt3.png
        floor_tiles = []
        dirt3_path = "game/assets/tiles/dirt3.png"
        try:
            if os.path.exists(dirt3_path):
                logger.debug(f"Loading floor tileset from: {dirt3_path}")
                dirt3_tileset = pygame.image.load(dirt3_path).convert_alpha()
                tileset_width, tileset_height = dirt3_tileset.get_size()
                
                tiles_x = tileset_width // tile_size
                tiles_y = tileset_height // tile_size
                
                for y in range(tiles_y):
                    for x in range(tiles_x):
                        tile_rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                        if tile_rect.right <= tileset_width and tile_rect.bottom <= tileset_height:
                            tile = dirt3_tileset.subsurface(tile_rect)
                            if tile.get_size() != (tile_size, tile_size):
                                tile = pygame.transform.scale(tile, (tile_size, tile_size))
                            floor_tiles.append(tile)
                
                logger.info(f"Loaded {len(floor_tiles)} tiles from dirt3.png")
            else:
                logger.warning(f"Floor tileset not found: {dirt3_path}")
        except Exception as e:
            logger.error(f"Error loading dirt3 tileset: {e}", exc_info=True)
        
        # Если не загрузили пол, создаем placeholder
        if not floor_tiles:
            placeholder = pygame.Surface((tile_size, tile_size))
            placeholder.fill((101, 67, 33))  # Коричневый
            floor_tiles = [placeholder]
            logger.warning("Using placeholder for floor tiles")
        
        self.tile_images["floor"] = floor_tiles
        logger.info(f"Total floor tiles loaded: {len(floor_tiles)}")
        
        # Загружаем wall.png (боковые стены - лево/право)
        wall_side_tiles = []
        wall_path = "game/assets/tiles/wall.png"
        try:
            if os.path.exists(wall_path):
                logger.debug(f"Loading side wall tileset from: {wall_path}")
                wall_tileset = pygame.image.load(wall_path).convert_alpha()
                tileset_width, tileset_height = wall_tileset.get_size()
                
                tiles_x = tileset_width // tile_size
                tiles_y = tileset_height // tile_size
                
                for y in range(tiles_y):
                    for x in range(tiles_x):
                        tile_rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                        if tile_rect.right <= tileset_width and tile_rect.bottom <= tileset_height:
                            tile = wall_tileset.subsurface(tile_rect)
                            # Убеждаемся, что тайл имеет альфа-канал для прозрачности
                            if not tile.get_flags() & pygame.SRCALPHA:
                                tile = tile.convert_alpha()
                            if tile.get_size() != (tile_size, tile_size):
                                tile = pygame.transform.scale(tile, (tile_size, tile_size))
                            wall_side_tiles.append(tile)
                
                logger.info(f"Loaded {len(wall_side_tiles)} tiles from wall.png (side walls)")
            else:
                logger.warning(f"Side wall tileset not found: {wall_path}")
        except Exception as e:
            logger.error(f"Error loading side wall tileset: {e}", exc_info=True)
        
        # Если не загрузили боковые стены, создаем placeholder
        if not wall_side_tiles:
            placeholder = pygame.Surface((tile_size, tile_size))
            placeholder.fill((80, 80, 80))  # Серый
            wall_side_tiles = [placeholder]
            logger.warning("Using placeholder for side wall tiles")
        
        self.tile_images["wall"] = wall_side_tiles
        logger.info(f"Total side wall tiles loaded: {len(wall_side_tiles)}")
        
        # Загружаем wall1.png (верхние/нижние стены)
        wall_top_bottom_tiles = []
        wall1_path = "game/assets/tiles/wall1.png"
        try:
            if os.path.exists(wall1_path):
                logger.debug(f"Loading top/bottom wall tileset from: {wall1_path}")
                wall1_tileset = pygame.image.load(wall1_path).convert_alpha()
                tileset_width, tileset_height = wall1_tileset.get_size()
                
                tiles_x = tileset_width // tile_size
                tiles_y = tileset_height // tile_size
                
                for y in range(tiles_y):
                    for x in range(tiles_x):
                        tile_rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                        if tile_rect.right <= tileset_width and tile_rect.bottom <= tileset_height:
                            tile = wall1_tileset.subsurface(tile_rect)
                            # Убеждаемся, что тайл имеет альфа-канал для прозрачности
                            if not tile.get_flags() & pygame.SRCALPHA:
                                tile = tile.convert_alpha()
                            if tile.get_size() != (tile_size, tile_size):
                                tile = pygame.transform.scale(tile, (tile_size, tile_size))
                            wall_top_bottom_tiles.append(tile)
                
                logger.info(f"Loaded {len(wall_top_bottom_tiles)} tiles from wall1.png (top/bottom walls)")
            else:
                logger.warning(f"Top/bottom wall tileset not found: {wall1_path}")
        except Exception as e:
            logger.error(f"Error loading top/bottom wall tileset: {e}", exc_info=True)
        
        # Если не загрузили верхние/нижние стены, создаем placeholder
        if not wall_top_bottom_tiles:
            placeholder = pygame.Surface((tile_size, tile_size))
            placeholder.fill((80, 80, 80))  # Серый
            wall_top_bottom_tiles = [placeholder]
            logger.warning("Using placeholder for top/bottom wall tiles")
        
        self.tile_images["wall1"] = wall_top_bottom_tiles
        logger.info(f"Total top/bottom wall tiles loaded: {len(wall_top_bottom_tiles)}")
        
        # Загружаем dirtstone.png как декоративные камушки
        dirtstone_path = "game/assets/tiles/dirtstone.png"
        dirtstone_tiles = []
        try:
            if os.path.exists(dirtstone_path):
                logger.debug(f"Loading dirtstone tileset from: {dirtstone_path}")
                dirtstone_tileset = pygame.image.load(dirtstone_path).convert_alpha()
                tileset_width, tileset_height = dirtstone_tileset.get_size()
                
                tiles_x = tileset_width // tile_size
                tiles_y = tileset_height // tile_size
                
                for y in range(tiles_y):
                    for x in range(tiles_x):
                        tile_rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                        if tile_rect.right <= tileset_width and tile_rect.bottom <= tileset_height:
                            tile = dirtstone_tileset.subsurface(tile_rect)
                            if tile.get_size() != (tile_size, tile_size):
                                tile = pygame.transform.scale(tile, (tile_size, tile_size))
                            dirtstone_tiles.append(tile)
                
                logger.info(f"Loaded {len(dirtstone_tiles)} dirtstone tiles")
            else:
                logger.warning(f"Dirtstone tileset not found: {dirtstone_path}")
        except Exception as e:
            logger.error(f"Error loading dirtstone tileset: {e}", exc_info=True)
        
        self.tile_images["dirtstone"] = dirtstone_tiles
        
        # Отключаем автоподбор стен для ортогонального рендеринга
        self.wall_autotile = False
        self.catacomb_tiles = None
    
    def _create_floor_placeholder(self) -> pygame.Surface:
        """Создает placeholder для пола"""
        placeholder = pygame.Surface((self.tile_size, self.tile_size))
        placeholder.fill((100, 50, 50))  # Коричневый
        return placeholder
    
    def _load_legacy_tile_images(self):
        """Загружает старые изображения тайлов (fallback)"""
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
                    logger.error(f"Error loading floor image {img_path}: {e}")
        
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
                    logger.error(f"Error loading wall image {img_path}: {e}")
        
        # Если изображения не загружены, создаем placeholder
        if not self.tile_images.get("floor"):
            placeholder = pygame.Surface((self.tile_size, self.tile_size))
            placeholder.fill((100, 50, 50))
            self.tile_images["floor"] = [placeholder]
        
        if not self.tile_images.get("wall"):
            placeholder = pygame.Surface((self.tile_size, self.tile_size))
            placeholder.fill((80, 80, 80))
            self.tile_images["wall"] = [placeholder]
        
        self.wall_autotile = False
        self.catacomb_tiles = None
    
    def generate(self):
        """Генерирует карту подземелья с BFS flood fill и прямыми коридорами"""
        min_rooms = 12
        max_attempts = 20  # Больше попыток для надежности
        
        logger.info(f"Generating map: {self.width}x{self.height} tiles, tile_size={self.tile_size}")
        
        for attempt in range(max_attempts):
            # Сброс карты
            self._reset_map()
            self.rooms = []
            self.corridors = []
            
            # 1. Только комнаты BSP (без коридоров по дереву)
            self.bsp_root = self._create_bsp_tree(0, 0, self.width, self.height, depth=0, max_depth=6)
            self._create_rooms(self.bsp_root)
            
            # Отладка: проверка генерации
            logger.debug(f"Attempt {attempt + 1}: Generated {len(self.rooms)} rooms")
            if len(self.rooms) > 0:
                # Проверяем map_data в центре карты
                center_x, center_y = self.width // 2, self.height // 2
                center_tile = self.map_data[center_y][center_x] if (center_y < self.height and center_x < self.width) else -1
                logger.debug(f"  Center tile ({center_x},{center_y}): {center_tile} (should be 1 for floor or 0 for wall)")
            
            # Проверяем количество комнат
            if len(self.rooms) < min_rooms:
                logger.debug(f"Attempt {attempt + 1}: Only {len(self.rooms)} rooms, regenerating...")
                continue
            
            # 2. Выбираем стартовую комнату (самая большая)
            self.start_room = max(self.rooms, key=lambda r: r[2] * r[3])
            start_pos = (
                self.start_room[0] + self.start_room[2] // 2,
                self.start_room[1] + self.start_room[3] // 2
            )
            
            # 3. Главный цикл: соединяем недостижимые комнаты
            success = False
            for corridor_attempt in range(50):  # Максимум 50 коридоров
                # BFS flood fill: все достижимые тайлы
                reachable_tiles = self._get_all_reachable(start_pos)
                
                # Если все комнаты достижимы — УСПЕХ
                if self._all_rooms_reachable(reachable_tiles):
                    # ВСЕГДА вызываем _create_walls() перед break (но не здесь, а после выхода из цикла)
                    logger.debug(f"SUCCESS: All rooms reachable (attempt {attempt + 1}, {corridor_attempt + 1} corridors)")
                    success = True
                    break
                
                # 4. Находим первую недостижимую комнату
                unreachable_room = self._find_first_unreachable_room(reachable_tiles)
                if not unreachable_room:
                    break
                
                # Центр недостижимой комнаты
                unreachable_center = (
                    unreachable_room[0] + unreachable_room[2] // 2,
                    unreachable_room[1] + unreachable_room[3] // 2
                )
                
                # 5. Ближайший достижимый тайл
                # Захватываем unreachable_center в замыкание для lambda
                unreachable_center_fixed = unreachable_center
                nearest_reachable = min(
                    reachable_tiles,
                    key=lambda p, uc=unreachable_center_fixed: abs(p[0] - uc[0]) + abs(p[1] - uc[1])
                )
                
                # 6. ПРЯМОЙ коридор (L-образный, ширина=2)
                self._carve_direct_corridor(nearest_reachable, unreachable_center)
            
            if success:
                # УСПЕХ: ВСЕГДА вызываем _create_walls() перед return
                logger.info(f"SUCCESS: Generated dungeon with {len(self.rooms)} rooms")
                logger.debug("  Calling _create_walls() (SUCCESS path)...")
                self._create_walls()
                # Отладка: финальная проверка
                floor_count = sum(1 for y in range(self.height) for x in range(self.width) if self.map_data[y][x] == 1)
                wall_count = sum(1 for y in range(self.height) for x in range(self.width) if self.map_data[y][x] == 0)
                void_count = self.width * self.height - floor_count - wall_count
                logger.debug(f"  Final map data: floors={floor_count}, walls={wall_count}, void={void_count}")
                return
        
        # Если не удалось после всех попыток - FALLBACK
        logger.warning(f"Failed to generate connected dungeon after {max_attempts} attempts")
        logger.debug("  Using fallback: connecting rooms and creating walls...")
        # Используем то, что есть - ВСЕГДА вызываем _create_walls()
        if self.bsp_root:
            self._connect_rooms(self.bsp_root)
        logger.debug("  Calling _create_walls() (FALLBACK path)...")
        self._create_walls()
        # Отладка: финальная проверка (fallback)
        floor_count = sum(1 for y in range(self.height) for x in range(self.width) if self.map_data[y][x] == 1)
        wall_count = sum(1 for y in range(self.height) for x in range(self.width) if self.map_data[y][x] == 0)
        void_count = self.width * self.height - floor_count - wall_count
        logger.debug(f"  Final map data (fallback): floors={floor_count}, walls={wall_count}, void={void_count}")
    
    def _reset_map(self):
        """Сбрасывает карту в начальное состояние"""
        self.map_data = [[self.void_value for _ in range(self.width)] for _ in range(self.height)]
    
    def _generate_void_background(self):
        """Генерирует фон для пустоты (темный градиент + шум) - оптимизированная версия"""
        # Создаем поверхность для фона (1024x1024 для бесконечного эффекта)
        bg_size = 1024
        self.void_background = pygame.Surface((bg_size, bg_size))
        
        # Темный базовый цвет (почти черный с легким синим оттенком)
        base_color = (3, 3, 6)
        self.void_background.fill(base_color)
        
        # Добавляем градиент используя массивы numpy если доступно, иначе простой подход
        try:
            import numpy as np
            # Создаем градиент быстрее с numpy
            arr = pygame.surfarray.array3d(self.void_background)
            center = bg_size // 2
            y_coords, x_coords = np.ogrid[:bg_size, :bg_size]
            dist_sq = (x_coords - center) ** 2 + (y_coords - center) ** 2
            max_dist_sq = (bg_size * 0.707) ** 2
            gradient = np.clip(dist_sq / max_dist_sq, 0, 1)
            
            # Применяем градиент
            arr[:, :, 0] = np.clip(2 + gradient * 3, 0, 255)
            arr[:, :, 1] = np.clip(2 + gradient * 3, 0, 255)
            arr[:, :, 2] = np.clip(4 + gradient * 4, 0, 255)
            
            # Добавляем шум
            noise = np.random.randint(-2, 3, (bg_size, bg_size, 3))
            arr = np.clip(arr + noise, 0, 255)
            
            pygame.surfarray.blit_array(self.void_background, arr)
        except ImportError:
            # Fallback: простая оптимизированная генерация без numpy
            # Используем меньший шаг для ускорения
            step = 4
            for y in range(0, bg_size, step):
                for x in range(0, bg_size, step):
                    # Расстояние от центра
                    dx = x - bg_size // 2
                    dy = y - bg_size // 2
                    dist = (dx * dx + dy * dy) ** 0.5
                    max_dist = bg_size * 0.707
                    
                    # Интерполяция цвета
                    t = min(1.0, dist / max_dist)
                    r = int(2 + t * 3)
                    g = int(2 + t * 3)
                    b = int(4 + t * 4)
                    
                    # Добавляем легкий шум
                    noise = random.randint(-2, 3)
                    r = max(0, min(255, r + noise))
                    g = max(0, min(255, g + noise))
                    b = max(0, min(255, b + noise))
                    
                    # Заполняем блок step x step
                    color = (r, g, b)
                    for sy in range(step):
                        for sx in range(step):
                            if x + sx < bg_size and y + sy < bg_size:
                                self.void_background.set_at((x + sx, y + sy), color)
        
        # Добавляем небольшой случайный шум для текстуры (быстрее)
        noise_count = bg_size * bg_size // 10000  # 0.01% пикселей
        for _ in range(noise_count):
            x = random.randint(0, bg_size - 1)
            y = random.randint(0, bg_size - 1)
            current_color = self.void_background.get_at((x, y))
            noise = random.randint(-3, 4)
            new_color = (
                max(0, min(15, current_color[0] + noise)),
                max(0, min(15, current_color[1] + noise)),
                max(0, min(20, current_color[2] + noise))
            )
            self.void_background.set_at((x, y), new_color)
    
    def _create_bsp_tree(self, x: int, y: int, width: int, height: int, depth: int, max_depth: int) -> Optional[BSPNode]:
        """Создает BSP дерево с равномерным разделением 40-60%"""
        # Проверяем минимальный размер листа
        if depth >= max_depth or width < self.min_leaf_size or height < self.min_leaf_size:
            return None
        
        node = BSPNode(x, y, width, height)
        
        # Случайный выбор оси разделения (предпочтительно по большей стороне)
        if width > height:
            split_horizontal = False  # Вертикальное разделение
        elif height > width:
            split_horizontal = True   # Горизонтальное разделение
        else:
            split_horizontal = random.random() < 0.5
        
        if split_horizontal:
            # Горизонтальное разделение (40-60%)
            if height < self.min_leaf_size * 2:
                return None
            min_split = int(height * 0.4)
            max_split = int(height * 0.6)
            split_pos = random.randint(min_split, max_split)
            node.left = self._create_bsp_tree(x, y, width, split_pos, depth + 1, max_depth)
            node.right = self._create_bsp_tree(x, y + split_pos, width, height - split_pos, depth + 1, max_depth)
        else:
            # Вертикальное разделение (40-60%)
            if width < self.min_leaf_size * 2:
                return None
            min_split = int(width * 0.4)
            max_split = int(width * 0.6)
            split_pos = random.randint(min_split, max_split)
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
        """Соединяет комнаты через BSP-дерево с гарантированной связностью"""
        self._connect_subtrees(node)
    
    def _connect_subtrees(self, node: Optional[BSPNode]):
        """Рекурсивно соединяет поддеревья BSP с гарантированной связностью"""
        if node is None or (node.left is None and node.right is None):
            return
        
        # Рекурсивно соединяем дочерние узлы
        self._connect_subtrees(node.left)
        self._connect_subtrees(node.right)
        
        # Получаем случайные комнаты из каждого поддерева
        room_left = self._get_random_leaf_room(node.left)
        room_right = self._get_random_leaf_room(node.right)
        
        if room_left and room_right:
            # Гарантированно соединяем две комнаты
            self._connect_two_rooms_guaranteed(room_left, room_right, node)
    
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
    
    def _get_random_leaf_room(self, node: Optional[BSPNode]) -> Optional[Tuple[int, int, int, int]]:
        """Получает случайную комнату из листьев поддерева"""
        if node is None:
            return None
        
        # Собираем все комнаты из поддерева
        all_rooms = []
        self._collect_rooms_from_node(node, all_rooms)
        
        if all_rooms:
            return random.choice(all_rooms)
        return None
    
    def _collect_rooms_from_node(self, node: Optional[BSPNode], rooms_list: List[Tuple[int, int, int, int]]):
        """Собирает все комнаты из поддерева в список"""
        if node is None:
            return
        
        if node.room:
            rooms_list.append(node.room)
        
        self._collect_rooms_from_node(node.left, rooms_list)
        self._collect_rooms_from_node(node.right, rooms_list)
    
    def _connect_two_rooms_guaranteed(self, room1: Tuple[int, int, int, int], room2: Tuple[int, int, int, int], node: BSPNode):
        """Гарантированно соединяет две комнаты через точки на полу"""
        r1x, r1y, r1w, r1h = room1
        r2x, r2y, r2w, r2h = room2
        
        # Выбираем точки на полу обеих комнат (гарантированно внутри пола)
        # Используем внутренние точки, не края, с проверкой границ
        r1x_max = max(r1x + 1, r1x + r1w - 2)
        r1y_max = max(r1y + 1, r1y + r1h - 2)
        r2x_max = max(r2x + 1, r2x + r2w - 2)
        r2y_max = max(r2y + 1, r2y + r2h - 2)
        
        if r1x_max <= r1x or r1y_max <= r1y or r2x_max <= r2x or r2y_max <= r2y:
            # Комната слишком мала
            return
        
        exit1_x = random.randint(r1x + 1, r1x_max)
        exit1_y = random.randint(r1y + 1, r1y_max)
        
        exit2_x = random.randint(r2x + 1, r2x_max)
        exit2_y = random.randint(r2y + 1, r2y_max)
        
        # Проверяем границы карты
        if (exit1_x >= self.width or exit1_y >= self.height or 
            exit2_x >= self.width or exit2_y >= self.height or
            exit1_x < 0 or exit1_y < 0 or exit2_x < 0 or exit2_y < 0):
            return
        
        # Проверяем, что точки действительно на полу (map_data == 1)
        # Но т.к. мы только что создали комнаты, они должны быть на полу
        # Эта проверка для безопасности
        if (self.map_data[exit1_y][exit1_x] != 1 or 
            self.map_data[exit2_y][exit2_x] != 1):
            # Попытка найти альтернативные точки на полу
            exit1_found = False
            exit2_found = False
            
            # Ищем точки на полу в первой комнате
            for ry in range(r1y + 1, min(r1y + r1h - 1, self.height - 1)):
                for rx in range(r1x + 1, min(r1x + r1w - 1, self.width - 1)):
                    if self.map_data[ry][rx] == 1:
                        exit1_x, exit1_y = rx, ry
                        exit1_found = True
                        break
                if exit1_found:
                    break
            
            # Ищем точки на полу во второй комнате
            for ry in range(r2y + 1, min(r2y + r2h - 1, self.height - 1)):
                for rx in range(r2x + 1, min(r2x + r2w - 1, self.width - 1)):
                    if self.map_data[ry][rx] == 1:
                        exit2_x, exit2_y = rx, ry
                        exit2_found = True
                        break
                if exit2_found:
                    break
            
            if not exit1_found or not exit2_found:
                # Не смогли найти точки на полу - пропускаем соединение
                return
        
        # Определяем направление разделения BSP
        split_horizontal = node.left.y + node.left.height <= node.right.y
        
        # ГАРАНТИРОВАННАЯ ширина коридора = 2 тайла (64px) для игрока 64x64
        corridor_width = self.corridor_width
        
        if split_horizontal:
            # Горизонтальное разделение - соединяем горизонтально с изгибом
            # Вычисляем линию раздела
            split_y = node.left.y + node.left.height
            
            # L-образный коридор: горизонтально до линии раздела, затем к второй комнате
            mid_x = (exit1_x + exit2_x) // 2
            
            # Горизонтальный сегмент от первой комнаты
            self._create_corridor_horizontal(exit1_x, exit1_y, mid_x, exit1_y, corridor_width)
            # Вертикальный сегмент по линии раздела
            start_vy = min(exit1_y, split_y)
            end_vy = max(exit2_y, split_y)
            self._create_corridor_vertical(mid_x, start_vy, mid_x, end_vy, corridor_width)
            # Горизонтальный сегмент ко второй комнате
            self._create_corridor_horizontal(mid_x, exit2_y, exit2_x, exit2_y, corridor_width)
        else:
            # Вертикальное разделение - соединяем вертикально с изгибом
            # Вычисляем линию раздела
            split_x = node.left.x + node.left.width
            
            # L-образный коридор: вертикально до линии раздела, затем ко второй комнате
            mid_y = (exit1_y + exit2_y) // 2
            
            # Вертикальный сегмент от первой комнаты
            self._create_corridor_vertical(exit1_x, exit1_y, exit1_x, mid_y, corridor_width)
            # Горизонтальный сегмент по линии раздела
            start_hx = min(exit1_x, split_x)
            end_hx = max(exit2_x, split_x)
            self._create_corridor_horizontal(start_hx, mid_y, end_hx, mid_y, corridor_width)
            # Вертикальный сегмент ко второй комнате
            self._create_corridor_vertical(exit2_x, mid_y, exit2_x, exit2_y, corridor_width)
    
    def _set_floor_tile(self, x: int, y: int):
        """Устанавливает тайл как пол (гарантирует проходимость)"""
        if 0 <= y < self.height and 0 <= x < self.width:
            # Если это void (-1) или стена (0), делаем пол (1)
            if self.map_data[y][x] != 1:
                self.map_data[y][x] = 1
    
    def _create_corridor_horizontal(self, x1: int, y: int, x2: int, y2: int, width: int):
        """
        Создает горизонтальный коридор с гарантией что это пол
        
        Args:
            x1, x2: X координаты в пикселях
            y: Y координата центра коридора в пикселях
            y2: Не используется (для совместимости)
            width: Ширина коридора в тайлах (гарантированно 2)
        """
        # Конвертируем координаты в тайлы
        start_x_tile = min(x1, x2) // self.tile_size
        end_x_tile = max(x1, x2) // self.tile_size
        center_y_tile = y // self.tile_size
        
        # Вычисляем начальную позицию коридора по Y (в тайлах)
        start_y_tile = center_y_tile - width // 2
        
        # Создаем коридор шириной width тайлов
        for tile_y in range(start_y_tile, start_y_tile + width):
            for tile_x in range(start_x_tile, end_x_tile + 1):
                if 0 <= tile_y < self.height and 0 <= tile_x < self.width:
                    self._set_floor_tile(tile_x, tile_y)
    
    def _create_corridor_vertical(self, x: int, y1: int, x2: int, y2: int, width: int):
        """
        Создает вертикальный коридор с гарантией что это пол
        
        Args:
            x: X координата центра коридора в пикселях
            y1, y2: Y координаты в пикселях
            x2: Не используется (для совместимости)
            width: Ширина коридора в тайлах (гарантированно 2)
        """
        # Конвертируем координаты в тайлы
        start_y_tile = min(y1, y2) // self.tile_size
        end_y_tile = max(y1, y2) // self.tile_size
        center_x_tile = x // self.tile_size
        
        # Вычисляем начальную позицию коридора по X (в тайлах)
        start_x_tile = center_x_tile - width // 2
        
        # Создаем коридор шириной width тайлов
        for tile_y in range(start_y_tile, end_y_tile + 1):
            for tile_x in range(start_x_tile, start_x_tile + width):
                if 0 <= tile_y < self.height and 0 <= tile_x < self.width:
                    self._set_floor_tile(tile_x, tile_y)
    
    def _get_all_reachable(self, start_pos: Tuple[int, int]) -> set:
        """
        BFS: все достижимые тайлы пола от стартовой позиции
        
        Args:
            start_pos: Стартовая позиция (x, y) в тайлах
            
        Returns:
            set: Множество достижимых тайлов (x, y) в тайлах
        """
        from collections import deque
        
        visited = set()
        queue = deque([start_pos])
        visited.add(start_pos)
        
        while queue:
            x, y = queue.popleft()
            
            # Проверяем соседей (только ортогональные)
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if (0 <= ny < self.height and 0 <= nx < self.width and
                    (nx, ny) not in visited and
                    self.map_data[ny][nx] == 1):  # Пол
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        
        return visited
    
    def _all_rooms_reachable(self, reachable_tiles: set) -> bool:
        """
        Проверяет, все ли комнаты пересекаются с достижимыми тайлами
        
        Args:
            reachable_tiles: Множество достижимых тайлов (x, y) в тайлах
            
        Returns:
            bool: True если все комнаты достижимы
        """
        for room in self.rooms:
            rx, ry, rw, rh = room
            # Проверяем, есть ли хотя бы один тайл комнаты в reachable_tiles
            room_reachable = False
            
            for ry_tile in range(ry, ry + rh):
                for rx_tile in range(rx, rx + rw):
                    if (rx_tile, ry_tile) in reachable_tiles:
                        room_reachable = True
                        break
                if room_reachable:
                    break
            
            if not room_reachable:
                return False
        
        return True
    
    def _find_first_unreachable_room(self, reachable_tiles: set) -> Optional[Tuple[int, int, int, int]]:
        """
        Находит первую недостижимую комнату
        
        Args:
            reachable_tiles: Множество достижимых тайлов (x, y) в тайлах
            
        Returns:
            Tuple или None: Первая недостижимая комната или None
        """
        for room in self.rooms:
            rx, ry, rw, rh = room
            # Проверяем, есть ли хотя бы один тайл комнаты в reachable_tiles
            room_reachable = any(
                (rx + i, ry + j) in reachable_tiles
                for i in range(rw) for j in range(rh)
            )
            
            if not room_reachable:
                return room
        
        return None
    
    def _get_wall_tile_index(self, x: int, y: int) -> int:
        """
        Определяет индекс тайла стены на основе 8 соседей (автоподбор с битовой маской)
        
        Использует классический алгоритм автоподбора: проверяет 8 соседей (N, NE, E, SE, S, SW, W, NW)
        и выбирает тайл стены по битовой маске паттерна соседей.
        
        Args:
            x: X координата тайла в тайлах
            y: Y координата тайла в тайлах
            
        Returns:
            int: Индекс тайла стены (0-19) для catacomb.png
        """
        if not self.wall_autotile or not self.wall_indices:
            # Если автоподбор выключен, возвращаем случайный тайл
            return (x + y * 7) % len(self.wall_indices) if self.wall_indices else 0
        
        # Проверяем соседей (8 направлений: N, NE, E, SE, S, SW, W, NW)
        # True = есть сосед-пол (1), False = нет (стена/пустота)
        check_neighbor = lambda nx, ny: (
            0 <= ny < self.height and 0 <= nx < self.width and 
            self.map_data[ny][nx] == 1  # Сосед - пол
        )
        
        # Ортогональные соседи (4 направления)
        north = check_neighbor(x, y - 1)     # N
        east = check_neighbor(x + 1, y)      # E
        south = check_neighbor(x, y + 1)     # S
        west = check_neighbor(x - 1, y)      # W
        
        # Диагональные соседи (4 направления)
        northeast = check_neighbor(x + 1, y - 1)  # NE
        southeast = check_neighbor(x + 1, y + 1)  # SE
        southwest = check_neighbor(x - 1, y + 1)  # SW
        northwest = check_neighbor(x - 1, y - 1)  # NW
        
        # Вычисляем битовую маску паттерна (8-битное число: N NE E SE S SW W NW)
        # 0 = нет пола (стена/пустота), 1 = есть пол
        pattern = (
            (north << 7) | (northeast << 6) | (east << 5) | (southeast << 4) |
            (south << 3) | (southwest << 2) | (west << 1) | northwest
        )
        
        # Маппинг паттернов на индексы тайлов стены
        # Используем wall_indices для выбора тайла
        if self.wall_indices:
            wall_index = pattern % len(self.wall_indices)
            return self.wall_indices[wall_index]
        
        # Fallback: возвращаем 0 если нет индексов
        return 0
    
    def _carve_direct_corridor(self, p1: Tuple[int, int], p2: Tuple[int, int]):
        """
        Создает ПРЯМОЙ L-образный коридор между двумя точками (в тайлах)
        
        Args:
            p1: Первая точка (x, y) в тайлах
            p2: Вторая точка (x, y) в тайлах
        """
        x1, y1 = p1
        x2, y2 = p2
        
        # L-образный коридор: сначала горизонтально, затем вертикально
        # Горизонтальная часть
        for y_offset in range(-1, 2):  # Ширина 2 тайла (от -1 до +1)
            y = y1 + y_offset
            for x in range(min(x1, x2), max(x1, x2) + 1):
                if 0 <= y < self.height and 0 <= x < self.width:
                    self._set_floor_tile(x, y)
        
        # Вертикальная часть
        for x_offset in range(-1, 2):  # Ширина 2 тайла (от -1 до +1)
            x = x2 + x_offset
            for y in range(min(y1, y2), max(y1, y2) + 1):
                if 0 <= x < self.width and 0 <= y < self.height:
                    self._set_floor_tile(x, y)
    
    def _create_walls(self):
        """
        ВСЕГДА создает стены вокруг пола (в соседних пустых тайлах).
        Заполняет все тайлы со значением -1 (пустота), которые соседствуют с тайлами 1 (пол).
        Также заполняет wall_index_map для каждого тайла стены.
        """
        logger.debug("_create_walls(): Starting...")
        
        # Подсчет перед созданием стен
        floor_count_before = sum(1 for y in range(self.height) for x in range(self.width) if self.map_data[y][x] == 1)
        wall_count_before = sum(1 for y in range(self.height) for x in range(self.width) if self.map_data[y][x] == 0)
        logger.debug(f"  Before: floors={floor_count_before}, walls={wall_count_before}")
        
        # Создаем временную копию для проверки (избегаем изменения во время итерации)
        walls_to_add = []
        
        # Проходим по всем тайлам карты
        for y in range(self.height):
            for x in range(self.width):
                if self.map_data[y][x] == 1:  # Пол
                    # Проверяем всех соседей (включая диагонали)
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue  # Пропускаем сам тайл
                            nx, ny = x + dx, y + dy
                            # Проверяем границы
                            if 0 <= ny < self.height and 0 <= nx < self.width:
                                # Если сосед - пустота (-1), делаем его стеной (0)
                                if self.map_data[ny][nx] == self.void_value:  # -1 = пустота
                                    walls_to_add.append((nx, ny))
        
        # Добавляем стены (ВСЕГДА заполняем 0 вокруг 1)
        for x, y in walls_to_add:
            self.map_data[y][x] = 0  # Стена
        
        # Заполняем wall_index_map для всех тайлов стен (включая новые и существующие)
        if self.wall_autotile and self.wall_indices:
            for y in range(self.height):
                for x in range(self.width):
                    if self.map_data[y][x] == 0:  # Стена
                        # Вычисляем индекс тайла стены с помощью автоподбора
                        wall_index = self._get_wall_tile_index(x, y)
                        self.wall_index_map[y][x] = wall_index
                    else:
                        self.wall_index_map[y][x] = -1  # Нет стены
        
        # Подсчет после создания стен
        walls_added = len(walls_to_add)
        floor_count_after = sum(1 for y in range(self.height) for x in range(self.width) if self.map_data[y][x] == 1)
        wall_count_after = sum(1 for y in range(self.height) for x in range(self.width) if self.map_data[y][x] == 0)
        logger.debug(f"  After: added {walls_added} walls, floors={floor_count_after}, walls={wall_count_after}")
    
    def draw(self, screen: pygame.Surface, camera_x: int = 0, camera_y: int = 0, camera_tile: Optional[Tuple[int, int]] = None):
        """
        Рисует тайлы на экран с ортогональной проекцией.
        
        Args:
            screen: pygame.Surface для отрисовки
            camera_x: Позиция камеры по X (в пикселях)
            camera_y: Позиция камеры по Y (в пикселях)
            camera_tile: Не используется (для обратной совместимости)
        """
        self._draw_call_count += 1
        screen_width, screen_height = screen.get_size()
        
        # Отладка: проверка map_data перед отрисовкой (только при первых вызовах)
        if self._draw_call_count <= 3:
            floor_count = sum(1 for y in range(self.height) for x in range(self.width) if self.map_data[y][x] == 1)
            wall_count = sum(1 for y in range(self.height) for x in range(self.width) if self.map_data[y][x] == 0)
            logger.debug(f"draw(): map_data stats: floors={floor_count}, walls={wall_count}, total_tiles={self.width * self.height}")
            if floor_count == 0 and wall_count == 0:
                logger.warning("No floors or walls in map_data!")
        
        # Отрисовываем фон пустоты (бесконечный темный градиент)
        if self.void_background:
            bg_size = self.void_background.get_size()[0]
            bg_offset_x = -(camera_x // bg_size) * bg_size - (camera_x % bg_size)
            bg_offset_y = -(camera_y // bg_size) * bg_size - (camera_y % bg_size)
            
            for by in range(-1, screen_height // bg_size + 2):
                for bx in range(-1, screen_width // bg_size + 2):
                    screen_x = bg_offset_x + bx * bg_size
                    screen_y = bg_offset_y + by * bg_size
                    screen.blit(self.void_background, (screen_x, screen_y))
        
        # ОРТОГОНАЛЬНАЯ ПРОЕКЦИЯ: простой grid-based рендеринг
        tile_size = self.tile_size  # 64x64
        
        # Вычисляем видимый диапазон тайлов для оптимизации
        start_x = max(0, camera_x // tile_size - 1)
        end_x = min(self.width, (camera_x + screen_width) // tile_size + 2)
        start_y = max(0, camera_y // tile_size - 1)
        end_y = min(self.height, (camera_y + screen_height) // tile_size + 2)
        
        # Отладка (только при первых вызовах)
        if self._draw_call_count <= 3:
            logger.debug(f"draw(): camera=({camera_x},{camera_y}), visible_range=({start_x},{start_y}) to ({end_x},{end_y})")
        
        drawn_tiles = 0
        blit_errors = 0
        
        # Проходим только по видимым тайлам
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile_value = self.map_data[y][x]
                
                # Игнорируем пустоту
                if tile_value == self.void_value:  # -1 = пустота
                    continue
                
                # ОРТОГОНАЛЬНАЯ ПРОЕКЦИЯ: screen_x = x * 64 - camera_x, screen_y = y * 64 - camera_y
                screen_x = x * tile_size - camera_x
                screen_y = y * tile_size - camera_y
                
                # Проверяем, попадает ли тайл на экран
                if (screen_x + tile_size < 0 or screen_x > screen_width or
                    screen_y + tile_size < 0 or screen_y > screen_height):
                    continue  # Тайл полностью вне экрана
                
                try:
                    if tile_value == 1:  # Пол
                        # Выбираем случайный тайл пола из доступных
                        floor_tiles = self.tile_images.get("floor", [])
                        if floor_tiles:
                            # Используем координаты для псевдослучайного выбора (для разнообразия)
                            tile_index = (x + y * 7) % len(floor_tiles)
                            tile_to_blit = floor_tiles[tile_index]
                        else:
                            tile_to_blit = None
                        
                        # Проверка валидности тайла и отрисовка
                        if tile_to_blit is not None and tile_to_blit.get_size() == (tile_size, tile_size):
                            screen.blit(tile_to_blit, (screen_x, screen_y))
                            drawn_tiles += 1
                        else:
                            # Fallback: коричневый placeholder для пола
                            placeholder = pygame.Surface((tile_size, tile_size))
                            placeholder.fill((101, 67, 33))  # Коричневый
                            screen.blit(placeholder, (screen_x, screen_y))
                            drawn_tiles += 1
                        
                        # Рисуем камушки dirtstone поверх пола (случайно, ~15% вероятность)
                        dirtstone_tiles = self.tile_images.get("dirtstone", [])
                        if dirtstone_tiles:
                            # Псевдослучайная вероятность на основе координат
                            stone_chance = (x * 13 + y * 17) % 100
                            if stone_chance < 15:  # 15% вероятность камушка
                                stone_index = (x + y * 19) % len(dirtstone_tiles)
                                stone_tile = dirtstone_tiles[stone_index]
                                if stone_tile is not None and stone_tile.get_size() == (tile_size, tile_size):
                                    screen.blit(stone_tile, (screen_x, screen_y))
                            
                    elif tile_value == 0:  # Стена
                        # Определяем позицию стены относительно пола для правильного выбора тайлсета
                        # Боковая стена (wall.png): вертикальная стена, пол находится слева или справа
                        # Верх/низ стена (wall1.png): горизонтальная стена, пол находится сверху или снизу
                        
                        # Проверяем соседей: где находится пол относительно этой стены
                        # Боковая стена (wall.png): пол слева или справа (вертикальная стена)
                        # Верх/низ стена (wall1.png): пол сверху или снизу (горизонтальная стена)
                        has_floor_left = (x > 0 and self.map_data[y][x - 1] == 1)
                        has_floor_right = (x < self.width - 1 and self.map_data[y][x + 1] == 1)
                        has_floor_top = (y > 0 and self.map_data[y - 1][x] == 1)
                        has_floor_bottom = (y < self.height - 1 and self.map_data[y + 1][x] == 1)
                        
                        # Определяем тип стены по расположению пола:
                        # Если пол слева или справа → вертикальная стена (боковая) → wall.png
                        # Если пол сверху или снизу → горизонтальная стена (верх/низ) → wall1.png
                        # Приоритет: если пол есть и горизонтально, и вертикально, используем боковую стену
                        is_vertical_wall = (has_floor_left or has_floor_right)
                        
                        # Если нет пола ни с одной стороны, используем боковую стену по умолчанию
                        if not (has_floor_left or has_floor_right or has_floor_top or has_floor_bottom):
                            is_vertical_wall = True
                        
                        # Выбираем правильный тайлсет
                        if is_vertical_wall:
                            # Боковая стена (вертикальная) - пол слева или справа - используем wall.png
                            wall_tiles = self.tile_images.get("wall", [])
                        else:
                            # Верх/низ стена (горизонтальная) - пол сверху или снизу - используем wall1.png
                            wall_tiles = self.tile_images.get("wall1", [])
                        
                        if wall_tiles:
                            # Используем координаты для псевдослучайного выбора (для разнообразия)
                            tile_index = (x + y * 11) % len(wall_tiles)
                            tile_to_blit = wall_tiles[tile_index]
                        else:
                            tile_to_blit = None
                        
                        # Проверка валидности тайла и отрисовка
                        if tile_to_blit is not None and tile_to_blit.get_size() == (tile_size, tile_size):
                            screen.blit(tile_to_blit, (screen_x, screen_y))
                            drawn_tiles += 1
                        else:
                            # Fallback: серый placeholder для стены
                            placeholder = pygame.Surface((tile_size, tile_size))
                            placeholder.fill((80, 80, 80))  # Серый
                            screen.blit(placeholder, (screen_x, screen_y))
                            drawn_tiles += 1
                except Exception as blit_err:
                    blit_errors += 1
                    if blit_errors <= 5:  # Показываем только первые 5 ошибок
                        logger.error(f"ERROR drawing tile at map=({x},{y}), screen=({screen_x},{screen_y}): {blit_err}")
        
        # Отладка: финальная статистика
        if self._draw_call_count <= 3:
            logger.debug(f"draw(): Drawn {drawn_tiles} tiles, errors={blit_errors}, camera=({camera_x},{camera_y})")
            if drawn_tiles == 0:
                floor_count = sum(1 for y in range(self.height) for x in range(self.width) if self.map_data[y][x] == 1)
                wall_count = sum(1 for y in range(self.height) for x in range(self.width) if self.map_data[y][x] == 0)
                logger.error(f"0 tiles drawn! map_data: floors={floor_count}, walls={wall_count}")
                logger.debug("Filling screen with brown fallback")
                screen.fill((101, 67, 33))  # Коричневый fallback
    
    def get_tile_at(self, px: int, py: int) -> int:
        """
        Возвращает тип тайла в позиции (в пикселях)
        
        Для ортогональной проекции: преобразует мировые координаты в координаты тайлов.
        
        Args:
            px: X координата в пикселях (мировые координаты)
            py: Y координата в пикселях (мировые координаты)
            
        Returns:
            int: Тип тайла (-1 = void, 0 = стена, 1 = пол)
        """
        # Прямое преобразование мировых координат в координаты тайлов
        # Для ортогональной проекции используем простое деление (тайлы 64x64)
        tile_x = px // self.tile_size
        tile_y = py // self.tile_size
        
        if 0 <= tile_y < self.height and 0 <= tile_x < self.width:
            return self.map_data[tile_y][tile_x]
        return self.void_value  # Пустота за пределами карты
    
    def get_world_pos(self, x_tile: int, y_tile: int) -> Tuple[int, int]:
        """
        Преобразует координаты тайла в мировые координаты (пиксели).
        
        Для отладки и позиционирования объектов на карте.
        
        Args:
            x_tile: X координата тайла
            y_tile: Y координата тайла
            
        Returns:
            Tuple[int, int]: (world_x, world_y) в пикселях
        """
        # Мировые координаты = координаты тайла * размер тайла
        world_x = x_tile * self.tile_size
        world_y = y_tile * self.tile_size
        return (world_x, world_y)
    
    def is_walkable(self, px: int, py: int) -> bool:
        """
        Проверяет, можно ли ходить по тайлу в позиции.
        Использует get_tile_at() для унификации логики.
        
        Args:
            px: X координата в пикселях (мировые координаты)
            py: Y координата в пикселях (мировые координаты)
            
        Returns:
            bool: True если тайл проходим (пол)
        """
        tile_value = self.get_tile_at(px, py)
        # Для ортогональной проекции: 1 = пол (проходим), 0 = стена (непроходима)
        return tile_value == 1
    
    def is_walkable_rect(self, x: int, y: int, width: int, height: int) -> bool:
        """
        Проверяет, можно ли ходить по прямоугольной области (для спрайтов).
        Использует get_tile_at() для унификации логики.
        
        Для игрока 64x64: проверяет центр спрайта (коллизия по центру).
        Игрок считается занимающим 1 тайл (центр спрайта).
        
        Args:
            x: X координата левого верхнего угла в пикселях (мировые координаты)
            y: Y координата левого верхнего угла в пикселях (мировые координаты)
            width: Ширина спрайта в пикселях (64)
            height: Высота спрайта в пикселях (64)
            
        Returns:
            bool: True если центр спрайта на проходимом тайле
        """
        # Игрок = 1 тайл (центр спрайта)
        center_x = x + width // 2
        center_y = y + height // 2
        
        # Используем get_tile_at() для унификации логики
        return self.is_walkable(center_x, center_y)
    
    def check_collision(self, rect: pygame.Rect) -> bool:
        """
        Проверяет коллизию прямоугольника (персонажа) с непроходимыми тайлами карты.
        Использует ортогональную AABB коллизию.
        
        Берет тайлы вокруг персонажа и проверяет пересечение с непроходимыми стенами.
        Стены (tile_value == 0) блокируют движение, пол (tile_value == 1) проходим.
        
        Args:
            rect: pygame.Rect персонажа (мировые координаты)
            
        Returns:
            bool: True если есть коллизия с непроходимой стеной
        """
        # Берем тайлы вокруг персонажа
        min_x = max(0, rect.left // self.tile_size - 1)
        max_x = min(self.width, rect.right // self.tile_size + 2)
        min_y = max(0, rect.top // self.tile_size - 1)
        max_y = min(self.height, rect.bottom // self.tile_size + 2)
        
        # Проверяем пересечение с непроходимыми стенами (tile_value == 0)
        for y in range(min_y, max_y):
            for x in range(min_x, max_x):
                # Используем get_world_pos() для получения мировых координат тайла
                world_x, world_y = self.get_world_pos(x, y)
                tile_value = self.get_tile_at(world_x, world_y)
                
                if tile_value == 0:  # Стена - блокирует движение
                    # Проверяем пересечение прямоугольника с тайлом стены (AABB коллизия)
                    wall_rect = pygame.Rect(world_x, world_y, self.tile_size, self.tile_size)
                    if rect.colliderect(wall_rect):
                        return True  # Коллизия с непроходимой стеной
        
        return False  # Нет коллизий

