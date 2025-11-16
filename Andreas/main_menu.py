import sys
import pygame
from ui.button import Button
from ui.fonts import FONT_BIG
from core.constants import WIDTH
from scenes.load_menu import LoadMenu
from scenes.town_scene import TownScene
import os
import json
from core.constants import SAVE_ROOT, SAVE_SLOTS


def any_save_exists():
    for slot in SAVE_SLOTS:
        player_path = os.path.join(SAVE_ROOT, slot, "player.json")
        if os.path.exists(player_path):
            return True
    return False

class MainMenu:
    def __init__(self):
        x = WIDTH // 2 - 150
        w = 300
        h = 60
        start_y = 180
        gap = 90

        if any_save_exists():
            # Mindestens 1 Save vorhanden → echtes Lade-Menü
            self.buttons = [
                Button("Spielstand laden", x, start_y + gap * 0, w, h, self.load_game),
                Button("Optionen",         x, start_y + gap * 1, w, h, self.options),
                Button("Beenden",          x, start_y + gap * 2, w, h, self.quit_game),
            ]

        else:
            # Keine Saves → neuer Button
            self.buttons = [
                Button("Neues Spiel starten", x, start_y + gap * 0, w, h, self.start_new_game),
                Button("Optionen",            x, start_y + gap * 1, w, h, self.options),
                Button("Beenden",             x, start_y + gap * 2, w, h, self.quit_game),
            ]

    # ---------------- CALLBACKS ---------------- #

    def start_new_game(self):
        import os, json
        from core.constants import SAVE_ROOT, SAVE_SLOTS
        from scenes.town_scene import TownScene

        slot_path = os.path.join(SAVE_ROOT, SAVE_SLOTS[0])
        os.makedirs(slot_path, exist_ok=True)

        player = {
            "name": "Neuer Held",
            "class_id": "warrior",
            "class_name": "Krieger",
            "level": 1,
            "experience": 0
        }

        with open(os.path.join(slot_path, "player.json"), "w", encoding="utf-8") as f:
            json.dump(player, f, indent=4)

        print("🆕 Neues Spiel gestartet in Slot 1!")

        return TownScene(0)

    # -----------------------------------------------------------------
    def load_game(self):
        from scenes.load_menu import LoadMenu
        return LoadMenu()

    # -----------------------------------------------------------------
    def options(self):
        print("⚙ Optionen (noch nicht implementiert)")

    # -----------------------------------------------------------------
    def quit_game(self):
        pygame.quit()
        sys.exit()

    # -----------------------------------------------------------------
    def update(self, events):
        for e in events:
            for b in self.buttons:
                result = b.handle_event(e)
                if result:
                    return result

    def draw(self, screen):
        screen.fill((30, 30, 30))
        title = FONT_BIG.render("Hauptmenü", True, (255, 255, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

        for b in self.buttons:
            b.draw(screen)
