#!/usr/bin/env python3
"""
Создаёт объёмные тайлы стен и правильный tileset с terrain set и битмасками.
Использует координаты из Tilesett.tres для terrain 0 (стены).
"""

from PIL import Image, ImageDraw, ImageEnhance
import os

TILE_SIZE = 32
INPUT_PATH = "tilesets/Terrain (32x32).png"
OUTPUT_PATH = "tilesets/wall_volume_autotile.png"
TILESET_PATH = "tilesets/wall_volume_tileset.tres"

# Структура автотейла: (строка, количество тайлов)
TILE_LAYOUT = [
    (0, 10),  # Строка 0: 10 тайлов (0-9)
    (1, 10),  # Строка 1: 10 тайлов (0-9)
    (2, 11),  # Строка 2: 11 тайлов (0-10)
    (3, 11),  # Строка 3: 11 тайлов (0-10)
    (4, 5),   # Строка 4: 5 тайлов (4-8)
]

# Координаты тайлов terrain 0 из Tilesett.tres
# Формат: позиция в автотейле -> (x, y) в исходном атласе
TERRAIN_0_COORDS = [
    # Строка 0 (10 тайлов)
    (2, 2),   # 0 - изолированный (все стороны)
    (3, 2),   # 1 - только сверху
    (10, 2),  # 2 - только справа
    (11, 2),  # 3 - сверху и справа
    (5, 2),   # 4 - только снизу
    (5, 2),   # 5 - сверху и снизу
    (14, 2),  # 6 - справа и снизу
    (7, 2),   # 7 - сверху, справа и снизу
    (3, 2),   # 8 - только слева (зеркало)
    (16, 2),  # 9 - сверху и слева
    
    # Строка 1 (10 тайлов)
    (10, 2),  # 10 - справа и слева
    (11, 2),  # 11 - сверху, справа и слева
    (14, 2),  # 12 - только снизу справа
    (7, 2),   # 13 - сверху и снизу справа
    (14, 2),  # 14 - снизу и справа
    (7, 2),   # 15 - снизу, справа и слева
    (16, 2),  # 16 - все кроме top-left
    (17, 2),  # 17 - все кроме top-right
    (3, 2),   # 18 - снизу и слева
    (7, 2),   # 19 - все кроме bottom-right
    
    # Строка 2 (11 тайлов)
    (16, 2),  # 20 - все кроме bottom-left
    (17, 2),  # 21 - все кроме bottom-right
    (7, 2),   # 22 - все стороны
    (2, 3),   # 23 - только углы
    (3, 3),   # 24 - углы и top
    (10, 2),  # 25 - углы и right
    (5, 2),   # 26 - углы и bottom
    (3, 2),   # 27 - углы и left
    (11, 2),  # 28 - углы, top и right
    (5, 2),   # 29 - углы, top и bottom
    (16, 2),  # 30 - углы, top и left
    
    # Строка 3 (11 тайлов)
    (14, 2),  # 32 - углы, right и bottom
    (10, 2),  # 33 - углы, right и left
    (3, 2),   # 34 - углы, bottom и left
    (7, 2),   # 35 - углы, top, right и bottom
    (11, 2),  # 36 - углы, top, right и left
    (16, 2),  # 37 - углы, top, bottom и left
    (14, 2),  # 38 - углы, right, bottom и left
    (7, 2),   # 39 - все углы и стороны
    (7, 4),   # 40 - специальные
    (10, 4),  # 41 - специальные
    (11, 4),  # 42 - специальные
    
    # Строка 4 (5 тайлов)
    (14, 4),  # 64 - дополнительные
    (16, 4),  # 65 - дополнительные
    (17, 4),  # 66 - дополнительные
    (7, 10),  # 67 - дополнительные
    (10, 10), # 68 - дополнительные
]

