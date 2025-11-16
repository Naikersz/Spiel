import os
import json
from datetime import datetime
from hero_system.hero_loader import load_hero_class, load_item_data, save_hero, calculate_total_stats


def create_hero(class_id, name, data_dir, base_path):
    """Erstellt einen neuen Helden basierend auf der Klassendatei."""
    hero_class = load_hero_class(class_id, data_dir)
    if not hero_class:
        raise ValueError(f"❌ Unbekannte Klasse: {class_id}")

    # Basiswerte übernehmen
    base_stats = {
        "health": hero_class["base_health"],
        "strength": hero_class["base_strength"],
        "intelligence": hero_class["base_intelligence"],
        "dexterity": hero_class["base_dexterity"],
        "speed": hero_class["base_speed"],
        "level": 1,
        "experience": 0
    }

    # Heldengerüst
    hero = {
        "name": name,
        "class_id": class_id,
        "class_name": hero_class["name"],
        "created_at": datetime.now().isoformat(),
        "stats": base_stats,
        "equipped": {  # jeder Held hat Ausrüstungsplätze, aber KEIN eigenes Inventar
            "weapon": None,
            "helmet": None,
            "chest": None,
            "pants": None,
            "gloves": None,
            "boots": None,
            "shield": None
        }
    }

    # Startausrüstung: aus Klassendefinition (immer Minimalwerte)
    hero["equipped"] = _assign_starter_gear(hero_class, data_dir)

    # Berechne endgültige Werte
    hero = calculate_total_stats(hero)

    # Speichern
    save_hero(hero, base_path)
    print(f"✅ Neuer Held erstellt und gespeichert: {hero['name']} ({hero['class_name']})")
    return hero


def _assign_starter_gear(hero_class, data_dir):
    """Lädt die Startitems aus den JSON-Dateien der Klasse mit Minimalwerten."""
    equipped = {
        "weapon": None,
        "helmet": None,
        "chest": None,
        "pants": None,
        "gloves": None,
        "boots": None,
        "shield": None
    }

    for item_name in hero_class.get("starter_items", []):
        item_data = load_item_data(item_name, data_dir)
        if not item_data:
            print(f"⚠️ Startitem nicht gefunden: {item_name}")
            continue

        # Minimalwerte nehmen
        item_copy = {**item_data}
        for key, val in item_copy.items():
            if isinstance(val, dict) and "min" in val and "max" in val:
                item_copy[key] = val["min"]

        # Slot erkennen und zuweisen
        slot = _detect_slot(item_name)
        if slot:
            equipped[slot] = item_copy

    return equipped


def _detect_slot(item_name):
    name = item_name.lower()
    if "sword" in name or "staff" in name or "dagger" in name:
        return "weapon"
    if "helm" in name or "hat" in name:
        return "helmet"
    if "chest" in name or "armor" in name or "robe" in name:
        return "chest"
    if "pants" in name or "legs" in name:
        return "pants"
    if "glove" in name:
        return "gloves"
    if "boots" in name or "shoe" in name:
        return "boots"
    if "shield" in name:
        return "shield"
    return None
