"""
Tilemap PyBSP - генерация подземелья по методу PyBSP_Dungeon_Generator
Чистая реализация BSP алгоритма из https://github.com/jpyankel/PyBSP_Dungeon_Generator
"""
import pygame
import random
import json
import os
import logging
from typing import List, Tuple, Optional, Dict, Any

# Настройка логирования
logger = logging.getLogger(__name__)


class TreeNode:
    """Узел BSP дерева (по методу PyBSP)"""
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.left = None
        self.right = None
        self.room = None  # Комната в этом узле (x, y, width, height)


class TilemapPyBSP:
    """Генератор карты подземелья по методу PyBSP"""
    
    def __init__(self, width: int = 100, height: int = 100, tile_size: int = 64,
                 min_node_size: Tuple[int, int] = (20, 20),
                 bias_ratio: float = 0.5,
                 bias_strength: float = 0.5,
                 bridge_width: int = 1,
                 seed: Optional[int] = None):
        """
        Инициализация Tilemap PyBSP
        
        Args:
            width: Ширина карты в тайлах
            height: Высота карты в тайлах
            tile_size: Размер тайла в пикселях
            min_node_size: Минимальный размер узла (width, height)
            bias_ratio: Вероятность выбора направления разделения (0.0-1.0)
            bias_strength: Сила смещения разделения (0.0-1.0)
            bridge_width: Ширина коридоров
        """
        self.width = width
        self.height = height
        self.tile_size = tile_size
        
        # Устанавливаем seed если указан
        if seed is not None:
            random.seed(seed)
        
        # Параметры PyBSP
        self.min_node_size = min_node_size
        self.bias_ratio = bias_ratio
        self.bias_strength = bias_strength
        self.bridge_width = bridge_width
        
        # Инициализация карты (-1 = пустота, 0 = стена, 1 = пол)
        self.void_value = -1
        self.map_data = [[self.void_value for _ in range(width)] for _ in range(height)]
        
        # Загрузка конфигурации тайлов
        self.tiles_config = self._load_tiles_config()
        
        # Загрузка изображений тайлов
        self.tile_images = {}
        self._load_tile_images()
        
        # Кэш для масштабированных тайлов (оптимизация памяти)
        self.scaled_cache = {}
        self.cached_wall_tiles = {}  # Кэш тайлов стен по координатам
        
        # Очищаем кэши при инициализации (после создания атрибутов)
        self._clear_tile_caches()
        
        # Данные генерации
        self.rooms = []
        self.corridors = []
        self.tree_root = None
        
        # Классификация тайлов стен (загружается из JSON)
        self.wall_tile_classification = {}
        self.mask_to_type = {}  # Маппинг битмасок на типы тайлов (старый формат)
        self.autotile_rules = {}  # Новый формат: маппинг битмасок на списки индексов тайлов
        
        # Угол поворота камеры (0, 1, 2, 3 для 0°, 90°, 180°, 270°)
        self.camera_angle = 0
        
        # Создаём fallback тайл для стен (яркий красный с буквой "W")
        self._create_fallback_wall_tile()
        
        # Фон для пустоты
        self.void_background = None
        self._generate_void_background()
        
        # Генерация карты
        self.generate()
    
    def _load_tiles_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию тайлов (с обработкой ошибок доступа)"""
        config_path = "game/assets/configs/tiles_config.json"
        try:
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except (OSError, IOError, json.JSONDecodeError) as e:
                    logger.error(f"Error loading tiles config: {e}")
        except OSError:
            pass  # Нет доступа к файлу
        
        return {
            "tile_size": 32,
            "room_settings": {
                "min_room_width": 6,
                "max_room_width": 12,
                "min_room_height": 6,
                "max_room_height": 12,
            }
        }
    
    def _load_tile_images(self):
        """Загружает изображения тайлов для ортогонального рендеринга"""
        tile_size = 64
        
        # Загружаем пол из lavarock.png
        lavarock_path = "game/assets/tiles/lavarock.png"
        try:
            if os.path.exists(lavarock_path):
                try:
                    lavarock_tileset = pygame.image.load(lavarock_path)
                    # Конвертируем только если display инициализирован и видеорежим установлен
                    try:
                        if pygame.display.get_init() and pygame.display.get_surface():
                            if lavarock_tileset.get_flags() & pygame.SRCALPHA:
                                lavarock_tileset = lavarock_tileset.convert_alpha()
                            else:
                                lavarock_tileset = lavarock_tileset.convert()
                    except (pygame.error, AttributeError):
                        pass  # Используем изображение без конвертации
                    tileset_width, tileset_height = lavarock_tileset.get_size()
                    tiles_x = tileset_width // tile_size
                    tiles_y = tileset_height // tile_size
                    floor_tiles = []
                    
                    for y in range(tiles_y):
                        for x in range(tiles_x):
                            tile_rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                            if tile_rect.right <= tileset_width and tile_rect.bottom <= tileset_height:
                                tile = lavarock_tileset.subsurface(tile_rect)
                                if tile.get_size() != (tile_size, tile_size):
                                    tile = pygame.transform.scale(tile, (tile_size, tile_size))
                                floor_tiles.append(tile)
                    
                    # Сохраняем варианты пола (минимум 4)
                    if len(floor_tiles) < 4 and floor_tiles:
                        # Дублируем если недостаточно
                        while len(floor_tiles) < 4:
                            floor_tiles.append(random.choice(floor_tiles))
                    
                    self.tile_images["floor"] = floor_tiles
                    logger.info(f"Loaded {len(floor_tiles)} floor tiles from lavarock.png")
                except Exception as e:
                    logger.error(f"Error loading lavarock.png: {e}")
        except OSError:
            pass   
        # Загружаем стены из dungeon.png (основной tileset стен)
        dungeon_path = "game/assets/tiles/dungeon.png"
        try:
            if os.path.exists(dungeon_path):
                try:
                    dungeon_tileset = pygame.image.load(dungeon_path)
                    # Конвертируем только если display инициализирован и видеорежим установлен
                    try:
                        if pygame.display.get_init() and pygame.display.get_surface():
                            if dungeon_tileset.get_flags() & pygame.SRCALPHA:
                                dungeon_tileset = dungeon_tileset.convert_alpha()
                            else:
                                dungeon_tileset = dungeon_tileset.convert()
                    except (pygame.error, AttributeError):
                        pass  # Используем изображение без конвертации
                    tileset_width, tileset_height = dungeon_tileset.get_size()
                    tiles_x = tileset_width // tile_size
                    tiles_y = tileset_height // tile_size
                    
                    # Загружаем все тайлы из dungeon.png
                    all_wall_tiles = []
                    for y in range(tiles_y):
                        for x in range(tiles_x):
                            tile_rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                            if tile_rect.right <= tileset_width and tile_rect.bottom <= tileset_height:
                                tile = dungeon_tileset.subsurface(tile_rect)
                                if not tile.get_flags() & pygame.SRCALPHA:
                                    tile = tile.convert_alpha()
                                if tile.get_size() != (tile_size, tile_size):
                                    tile = pygame.transform.scale(tile, (tile_size, tile_size))
                                all_wall_tiles.append(tile)
                    
                    # Сохраняем оригинальный tileset для извлечения тайлов по координатам
                    self.tile_images["dungeon_tileset"] = dungeon_tileset
                    
                    # Используем все тайлы для стен (и боковых, и верх/низ)
                    self.tile_images["wall"] = all_wall_tiles
                    self.tile_images["wall1"] = all_wall_tiles  # Используем те же тайлы
                    logger.info(f"Loaded {len(all_wall_tiles)} tiles from dungeon.png")
                except Exception as e:
                    logger.error(f"Error loading dungeon.png: {e}")
        except OSError:
            pass
        
        # Fallback: пытаемся загрузить wall.png и wall1.png если dungeon.png не найден
        if not self.tile_images.get("wall"):
            wall_path = "game/assets/tiles/wall.png"
            try:
                if os.path.exists(wall_path):
                    try:
                        wall_tileset = pygame.image.load(wall_path)
                        # Конвертируем только если display инициализирован и видеорежим установлен
                        try:
                            if pygame.display.get_init() and pygame.display.get_surface():
                                if wall_tileset.get_flags() & pygame.SRCALPHA:
                                    wall_tileset = wall_tileset.convert_alpha()
                                else:
                                    wall_tileset = wall_tileset.convert()
                        except (pygame.error, AttributeError):
                            pass  # Используем изображение без конвертации
                        tileset_width, tileset_height = wall_tileset.get_size()
                        tiles_x = tileset_width // tile_size
                        tiles_y = tileset_height // tile_size
                        wall_side_tiles = []
                        for y in range(tiles_y):
                            for x in range(tiles_x):
                                tile_rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                                if tile_rect.right <= tileset_width and tile_rect.bottom <= tileset_height:
                                    tile = wall_tileset.subsurface(tile_rect)
                                    if not tile.get_flags() & pygame.SRCALPHA:
                                        tile = tile.convert_alpha()
                                    if tile.get_size() != (tile_size, tile_size):
                                        tile = pygame.transform.scale(tile, (tile_size, tile_size))
                                    wall_side_tiles.append(tile)
                        self.tile_images["wall"] = wall_side_tiles
                        logger.info(f"Loaded {len(wall_side_tiles)} tiles from wall.png (fallback)")
                    except Exception as e:
                        logger.error(f"Error loading wall.png: {e}")
            except OSError:
                pass
            
            wall1_path = "game/assets/tiles/wall1.png"
            try:
                if os.path.exists(wall1_path):
                    try:
                        wall1_tileset = pygame.image.load(wall1_path)
                        # Конвертируем только если display инициализирован и видеорежим установлен
                        try:
                            if pygame.display.get_init() and pygame.display.get_surface():
                                if wall1_tileset.get_flags() & pygame.SRCALPHA:
                                    wall1_tileset = wall1_tileset.convert_alpha()
                                else:
                                    wall1_tileset = wall1_tileset.convert()
                        except (pygame.error, AttributeError):
                            pass  # Используем изображение без конвертации
                        tileset_width, tileset_height = wall1_tileset.get_size()
                        tiles_x = tileset_width // tile_size
                        tiles_y = tileset_height // tile_size
                        wall_top_bottom_tiles = []
                        for y in range(tiles_y):
                            for x in range(tiles_x):
                                tile_rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                                if tile_rect.right <= tileset_width and tile_rect.bottom <= tileset_height:
                                    tile = wall1_tileset.subsurface(tile_rect)
                                    if not tile.get_flags() & pygame.SRCALPHA:
                                        tile = tile.convert_alpha()
                                    if tile.get_size() != (tile_size, tile_size):
                                        tile = pygame.transform.scale(tile, (tile_size, tile_size))
                                    wall_top_bottom_tiles.append(tile)
                        self.tile_images["wall1"] = wall_top_bottom_tiles
                        logger.info(f"Loaded {len(wall_top_bottom_tiles)} tiles from wall1.png (fallback)")
                    except Exception as e:
                        logger.error(f"Error loading wall1.png: {e}")
            except OSError:
                pass
        
        # Загружаем декоративные камни из dirtstone.png
        dirtstone_path = "game/assets/tiles/dirtstone.png"
        try:
            if os.path.exists(dirtstone_path):
                try:
                    dirtstone_tileset = pygame.image.load(dirtstone_path)
                    # Конвертируем только если display инициализирован и видеорежим установлен
                    try:
                        if pygame.display.get_init() and pygame.display.get_surface():
                            if dirtstone_tileset.get_flags() & pygame.SRCALPHA:
                                dirtstone_tileset = dirtstone_tileset.convert_alpha()
                            else:
                                dirtstone_tileset = dirtstone_tileset.convert()
                    except (pygame.error, AttributeError):
                        pass  # Используем изображение без конвертации
                    tileset_width, tileset_height = dirtstone_tileset.get_size()
                    tiles_x = tileset_width // tile_size
                    tiles_y = tileset_height // tile_size
                    dirtstone_tiles = []
                    for y in range(tiles_y):
                        for x in range(tiles_x):
                            tile_rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                            if tile_rect.right <= tileset_width and tile_rect.bottom <= tileset_height:
                                tile = dirtstone_tileset.subsurface(tile_rect)
                                if tile.get_size() != (tile_size, tile_size):
                                    tile = pygame.transform.scale(tile, (tile_size, tile_size))
                                dirtstone_tiles.append(tile)
                    self.tile_images["dirtstone"] = dirtstone_tiles
                    logger.info(f"Loaded {len(dirtstone_tiles)} tiles from dirtstone.png")
                except Exception as e:
                    logger.error(f"Error loading dirtstone.png: {e}")
        except OSError:
            pass
    
    def _clear_tile_caches(self):
        """Очищает кэши тайлов (вызывается при смене tile_size или регенерации)"""
        self.scaled_cache.clear()
        self.cached_wall_tiles.clear()
    
    def _create_fallback_wall_tile(self):
        """Создаёт яркий fallback тайл для стен (красный с буквой 'W')"""
        try:
            fallback = pygame.Surface((self.tile_size, self.tile_size))
            fallback.fill((200, 50, 50))  # Яркий красный
            # Рисуем букву "W" для отладки
            font = pygame.font.Font(None, 48)
            text = font.render("W", True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.tile_size // 2, self.tile_size // 2))
            fallback.blit(text, text_rect)
            self.fallback_wall_tile = fallback
        except Exception:
            # Если не удалось создать, используем простой цветной квадрат
            self.fallback_wall_tile = pygame.Surface((self.tile_size, self.tile_size))
            self.fallback_wall_tile.fill((200, 50, 50))
    
    def _generate_void_background(self):
        """Генерирует фон для пустоты (упрощённый вариант)"""
        # Используем минимальный размер для экономии памяти
        bg_size = min(512, max(self.width, self.height) * self.tile_size)
        try:
            self.void_background = pygame.Surface((bg_size, bg_size))
            self.void_background.fill((10, 10, 15))
        except Exception:
            self.void_background = None
    
    def _draw_void_background(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        """Отрисовывает фон пустоты (тайлинг для покрытия всего экрана)"""
        if not self.void_background:
            return
        
        bg_w, bg_h = self.void_background.get_size()
        screen_w, screen_h = screen.get_size()
        
        # Вычисляем начальные координаты для тайлинга
        start_bg_x = -(camera_x % bg_w)
        start_bg_y = -(camera_y % bg_h)
        
        # Рисуем фон с тайлингом
        for y in range(start_bg_y, screen_h, bg_h):
            for x in range(start_bg_x, screen_w, bg_w):
                screen.blit(self.void_background, (x, y))
    
    def generate(self):
        """Генерирует карту подземелья по методу PyBSP"""
        logger.info(f"Generating PyBSP dungeon: {self.width}x{self.height} tiles")
        
        # Сброс карты
        self.map_data = [[self.void_value for _ in range(self.width)] for _ in range(self.height)]
        self.rooms = []
        self.corridors = []
        
        # 1. Создаем корневой узел
        self.tree_root = TreeNode(0, 0, self.width, self.height)
        
        # 2. Разрастаем дерево (grow)
        self._grow_tree(self.tree_root)
        
        # 3. Создаем комнаты в листьях
        self._create_rooms_in_leaves(self.tree_root)
        
        # 4. Соединяем комнаты через z-bridge
        self._connect_rooms_with_bridges(self.tree_root)
        
        # 5. Создаем стены вокруг пола
        self._create_walls()
        
        # 6. Очистка тупиков (удаление мёртвых концов)
        self._remove_dead_ends()
        
        # 7. Загружаем классификацию тайлов стен из JSON если есть
        self._load_wall_tile_classification()
        
        # 8. Визуализация для отладки (опционально, только один раз)
        # Отключено по умолчанию, чтобы не засорять консоль
        # Раскомментируйте следующую строку для отладки:
        # if logger.level <= 10:  # DEBUG level
        #     self._debug_print_map()
        
        logger.info(f"Generated {len(self.rooms)} rooms, {len(self.corridors)} corridors")
    
    def _load_wall_tile_classification(self):
        """Загружает классификацию тайлов стен из JSON файла с битмасками (новый формат с индексами)"""
        json_path = "wall_tiles.json"
        try:
            if os.path.exists(json_path):
                try:
                    import json
                    with open(json_path, 'r', encoding='utf-8') as f:
                        classification = json.load(f)
                        # Новый формат: autotile_rules содержит маппинг битмасок на списки индексов
                        self.autotile_rules = classification.get("autotile_rules", {})
                        # Сохраняем путь к tileset изображению
                        self.tileset_image_path = classification.get("tileset_image", "game/assets/tiles/dungeon.png")
                        logger.info(f"Loaded wall tile classification from {json_path}")
                        logger.info(f"  Autotile rules: {len(self.autotile_rules)} patterns")
                        logger.info(f"  Tileset image: {self.tileset_image_path}")
                except (OSError, IOError, json.JSONDecodeError) as e:
                    logger.error(f"Error loading wall tile classification: {e}")
                    self.autotile_rules = {}
                    self.tileset_image_path = "game/assets/tiles/dungeon.png"
            else:
                self.autotile_rules = {}
                self.tileset_image_path = "game/assets/tiles/dungeon.png"
                logger.debug(f"Wall tile classification not found: {json_path}")
        except OSError:
            self.autotile_rules = {}
            self.tileset_image_path = "game/assets/tiles/dungeon.png"
    
    def _is_hole_tile(self, tile: pygame.Surface) -> bool:
        """Проверяет, является ли тайл пола дырой"""
        width, height = tile.get_size()
        # Дыры обычно тёмные в центре
        center_color = tile.get_at((width//2, height//2))
        return sum(center_color[:3]) < 50
    
    def _is_transition_tile(self, tile: pygame.Surface) -> bool:
        """Проверяет, является ли тайл пола переходным элементом"""
        width, height = tile.get_size()
        # Переходы имеют градиент или смешанную текстуру
        edge_colors = [tile.get_at((0, 0))[:3], tile.get_at((width-1, 0))[:3],
                       tile.get_at((0, height-1))[:3], tile.get_at((width-1, height-1))[:3]]
        center_color = tile.get_at((width//2, height//2))[:3]
        
        # Если края сильно отличаются от центра - это переход
        edge_avg = [sum(c[i] for c in edge_colors) / len(edge_colors) for i in range(3)]
        diff = sum(abs(edge_avg[i] - center_color[i]) for i in range(3))
        return diff > 50
    
    def _grow_tree(self, node: TreeNode):
        """
        Разрастает BSP дерево (метод grow из PyBSP)
        Разделяет узлы до достижения минимального размера
        """
        # Проверяем, можно ли разделить
        can_split_horizontal = node.height >= self.min_node_size[1] * 2
        can_split_vertical = node.width >= self.min_node_size[0] * 2
        
        if not can_split_horizontal and not can_split_vertical:
            # Нельзя разделить - это лист
            return
        
        # Определяем направление разделения
        if can_split_horizontal and can_split_vertical:
            # Можем разделить в любом направлении - используем bias_ratio
            split_horizontal = random.random() < self.bias_ratio
        elif can_split_horizontal:
            split_horizontal = True
        else:
            split_horizontal = False
        
        if split_horizontal:
            # Горизонтальное разделение
            min_split = int(node.height * (0.5 - self.bias_strength * 0.1))
            max_split = int(node.height * (0.5 + self.bias_strength * 0.1))
            min_split = max(self.min_node_size[1], min_split)
            max_split = min(node.height - self.min_node_size[1], max_split)
            
            if min_split >= max_split:
                return
            
            split_pos = random.randint(min_split, max_split)
            
            node.left = TreeNode(node.x, node.y, node.width, split_pos)
            node.right = TreeNode(node.x, node.y + split_pos, node.width, node.height - split_pos)
        else:
            # Вертикальное разделение
            min_split = int(node.width * (0.5 - self.bias_strength * 0.1))
            max_split = int(node.width * (0.5 + self.bias_strength * 0.1))
            min_split = max(self.min_node_size[0], min_split)
            max_split = min(node.width - self.min_node_size[0], max_split)
            
            if min_split >= max_split:
                return
            
            split_pos = random.randint(min_split, max_split)
            
            node.left = TreeNode(node.x, node.y, split_pos, node.height)
            node.right = TreeNode(node.x + split_pos, node.y, node.width - split_pos, node.height)
        
        # Рекурсивно разрастаем дочерние узлы
        self._grow_tree(node.left)
        self._grow_tree(node.right)
    
    def _create_rooms_in_leaves(self, node: TreeNode):
        """
        Создает комнаты в листьях дерева (узлы без дочерних)
        Не все узлы обязательно имеют комнату - для разнообразия
        """
        if node is None:
            return
        
        if node.left is None and node.right is None:
            # Это лист - с вероятностью 85% создаем комнату
            if random.random() < 0.85:
                room_settings = self.tiles_config.get("room_settings", {})
                min_w = room_settings.get("min_room_width", 6)
                max_w = room_settings.get("max_room_width", 12)
                min_h = room_settings.get("min_room_height", 6)
                max_h = room_settings.get("max_room_height", 12)
                
                # Размер комнаты в пределах узла (с отступами для стен)
                padding = random.randint(2, 4)  # Отступ от края узла
                room_width = min(random.randint(min_w, max_w), node.width - padding * 2)
                room_height = min(random.randint(min_h, max_h), node.height - padding * 2)
                room_width = max(4, room_width)
                room_height = max(4, room_height)
                
                # Позиция комнаты внутри узла (с отступом) - исправлена проверка границ
                max_x_offset = max(padding, node.width - room_width - padding)
                max_y_offset = max(padding, node.height - room_height - padding)
                if max_x_offset < padding or max_y_offset < padding:
                    # Если комната не помещается, используем минимальный отступ
                    room_x = node.x + padding
                    room_y = node.y + padding
                    room_width = min(room_width, node.width - padding * 2)
                    room_height = min(room_height, node.height - padding * 2)
                else:
                    room_x = node.x + random.randint(padding, max_x_offset)
                    room_y = node.y + random.randint(padding, max_y_offset)
                
                # Сохраняем комнату
                room = (room_x, room_y, room_width, room_height)
                node.room = room
                self.rooms.append(room)
                
                # Заполняем пол в комнате
                for ry in range(room_y, room_y + room_height):
                    for rx in range(room_x, room_x + room_width):
                        if 0 <= ry < self.height and 0 <= rx < self.width:
                            self.map_data[ry][rx] = 1  # Пол
        else:
            # Рекурсивно обрабатываем дочерние узлы
            self._create_rooms_in_leaves(node.left)
            self._create_rooms_in_leaves(node.right)
    
    def _get_room_from_node(self, node: TreeNode) -> Optional[Tuple[int, int, int, int]]:
        """Получает комнату из узла или его дочерних узлов"""
        if node is None:
            return None
        
        if node.room is not None:
            return node.room
        
        # Пробуем получить из дочерних узлов
        room = self._get_room_from_node(node.left)
        if room is None:
            room = self._get_room_from_node(node.right)
        
        return room
    
    def _connect_rooms_with_bridges(self, node: TreeNode):
        """
        Соединяет комнаты через z-bridge (L-образные коридоры)
        По методу PyBSP: каждая комната пытается соединиться с другой, еще не соединенной
        """
        if node is None or (node.left is None and node.right is None):
            return
        
        # Рекурсивно соединяем дочерние узлы
        self._connect_rooms_with_bridges(node.left)
        self._connect_rooms_with_bridges(node.right)
        
        # Получаем комнаты из левого и правого поддеревьев
        room_left = self._get_room_from_node(node.left)
        room_right = self._get_room_from_node(node.right)
        
        if room_left and room_right:
            # Создаем z-bridge (L-образный коридор) между комнатами
            self._create_z_bridge(room_left, room_right)
    
    def _create_z_bridge(self, room1: Tuple[int, int, int, int], room2: Tuple[int, int, int, int]):
        """
        Создает z-bridge (L-образный коридор) между двумя комнатами
        Добавляет двери в местах соединения с комнатами
        """
        # Центры комнат
        center1_x = room1[0] + room1[2] // 2
        center1_y = room1[1] + room1[3] // 2
        center2_x = room2[0] + room2[2] // 2
        center2_y = room2[1] + room2[3] // 2
        
        # Варьируем ширину коридора
        bridge_w = self.bridge_width + random.randint(-1, 1)
        bridge_w = max(1, min(3, bridge_w))  # От 1 до 3
        
        # Создаем L-образный коридор
        if random.random() < 0.5:
            # Сначала горизонтально, потом вертикально
            for x in range(min(center1_x, center2_x), max(center1_x, center2_x) + 1):
                for wy in range(-bridge_w // 2, bridge_w // 2 + 1):
                    y = center1_y + wy
                    if 0 <= y < self.height and 0 <= x < self.width:
                        self.map_data[y][x] = 1  # Пол
            
            for y in range(min(center1_y, center2_y), max(center1_y, center2_y) + 1):
                for wx in range(-bridge_w // 2, bridge_w // 2 + 1):
                    x = center2_x + wx
                    if 0 <= y < self.height and 0 <= x < self.width:
                        self.map_data[y][x] = 1  # Пол
            
            # Добавляем двери
            self._add_door(center1_x, center1_y, room1)
            self._add_door(center2_x, center2_y, room2)
        else:
            # Сначала вертикально, потом горизонтально
            for y in range(min(center1_y, center2_y), max(center1_y, center2_y) + 1):
                for wx in range(-bridge_w // 2, bridge_w // 2 + 1):
                    x = center1_x + wx
                    if 0 <= y < self.height and 0 <= x < self.width:
                        self.map_data[y][x] = 1  # Пол
            
            for x in range(min(center1_x, center2_x), max(center1_x, center2_x) + 1):
                for wy in range(-bridge_w // 2, bridge_w // 2 + 1):
                    y = center2_y + wy
                    if 0 <= y < self.height and 0 <= x < self.width:
                        self.map_data[y][x] = 1  # Пол
            
            # Добавляем двери
            self._add_door(center1_x, center1_y, room1)
            self._add_door(center2_x, center2_y, room2)
        
        # Сохраняем коридор
        self.corridors.append((room1, room2))
    
    def _add_door(self, door_x: int, door_y: int, room: Tuple[int, int, int, int]):
        """
        Добавляет дверь (проём) в месте соединения коридора с комнатой
        Упрощённая версия - просто гарантирует, что точка (door_x, door_y) - пол
        """
        try:
            # Находим ближайшую точку на границе комнаты
            room_x, room_y, room_w, room_h = room
            
            # Проверяем валидность комнаты
            if room_w <= 0 or room_h <= 0:
                return
            
            # Определяем, на какой стороне комнаты находится дверь
            if abs(door_x - room_x) < abs(door_x - (room_x + room_w - 1)):
                # Левая сторона
                door_x = max(0, room_x - 1)
                door_y = max(room_y + 1, min(door_y, room_y + room_h - 2))
            elif abs(door_x - (room_x + room_w - 1)) < abs(door_x - room_x):
                # Правая сторона
                door_x = min(self.width - 1, room_x + room_w)
                door_y = max(room_y + 1, min(door_y, room_y + room_h - 2))
            elif abs(door_y - room_y) < abs(door_y - (room_y + room_h - 1)):
                # Верхняя сторона
                door_x = max(room_x + 1, min(door_x, room_x + room_w - 2))
                door_y = max(0, room_y - 1)
            else:
                # Нижняя сторона
                door_x = max(room_x + 1, min(door_x, room_x + room_w - 2))
                door_y = min(self.height - 1, room_y + room_h)
            
            # Просто делаем эту точку полом (не трогаем соседние стены!)
            if 0 <= door_x < self.width and 0 <= door_y < self.height:
                if self.map_data[door_y][door_x] == 0:  # Если там стена
                    self.map_data[door_y][door_x] = 1  # Делаем пол (проём)
        except (IndexError, ValueError) as e:
            logger.debug(f"_add_door error at ({door_x}, {door_y}): {e}")
    
    def _create_walls(self):
        """Создает стены вокруг пола (0 = стена, 1 = пол)
        Проверяет ТОЛЬКО 4 стороны (N, E, S, W), чтобы не создавать стены внутри пола
        """
        wall_count = 0
        for y in range(self.height):
            for x in range(self.width):
                if self.map_data[y][x] == self.void_value:
                    # Проверяем ТОЛЬКО 4 стороны (не диагонали!)
                    has_floor_nearby = False
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= ny < self.height and 0 <= nx < self.width:
                            if self.map_data[ny][nx] == 1:  # Пол рядом
                                has_floor_nearby = True
                                break
                    
                    if has_floor_nearby:
                        self.map_data[y][x] = 0  # Стена
                        wall_count += 1
        
        logger.debug(f"_create_walls(): Created {wall_count} wall tiles")
    
    def _remove_dead_ends(self):
        """
        Удаляет мёртвые тупики (dead-ends) из подземелья
        Тупик = клетка пола, у которой только 1 соседняя клетка пола
        НЕ удаляет тупики внутри комнат (проверяет принадлежность к комнате)
        """
        try:
            max_iterations = 10  # Максимум итераций для очистки
            removed_count = 0
            
            # Создаём множество координат комнат для быстрой проверки
            room_tiles = set()
            for room in self.rooms:
                room_x, room_y, room_w, room_h = room
                for ry in range(room_y, room_y + room_h):
                    for rx in range(room_x, room_x + room_w):
                        room_tiles.add((rx, ry))
            
            for iteration in range(max_iterations):
                dead_ends = []
                
                # Находим все тупики (но не в комнатах!)
                for y in range(1, self.height - 1):
                    for x in range(1, self.width - 1):
                        try:
                            if self.map_data[y][x] == 1:  # Пол
                                # Пропускаем если это тайл внутри комнаты
                                if (x, y) in room_tiles:
                                    continue
                                
                                # Считаем соседние клетки пола
                                floor_neighbors = 0
                                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                                    nx, ny = x + dx, y + dy
                                    if 0 <= nx < self.width and 0 <= ny < self.height:
                                        if self.map_data[ny][nx] == 1:
                                            floor_neighbors += 1
                                
                                # Если только 1 сосед - это тупик
                                if floor_neighbors == 1:
                                    dead_ends.append((x, y))
                        except IndexError:
                            continue
                
                # Удаляем тупики (превращаем в пустоту)
                if not dead_ends:
                    break
                
                for x, y in dead_ends:
                    try:
                        self.map_data[y][x] = self.void_value
                        removed_count += 1
                    except IndexError:
                        continue
                
                logger.debug(f"_remove_dead_ends(): Iteration {iteration + 1}, removed {len(dead_ends)} dead ends")
            
            if removed_count > 0:
                logger.info(f"_remove_dead_ends(): Total removed {removed_count} dead end tiles")
        except Exception as e:
            logger.error(f"_remove_dead_ends() error: {e}")
    
    def _debug_print_map(self):
        """Выводит карту в консоль для отладки"""
        print("\n=== DEBUG: Map Data ===")
        print(f"Size: {self.width}x{self.height}")
        print("Legend: . = void, # = wall, F = floor")
        print()
        
        # Показываем только первые 50x30 для читаемости
        max_w = min(50, self.width)
        max_h = min(30, self.height)
        
        for y in range(max_h):
            line = ""
            for x in range(max_w):
                val = self.map_data[y][x]
                if val == self.void_value:
                    line += "."
                elif val == 0:
                    line += "#"
                elif val == 1:
                    line += "F"
                else:
                    line += str(val)
            print(line)
        
        print(f"\nRooms: {len(self.rooms)}, Corridors: {len(self.corridors)}")
        print("=" * 30 + "\n")
    
    def _get_wall_tile_by_neighbors(self, x: int, y: int) -> pygame.Surface:
        cache_key = (x, y)
        if cache_key in self.cached_wall_tiles:
            return self.cached_wall_tiles[cache_key]

        mask = 0
        directions = [
            ((0, -1), 0), ((1, -1), 1), ((1, 0), 2), ((1, 1), 3),
            ((0, 1), 4), ((-1, 1), 5), ((-1, 0), 6), ((-1, -1), 7)
        ]
        
        for (dx, dy), bit_pos in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                if self.map_data[ny][nx] != 0:  # НЕ стена → пол или пустота
                    mask |= (1 << bit_pos)
        
        # Поворачиваем битмаску в соответствии с углом камеры
        mask = self._rotate_mask(mask, self.camera_angle)
        
        # Загружаем правила
        rules = getattr(self, 'autotile_rules', {})
        indices = rules.get(str(mask)) or [0]  # если маска не найдена → 0
        
        # Инициализируем chosen_index значением по умолчанию
        chosen_index = 0
        
        try:
            # Выбираем случайный индекс из списка
            if indices:
                chosen_index = random.choice(indices)
            
            # Если это боковая стена — выбираем правильную часть по высоте
            if chosen_index in {3, 4, 16, 17, 42, 43}:
                chosen_index = self._select_side_wall_part(x, y, [3, 4, 16, 17, 42, 43])
        except (IndexError, ValueError) as e:
            logger.debug(f"Error choosing tile index at ({x}, {y}): {e}")
            chosen_index = 0
        
        # Берём тайл из dungeon_tileset
        tileset = self.tile_images.get("dungeon_tileset")
        if tileset:
            try:
                tile = self._get_tile_by_index(tileset, chosen_index, self.tile_size)
                if tile and tile.get_size() != (self.tile_size, self.tile_size):
                    tile = pygame.transform.scale(tile, (self.tile_size, self.tile_size))
                if not tile:
                    tile = self.fallback_wall_tile
            except (KeyError, IndexError, ValueError, pygame.error) as e:
                logger.debug(f"_get_wall_tile_by_neighbors error at ({x}, {y}): {e}")
                tile = self.fallback_wall_tile
        else:
            tile = self.fallback_wall_tile
        
        self.cached_wall_tiles[cache_key] = tile
        return tile
    
    def _rotate_mask(self, mask: int, angle: int) -> int:
        """
        Поворачивает 8-битную Wang mask на угол (0, 1, 2, 3 для 0°, 90°, 180°, 270°)
        
        Битмаска: N NE E SE S SW W NW (биты 0-7)
        Поворот по часовой стрелке: N→E→S→W→N
        
        Args:
            mask: Исходная битмаска
            angle: Угол поворота (0, 1, 2, 3)
            
        Returns:
            int: Повернутая битмаска
        """
        if angle == 0:
            return mask
        
        # Извлекаем биты для каждого направления
        # Исходный порядок: N(0), NE(1), E(2), SE(3), S(4), SW(5), W(6), NW(7)
        bits = [
            (mask >> 0) & 1,  # N
            (mask >> 1) & 1,  # NE
            (mask >> 2) & 1,  # E
            (mask >> 3) & 1,  # SE
            (mask >> 4) & 1,  # S
            (mask >> 5) & 1,  # SW
            (mask >> 6) & 1,  # W
            (mask >> 7) & 1   # NW
        ]
        
        # Поворот на 90° по часовой стрелке: N→E, E→S, S→W, W→N
        # Также поворачиваем диагонали: NE→SE, SE→SW, SW→NW, NW→NE
        rotated_bits = [0] * 8
        
        if angle == 1:  # 90° по часовой
            rotated_bits[0] = bits[6]  # N ← W
            rotated_bits[1] = bits[7]  # NE ← NW
            rotated_bits[2] = bits[0]  # E ← N
            rotated_bits[3] = bits[1]  # SE ← NE
            rotated_bits[4] = bits[2]  # S ← E
            rotated_bits[5] = bits[3]  # SW ← SE
            rotated_bits[6] = bits[4]  # W ← S
            rotated_bits[7] = bits[5]  # NW ← SW
        elif angle == 2:  # 180°
            rotated_bits[0] = bits[4]  # N ← S
            rotated_bits[1] = bits[5]  # NE ← SW
            rotated_bits[2] = bits[6]  # E ← W
            rotated_bits[3] = bits[7]  # SE ← NW
            rotated_bits[4] = bits[0]  # S ← N
            rotated_bits[5] = bits[1]  # SW ← NE
            rotated_bits[6] = bits[2]  # W ← E
            rotated_bits[7] = bits[3]  # NW ← SE
        elif angle == 3:  # 270° (90° против часовой)
            rotated_bits[0] = bits[2]  # N ← E
            rotated_bits[1] = bits[3]  # NE ← SE
            rotated_bits[2] = bits[4]  # E ← S
            rotated_bits[3] = bits[5]  # SE ← SW
            rotated_bits[4] = bits[6]  # S ← W
            rotated_bits[5] = bits[7]  # SW ← NW
            rotated_bits[6] = bits[0]  # W ← N
            rotated_bits[7] = bits[1]  # NW ← NE
        
        # Собираем новую маску
        rotated_mask = 0
        for i, bit in enumerate(rotated_bits):
            if bit:
                rotated_mask |= (1 << i)
        
        return rotated_mask
    
    def rotate_map(self):
        """Поворачивает карту на 90° по часовой стрелке"""
        self.camera_angle = (self.camera_angle + 1) % 4
        # Очищаем кэш тайлов стен при повороте
        self.cached_wall_tiles.clear()
        logger.info(f"Карта повернута на {self.camera_angle * 90}°")
    
    def _determine_tile_type_by_mask(self, mask: int) -> str:
        """
        Определяет тип тайла стены по битмаске (fallback если нет маппинга в JSON)
        Использует данные из wall_tiles.json для корректного автотейлинга
        """
        # 8-битная маска: N NE E SE S SW W NW
        n  = bool(mask & 1)
        ne = bool(mask & 2)
        e  = bool(mask & 4)
        se = bool(mask & 8)
        s  = bool(mask & 16)
        sw = bool(mask & 32)
        w  = bool(mask & 64)
        nw = bool(mask & 128)
        
        # 1. Полная стена (ни одного проёма) - используем прямую стену
        if mask == 0:
            return "wall_straight"
        
        # 2. Арки (проём в одну сторону)
        if mask == 1:   return "arch_n"
        if mask == 4:   return "arch_e"
        if mask == 16:  return "arch_s"
        if mask == 64:  return "arch_w"
        
        # 3. Углы внешние (проём в диагонали)
        if mask == 2:   return "corner_outer"  # NE
        if mask == 8:   return "corner_outer"  # SE
        if mask == 32:  return "corner_outer"  # SW
        if mask == 128: return "corner_outer"  # NW
        
        # 4. Углы внутренние (пол в двух смежных направлениях, но не в диагонали)
        if (n and w and not nw): return "corner_inner"  # NW
        if (n and e and not ne): return "corner_inner"  # NE
        if (s and e and not se): return "corner_inner"  # SE
        if (s and w and not sw): return "corner_inner"  # SW
        
        # 5. Вертикальные стены (пол слева или справа)
        if w and not e:  # Пол только слева - правая сторона
            return "wall_right"
        if e and not w:  # Пол только справа - левая сторона
            return "wall_left"
        if w and e:  # Пол с обеих сторон - прямая стена
            return "wall_straight"
        
        # 6. Горизонтальные стены (пол сверху или снизу)
        if n and not s:  # Пол только сверху
            return "wall_straight"
        if s and not n:  # Пол только снизу
            return "wall_straight"
        if n and s:  # Пол сверху и снизу
            return "wall_straight"
        
        # 7. T-перекрёстки и перекрёстки - используем прямую стену
        if n and s and w: return "wall_straight"
        if n and s and e: return "wall_straight"
        if w and e and n: return "wall_straight"
        if w and e and s: return "wall_straight"
        if n and s and w and e: return "wall_straight"
        
        # 8. Концы - используем прямую стену
        if n: return "wall_straight"
        if e: return "wall_straight"
        if s: return "wall_straight"
        if w: return "wall_straight"
        
        # Fallback: прямая стена
        return "wall_straight"
    
    def _get_tile_by_index(self, tileset: pygame.Surface, tile_index: int, tile_size: int) -> pygame.Surface:
        """
        Извлекает тайл из tileset по индексу (grid-based)
        
        Args:
            tileset: Изображение tileset
            tile_index: Индекс тайла (0-based, слева направо, сверху вниз)
            tile_size: Размер одного тайла в пикселях
            
        Returns:
            pygame.Surface: Извлеченный тайл
        """
        tileset_w, tileset_h = tileset.get_size()
        tiles_per_row = tileset_w // tile_size
        
        # Вычисляем координаты тайла в grid
        tile_x = (tile_index % tiles_per_row) * tile_size
        tile_y = (tile_index // tiles_per_row) * tile_size
        
        # Проверяем границы
        if 0 <= tile_x < tileset_w and 0 <= tile_y < tileset_h:
            # Извлекаем тайл
            tile = tileset.subsurface((tile_x, tile_y, tile_size, tile_size))
            # Масштабируем если нужно
            if tile.get_size() != (tile_size, tile_size):
                tile = pygame.transform.scale(tile, (tile_size, tile_size))
            return tile
        
        # Fallback: возвращаем пустой тайл
        return pygame.Surface((tile_size, tile_size))
    
    def _select_side_wall_part(self, x: int, y: int, tile_indices: list) -> int:
        """
        Выбирает правильную часть боковой стены на основе позиции относительно пола
        
        Для боковых стен (перпендикулярно персонажу) нужно выбирать часть стены
        на основе высоты: нижняя часть у пола, средние части, верхняя часть.
        
        Args:
            x: X координата тайла стены
            y: Y координата тайла стены
            tile_indices: Список индексов тайлов для боковой стены [3, 4, 16, 17, 42, 43]
            
        Returns:
            int: Индекс тайла из списка
        """
        # Определяем позицию тайла относительно пола
        position_from_floor = self._get_wall_position_from_floor(x, y)
        
        # Маппинг позиции на индекс в списке
        # Предполагаем, что индексы идут снизу вверх:
        # [3, 4, 16, 17, 42, 43] = [нижняя1, нижняя2, средняя1, средняя2, верхняя1, верхняя2]
        if len(tile_indices) >= 6:
            if position_from_floor == 0:
                # Нижняя часть у пола - выбираем из первых двух
                return random.choice(tile_indices[0:2])
            elif position_from_floor == 1:
                # Первая средняя часть
                return random.choice(tile_indices[2:4]) if len(tile_indices) >= 4 else tile_indices[2]
            else:
                # Верхняя часть (позиция 2+)
                return random.choice(tile_indices[4:6]) if len(tile_indices) >= 6 else tile_indices[-1]
        else:
            # Если список короче, используем простой выбор
            return random.choice(tile_indices)
    
    def _get_wall_position_from_floor(self, x: int, y: int) -> int:
        """
        Определяет позицию тайла стены относительно пола (снизу вверх)
        
        Ищет ближайший пол снизу и считает, на какой позиции находится этот тайл стены.
        Позиция 0 = тайл у пола (нижняя часть арки)
        Позиция 1 = первый тайл над полом (первая средняя часть)
        Позиция 2 = второй тайл над полом (вторая средняя часть)
        Позиция 3+ = верхние тайлы (верхняя часть арки)
        
        Args:
            x: X координата тайла стены
            y: Y координата тайла стены
            
        Returns:
            int: Позиция тайла относительно пола (0 = у пола, 1+ = выше)
        """
        # Ищем пол снизу (стены обычно находятся над полом)
        current_y = y + 1
        floor_y = None
        
        # Ищем ближайший пол снизу (вниз по Y)
        while current_y < self.height:
            if self.map_data[current_y][x] == 1:  # Пол
                floor_y = current_y
                break
            current_y += 1
        
        # Если пол не найден снизу, ищем сверху (для стен над полом)
        if floor_y is None:
            current_y = y - 1
            while current_y >= 0:
                if self.map_data[current_y][x] == 1:  # Пол
                    floor_y = current_y
                    break
                current_y -= 1
        
        # Если пол найден, вычисляем позицию
        if floor_y is not None:
            # Позиция = расстояние от пола до этого тайла стены
            # Если пол снизу (floor_y > y), позиция = floor_y - y - 1
            # Если пол сверху (floor_y < y), позиция = y - floor_y - 1
            if floor_y > y:
                # Пол снизу - стена над полом
                position = floor_y - y - 1
            else:
                # Пол сверху - стена под полом (необычно, но возможно)
                position = y - floor_y - 1
            return max(0, position)
        
        # Если пол не найден, считаем что это нижний тайл (позиция 0)
        return 0
    
    def _select_arch_part(self, arch_type: str, position_from_floor: int) -> str:
        """
        Выбирает правильную часть арки на основе позиции относительно пола
        
        Последовательность арки снизу вверх:
        - arch_bottom (y=224) - нижняя часть у пола (позиция 0)
        - arch_mid_lower (y=192) - первая средняя часть (позиция 1)
        - arch_mid_upper (y=160) - вторая средняя часть (позиция 2)
        - arch_top (y=128) - верхняя часть (позиция 3+)
        
        Args:
            arch_type: Базовый тип арки (arch_n, arch_s, arch_e, arch_w)
            position_from_floor: Позиция тайла относительно пола (0 = у пола)
            
        Returns:
            str: Тип части арки с учетом позиции
        """
        # Выбираем часть арки на основе позиции
        if position_from_floor == 0:
            # Нижняя часть у пола
            return "arch_bottom"
        elif position_from_floor == 1:
            # Первая средняя часть
            return "arch_mid_lower"
        elif position_from_floor == 2:
            # Вторая средняя часть
            return "arch_mid_upper"
        else:
            # Верхняя часть (позиция 3+)
            return "arch_top"
    
    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        """Отрисовывает карту на экране (ортогональная проекция)"""
        tile_size = self.tile_size
        
        # Сначала рисуем фон пустоты (если есть)
        if self.void_background:
            self._draw_void_background(screen, camera_x, camera_y)
        
        # Определяем видимый диапазон тайлов
        start_x = max(0, camera_x // tile_size - 1)
        end_x = min(self.width, (camera_x + screen.get_width()) // tile_size + 1)
        start_y = max(0, camera_y // tile_size - 1)
        end_y = min(self.height, (camera_y + screen.get_height()) // tile_size + 1)
        
        drawn_tiles = 0
        drawn_walls = 0
        drawn_floors = 0
        
        # Сначала рисуем пол, потом стены (чтобы стены были поверх)
        tiles_to_draw = []
        
        # Собираем все тайлы для отрисовки
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile_value = self.map_data[y][x]
                
                # Игнорируем пустоту (она уже нарисована фоном)
                if tile_value == self.void_value:
                    continue
                
                # Ортогональная проекция
                screen_x = x * tile_size - camera_x
                screen_y = y * tile_size - camera_y
                
                # Проверяем, попадает ли тайл на экран (расширяем границы для стен)
                if screen_x < -tile_size or screen_x > screen.get_width() + tile_size or \
                   screen_y < -tile_size or screen_y > screen.get_height() + tile_size:
                    continue
                
                tiles_to_draw.append((x, y, tile_value, screen_x, screen_y))
        
        # Сортируем: сначала пол (1), потом стены (0)
        # Важно: пол (1) должен быть первым, стены (0) - вторыми (reverse=True: 1 > 0)
        tiles_to_draw.sort(key=lambda t: t[2], reverse=True)
        
        # Отрисовываем тайлы
        for x, y, tile_value, screen_x, screen_y in tiles_to_draw:
            try:
                if tile_value == 1:  # Пол
                    floor_tiles = self.tile_images.get("floor", [])
                    if floor_tiles:
                        floor_index = (x + y * 7) % len(floor_tiles)
                        floor_tile = floor_tiles[floor_index]
                        if floor_tile is not None:
                            # Кэшируем масштабированные тайлы
                            cache_key = f"floor_{floor_index}_{tile_size}"
                            if cache_key not in self.scaled_cache:
                                if floor_tile.get_size() != (tile_size, tile_size):
                                    self.scaled_cache[cache_key] = pygame.transform.scale(floor_tile, (tile_size, tile_size))
                                else:
                                    self.scaled_cache[cache_key] = floor_tile
                            screen.blit(self.scaled_cache[cache_key], (screen_x, screen_y))
                            drawn_floors += 1
                            
                            # Камушки с шансом ~15%
                            if random.random() < 0.15:
                                dirtstone_tiles = self.tile_images.get("dirtstone", [])
                                if dirtstone_tiles:
                                    stone_index = (x + y * 19) % len(dirtstone_tiles)
                                    stone_tile = dirtstone_tiles[stone_index]
                                    if stone_tile is not None:
                                        stone_cache_key = f"stone_{stone_index}_{tile_size}"
                                        if stone_cache_key not in self.scaled_cache:
                                            if stone_tile.get_size() != (tile_size, tile_size):
                                                self.scaled_cache[stone_cache_key] = pygame.transform.scale(stone_tile, (tile_size, tile_size))
                                            else:
                                                self.scaled_cache[stone_cache_key] = stone_tile
                                        screen.blit(self.scaled_cache[stone_cache_key], (screen_x, screen_y))
                    else:
                        # Fallback для пола
                        placeholder_key = "floor_placeholder"
                        if placeholder_key not in self.scaled_cache:
                            placeholder = pygame.Surface((tile_size, tile_size))
                            placeholder.fill((100, 50, 50))  # Коричневый
                            self.scaled_cache[placeholder_key] = placeholder
                        screen.blit(self.scaled_cache[placeholder_key], (screen_x, screen_y))
                        drawn_floors += 1
                
                elif tile_value == 0:  # Стена (0 = стена в map_data)
                    # Автотайлинг: определяем правильный тайл стены на основе соседей
                    # Метод ВСЕГДА возвращает тайл (никогда None)
                    wall_tile = self._get_wall_tile_by_neighbors(x, y)
                    screen.blit(wall_tile, (screen_x, screen_y))
                    drawn_walls += 1
            except Exception as e:
                if drawn_tiles < 5:
                    logger.error(f"Error drawing tile at ({x},{y}): {e}")
        
        drawn_tiles = drawn_floors + drawn_walls
    
    def get_tile_at(self, px: int, py: int) -> int:
        """Возвращает значение тайла в пикселях (с проверкой границ)"""
        tile_x = px // self.tile_size
        tile_y = py // self.tile_size
        # Проверяем границы (может быть отрицательным)
        tile_x = max(0, min(self.width - 1, tile_x))
        tile_y = max(0, min(self.height - 1, tile_y))
        if 0 <= tile_y < self.height and 0 <= tile_x < self.width:
            return self.map_data[tile_y][tile_x]
        return self.void_value
    
    def is_walkable(self, px: int, py: int) -> bool:
        """Проверяет, можно ли пройти по тайлу"""
        tile_value = self.get_tile_at(px, py)
        return tile_value == 1  # Пол проходим
    
    def is_walkable_rect(self, x: int, y: int, width: int, height: int) -> bool:
        """
        Проверяет, можно ли ходить по прямоугольной области (для спрайтов).
        Проверяет 4 угла прямоугольника для более точной коллизии.
        
        Args:
            x: X координата левого верхнего угла в пикселях
            y: Y координата левого верхнего угла в пикселях
            width: Ширина спрайта в пикселях
            height: Высота спрайта в пикселях
            
        Returns:
            bool: True если все углы на проходимых тайлах
        """
        # Проверяем 4 угла прямоугольника
        corners = [
            (x, y),  # Левый верхний
            (x + width, y),  # Правый верхний
            (x, y + height),  # Левый нижний
            (x + width, y + height)  # Правый нижний
        ]
        
        for corner_x, corner_y in corners:
            if not self.is_walkable(corner_x, corner_y):
                return False
        return True
    
    def check_collision(self, rect: pygame.Rect) -> bool:
        """Проверяет коллизию прямоугольника со стенами"""
        tile_size = self.tile_size
        
        # Получаем тайлы, которые пересекает прямоугольник
        min_tile_x = max(0, rect.left // tile_size)
        max_tile_x = min(self.width - 1, rect.right // tile_size)
        min_tile_y = max(0, rect.top // tile_size)
        max_tile_y = min(self.height - 1, rect.bottom // tile_size)
        
        for ty in range(min_tile_y, max_tile_y + 1):
            for tx in range(min_tile_x, max_tile_x + 1):
                if self.map_data[ty][tx] == 0:  # Стена
                    wall_rect = pygame.Rect(tx * tile_size, ty * tile_size, tile_size, tile_size)
                    if rect.colliderect(wall_rect):
                        return True  # Коллизия
        
        return False  # Нет коллизии
    
    def get_start_position(self) -> Tuple[int, int]:
        """
        Возвращает стартовую позицию (центр случайной комнаты)
        
        Returns:
            Tuple[int, int]: (x, y) в пикселях
        """
        if not self.rooms:
            # Если нет комнат, возвращаем центр карты
            return (self.width * self.tile_size // 2, self.height * self.tile_size // 2)
        
        # Выбираем случайную комнату
        room = random.choice(self.rooms)
        room_x, room_y, room_w, room_h = room
        
        # Центр комнаты в пикселях
        center_x = (room_x + room_w // 2) * self.tile_size
        center_y = (room_y + room_h // 2) * self.tile_size
        
        return (center_x, center_y)
    
    def regenerate(self, seed: Optional[int] = None):
        """
        Регенерирует карту заново
        
        Args:
            seed: Опциональный seed для random (если None - случайный)
        """
        if seed is not None:
            random.seed(seed)
        
        # Очищаем кэши
        self.scaled_cache.clear()
        self.cached_wall_tiles.clear()
        
        # Сброс карты
        self.map_data = [[self.void_value for _ in range(self.width)] for _ in range(self.height)]
        self.rooms = []
        self.corridors = []
        self.tree_root = None
        
        # Генерация
        self.generate()
    
    def export_map(self, output_path: str = "dungeon_map.json"):
        """
        Экспортирует карту в JSON файл
        
        Args:
            output_path: Путь к выходному файлу
        """
        try:
            export_data = {
                "width": self.width,
                "height": self.height,
                "tile_size": self.tile_size,
                "map_data": self.map_data,
                "rooms": self.rooms,
                "corridors": self.corridors
            }
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            logger.info(f"Map exported to {output_path}")
        except Exception as e:
            logger.error(f"Error exporting map: {e}")