# Битмаски для каждого тайла (стандартная схема 47-тайлового автотейла)
# Формат: (top_left, top, top_right, left, right, bottom_left, bottom, bottom_right)
TERRAIN_PEERING_BITS = [
    # Строка 0
    (True, True, True, True, True, True, True, True),    # 0 - все
    (False, True, False, False, False, False, False, False),  # 1 - только top
    (False, False, False, False, True, False, False, False),  # 2 - только right
    (False, True, False, False, True, False, False, False),  # 3 - top + right
    (False, False, False, False, False, False, True, False),  # 4 - только bottom
    (False, True, False, False, False, False, True, False),   # 5 - top + bottom
    (False, False, False, False, True, False, True, False),   # 6 - right + bottom
    (False, True, False, False, True, False, True, False),   # 7 - top + right + bottom
    (False, False, False, True, False, False, False, False),  # 8 - только left
    (False, True, False, True, False, False, False, False),   # 9 - top + left
    
    # Строка 1
    (False, False, False, True, True, False, False, False),   # 10 - left + right
    (False, True, False, True, True, False, False, False),   # 11 - top + left + right
    (False, False, False, False, True, False, True, False),  # 12 - right + bottom
    (False, True, False, False, True, False, True, False),   # 13 - top + right + bottom
    (False, False, False, False, True, False, True, False),   # 14 - right + bottom
    (False, False, False, True, True, False, True, False),    # 15 - left + right + bottom
    (True, True, True, True, True, False, True, True),       # 16 - все кроме bottom_left
    (True, True, True, True, True, True, True, False),       # 17 - все кроме bottom_right
    (False, False, False, True, False, False, True, False),  # 18 - left + bottom
    (True, True, True, True, True, True, True, False),      # 19 - все кроме bottom_right
    
    # Строка 2
    (True, True, True, True, True, False, True, True),       # 20 - все кроме bottom_left
    (True, True, True, True, True, True, True, False),       # 21 - все кроме bottom_right
    (True, True, True, True, True, True, True, True),       # 22 - все
    (True, False, True, False, False, True, False, True),   # 23 - только углы
    (True, True, True, False, False, True, False, True),    # 24 - углы + top
    (True, False, True, False, True, True, False, True),    # 25 - углы + right
    (True, False, True, False, False, True, True, True),     # 26 - углы + bottom
    (True, False, True, True, False, True, False, True),    # 27 - углы + left
    (True, True, True, False, True, True, False, True),    # 28 - углы + top + right
    (True, True, True, False, False, True, True, True),     # 29 - углы + top + bottom
    (True, True, True, True, False, True, False, True),    # 30 - углы + top + left
    
    # Строка 3
    (True, False, True, False, True, True, True, True),      # 32 - углы + right + bottom
    (True, False, True, True, True, True, False, True),     # 33 - углы + right + left
    (True, False, True, True, False, True, True, True),     # 34 - углы + bottom + left
    (True, True, True, False, True, True, True, True),     # 35 - углы + top + right + bottom
    (True, True, True, True, True, True, False, True),     # 36 - углы + top + right + left
    (True, True, True, True, False, True, True, True),     # 37 - углы + top + bottom + left
    (True, False, True, True, True, True, True, True),     # 38 - углы + right + bottom + left
    (True, True, True, True, True, True, True, True),       # 39 - все
    (True, True, True, True, True, True, True, True),       # 40 - все
    (True, True, True, True, True, True, True, True),      # 41 - все
    (True, True, True, True, True, True, True, True),       # 42 - все
    
    # Строка 4
    (True, True, True, True, True, True, True, True),      # 64 - все
    (True, True, True, True, True, True, True, True),      # 65 - все
    (True, True, True, True, True, True, True, True),      # 66 - все
    (True, True, True, True, True, True, True, True),       # 67 - все
    (True, True, True, True, True, True, True, True),      # 68 - все
]

def create_volume_tile(base_tile: Image.Image) -> Image.Image:
    """Создаёт объёмный тайл с выраженным эффектом."""
    tile = base_tile.copy().convert('RGBA')
    w, h = tile.size
    
    # Сильно затемняем
    enhancer = ImageEnhance.Brightness(tile)
    tile = enhancer.enhance(0.55)
    
    # Увеличиваем контрастность
    enhancer = ImageEnhance.Contrast(tile)
    tile = enhancer.enhance(1.4)
    
    # Градиент тени снизу
    shadow = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    for y in range(h):
        progress = 1.0 - (y / h)
        alpha = int(200 * (progress ** 1.5))
        color = (8, 4, 2, alpha)
        draw.line([(0, y), (w, y)], fill=color)
    
    tile = Image.alpha_composite(tile, shadow)
    
    # Границы
    draw = ImageDraw.Draw(tile)
    draw.rectangle([(0, h-3), (w, h-1)], fill=(0, 0, 0, 240))
    draw.rectangle([(0, 0), (2, h-1)], fill=(0, 0, 0, 180))
    draw.rectangle([(w-2, 0), (w, h-1)], fill=(0, 0, 0, 180))
    
    # Тень слева
    left_shadow = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    left_draw = ImageDraw.Draw(left_shadow)
    for x in range(min(8, w)):
        alpha = int(80 * (1 - x / 8))
        color = (0, 0, 0, alpha)
        left_draw.line([(x, 0), (x, h-1)], fill=color)
    tile = Image.alpha_composite(tile, left_shadow)
    
    return tile

