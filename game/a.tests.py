"""
Roguelike Game
creat player with stats and random inventory from armor.json and weapons.json 
"""
import json

try:
    with open('armor.json', 'r', encoding='utf-8') as arm:
        arm.read()
        arm.close()
        except Exception as e:
#with open('game/weapons.json', 'r', encoding='utf-8') as w:
 #   weapons = json.load(w)


#test print (armor)