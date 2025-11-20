extends Node2D

@onready var dungeon := $DungeonTileMap
var tilemap: TileMap
var player: CharacterBody2D
var hp_bar: ProgressBar
var rotate_button: Button

func _ready():
# Получаем ссылки на узлы после того, как сцена полностью загружена
	tilemap = get_node_or_null("DungeonTileMap")
	player = get_node_or_null("Player")
	hp_bar = get_node_or_null("Camera2D/CanvasLayer/UI/HPBar")
	rotate_button = get_node_or_null("Camera2D/CanvasLayer/UI/RotateButton")
	
	# Отладочная информация
	if not tilemap:
		print("Warning: DungeonTileMap not found in scene")
	if not player:
		print("Warning: Player not found in scene")
	if not hp_bar:
		print("Warning: HPBar not found in scene")
	
	# Проверяем, что кнопка существует перед подключением сигнала
	if rotate_button:
		rotate_button.pressed.connect(_on_rotate_pressed)
		print("RotateButton connected successfully")
	else:
		print("Warning: RotateButton not found in scene - path: Camera2D/CanvasLayer/UI/RotateButton")

func _update_hp_bar():
	# Проверяем, что hp_bar существует
	if hp_bar:
		# временно
		hp_bar.value = 100

func _on_rotate_pressed():
	# Проверяем, что tilemap существует перед поворотом
	if tilemap:
		# пока просто поворот TileMap
		tilemap.rotation_degrees += 90

func _physics_process(delta):
	# Движение обрабатывается в Player.gd, здесь только обновляем UI
	_update_hp_bar()
func _spawn_player_in_first_room() -> void:
	for y in range(dungeon.map_height_tiles):
		for x in range(dungeon.map_width_tiles):
			if dungeon.is_walkable_tile(Vector2i(x, y)):
				var world_pos sssssssssssssss= dungeon.map_to_local(Vector2i(x, y))
				player.global_position = world_pos
				return
