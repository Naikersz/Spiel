"""
create player mit stats (name, Str, Vit, Int, Dex, Luk)
"""
def create_player(name, Str, Vit, Int, Dex, Luk):
    player = {
        "name": name,
        "Str": Str,
        "Vit": Vit,
        "Int": Int,
        "Dex": Dex,
        "Luk": Luk,
        "exp": 0,
        "level": 1,
        "HP": Vit * 10,
        "damage": Str * 2,
        "defense": Vit,
        "attack_speed": 1.0
    }
    return player

input_player = create_player("Hero", 5, 5, 3, 4, 2)

import json

with open('players.json', 'w') as f:
    json.dump([input_player], f)
    
secend_player = create_player("Warrior", 7, 6, 2, 3, 1)
with open('players.json', 'r') as f:
    players = json.load(f)
players.append(secend_player)
with open('players.json', 'w') as f:
    json.dump(players, f)
    
#print first players from json file
with open('players.json', 'r') as f:
    players = json.load(f)
print(players[0],"\n")
print(players[1])

"""
create add equipment function that increases player stats based on equipment stats
"""

def add_equipment(player, equipment):
    for stat, value in equipment.items():
        if stat in player:
            player[stat] += value
    # Recalculate HP, damage, defense after adding equipment
    player["HP"] = player["Vit"] * 10
    player["damage"] = player["Str"] * 2
    player["defense"] = player["Vit"]
    return player


chestplate = {"name": "leatherplate", "defense": 2}
shield = {"name": "woodenshield", "defense": 3}

print(players[0],"\n")
"""
create function that calulates player level based on exp points
create function that levels up player and increases stats accordingly

crate function that calculates player HP, damage, defance based on stats


create enemy mit stats (name, Str, Vit, Int, Dex, Luk)
crate a joson file to save upto 4 player and enemy stats

crate function attack(attacker, defender)
that calculates damage based on attacker's Str and defender's Vit
and reduces defender's HP accordingly.


"""