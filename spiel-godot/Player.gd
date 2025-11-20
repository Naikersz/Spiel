"""
Player.gd - Управление персонажем с поддержкой одежды

ИНСТРУКЦИЯ ПО ДОБАВЛЕНИЮ ОДЕЖДЫ:
================================

1. В Godot Editor:
   - Откройте сцену main.tscn
   - Найдите узел Player/Graphics
   - Добавьте AnimatedSprite2D узлы для каждой части одежды с именами:
     * HatLeather (или Hat) - шляпа
     * LeatherArmor (или Armor) - торс/броня
     * Gloves - перчатки
     * Pants - штаны
     * Boots - ботинки
     * Mantal - наплечники
     * Cuffs - манжеты

2. Настройте SpriteFrames для каждого узла:
   - В Inspector выберите SpriteFrames
   - Создайте анимации с именами:
     * idle_down, idle_up, idle_left, idle_right
     * walk_down, walk_up, walk_left, walk_right
   - Добавьте фреймы для каждой анимации

3. Клавиши для экипировки (временно):
   - Клавиша 1 - Hat/Hut (шляпа)
   - Клавиша 2 - Leather Armor (торс)
   - Клавиша 3 - Gloves (перчатки)
   - Клавиша 4 - Pants (штаны)
   - Клавиша 5 - Boots (ботинки)
   - Клавиша 6 - Mantal (наплечники)
   - Клавиша 7 - Cuffs (манжеты)

ГДЕ ИЗМЕНИТЬ НАСТРОЙКИ:
=======================
- Имена узлов одежды: функция _initialize_clothing() (строки 33-48)
- Обработка клавиш: функция _unhandled_input() (строки 76-93)
- Добавление новых частей одежды: добавьте в _initialize_clothing() и _play_animation()
"""

extends CharacterBody2D

@onready var graphics = $Graphics
@onready var body_anim: AnimatedSprite2D = $Graphics/Body
@onready var head_anim: AnimatedSprite2D = $Graphics/Head

# Части одежды (кожаная из pygame игры) - опциональные узлы
var hat_anim: AnimatedSprite2D = null           # 1 - Hat/Hut (шляпа)
var leather_armor_anim: AnimatedSprite2D = null # 2 - Leather Armor (торс)
var gloves_anim: AnimatedSprite2D = null        # 3 - Gloves (перчатки)
var pants_anim: AnimatedSprite2D = null         # 4 - Pants/Hose (штаны)
var boots_anim: AnimatedSprite2D = null         # 5 - Boots (ботинки)
var mantal_anim: AnimatedSprite2D = null        # 6 - Mantal (наплечники/плечи)
var cuffs_anim: AnimatedSprite2D = null         # 7 - Cuffs (манжеты/запястья)

# Словарь для быстрого доступа к одежде
var clothing_items: Dictionary = {}

var speed: float = 200.0

# Направление: "down", "up", "left", "right"
var facing: String = "down"
# Последнее направление движения (сохраняется для idle)
var last_facing: String = "down"

func _ready() -> void:
	# Инициализируем все части одежды
	_initialize_clothing()
	$Camera2D.make_current()
	
	# Инициализируем с idle анимацией
	_play_animation("idle", last_facing)

func _initialize_clothing() -> void:
	# Загружаем все части одежды (если они есть в сцене)
	# Порядок соответствует клавишам 1-7
	hat_anim = _get_clothing_node("Graphics/HatLeather")
	leather_armor_anim = _get_clothing_node("Graphics/ArmorLeather")
	gloves_anim = _get_clothing_node("Graphics/GlovesLeather")
	pants_anim = _get_clothing_node("Graphics/PantsLeather")
	boots_anim = _get_clothing_node("Graphics/BootsLeather")
	mantal_anim = _get_clothing_node("Graphics/MantalLeather")
	cuffs_anim = _get_clothing_node("Graphics/CuffsLeather")
	
	# Словарь для быстрого доступа по именам
	clothing_items = {
		"hat": hat_anim,
		"leather_armor": leather_armor_anim,
		"armor": leather_armor_anim,
		"gloves": gloves_anim,
		"pants": pants_anim,
		"boots": boots_anim,
		"mantal": mantal_anim,
		"cuffs": cuffs_anim
	}
	
	# Все части одежды по умолчанию скрыты
	for item_name in clothing_items:
		if clothing_items[item_name]:
			clothing_items[item_name].visible = false

