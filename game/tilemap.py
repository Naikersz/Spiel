"""
Tilemap - генерация подземелья (обертка для PyBSP)
Использует TilemapPyBSP с автотейлингом
"""
from .tilemap_pybsp import TilemapPyBSP
from typing import Tuple, Optional


class Tilemap(TilemapPyBSP):
    """Обертка TilemapPyBSP с обратной совместимостью"""
    
    def __init__(self, width: int = 100, height: int = 100, tile_size: int = 64,
                 num_rooms: int = 25,
                 blocks_range: Tuple[int, int] = (3, 15),
                 doors_range: Tuple[int, int] = (2, 4),
                 seed: Optional[int] = None,
                 # Параметры BSP для обратной совместимости
                 min_node_size: Optional[Tuple[int, int]] = None,
                 bias_ratio: float = 0.5,
                 bias_strength: float = 0.5,
                 bridge_width: int = 1):
        """
        Инициализация Tilemap (обертка для PyBSP генерации с автотейлингом)
        
        Args:
            width: Ширина карты в тайлах
            height: Высота карты в тайлах
            tile_size: Размер тайла в пикселях
            num_rooms: Игнорируется (для обратной совместимости)
            blocks_range: Игнорируется (для обратной совместимости)
            doors_range: Игнорируется (для обратной совместимости)
            seed: Опциональный seed для random
            min_node_size: Минимальный размер узла BSP (width, height)
            bias_ratio: Вероятность выбора направления разделения (0.0-1.0)
            bias_strength: Сила смещения разделения (0.0-1.0)
            bridge_width: Ширина коридоров
        """
        # Используем min_node_size если указан, иначе дефолт
        if min_node_size is None:
            min_node_size = (20, 20)
        
        # Вызываем родительский конструктор TilemapPyBSP
        super().__init__(
            width=width,
            height=height,
            tile_size=tile_size,
            min_node_size=min_node_size,
            bias_ratio=bias_ratio,
            bias_strength=bias_strength,
            bridge_width=bridge_width,
            seed=seed
        )


# Экспортируем для обратной совместимости
__all__ = ['Tilemap']
