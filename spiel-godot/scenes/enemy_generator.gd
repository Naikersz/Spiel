extends Node

## EnemyGenerator.gd
## GDScript-Port der Python-Klasse EnemyGenerator (game.aw/core/enemy_generator.py)
## Lädt Monster/Verzauberungen aus res://data und kann Gegner-Listen erzeugen.

const MONSTER_PATH := "res://data/monster.json"
const ENCHANT_PATH := "res://data/monster_enchantments.json"

var monsters: Array = []
var enchantments: Array = []
var rng := RandomNumberGenerator.new()


func _init() -> void:
	rng.randomize()
	monsters = _load_json_array(MONSTER_PATH)
	enchantments = _load_json_array(ENCHANT_PATH)


func _load_json_array(path: String) -> Array:
	var result: Array = []
	if not FileAccess.file_exists(path):
		push_warning("EnemyGenerator: Datei nicht gefunden: %s" % path)
		return result
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return result
	var txt := f.get_as_text()
	f.close()
	var json := JSON.new()
	if json.parse(txt) != OK:
		push_warning("EnemyGenerator: JSON Parse-Fehler in %s" % path)
		return result
	if json.data is Array:
		result = json.data
	return result


func _pick_monster_in_level_range(min_level: int, max_level: int) -> Dictionary:
	var candidates: Array = []
	for m in monsters:
		var lvl := int(m.get("level", 1))
		if lvl >= min_level and lvl <= max_level:
			candidates.append(m)
	if candidates.is_empty():
		candidates = monsters.duplicate()
	if candidates.is_empty():
		return {}
	return candidates[rng.randi_range(0, candidates.size() - 1)]


func _get_max_tier_for_level(monster_level: int) -> int:
	if monster_level <= 0:
		return 1
	return 1 + int((monster_level - 1) / 20)


func _randomize_stats(monster_data: Dictionary) -> Dictionary:
	var stats_data: Dictionary = monster_data.get("stats", {})
	var stats: Dictionary = {}

	var hp_min := int(stats_data.get("hp_min", 10))
	var hp_max := int(stats_data.get("hp_max", 20))
	var hp := rng.randi_range(hp_min, hp_max)
	stats["hp"] = hp
	stats["max_hp"] = hp

	var dmg_min := int(stats_data.get("damage_min", 1))
	var dmg_max := int(stats_data.get("damage_max", 5))
	stats["damage"] = rng.randi_range(dmg_min, dmg_max)

	var def_min := int(stats_data.get("defense_min", 0))
	var def_max := int(stats_data.get("defense_max", 5))
	stats["defense"] = rng.randi_range(def_min, def_max)

	var atk_spd_min := float(stats_data.get("attack_speed_min", 1.0))
	var atk_spd_max := float(stats_data.get("attack_speed_max", 2.0))
	stats["attack_speed"] = rng.randf_range(atk_spd_min, atk_spd_max)

	var eva_min := int(stats_data.get("evasion_min", 0))
	var eva_max := int(stats_data.get("evasion_max", 10))
	stats["evasion"] = rng.randi_range(eva_min, eva_max)

	return stats


func _get_available_enchantments(monster_level: int) -> Array:
	var available: Array = []
	for enchant in enchantments:
		var min_level := int(enchant.get("min_level", 1))
		if monster_level >= min_level:
			available.append(enchant)
	return available


func _select_random_enchantments(
	available_enchantments: Array,
	count: int,
	max_slots: int = 6,
	monster_level: int = 1
) -> Array:
	if available_enchantments.is_empty() or count <= 0:
		return []

	count = min(count, max_slots, available_enchantments.size())

	var pool := available_enchantments.duplicate()
	var selected: Array = []
	for i in range(count):
		if pool.is_empty():
			break
		var idx := rng.randi_range(0, pool.size() - 1)
		selected.append(pool[idx])
		pool.remove_at(idx)

	var result: Array = []
	var max_tier := _get_max_tier_for_level(monster_level)

	for enchant in selected:
		var value_min := int(enchant.get("value_min", 0))
		var value_max := int(enchant.get("value_max", value_min))
		var value := value_min
		if value_max > value_min:
			value = rng.randi_range(value_min, value_max)

		var rolled_tier := rng.randi_range(1, max_tier)
		var scaled_value := value * rolled_tier

		var enchant_copy: Dictionary = enchant.duplicate(true)
		enchant_copy["value"] = scaled_value
		enchant_copy["rolled_tier"] = rolled_tier
		result.append(enchant_copy)

	return result


