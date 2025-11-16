"""
Tileset Loader - загрузка и управление тайлсетами для ортогонального рендеринга
Поддерживает DIRTSTONE, DIRT4/DIRT3, WALL/WALL1 tilesets
"""
import pygame
import os
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class TilesetLoader:
    """Загружает и управляет тайлсетами из spritesheets"""
    
    def __init__(self, base_path: str = ""):
        """
        Инициализация загрузчика тайлсетов
        
        Args:
            base_path: Базовый путь к проекту
        """
        self.base_path = base_path
        self.tile_size = 64
        self.tilesets: Dict[str, List[pygame.Surface]] = {}
        
    def load_tileset(self, filename: str, grid_width: int, grid_height: int, 
                     tile_size: int = 64) -> List[pygame.Surface]:
        """
        Загружает тайлсет из файла и разрезает на отдельные тайлы
        
        Args:
            filename: Имя файла (например, "dirtstone.png")
            grid_width: Ширина сетки тайлов
            grid_height: Высота сетки тайлов
            tile_size: Размер одного тайла в пикселях
            
        Returns:
            List[pygame.Surface]: Список тайлов
        """
        filepath = os.path.join(self.base_path, "game/assets/tiles", filename)
        if not os.path.exists(filepath):
            logger.warning(f"Tileset file not found: {filepath}")
            return []
        
        try:
            tileset_image = pygame.image.load(filepath).convert_alpha()
            tileset_width, tileset_height = tileset_image.get_size()
            
            # Проверяем размеры
            expected_width = grid_width * tile_size
            expected_height = grid_height * tile_size
            
            if tileset_width != expected_width or tileset_height != expected_height:
                logger.warning(
                    f"Tileset {filename} size mismatch: "
                    f"expected {expected_width}x{expected_height}, "
                    f"got {tileset_width}x{tileset_height}"
                )
            
            tiles = []
            for y in range(grid_height):
                for x in range(grid_width):
                    tile_rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                    if tile_rect.right <= tileset_width and tile_rect.bottom <= tileset_height:
                        tile = tileset_image.subsurface(tile_rect)
                        # Убеждаемся, что тайл правильного размера
                        if tile.get_size() != (tile_size, tile_size):
                            tile = pygame.transform.scale(tile, (tile_size, tile_size))
                        tiles.append(tile)
            
            logger.info(f"Loaded {len(tiles)} tiles from {filename} ({grid_width}x{grid_height} grid)")
            return tiles
            
        except Exception as e:
            logger.error(f"Error loading tileset {filename}: {e}", exc_info=True)
            return []
    
    def load_dirtstone_tiles(self) -> List[pygame.Surface]:
        """Загружает DIRTSTONE tileset (8x8 grid, 64 tiles)"""
        tiles = self.load_tileset("dirtstone.png", 8, 8, self.tile_size)
        self.tilesets["dirtstone"] = tiles
        return tiles
    
    def load_dirt_tiles(self) -> Tuple[List[pygame.Surface], List[pygame.Surface]]:
        """
        Загружает DIRT4 и DIRT3 tilesets (12x12 grid, 144 tiles total)
        
        Returns:
            Tuple[List[pygame.Surface], List[pygame.Surface]]: (dirt4_tiles, dirt3_tiles)
        """
        all_tiles = self.load_tileset("dirt4_dirt3.png", 12, 12, self.tile_size)
        
        # Первые 72 тайла - DIRT4, остальные 72 - DIRT3
        dirt4_tiles = all_tiles[:72] if len(all_tiles) >= 72 else all_tiles[:len(all_tiles)//2]
        dirt3_tiles = all_tiles[72:] if len(all_tiles) >= 144 else all_tiles[len(all_tiles)//2:]
        
        self.tilesets["dirt4"] = dirt4_tiles
        self.tilesets["dirt3"] = dirt3_tiles
        
        return dirt4_tiles, dirt3_tiles
    
    def load_wall_tiles(self) -> Tuple[List[pygame.Surface], List[pygame.Surface]]:
        """
        Загружает WALL и WALL1 tilesets (10x10 grid, 100 tiles total)
        
        Returns:
            Tuple[List[pygame.Surface], List[pygame.Surface]]: (wall_tiles, wall1_tiles)
        """
        all_tiles = self.load_tileset("wall_wall1.png", 10, 10, self.tile_size)
        
        # Первые 50 тайлов - WALL, остальные 50 - WALL1
        wall_tiles = all_tiles[:50] if len(all_tiles) >= 50 else all_tiles[:len(all_tiles)//2]
        wall1_tiles = all_tiles[50:] if len(all_tiles) >= 100 else all_tiles[len(all_tiles)//2:]
        
        self.tilesets["wall"] = wall_tiles
        self.tilesets["wall1"] = wall1_tiles
        
        return wall_tiles, wall1_tiles
    
    def get_tile(self, tileset_name: str, index: int) -> Optional[pygame.Surface]:
        """
        Получает тайл по индексу из загруженного tileset
        
        Args:
            tileset_name: Имя tileset ("dirtstone", "dirt4", "dirt3", "wall", "wall1")
            index: Индекс тайла
            
        Returns:
            pygame.Surface или None если тайл не найден
        """
        if tileset_name not in self.tilesets:
            return None
        
        tiles = self.tilesets[tileset_name]
        if 0 <= index < len(tiles):
            return tiles[index]
        
        return None
    
    def get_random_tile(self, tileset_name: str, x: int, y: int) -> Optional[pygame.Surface]:
        """
        Получает псевдослучайный тайл на основе координат
        
        Args:
            tileset_name: Имя tileset
            x: X координата тайла на карте
            y: Y координата тайла на карте
            
        Returns:
            pygame.Surface или None
        """
        if tileset_name not in self.tilesets:
            return None
        
        tiles = self.tilesets[tileset_name]
        if not tiles:
            return None
        
        # Псевдослучайный выбор на основе координат
        index = (x + y * 7) % len(tiles)
        return tiles[index]

