class Player:
    def __init__(self, name, strength, intelligence, charisma, gold):
        self.name = name
        self.strength = strength
        self.intelligence = intelligence
        self.charisma = charisma
        self.hp = 10 + strength  # сила влияет на здоровье
        self.gold = 0 + gold

    def show_stats(self):
        full_dot = '●'
        empty_dot = '○'
        def bar(value):
            return full_dot * value + empty_dot * (10 - value)
        print(f"\n{self.name}\nSTR {bar(self.strength)}\nINT {bar(self.intelligence)}\nCHA {bar(self.charisma)}")
        print(f"HP: {self.hp}, Gold: {self.gold}\n")
        
player = Player()        
player.show_stats()