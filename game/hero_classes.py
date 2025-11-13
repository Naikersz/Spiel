class Warrior():
    def __init__(self, name):
        self.name = name
        self.strength = 3
        self.dexterity = 2
        self.intelligence = 1
        self.health = 100 + self.strength * 5
        self.mana = 30 + self.intelligence * 2
        self.defense = 8 + self.dexterity * 2
        self.inventory = {
            'weapons': ['sword_iron'],
            'armor': ['chainmail'],
        }
        
class Mage():
    def __init__(self, name):
        self.name = name
        self.strength = 1
        self.dexterity = 2
        self.intelligence = 3
        self.health = 70 + self.strength * 3
        self.mana = 100 + self.intelligence * 5
        self.defense = 3 + self.dexterity * 2
        self.inventory = {
            'weapons': ['staff_wooden'],
            'armor': ['cloth_robe'],
        }
        
class Rogue():
    def __init__(self, name):
        self.name = name
        self.strength = 2
        self.dexterity = 3
        self.intelligence = 1
        self.health = 80 + self.strength * 4
        self.mana = 50 + self.intelligence * 3
        self.defense = 5 + self.dexterity * 2
        self.inventory = {
            'weapons': ['dagger'],
            'armor': ['leather_armor'],
        }


