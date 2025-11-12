"""
Roguelike Game
creat player with stats and random inventory from armor.json and weapons.json 
"""
import json
with open('armor.json', 'r', encoding='utf-8') as f:
    armor = json.load(f)
with open('game/weapons.json', 'r', encoding='utf-8') as w:
    weapons = json.load(w)


#test print (armor)
print("Armor items:")