func _get_clothing_node(path: String) -> AnimatedSprite2D:
	# Безопасно получаем узел одежды
	if has_node(path):
		var node = get_node(path)
		if node is AnimatedSprite2D:
			return node
	return null

func _unhandled_input(event: InputEvent) -> void:
	# Обработка клавиш 1-7 для временной экипировки одежды
	if event is InputEventKey and event.pressed:
		match event.keycode:
			KEY_1:
				toggle_clothing("hat")
			KEY_2:
				toggle_clothing("leather_armor")
			KEY_3:
				toggle_clothing("gloves")
			KEY_4:
				toggle_clothing("pants")
			KEY_5:
				toggle_clothing("boots")
			KEY_6:
				toggle_clothing("mantal")
			KEY_7:
				toggle_clothing("cuffs")

func _physics_process(delta: float) -> void:
	var input_vector := Vector2.ZERO

	if Input.is_action_pressed("move_right"):
		input_vector.x += 1
	if Input.is_action_pressed("move_left"):
		input_vector.x -= 1
	if Input.is_action_pressed("move_down"):
		input_vector.y += 1
	if Input.is_action_pressed("move_up"):
		input_vector.y -= 1

	if input_vector != Vector2.ZERO:
		input_vector = input_vector.normalized()
		velocity = input_vector * speed
		move_and_slide()
		
		# Обновляем направление при движении
		_update_facing(input_vector)
		last_facing = facing  # Сохраняем последнее направление
		_play_animation("walk", facing)
	else:
		velocity = Vector2.ZERO
		# Используем последнее направление для idle
		_play_animation("idle", last_facing)


func toggle_clothing(item_name: String) -> void:
	# Переключает видимость части одежды
	if item_name in clothing_items:
		var clothing = clothing_items[item_name]
		if clothing:
			clothing.visible = not clothing.visible
			# Обновляем анимацию для этого слоя
			var current_anim_type = "walk" if velocity != Vector2.ZERO else "idle"
			var anim_name = current_anim_type + "_" + last_facing
			_set_animation_on_sprite(clothing, anim_name, current_anim_type)
			print("Toggled ", item_name, ": ", clothing.visible)
		else:
			print("Warning: Clothing item '", item_name, "' not found in scene. Add it to Graphics node in scene.")
	else:
		print("Warning: Unknown clothing item: ", item_name)

func _update_facing(dir: Vector2) -> void:
	# Определяем направление по доминирующей оси движения
	# Если горизонтальное движение больше вертикального - приоритет горизонтали
	if abs(dir.x) > abs(dir.y):
		if dir.x > 0:
			facing = "right"
		else:
			facing = "left"
	else:
		# Вертикальное движение приоритетнее
		if dir.y > 0:
			facing = "down"
		else:
			facing = "up"

func _play_animation(anim_type: String, direction: String) -> void:
	# Формируем имя анимации: "idle_down", "walk_right" и т.д.
	var anim_name = anim_type + "_" + direction
	
	# Устанавливаем анимацию для всех слоев
	_set_animation_on_sprite(body_anim, anim_name, anim_type)
	_set_animation_on_sprite(head_anim, anim_name, anim_type)
	
	# Устанавливаем анимацию для всех видимых частей одежды
	if hat_anim and hat_anim.visible:
		_set_animation_on_sprite(hat_anim, anim_name, anim_type)
	if leather_armor_anim and leather_armor_anim.visible:
		_set_animation_on_sprite(leather_armor_anim, anim_name, anim_type)
	if gloves_anim and gloves_anim.visible:
		_set_animation_on_sprite(gloves_anim, anim_name, anim_type)
	if pants_anim and pants_anim.visible:
		_set_animation_on_sprite(pants_anim, anim_name, anim_type)
	if boots_anim and boots_anim.visible:
		_set_animation_on_sprite(boots_anim, anim_name, anim_type)
	if mantal_anim and mantal_anim.visible:
		_set_animation_on_sprite(mantal_anim, anim_name, anim_type)
	if cuffs_anim and cuffs_anim.visible:
		_set_animation_on_sprite(cuffs_anim, anim_name, anim_type)

func _set_animation_on_sprite(sprite: AnimatedSprite2D, anim_name: String, _fallback_anim: String = "") -> void:
	if not sprite or not sprite.sprite_frames:
		return
	
	# Есть ли такая анимация у этого слоя?
	if sprite.sprite_frames.has_animation(anim_name):
		if sprite.animation != anim_name:
			sprite.play(anim_name)
