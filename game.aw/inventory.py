import json
import os

class Inventory:
    def __init__(self, save_dir: str):
        self.save_dir = save_dir
        self.save_file = os.path.join(save_dir, "inventory.json")

        # falls der Speicherordner nicht existiert → erstellen
        os.makedirs(save_dir, exist_ok=True)

        # Inventar aus Datei laden oder leeres erstellen
        self.items = self.load_inventory()

    def load_inventory(self):
        """Lädt bestehendes Inventar aus Datei."""
        if os.path.exists(self.save_file):
            with open(self.save_file, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    print("⚠️  Fehler beim Laden der Inventardatei – neues Inventar wird erstellt.")
                    return []
        return []

    def save_inventory(self):
        """Speichert das aktuelle Inventar dauerhaft."""
        with open(self.save_file, "w", encoding="utf-8") as f:
            json.dump(self.items, f, indent=2, ensure_ascii=False)

    def add_items(self, new_items: list):
        """Fügt neue Items zum Inventar hinzu."""
        if not new_items:
            return
        for item in new_items:
            self.items.append(item)
        print(f"📦 {len(new_items)} neue Items ins Inventar aufgenommen.")
        self.save_inventory()

    def show_inventory(self):
        """Gibt den aktuellen Inventarinhalt aus."""
        if not self.items:
            print("🪶 Dein Inventar ist leer.")
            return

        print("🎒 Inventar:")
        for i, item in enumerate(self.items, start=1):
            print(f"  {i}. {item['name']} (Level {item['item_level']})")
            if item.get("enchantments"):
                for ench in item["enchantments"]:
                    print(f"     • {ench['name']} +{ench['value']} ({ench['type']})")
        print()
