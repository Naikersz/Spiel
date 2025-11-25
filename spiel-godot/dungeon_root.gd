extends Node2D

# ========== НАСТРОЙКИ ==========
@export var map_width_tiles: int = 60
@export var map_height_tiles: int = 40
@export var min_room_size: int = 6
@export var max_room_size: int = 12
@export var max_depth: int = 8

# ========== ССЫЛКИ НА TileMapLayer (ВАЖНО: НЕ TileMap!) ==========
@onready var floor_layer: TileMapLayer = $TileMapFloor/FloorLayer
@onready var wall_layer: TileMapLayer = $TileMapFloor/WallLayer
@onready var top_layer: TileMapLayer = $TileMapFloor/TopLayer  

# ========== ВНУТРЕННЯЯ КАРТА ==========
enum TileType { EMPTY, FLOOR, WALL }
var _grid: Array = []
var _rng := RandomNumberGenerator.new()

# ---------- BSP УЗЕЛ ----------
class BSPNode:
	var rect: Rect2i
	var left: BSPNode = null
	var right: BSPNode = null
	var room: Rect2i = Rect2i()

	func is_leaf() -> bool:
		return left == null and right == null

var _bsp_root: BSPNode = null


func _ready():
	_rng.randomize()
	generate_dungeon()


# ---------- ГЛАВНАЯ ----------
func generate_dungeon():
	_make_empty_grid()

	var root_rect := Rect2i(0, 0, map_width_tiles, map_height_tiles)
	_bsp_root = _split_space(root_rect, 0)

	_create_rooms_in_leaves(_bsp_root)
	_connect_adjacent_leaves(_bsp_root)

	_create_walls_around_floor()
	_apply_grid_to_layers()


# ---------- СОЗДАНИЕ ПУСТОЙ СЕТКИ ----------

func _make_empty_grid() -> void:
	_grid.clear()
	for y in map_height_tiles:
		var row: Array = []
		for x in map_width_tiles:
			row.append(TileType.EMPTY)
		_grid.append(row)

# ---------- BSP РАЗБИЕНИЕ ----------

func _split_space(region: Rect2i, depth: int) -> BSPNode:
	var node := BSPNode.new()
	node.rect = region

	if depth >= max_depth:
		return node

	var split_horizontally: bool

	if region.size.x > region.size.y:
		split_horizontally = false
	elif region.size.y > region.size.x:
		split_horizontally = true
	else:
		split_horizontally = _rng.randi() % 2 == 0

	if split_horizontally:
		var min_split := region.position.y + min_room_size
		var max_split := region.position.y + region.size.y - min_room_size
		if max_split <= min_split:
			return node
		var split_y := _rng.randi_range(min_split, max_split)

		var top := Rect2i(region.position.x, region.position.y,
				region.size.x, split_y - region.position.y)
		var bottom := Rect2i(region.position.x, split_y,
				region.size.x, region.position.y + region.size.y - split_y)

		node.left = _split_space(top, depth + 1)
		node.right = _split_space(bottom, depth + 1)
	else:
		var min_split_x := region.position.x + min_room_size
		var max_split_x := region.size.x + region.position.x - min_room_size
		if min_split_x >= max_split_x:
			return node

		var split_x := _rng.randi_range(min_split_x, max_split_x)

		var left_rect := Rect2i(region.position.x, region.position.y,
				split_x - region.position.x, region.size.y)
		var right_rect := Rect2i(split_x, region.position.y,
				region.position.x + region.size.x - split_x, region.size.y)

		node.left = _split_space(left_rect, depth + 1)
		node.right = _split_space(right_rect, depth + 1)

	return node

# ---------- КОМНАТЫ В ЛИСТЬЯХ ----------

func _create_rooms_in_leaves(node: BSPNode) -> void:
	if node == null:
		return

	if node.is_leaf():
		node.room = _create_room_in_region(node.rect)
		# DEBUG: смотрим, какие комнаты вообще создаются
		if node.room.size.x > 0 and node.room.size.y > 0:
			print("ROOM:", node.room)
			_carve_room(node.room)
	else:
		_create_rooms_in_leaves(node.left)
		_create_rooms_in_leaves(node.right)

