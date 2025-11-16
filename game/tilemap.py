"""
Tilemap - генерация подземелья (обертка для PyBSP)
Для возврата к старой реализации импортируйте из tilemap_original
"""
from .tilemap_block_based import TilemapBlockBased
from typing import Tuple, Optional


class Tilemap(TilemapBlockBased):
    """Обертка TilemapBlockBased с обратной совместимостью"""
    
    def __init__(self, width: int = 100, height: int = 100, tile_size: int = 64,
                 num_rooms: int = 25,
                 blocks_range: Tuple[int, int] = (3, 15),
                 doors_range: Tuple[int, int] = (2, 4),
                 seed: Optional[int] = None,
                 # Старые параметры для обратной совместимости (игнорируются)
                 min_node_size: Optional[Tuple[int, int]] = None,
                 bias_ratio: float = 0.5,
                 bias_strength: float = 0.5,
                 bridge_width: int = 1):
        """
        Инициализация Tilemap (обертка для Block-Based генерации)
        
        Args:
            width: Ширина карты в тайлах
            height: Высота карты в тайлах
            tile_size: Размер тайла в пикселях
            num_rooms: Количество комнат
            blocks_range: Диапазон блоков в комнате (min, max)
            doors_range: Диапазон дверей в комнате (min, max)
            seed: Опциональный seed для random
        """
        # Вызываем родительский конструктор
        super().__init__(
            width=width,
            height=height,
            tile_size=tile_size,
            num_rooms=num_rooms,
            blocks_range=blocks_range,
            doors_range=doors_range,
            seed=seed
        )


# Экспортируем для обратной совместимости
__all__ = ['Tilemap']
