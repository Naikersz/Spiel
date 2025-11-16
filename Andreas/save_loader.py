import os
import json
import pygame

def load_heroes_from_save(save_dir):
    hero_dir = os.path.join(save_dir, "heroes")
    if not os.path.isdir(hero_dir):
        return []

    heroes = []
    for file in os.listdir(hero_dir):
        if file.endswith(".json"):
            path = os.path.join(hero_dir, file)
            with open(path, "r", encoding="utf-8") as f:
                hero = json.load(f)
                heroes.append(hero)

    return heroes[:4]  # Maximal 4 Helden

