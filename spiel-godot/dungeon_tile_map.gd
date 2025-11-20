extends TileMap
"""
DungeonTileMap.gd
Улучшенная BSP генерация подземелья:
- рекурсивное деление области на прямоугольники с BSP деревом
- правильное соединение соседних листов дерева
- стены с autotiling через пост-проход
- чистая система классификации тайлов

НАСТРОЙКА КОЛЛИЗИИ:
В редакторе Godot откройте ваш TileSet ресурс:
1. Выберите источник тайлов для стен (SOURCE_ID_WALL)
2. Перейдите в раздел "Physics Layers"
3. Включите Physics Layer 0 (или создайте новый)
4. Для каждого тайла стены установите коллизию:
   - Выберите тайл в атласе
   - В разделе Physics установите форму коллизии (обычно Rectanglцe)
   - Коллизия будет автоматически применяться ко всем тайлам стен
"""

# Для Godot 4.x
const SOURCE_ID_WALL := 0  # ID источника тайлов для стен
const SOURCE_ID_FLOOR := 1  # ID источника тайлов для пола (второй тайлсет)
const TILE_FLOOR := Vector2i(10, 3)  # Координаты тайла пола (из второго тайлсета)

# Базовый тайл стены для autotiling
# Autotiling автоматически выбирает правильный тайл на основе соседей
# Если у вас есть разные тайлы для разных конфигураций, можно расширить функцию _get_autotile_wall()
const TILE_WALL_BASE := Vector2i(0, 0)  # Базовый тайл стены (укажите координаты из вашего тайлсета)

# Типы тайлов
enum TileType {
	EMPTY,
	FLOOR,
	WALL
}

# Структура BSP узла
class BSPNode:
	var rect: Rect2i
	var left: BSPNode = null
	var right: BSPNode = null
	var room: Rect2i = Rect2i()  # Пустая комната, если это лист

	func is_leaf() -> bool:
		return left == null and right == null

@export var map_width_tiles: int = 100      # ширина карты в тайлах
@export var map_height_tiles: int = 100     # высота карты в тайлах
@export var min_room_size: int = 8          # минимальная комната (в тайлах)
@export var max_room_size: int = 14         # максимальная комната
@export var max_depth: int = 7              # глубина BSP

var _bsp_root: BSPNode = null
var _rng := RandomNumberGenerator.new()

func _ready() -> void:
	_rng.randomize()
	# Можно сразу генерить при старте, или вызывать из LevelTown
	generate_dungeon()


func generate_dungeon() -> void:
	clear()
	_bsp_root = null

	# Шаг 1: Создаем BSP дерево
	var root_rect := Rect2i(0, 0, map_width_tiles, map_height_tiles)
	_bsp_root = _split_space(root_rect, 0)

	# Шаг 2: Создаем комнаты в листах
	_create_rooms_in_leaves(_bsp_root)

	# Шаг 3: Соединяем соседние листы коридорами (только пол)
	_connect_adjacent_leaves(_bsp_root)

	# Шаг 4: Пост-проход для построения стен с autotiling
	_build_walls_with_autotiling()


# Разделяет пространство и создает BSP дерево
func _split_space(region: Rect2i, depth: int) -> BSPNode:
	var node := BSPNode.new()
	node.rect = region

	if depth >= max_depth:
		# Лист - создаем комнату позже
		return node

	var split_horizontally := false

	# Решаем, как делить – по большей стороне
	if region.size.x > region.size.y:
		split_horizontally = false
	elif region.size.y > region.size.x:
		split_horizontally = true
	else:
		split_horizontally = _rng.randi() % 2 == 0

	if split_horizontally:
		# Горизонтальный сплит (делим по Y)
		var min_split := region.position.y + min_room_size
		var max_split := region.position.y + region.size.y - min_room_size
		if max_split <= min_split:
			# Не можем разделить - это лист
			return node
		var split_y := _rng.randi_range(min_split, max_split)
		var top := Rect2i(region.position.x, region.position.y, region.size.x, split_y - region.position.y)
		var bottom := Rect2i(region.position.x, split_y, region.size.x, region.position.y + region.size.y - split_y)
		node.left = _split_space(top, depth + 1)
		node.right = _split_space(bottom, depth + 1)
	else:
		# Вертикальный сплит (делим по X)
		var min_split_x := region.position.x + min_room_size
		var max_split_x := region.position.x + region.size.x - min_room_size
		if min_split_x >= max_split_x:
			# Не можем разделить - это лист
			return node
		var split_x := _rng.randi_range(min_split_x, max_split_x)
		var left_rect := Rect2i(region.position.x, region.position.y, split_x - region.position.x, region.size.y)
		var right_rect := Rect2i(split_x, region.position.y, region.position.x + region.size.x - split_x, region.size.y)
		node.left = _split_space(left_rect, depth + 1)
		node.right = _split_space(right_rect, depth + 1)

	return node


