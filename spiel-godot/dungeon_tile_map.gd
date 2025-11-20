extends TileMap
"""
DungeonTileMap.gd
Простая BSP генерация подземелья:
- рекурсивное деление области на прямоугольники
- выбор комнаты в каждом листе
- соединение комнат коридорами
"""

const TILE_FLOOR := 1   # ID тайла пола в TileSet (поставь свой)
const TILE_WALL  := 0   # ID тайла стены в TileSet (поставь свой)

@export var map_width_tiles: int = 100      # ширина карты в тайлах
@export var map_height_tiles: int = 100     # высота карты в тайлах
@export var min_room_size: int = 6          # минимальная комната (в тайлах)
@export var max_room_size: int = 14         # максимальная комната
@export var max_depth: int = 5              # глубина BSP

var _rooms: Array[Rect2i] = []              # конечные комнаты
var _rng := RandomNumberGenerator.new()

func _ready() -> void:
	_rng.randomize()
	# Можно сразу генерить при старте, или вызывать из LevelTown
	# generate_dungeon()


func generate_dungeon() -> void:
	clear()
	_rooms.clear()

	# Заполняем всё стенами
	for y in range(map_height_tiles):
		for x in range(map_width_tiles):
			set_cell(0, Vector2i(x, y), TILE_WALL)

	# Начальный прямоугольник для BSP
	var root_rect := Rect2i(0, 0, map_width_tiles, map_height_tiles)
	_split_space(root_rect, 0)

	# Рисуем комнаты
	for room in _rooms:
		_carve_room(room)

	# Соединяем комнаты коридорами (просто по порядку)
	for i in range(1, _rooms.size()):
		var room_a := _rooms[i - 1]
		var room_b := _rooms[i]
		_connect_rooms(room_a, room_b)


func _split_space(region: Rect2i, depth: int) -> void:
	if depth >= max_depth:
		# Дальше не делим – создаём комнату внутри этого региона
		var room := _create_room_in_region(region)
		if room:
			_rooms.append(room)
		return

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
			var room := _create_room_in_region(region)
			if room:
				_rooms.append(room)
			return
		var split_y := _rng.randi_range(min_split, max_split)
		var top := Rect2i(region.position.x, region.position.y, region.size.x, split_y - region.position.y)
		var bottom := Rect2i(region.position.x, split_y, region.size.x, region.position.y + region.size.y - split_y)
		_split_space(top, depth + 1)
		_split_space(bottom, depth + 1)
	else:
		# Вертикальный сплит (делим по X)
		var min_split_x := region.position.x + min_room_size
		var max_split_x := region.position.x + region.size.x - min_room_size
		if max_split_x <= min_split_x:
			var room2 := _create_room_in_region(region)
			if room2:
				_rooms.append(room2)
			return
		var split_x := _rng.randi_range(min_split_x, max_split_x)
		var left := Rect2i(region.position.x, region.position.y, split_x - region.position.x, region.size.y)
		var right := Rect2i(split_x, region.position.y, region.position.x + region.size.x - split_x, region.size.y)
		_split_space(left, depth + 1)
		_split_space(right, depth + 1)


func _create_room_in_region(region: Rect2i) -> Rect2i:
	# Генерим случайный размер комнаты внутри региона
	var room_width := _rng.randi_range(min_room_size, min(max_room_size, region.size.x - 2))
	var room_height := _rng.randi_range(min_room_size, min(max_room_size, region.size.y - 2))

	if room_width <= 0 or room_height <= 0:
		return Rect2i(0, 0, 0, 0)

	var room_x := _rng.randi_range(region.position.x + 1, region.position.x + region.size.x - room_width - 1)
	var room_y := _rng.randi_range(region.position.y + 1, region.position.y + region.size.y - room_height - 1)

	return Rect2i(room_x, room_y, room_width, room_height)


func _carve_room(room: Rect2i) -> void:
	for y in range(room.position.y, room.position.y + room.size.y):
		for x in range(room.position.x, room.position.x + room.size.x):
			set_cell(0, Vector2i(x, y), TILE_FLOOR)


func _connect_rooms(room_a: Rect2i, room_b: Rect2i) -> void:
	# Центры комнат
	var center_a := Vector2i(
		room_a.position.x + room_a.size.x / 2,
		room_a.position.y + room_a.size.y / 2
	)
	var center_b := Vector2i(
		room_b.position.x + room_b.size.x / 2,
		room_b.position.y + room_b.size.y / 2
	)

	# Простой "Г"-образный коридор
	if _rng.randi() % 2 == 0:
		_carve_h_corridor(center_a.x, center_b.x, center_a.y)
		_carve_v_corridor(center_a.y, center_b.y, center_b.x)
	else:
		_carve_v_corridor(center_a.y, center_b.y, center_a.x)
		_carve_h_corridor(center_a.x, center_b.x, center_b.y)


func _carve_h_corridor(x1: int, x2: int, y: int) -> void:
	for x in range(min(x1, x2), max(x1, x2) + 1):
		set_cell(0, Vector2i(x, y), TILE_FLOOR)


func _carve_v_corridor(y1: int, y2: int, x: int) -> void:
	for y in range(min(y1, y2), max(y1, y2) + 1):
		set_cell(0, Vector2i(x, y), TILE_FLOOR)


# Дополнительно: проверка, проходим ли тайл
func is_walkable_tile(tile_pos: Vector2i) -> bool:
	var tile_id := get_cell_source_id(0, tile_pos)
	return tile_id == TILE_FLOOR
