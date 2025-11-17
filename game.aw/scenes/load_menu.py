import os
import json
import pygame

from ui.button import Button
from core.constants import SAVE_SLOTS, SAVE_ROOT, WIDTH
from ui.fonts import FONT, FONT_BIG, FONT_SMALL
from scenes.town_scene import TownScene


class LoadMenu:
    def __init__(self):
        # SAVE_ROOT sicherstellen
        os.makedirs(SAVE_ROOT, exist_ok=True)

        self.buttons = []
        self.slots_data = []

        self.build_menu()   # <-- direkt bauen

    # ------------------------------------------------------------------
    # Player-JSON laden
    # ------------------------------------------------------------------
    def load_player_data(self, slot_path):
        player_path = os.path.join(slot_path, "player.json")
        if not os.path.exists(player_path):
            return None

        try:
            with open(player_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return None

        return {
            "name": data.get("name", "Unbekannt"),
            "level": data.get("level", 1),
            "class_name": data.get("class_name", "???")
        }

    # ------------------------------------------------------------------
    # Neues Save erstellen
    # ------------------------------------------------------------------
    def create_new_save(self, slot_index):
        slot_dir = os.path.join(SAVE_ROOT, SAVE_SLOTS[slot_index])
        os.makedirs(slot_dir, exist_ok=True)

        player = {
            "name": "Neuer Held",
            "class_id": "warrior",
            "class_name": "Krieger",
            "level": 1,
            "experience": 0
        }

        with open(os.path.join(slot_dir, "player.json"), "w", encoding="utf-8") as f:
            json.dump(player, f, indent=4)

        print(f"🆕 Neuer Spielstand erstellt in Slot {slot_index+1}")

        # nach Erstellen neu aufbauen!
        self.build_menu()

        return TownScene(slot_index)

    # ------------------------------------------------------------------
    # Menü neu bauen (immer vollständig)
    # ------------------------------------------------------------------
    def build_menu(self):
        self.buttons = []
        self.slots_data = []

        x = 100
        y = 150
        width = 700
        height = 140
        spacing = 160

        for i, slot in enumerate(SAVE_SLOTS):
            slot_path = os.path.join(SAVE_ROOT, slot)

            os.makedirs(slot_path, exist_ok=True)   # <-- sicherstellen

            pdata = self.load_player_data(slot_path)
            self.slots_data.append(pdata)

            # Wenn Save vorhanden → laden
            if pdata:
                def make_load_cb(index=i):
                    return lambda: TownScene(index)
                callback = make_load_cb()
                text = f"{i+1}. Spiel laden"

            # Wenn kein Save → neues Spiel
            else:
                def make_new_cb(index=i):
                    return lambda: self.create_new_save(index)
                callback = make_new_cb()
                text = "Neues Spiel starten"

            btn = Button(text, x, y + i * spacing, width, height, callback)
            self.buttons.append(btn)

    # ------------------------------------------------------------------
    def update(self, events):
        for ev in events:
            for btn in self.buttons:
                res = btn.handle_event(ev)
                if res:
                    return res

    # ------------------------------------------------------------------
    def draw_slot(self, screen, btn, pdata):
        r = btn.rect

        pygame.draw.rect(screen, (60, 60, 60), r, border_radius=10)
        pygame.draw.rect(
            screen,
            (30, 30, 30),
            (r.x + 6, r.y + 6, r.width - 12, r.height - 12),
            border_radius=8
        )

        # Button text
        text_surf = FONT.render(btn.text, True, (255, 255, 255))
        screen.blit(text_surf, (r.centerx - text_surf.get_width() // 2, r.y + 15))

        if pdata is None:
            return

        # Save-Infos
        name_txt = FONT.render(pdata["name"], True, (255, 255, 255))
        lvl_txt = FONT_SMALL.render(
            f"Level {pdata['level']} – {pdata['class_name']}",
            True,
            (200, 200, 200)
        )

        screen.blit(name_txt, (r.x + 80, r.y + 60))
        screen.blit(lvl_txt, (r.x + 80, r.y + 100))

    # ------------------------------------------------------------------
    def draw(self, screen):
        screen.fill((25, 25, 25))

        title = FONT_BIG.render("Spielstand laden", True, (255, 255, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))

        for i, btn in enumerate(self.buttons):
            btn.draw(screen)
            self.draw_slot(screen, btn, self.slots_data[i])
