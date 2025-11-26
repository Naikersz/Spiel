extends Node2D

## normal_room_enemy_spawner.gd
## Генерирует врагов внутри NormalRoom1 с использованием EnemyGenerator.gd

const EnemyGeneratorScript := preload("res://Skripts/enemy_generator.gd")

@export var field_number: int = 1

@onready var tilemap_layer: TileMapLayer = $TileMap/TileMapLayer

var enemy_generator: Node = null


func _ready() -> void:
	enemy_generator = EnemyGeneratorScript.new()
	var enemies_data: Array = enemy_generator.generate_field_enemies(field_number)
	_spawn_enemies(enemies_data)


func _spawn_enemies(enemies_data: Array) -> void:
	if tilemap_layer == null:
		push_warning("normal_room_enemy_spawner: TileMapLayer nicht gefunden, spawne um (0,0)")
		for i in range(enemies_data.size()):
			var pos := Vector2(randf_range(-50, 50), randf_range(-50, 50))
			_create_enemy_visual(pos, enemies_data[i])
		return

	var used_rect: Rect2i = tilemap_layer.get_used_rect()

	for enemy_data in enemies_data:
		var tries := 50
		var world_pos := Vector2.ZERO
		var found := false

		while tries > 0 and not found:
			var cx := randi_range(used_rect.position.x, used_rect.position.x + used_rect.size.x - 1)
			var cy := randi_range(used_rect.position.y, used_rect.position.y + used_rect.size.y - 1)
			var cell := Vector2i(cx, cy)
			if _is_floor_cell(cell):
				world_pos = tilemap_layer.map_to_local(cell)
				found = true
			tries -= 1

		if not found:
			world_pos = Vector2.ZERO

		_create_enemy_visual(world_pos, enemy_data)


func _is_floor_cell(cell: Vector2i) -> bool:
	if tilemap_layer == null:
		return false

	# Muss ein Tile sein
	if tilemap_layer.get_cell_source_id(cell) == -1:
		return false

	# Floor-Heuristik: Tile + alle 4 Nachbarn sind ebenfalls Tiles
	var dirs := [
		Vector2i(1, 0),
		Vector2i(-1, 0),
		Vector2i(0, 1),
		Vector2i(0, -1),
	]
	for d in dirs:
		var n: Vector2i = cell + d
		if tilemap_layer.get_cell_source_id(n) == -1:
			return false

	return true


func _create_enemy_visual(pos: Vector2, enemy_data: Dictionary) -> void:
	var enemy := Node2D.new()
	enemy.name = String(enemy_data.get("name", "Enemy"))
	enemy.position = pos
	enemy.z_index = 5
	add_child(enemy)

	# Roter Punkt
	var marker := ColorRect.new()
	marker.color = Color(1, 0, 0, 0.9)
	marker.size = Vector2(10, 10)
	marker.position = Vector2(-5, -5)
	enemy.add_child(marker)

	# HP-Balken basierend auf Stats
	var stats: Dictionary = enemy_data.get("final_stats", enemy_data.get("generated_stats", {}))
	var max_hp := int(stats.get("max_hp", stats.get("hp", 10)))
	var hp := int(stats.get("hp", max_hp))
	var hp_ratio := 1.0
	if max_hp > 0:
		hp_ratio = clamp(float(hp) / float(max_hp), 0.0, 1.0)

	var bar_bg := ColorRect.new()
	bar_bg.color = Color(0.1, 0.1, 0.1, 0.9)
	bar_bg.size = Vector2(18, 4)
	bar_bg.position = Vector2(-9, -11)
	enemy.add_child(bar_bg)

	var bar_fg := ColorRect.new()
	bar_fg.color = Color(0, 1, 0, 0.9)
	bar_fg.size = Vector2(18 * hp_ratio, 4)
	bar_fg.position = Vector2(-9, -11)
	enemy.add_child(bar_fg)