func _apply_enchantments_to_stats(base_stats: Dictionary, enchantments_list: Array) -> Dictionary:
	# Stark vereinfachte Version: wendet nur direkten Schaden/Def-Bonus an.
	var final_stats: Dictionary = base_stats.duplicate(true)

	for enchant in enchantments_list:
		var t := String(enchant.get("type", ""))
		var v := float(enchant.get("value", 0))

		if t == "damage":
			final_stats["damage"] = final_stats.get("damage", 0) + v
		elif t == "res_physical":
			final_stats["defense"] = final_stats.get("defense", 0) + v
		# Erweiterbar für Prozentwerte usw.

	return final_stats


func generate_enemy(
	monster_id: String = "",
	enchantment_count: int = 0,
	min_level: int = -1,
	max_level: int = -1
) -> Dictionary:
	if monsters.is_empty():
		return {}

	var monster: Dictionary = {}

	if monster_id != "":
		for m in monsters:
			if String(m.get("id", "")) == monster_id:
				monster = m
				break
	if monster.is_empty():
		if min_level > 0 or max_level > 0:
			var min_lvl := (min_level if min_level > 0 else 1)
			var max_lvl := (max_level if max_level > 0 else 999)
			monster = _pick_monster_in_level_range(min_lvl, max_lvl)
		else:
			monster = monsters[rng.randi_range(0, monsters.size() - 1)]

	if monster.is_empty():
		return {}

	var enemy: Dictionary = monster.duplicate(true)

	var stats := _randomize_stats(monster)
	enemy["generated_stats"] = stats

	var ench: Array = []
	if enchantment_count > 0:
		var available := _get_available_enchantments(int(monster.get("level", 1)))
		var max_slots := int(monster.get("enchant_slots", 6))
		ench = _select_random_enchantments(
			available,
			enchantment_count,
			max_slots,
			int(monster.get("level", 1))
		)

	enemy["enchantments"] = ench
	enemy["final_stats"] = _apply_enchantments_to_stats(stats, ench)

	return enemy


func generate_field_enemies(field_number: int, config: Dictionary = {}) -> Array:
	var enemies: Array = []

	# Dev-Konfiguration
	if not config.is_empty():
		var enemy_count: int = max(1, int(config.get("enemy_count", 5)))
		var ench_min := int(config.get("enchantment_min", 0))
		var ench_max := int(config.get("enchantment_max", 0))
		var lvl_min := int(config.get("monster_level_min", 1))
		var lvl_max := int(config.get("monster_level_max", 100))

		if ench_max < ench_min:
			ench_max = ench_min

		for i in range(enemy_count):
			var enchant_count := 0
			if ench_max > 0:
				enchant_count = rng.randi_range(ench_min, ench_max)

			var e := generate_enemy("", enchant_count, lvl_min, lvl_max)
			if not e.is_empty():
				enemies.append(e)

		return enemies

	# Standard-Verhalten wie in Python
	if field_number == 1:
		for i in range(3):
			var e1 := generate_enemy("", 0)
			if not e1.is_empty():
				enemies.append(e1)

		var e2 := generate_enemy("", rng.randi_range(1, 3))
		if not e2.is_empty():
			enemies.append(e2)

		var e3 := generate_enemy("", rng.randi_range(4, 6))
		if not e3.is_empty():
			enemies.append(e3)
	else:
		for i in range(5):
			var e := generate_enemy("", 0)
			if not e.is_empty():
				enemies.append(e)

	return enemies
