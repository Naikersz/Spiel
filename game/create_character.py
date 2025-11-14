class Player:
    def __init__(self, name, strength, intelligence, charisma, gold=0):
        self.name = name
        self.strength = strength
        self.intelligence = intelligence
        self.charisma = charisma
        self.hp = 10 + strength  # сила влияет на здоровье
        self.gold = gold

    def show_stats(self):
        full_dot = '●'
        empty_dot = '○'

        def bar(value):
            return full_dot * value + empty_dot * (10 - value)

        print(f"\n{self.name}")
        print(f"STR {bar(self.strength)}")
        print(f"INT {bar(self.intelligence)}")
        print(f"CHA {bar(self.charisma)}")
        print(f"HP: {self.hp}, Gold: {self.gold}\n")


def create_character(name, strength, intelligence, charisma):
    # проверки на корректность
    if not isinstance(name, str):
        return "The character name should be a string"
    if len(name) > 10:
        return "The character name is too long"
    if any(c.isspace() for c in name):
        return "The character name should not contain spaces"
    if not all(isinstance(stat, int) for stat in (strength, intelligence, charisma)):
        return "All stats should be integers"
    if strength < 1 or intelligence < 1 or charisma < 1:
        return "All stats should be no less than 1"
    if strength > 4 or intelligence > 4 or charisma > 4:
        return "All stats should be no more than 4"
    if strength + intelligence + charisma != 7:
        return "The character should start with 7 points"

    # создание экземпляра класса Player
    player = Player(name, strength, intelligence, charisma)
    return player


# === Пример работы ===
if __name__ == "__main__":
    name = input("Enter character name: ").capitalize()
    strength = int(input("Strength (1-4): "))
    intelligence = int(input("Intelligence (1-4): "))
    charisma = int(input("Charisma (1-4): "))

    result = create_character(name, strength, intelligence, charisma)

    if isinstance(result, Player):
        result.show_stats()
    else:
        print("❌", result)

"""full_dot = '●'
empty_dot = '○'
def create_character(name,strength,intelligence,charisma):
    if not isinstance(name, str):
        return "The character name should be a string"
    if len(name) > 10:
        return "The character name is too long"
    if any(c.isspace() for c in name):
        return "The character name should not contain spaces"
    if not all(isinstance(stat, int) for stat in (strength,intelligence, charisma)):
        return "All stats should be integers"
    if strength < 1 or intelligence < 1 or charisma < 1:
        return "All stats should be no less than 1"
    if strength > 4 or intelligence > 4 or charisma > 4:
        return "All stats should be no more than 4"
    if strength+intelligence+charisma != 7:
        return "The character should start with 7 points"
    def stat_bar(value):
        return "●" * value + "○" * (10 - value)
    return f"{name}\nSTR {stat_bar(strength)}\nINT {stat_bar(intelligence)}\nCHA {stat_bar(charisma)}"
name = input().capitalize()
strength = int(input())
intelligence = int(input())
charisma = int(input())    
print(create_character(name,strength,intelligence,charisma))"""