# Создает комнаты во всех листах дерева
func _create_rooms_in_leaves(node: BSPNode) -> void:
	if node == null:
		return

	if node.is_leaf():
		node.room = _create_room_in_region(node.rect)
		if node.room.size.x > 0 and node.room.size.y > 0:
			_carve_room(node.room)
	else:
		_create_rooms_in_leaves(node.left)
		_create_rooms_in_leaves(node.right)


# Соединяет соседние листы дерева коридорами
func _connect_adjacent_leaves(node: BSPNode) -> void:
	if node == null or node.is_leaf():
		return

	# Рекурсивно соединяем детей
	_connect_adjacent_leaves(node.left)
	_connect_adjacent_leaves(node.right)

	# Соединяем левого и правого ребенка
	if node.left != null and node.right != null:
		var left_room := _find_room_in_node(node.left)
		var right_room := _find_room_in_node(node.right)

		if left_room.size.x > 0 and right_room.size.x > 0:
			_connect_rooms_with_corridor(left_room, right_room)


# Находит комнату в узле (рекурсивно для внутренних узлов)
func _find_room_in_node(node: BSPNode) -> Rect2i:
	if node == null:
		return Rect2i()

	if node.is_leaf():
		return node.room

	# Для внутренних узлов берем комнату из любого листа
	var left_room := _find_room_in_node(node.left)
	if left_room.size.x > 0:
		return left_room

	return _find_room_in_node(node.right)


# Создает комнату внутри региона
func _create_room_in_region(region: Rect2i) -> Rect2i:
	# Генерим случайный размер комнаты внутри региона
	var room_width := _rng.randi_range(min_room_size, min(max_room_size, region.size.x - 2))
	var room_height := _rng.randi_range(min_room_size, min(max_room_size, region.size.y - 2))

	if room_width <= 0 or room_height <= 0:
		return Rect2i(0, 0, 0, 0)

	var room_x := _rng.randi_range(region.position.x + 1, region.position.x + region.size.x - room_width - 1)
	var room_y := _rng.randi_range(region.position.y + 1, region.position.y + region.size.y - room_height - 1)

	return Rect2i(room_x, room_y, room_width, room_height)


# Рисует пол в комнате
func _carve_room(room: Rect2i) -> void:
	for y in range(room.position.y, room.position.y + room.size.y):
		for x in range(room.position.x, room.position.x + room.size.x):
			set_cell(0, Vector2i(x, y), SOURCE_ID_FLOOR, TILE_FLOOR)


# Соединяет две комнаты коридором (всегда L-образный)
func _connect_rooms_with_corridor(room_a: Rect2i, room_b: Rect2i) -> void:
	# Центры комнат
	var center_a := Vector2i(
		room_a.position.x + (room_a.size.x / 2) as int,
		room_a.position.y + (room_a.size.y / 2) as int
	)
	var center_b := Vector2i(
		room_b.position.x + (room_b.size.x / 2) as int,
		room_b.position.y + (room_b.size.y / 2) as int
	)

	# Всегда делаем L-образный коридор: сначала горизонтально, потом вертикально
	_carve_h_corridor(center_a.x, center_b.x, center_a.y)
	_carve_v_corridor(center_a.y, center_b.y, center_b.x)


# Рисует горизонтальный коридор (пол)
func _carve_h_corridor(x1: int, x2: int, y: int) -> void:
	var x_start: int = min(x1, x2) as int
	var x_end: int = max(x1, x2) as int
	for x in range(x_start, x_end + 1):
		if _get_tile_type(Vector2i(x, y)) == TileType.EMPTY:
			set_cell(0, Vector2i(x, y), SOURCE_ID_FLOOR, TILE_FLOOR)


# Рисует вертикальный коридор (пол)
func _carve_v_corridor(y1: int, y2: int, x: int) -> void:
	var y_start: int = min(y1, y2) as int
	var y_end: int = max(y1, y2) as int
	for y in range(y_start, y_end + 1):
		if _get_tile_type(Vector2i(x, y)) == TileType.EMPTY:
			set_cell(0, Vector2i(x, y), SOURCE_ID_FLOOR, TILE_FLOOR)


