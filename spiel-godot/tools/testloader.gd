extends Node2D

# Сцена игрока
@export var player_prefab: PackedScene = preload("res://levels/player.tscn")

# Уже существующий инстанс комнаты в дереве
@onready var room_root: Node2D = $NormalRoom

# Фолбэк позиция, если не найдём PlayerSpawn в комнате
@onready var fallback_spawn: Node2D = $PlayerSpawn   # сделай Marker2D с таким именем

func _ready():
	if room_root == null:
		push_error("❌ Не найдена нода NormalRoom в TestRunner!")
		return

	var spawn_pos := get_spawn_position(room_root)
	spawn_player(spawn_pos)


func get_spawn_position(room: Node2D) -> Vector2:
	# Пытаемся найти спавн внутри комнаты
	var s := room.get_node_or_null("PlayerSpawn")
	if s and s is Marker2D:
		return s.global_position

	# Иначе используем запасной спавн в TestRunner
	if fallback_spawn:
		return fallback_spawn.global_position

	push_warning("⚠ Нет PlayerSpawn и fallback_spawn, спавню в (0,0)")
	return Vector2.ZERO


func spawn_player(pos: Vector2) -> void:
	if not player_prefab:
		push_error("❌ player_prefab не задан")
		return

	var player = player_prefab.instantiate()
	add_child(player)
	player.global_position = pos
