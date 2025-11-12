"""
Roguelike Game
creat player with stats and random inventory from armor.json and weapons.json 
"""
# import pygame
import json
from hero_classes import Warrior, Mage, Rogue

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Daten laden
armor_data = load_json('game/armor.json')
weapons_data = load_json('game/weapons.json')

def create_player(name, player_class):
    # Spielerklasse erzeugen
    if player_class == "Warrior":
        player = Warrior(name)
    elif player_class == "Mage":
        player = Mage(name)
    elif player_class == "Rogue":
        player = Rogue(name)
    else:
        raise ValueError("Invalid player class")

    # Waffen-Daten einfügen
    new_weapons = []
    for w in player.inventory.get('weapons', []):
        weapon_stats = weapons_data["weapons"].get(w)
        if weapon_stats:
            new_weapons.append(weapon_stats)
        else:
            new_weapons.append({"name": w, "error": "not found"})
    player.inventory["weapons"] = new_weapons

    # Rüstungs-Daten einfügen
    new_armor = []
    for a in player.inventory.get('armor', []):
        armor_stats = armor_data["armor"].get(a)
        if armor_stats:
            new_armor.append(armor_stats)
        else:
            new_armor.append({"name": a, "error": "not found"})
    player.inventory["armor"] = new_armor

    return player


def save_player_to_json(player):
    # Alle Attribute in ein Dictionary umwandeln
    player_data = {
        "name": player.name,
        "class": player.__class__.__name__,
        "stats": {
            "strength": player.strength,
            "dexterity": player.dexterity,
            "intelligence": player.intelligence,
            "health": player.health,
            "mana": player.mana,
            "defense": player.defense
        },
        "inventory": player.inventory
    }

    file_name = f"player_{player.name.lower()}.json"
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(player_data, f, indent=4, ensure_ascii=False)

    print(f"✅ Spieler '{player.name}' gespeichert unter '{file_name}'")
    return player_data


# Beispiel: Warrior erstellen, anzeigen und speichern
player1 = create_player("Conan", "Warrior")

# Ausgabe der Daten
print(json.dumps(save_player_to_json(player1), indent=4, ensure_ascii=False))
#looks up player inventory details



# with open('game/armor.json', 'r', encoding='utf-8') as f:
#     armor = json.load(f)
# with open('game/weapons.json', 'r', encoding='utf-8') as w:
#     weapons = json.load(w)

# def create_player(name, player_class):
#     player = {
#         'name': name,
#         'class': player_class,
#         'stats': {
#             'strength': 10,
#             'dexterity': 10,
#             'intelligence': 10,
#             'constitution': 10
#         },
#         'inventory': {
#             'armor': [],
#             'weapons': []
#         }
#     }
#     # Add random armor and weapon to inventory
#     import random
#     player['inventory']['armor'].append(random.choice(list(armor['armor'].values())))
#     player['inventory']['weapons'].append(random.choice(list(weapons['weapons'].values())))
#     return player

# print(create_player("Hero", "Warrior"))

# #push player to players.json
# with open('game/players.json', 'r+', encoding='utf-8') as p:
#     players = json.load(p)
#     players.append(create_player("Hero", "Warrior"))
#     p.seek(0)
#     json.dump(players, p, indent=4)

# #test print (1 armor) from armor.json
# # print(*armor['armor'].values(), sep='\n')



# # #if abfrage ob players.json nicht leer ist
# # if "game/players.json":

# # #test print (erster player) from players.json mit armor und weapon ohne values
# #     with open('game/players.json', 'r', encoding='utf-8') as p:
# #         players = json.load(p)
# #         print(players[0])