# Пост-проход для построения стен с autotiling
func _build_walls_with_autotiling() -> void:
	# Первый проход: ставим стены там, где EMPTY и рядом есть FLOOR
	for y in range(map_height_tiles):
		for x in range(map_width_tiles):
			var pos := Vector2i(x, y)
			var tile_type := _get_tile_type(pos)

			if tile_type == TileType.EMPTY:
				# Проверяем, есть ли рядом пол
				if _has_floor_neighbor(pos):
					set_cell(0, pos, SOURCE_ID_WALL, TILE_WALL_BASE)

	# Второй проход: применяем autotiling для всех стен
	for y in range(map_height_tiles):
		for x in range(map_width_tiles):
			var pos := Vector2i(x, y)
			if _get_tile_type(pos) == TileType.WALL:
				var wall_tile := _get_autotile_wall(pos)
				set_cell(0, pos, SOURCE_ID_WALL, wall_tile)

	# Третий проход: удаляем стены, которые не граничат с полом
	for y in range(map_height_tiles):
		for x in range(map_width_tiles):
			var pos := Vector2i(x, y)
			if _get_tile_type(pos) == TileType.WALL:
				if not _has_floor_neighbor(pos):
					set_cell(0, pos, -1)  # Удаляем тайл


# Проверяет, есть ли пол среди соседей (N, S, E, W)
func _has_floor_neighbor(pos: Vector2i) -> bool:
	var neighbors := [
		Vector2i(pos.x, pos.y - 1),  # N
		Vector2i(pos.x, pos.y + 1),  # S
		Vector2i(pos.x + 1, pos.y),  # E
		Vector2i(pos.x - 1, pos.y)   # W
	]

	for neighbor in neighbors:
		if _get_tile_type(neighbor) == TileType.FLOOR:
			return true
	return true
# Основные ориентации стен
const TILE_WALL_TOP := Vector2i(0, 3)
const TILE_WALL_BOTTOM := Vector2i(0, 4)
const TILE_WALL_LEFT := Vector2i(3, 1)
const TILE_WALL_RIGHT := Vector2i(4, 1)

# Для коридоров
const TILE_WALL_HORIZONTAL := Vector2i(5, 1)
const TILE_WALL_VERTICAL := Vector2i(2, 2)

# Углы (TL / TR / BL / BR)
const TILE_WALL_CORNER_TL := Vector2i(6, 0)
const TILE_WALL_CORNER_TR := Vector2i(7, 0)
const TILE_WALL_CORNER_BL := Vector2i(6, 1)
const TILE_WALL_CORNER_BR := Vector2i(7, 1)


func _get_tile_type(pos: Vector2i) -> int:
	# Возвращает TileType для позиции на TileMap (позволяет _get_autotile_wall работать)
	if pos.x < 0 or pos.y < 0 or pos.x >= map_width_tiles or pos.y >= map_height_tiles:
		return TileType.EMPTY
	var src := get_cell_source_id(0, pos)
	if src == -1:
		return TileType.EMPTY
	if src == SOURCE_ID_FLOOR:
		return TileType.FLOOR
	return TileType.WALL

func _get_autotile_wall(pos: Vector2i) -> Vector2i:
	var has_n := _get_tile_type(Vector2i(pos.x, pos.y - 1)) == TileType.FLOOR
	var has_s := _get_tile_type(Vector2i(pos.x, pos.y + 1)) == TileType.FLOOR
	var has_e := _get_tile_type(Vector2i(pos.x + 1, pos.y)) == TileType.FLOOR
	var has_w := _get_tile_type(Vector2i(pos.x - 1, pos.y)) == TileType.FLOOR

	var has_ne := _get_tile_type(Vector2i(pos.x + 1, pos.y - 1)) == TileType.FLOOR
	var has_nw := _get_tile_type(Vector2i(pos.x - 1, pos.y - 1)) == TileType.FLOOR
	var has_se := _get_tile_type(Vector2i(pos.x + 1, pos.y + 1)) == TileType.FLOOR
	var has_sw := _get_tile_type(Vector2i(pos.x - 1, pos.y + 1)) == TileType.FLOOR

	# Приоритет: углы -> горизонт/вертикаль -> базовый
	if has_n and has_w and not has_nw:
		return TILE_WALL_CORNER_TL
	if has_n and has_e and not has_ne:
		return TILE_WALL_CORNER_TR
	if has_s and has_w and not has_sw:
		return TILE_WALL_CORNER_BL
	if has_s and has_e and not has_se:
		return TILE_WALL_CORNER_BR

	# Горизонтальные (пол сверху/снизу)
	if has_n or has_s:
		return TILE_WALL_HORIZONTAL

	# Вертикальные (пол слева/справа)
	if has_e or has_w:
		return TILE_WALL_VERTICAL

	# По умолчанию — базовый тайл
	return TILE_WALL_BASE

# Дополнительно: проверка, проходим ли тайл
func is_walkable_tile(tile_pos: Vector2i) -> bool:
	return _get_tile_type(tile_pos) == TileType.FLOOR