func _create_room_in_region(region: Rect2i) -> Rect2i:
	var room_width := _rng.randi_range(
		min_room_size,
		min(max_room_size, region.size.x - 2)
	)
	var room_height := _rng.randi_range(
		min_room_size,
		min(max_room_size, region.size.y - 2)
	)

	if room_width <= 0 or room_height <= 0:
		return Rect2i(0, 0, 0, 0)

	var room_x := _rng.randi_range(
		region.position.x + 1,
		region.position.x + region.size.x - room_width - 1
	)
	var room_y := _rng.randi_range(
		region.position.y + 1,
		region.position.y + region.size.y - room_height - 1
	)

	return Rect2i(room_x, room_y, room_width, room_height)

func _carve_room(room: Rect2i) -> void:
	for y in range(room.position.y, room.position.y + room.size.y):
		for x in range(room.position.x, room.position.x + room.size.x):
			_set_grid(Vector2i(x, y), TileType.FLOOR)

# ---------- КОРИДОРЫ МЕЖДУ КОМНАТАМИ ----------

func _connect_adjacent_leaves(node: BSPNode) -> void:
	if node == null or node.is_leaf():
		return

	_connect_adjacent_leaves(node.left)
	_connect_adjacent_leaves(node.right)

	if node.left != null and node.right != null:
		var left_room := _find_room_in_node(node.left)
		var right_room := _find_room_in_node(node.right)

		if left_room.size.x > 0 and right_room.size.x > 0:
			_connect_rooms_with_corridor(left_room, right_room)

func _find_room_in_node(node: BSPNode) -> Rect2i:
	if node == null:
		return Rect2i()

	if node.is_leaf():
		return node.room

	var left_room := _find_room_in_node(node.left)
	if left_room.size.x > 0:
		return left_room

	return _find_room_in_node(node.right)

func _connect_rooms_with_corridor(room_a: Rect2i, room_b: Rect2i) -> void:
	var center_a := Vector2i(
		room_a.position.x + room_a.size.x / 2,
		room_a.position.y + room_a.size.y / 2
	)
	var center_b := Vector2i(
		room_b.position.x + room_b.size.x / 2,
		room_b.position.y + room_b.size.y / 2
	)

	_carve_h_corridor(center_a.x, center_b.x, center_a.y)
	_carve_v_corridor(center_a.y, center_b.y, center_b.x)

func _carve_h_corridor(x1: int, x2: int, y: int) -> void:
	var x_start: int = min(x1, x2)
	var x_end: int = max(x1, x2)

	for x in range(x_start, x_end + 1):
		_set_grid(Vector2i(x, y), TileType.FLOOR)
		_set_grid(Vector2i(x, y + 1), TileType.FLOOR) # ← расширяем вниз

func _carve_v_corridor(y1: int, y2: int, x: int) -> void:
	var y_start: int = min(y1, y2)
	var y_end: int = max(y1, y2)

	for y in range(y_start, y_end + 1):
		_set_grid(Vector2i(x, y), TileType.FLOOR)
		_set_grid(Vector2i(x + 1, y), TileType.FLOOR) # ← расширяем вправо

# ---------- СОЗДАЁМ СТЕНЫ ВОКРУГ ПОЛА ----------