def extract_tile(atlas: Image.Image, x: int, y: int) -> Image.Image:
    """Извлекает тайл из атласа."""
    left = x * TILE_SIZE
    top = y * TILE_SIZE
    return atlas.crop((left, top, left + TILE_SIZE, top + TILE_SIZE))

def generate_tileset_file():
    """Генерирует tileset файл с terrain set и битмасками."""
    
    lines = [
        '[gd_resource type="TileSet" load_steps=3 format=3 uid="uid://wallvolumetileset"]',
        '',
        '[ext_resource type="Texture2D" path="res://tilesets/wall_volume_autotile.png" id="1_wallvol"]',
        '',
        '[sub_resource type="TileSetAtlasSource" id="TileSetAtlasSource_wallvol"]',
        'texture = ExtResource("1_wallvol")',
        'texture_region_size = Vector2i(32, 32)',
    ]
    
    # Генерируем тайлы с битмасками
    tile_index = 0
    for row, count in TILE_LAYOUT:
        for col in range(count):
            if tile_index < len(TERRAIN_PEERING_BITS):
                bits = TERRAIN_PEERING_BITS[tile_index]
                
                lines.append(f'{col}:{row}/0 = 0')
                lines.append(f'{col}:{row}/0/terrain_set = 0')
                lines.append(f'{col}:{row}/0/terrain = 0')
                
                # Добавляем peering bits
                bit_names = [
                    'top_left_corner', 'top_side', 'top_right_corner',
                    'left_side', 'right_side',
                    'bottom_left_corner', 'bottom_side', 'bottom_right_corner'
                ]
                
                for i, bit_name in enumerate(bit_names):
                    if bits[i]:
                        lines.append(f'{col}:{row}/0/terrains_peering_bit/{bit_name} = 0')
            
            tile_index += 1
    
    lines.extend([
        '',
        '[sub_resource type="TileSetTerrainSet" id="TileSetTerrainSet_0"]',
        'mode = 2',
        'terrains/0 = SubResource("TileSetTerrain_0")',
        '',
        '[sub_resource type="TileSetTerrain" id="TileSetTerrain_0"]',
        'name = &"WallVolume"',
        '',
        '[resource]',
        'tile_size = Vector2i(32, 32)',
        'sources/0 = SubResource("TileSetAtlasSource_wallvol")',
        'terrain_sets/0 = SubResource("TileSetTerrainSet_0")',
    ])
    
    with open(TILESET_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"✓ Создан tileset: {TILESET_PATH}")

def generate_volume_texture():
    """Генерирует объёмную текстуру."""
    
    if not os.path.exists(INPUT_PATH):
        print(f"Ошибка: файл не найден: {INPUT_PATH}")
        return
    
    atlas = Image.open(INPUT_PATH).convert('RGBA')
    atlas_width = atlas.size[0] // TILE_SIZE
    atlas_height = atlas.size[1] // TILE_SIZE
    
    max_width = max(count for _, count in TILE_LAYOUT)
    total_height = len(TILE_LAYOUT)
    
    canvas = Image.new('RGBA', (max_width * TILE_SIZE, total_height * TILE_SIZE), (0, 0, 0, 0))
    
    tile_index = 0
    for row, count in TILE_LAYOUT:
        for col in range(count):
            if tile_index < len(TERRAIN_0_COORDS):
                base_x, base_y = TERRAIN_0_COORDS[tile_index]
                
                if base_x >= atlas_width or base_y >= atlas_height:
                    base_x, base_y = 2, 2
                
                base_tile = extract_tile(atlas, base_x, base_y)
                volume_tile = create_volume_tile(base_tile)
                
                x = col * TILE_SIZE
                y = row * TILE_SIZE
                canvas.paste(volume_tile, (x, y), volume_tile)
            
            tile_index += 1
    
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    canvas.save(OUTPUT_PATH)
    print(f"✓ Создана текстура: {OUTPUT_PATH}")

if __name__ == "__main__":
    generate_volume_texture()
    generate_tileset_file()
    print("✓ Готово! Объёмные тайлы и tileset созданы.")

