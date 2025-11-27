extends Node2D

const EnemyGeneratorScript := preload("res://core/enemy_generator.gd")

var dungeon: Node2D = null        # Node mit dungeon_root.gd
var player: CharacterBody2D = null
var hp_bar: ProgressBar = null
var rotate_button: Button = null
var pause_menu: Control = null
var pause_resume_button: Button = null
var pause_exit_button: Button = null

var enemy_generator: Node = null
var enemies: Array = []


func _ready():
	# Gegner-Generator initialisieren
	enemy_generator = EnemyGeneratorScript.new()

	# Referenzen sicher holen (können in verschiedenen Szenen unterschiedlich sein)
	dungeon = get_node_or_null("DungeonTileMap")
	player = get_node_or_null("Player")
	hp_bar = get_node_or_null("Camera2D/CanvasLayer/UI/HPBar")
	rotate_button = get_node_or_null("Camera2D/CanvasLayer/UI/RotateButton")
	pause_menu = get_node_or_null("Camera2D/CanvasLayer/PauseMenu")
	if pause_menu:
		pause_resume_button = pause_menu.get_node_or_null("VBoxContainer/ResumeButton")
		pause_exit_button = pause_menu.get_node_or_null("VBoxContainer/ExitButton")

	# Отладочная информация
	if not dungeon:
		print("Warning: DungeonTileMap (Dungeon) not found in scene")
	if not player:
		print("Warning: Player not found in scene")
	if not hp_bar:
		print("Warning: HPBar not found in scene")
	if not pause_menu:
		print("Warning: PauseMenu not found in scene")

	# Проверяем, что кнопка существует перед подключением сигнала
	if rotate_button:
		rotate_button.pressed.connect(_on_rotate_pressed)
		print("RotateButton connected successfully")
	else:
		print("Warning: RotateButton not found in scene - path: Camera2D/CanvasLayer/UI/RotateButton")

	# Pause-Menü Buttons verbinden
	if pause_resume_button:
		pause_resume_button.pressed.connect(_on_pause_resume_pressed)
	if pause_exit_button:
		pause_exit_button.pressed.connect(_on_pause_exit_pressed)

	# Pause-Menü standardmäßig verstecken
	if pause_menu:
		pause_menu.visible = false

	# Spieler + Gegner im Dungeon platzieren
	_spawn_player_in_first_room()
	_spawn_enemies_in_dungeon()


func _update_hp_bar():
	# Проверяем, что hp_bar существует
	if hp_bar:
		# временно
		hp_bar.value = 100


func _on_rotate_pressed():
	# Проверяем, что dungeon существует перед поворотом
	if dungeon:
		dungeon.rotation_degrees += 90


func _physics_process(_delta):
	# Движение обрабатывается в Player.gd, здесь только обновляем UI
	_update_hp_bar()


func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_ESCAPE:
			_toggle_pause_menu()


func _toggle_pause_menu() -> void:
	if not pause_menu:
		return
	pause_menu.visible = not pause_menu.visible
	# Optional: Wenn du wirklich pausieren willst, diese Zeile wieder aktivieren:
	# get_tree().paused = pause_menu.visible


## (A) Spieler im ersten begehbaren Raum platzieren
func _spawn_player_in_first_room() -> void:
	if dungeon == null or player == null:
		return

	for y in range(dungeon.map_height_tiles):
		for x in range(dungeon.map_width_tiles):
			if dungeon.is_walkable_tile(Vector2i(x, y)):
				var world_pos = dungeon.map_to_local(Vector2i(x, y))
				player.global_position = world_pos
				return


## (C) Gegner mit Hilfe des Generators im Dungeon spawnen
func _spawn_enemies_in_dungeon() -> void:
	if dungeon == null or enemy_generator == null:
		return

	# Platzhalter-Player-Stats (kann später aus Save/Constants geladen werden)
	var player_stats: Dictionary = {
		"damage": 10,
		"defense": 5,
		"level": 1
	}

	enemies.clear()
	enemies = enemy_generator.generate_enemies_for_dungeon(dungeon, player_stats, 5)

	for enemy_data in enemies:
		var pos: Vector2 = enemy_data.get("world_pos", Vector2.ZERO)

		# Sehr einfache Visualisierung: ein farbiger Marker im Dungeon
		var marker := Node2D.new()
		marker.position = pos
		add_child(marker)

		var debug_sprite := ColorRect.new()
		debug_sprite.color = Color(1, 0, 0, 0.7)  # halbtransparenter roter Block
		debug_sprite.size = Vector2(16, 16)
		debug_sprite.position = Vector2(-8, -8)
		marker.add_child(debug_sprite)


func _on_pause_resume_pressed() -> void:
	if pause_menu:
		pause_menu.visible = false
	get_tree().paused = false


func _on_pause_exit_pressed() -> void:
	# Spiel fortsetzen, bevor Szene gewechselt wird
	get_tree().paused = false
	print("Pause-Menü: Zurück zur Level-Auswahl")
	get_tree().call_deferred("change_scene_to_file", "res://scenes/level_selection_scene.tscn")