func _create_walls_around_floor() -> void:
	var new_walls: Array[Vector2i] = []
	
	# Проходим ТОЛЬКО по клеткам с полом
	for y in map_height_tiles:
		for x in map_width_tiles:
			var pos := Vector2i(x, y)
			if _get_grid(pos) != TileType.FLOOR:
				continue
				
			# Проверяем 8 соседей
			for dy in [-1, 0, 1]:
				for dx in [-1, 0, 1]:
					if dx == 0 and dy == 0:
						continue
					var neighbor := pos + Vector2i(dx, dy)
					
					# Если сосед за пределами или EMPTY → это место для стены
					if !_is_in_bounds(neighbor) or _get_grid(neighbor) == TileType.EMPTY:
						# Но только если там ещё НЕ пол и НЕ стена (на всякий случай)
						if _get_grid(neighbor) != TileType.FLOOR:
							new_walls.append(neighbor)
	
	# Теперь ОДНИМ проходом ставим все стены
	for wall_pos in new_walls:
		_set_grid(wall_pos, TileType.WALL)
	
	# Опционально: рамка по краям
	for x in map_width_tiles:
		if _get_grid(Vector2i(x, 0)) != TileType.FLOOR:
			_set_grid(Vector2i(x, 0), TileType.WALL)
		if _get_grid(Vector2i(x, map_height_tiles - 1)) != TileType.FLOOR:
			_set_grid(Vector2i(x, map_height_tiles - 1), TileType.WALL)
	for y in map_height_tiles:
		if _get_grid(Vector2i(0, y)) != TileType.FLOOR:
			_set_grid(Vector2i(0, y), TileType.WALL)
		if _get_grid(Vector2i(map_width_tiles - 1, y)) != TileType.FLOOR:
			_set_grid(Vector2i(map_width_tiles - 1, y), TileType.WALL)
			
func _is_in_bounds(pos: Vector2i) -> bool:
	return pos.x >= 0 && pos.y >= 0 && pos.x < map_width_tiles && pos.y < map_height_tiles
	
func _count_neighbors(pos: Vector2i) -> int:
	var dirs = [
		Vector2i(1, 0),
		Vector2i(-1, 0),
		Vector2i(0, 1),
		Vector2i(0, -1)
	]

	var c := 0
	for d in dirs:
		var t := _get_grid(pos + d)
		if t == TileType.FLOOR or t == TileType.WALL:
			c += 1

	return c

func _set_grid(pos: Vector2i, t: int) -> void:
	if pos.x < 0 or pos.y < 0 or pos.x >= map_width_tiles or pos.y >= map_height_tiles:
		return
	_grid[pos.y][pos.x] = t

func _get_grid(pos: Vector2i) -> int:
	if pos.x < 0 or pos.y < 0 or pos.x >= map_width_tiles or pos.y >= map_height_tiles:
		return TileType.EMPTY
	return _grid[pos.y][pos.x]

func _has_neighbor(pos: Vector2i, t: int) -> bool:
	var neighbors := [
		Vector2i(pos.x, pos.y - 1),
		Vector2i(pos.x, pos.y + 1),
		Vector2i(pos.x + 1, pos.y),
		Vector2i(pos.x - 1, pos.y)
	]
	for n in neighbors:
		if _get_grid(n) == t:
			return true
	return false
	
# ---------- РАСКЛАДКА ПО 3 УРОВНЯМ ----------
func _apply_grid_to_layers():
	floor_layer.clear()
	wall_layer.clear()
	top_layer.clear()
	
	var floor_cells: Array[Vector2i] = []
	var wall_cells: Array[Vector2i] = []
	
	for y in map_height_tiles:
		for x in map_width_tiles:
			var pos := Vector2i(x, y)
			match _get_grid(pos):
				TileType.FLOOR:
					floor_cells.append(pos)
				TileType.WALL:
					wall_cells.append(pos)
	
	# Пол
	if not floor_cells.is_empty():
		floor_layer.set_cells_terrain_connect(floor_cells, 0, 1)
	
	# Стены снизу
	if not wall_cells.is_empty():
		wall_layer.set_cells_terrain_connect(wall_cells, 0, 0)
	
	# Бортики сверху стен
	_build_walltops()

# ========== БОРТИКИ — ГЛАВНАЯ МАГИЯ 3D ==========
func _build_walltops():
	var top_cells: Array[Vector2i] = []
	
	# Проходим по всем стенам
	for pos in wall_layer.get_used_cells():
		var above := pos + Vector2i(0, -1)
		
		# Если сверху от стены — НЕ стена (пол или пустота)
		if wall_layer.get_cell_source_id(above) == -1:
			top_cells.append(pos)  # бортик в той же клетке!
	
	# Автотейлинг бортиков
	if not top_cells.is_empty():
		top_layer.set_cells_terrain_connect(top_cells, 0, 2)
