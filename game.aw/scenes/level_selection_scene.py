import pygame
from ui.button import Button
from ui.fonts import FONT
from core.constants import WIDTH, HEIGHT


class LevelSelectionScene:
    def __init__(self, slot_index):
        self.slot_index = slot_index
        self.buttons = []
        self.create_buttons()

    # --------------------------------------------------------
    # Buttons erzeugen
    # --------------------------------------------------------
    def create_buttons(self):
        self.buttons = []

        w, h = 200, 50
        center_x = WIDTH // 2
        start_y = 180
        gap = 60

        # Feld 1–5 (linke Spalte)
        for i in range(1, 6):
            x = center_x - w - 40
            y = start_y + gap * (i - 1)
            self.buttons.append(
                Button(
                    f"Feld {i}",
                    x,
                    y,
                    w,
                    h,
                    lambda level=i: self.start_battle("Feld", level)
                )
            )

        # Cave 1–5 (rechte Spalte)
        for i in range(1, 6):
            x = center_x + 40
            y = start_y + gap * (i - 1)
            self.buttons.append(
                Button(
                    f"Cave {i}",
                    x,
                    y,
                    w,
                    h,
                    lambda level=i: self.start_battle("Cave", level)
                )
            )

        # Zurück-Button unten
        back_w, back_h = 180, 50
        back_x = WIDTH // 2 - back_w // 2
        back_y = start_y + gap * 5 + 20
        self.buttons.append(
            Button(
                "Zurück",
                back_x,
                back_y,
                back_w,
                back_h,
                self.back_to_town
            )
        )

    # --------------------------------------------------------
    # Button-Callbacks
    # --------------------------------------------------------
    def start_battle(self, level_type, level_number):
        print(f"⚔️ {level_type} {level_number} gestartet!")
        from scenes.battle_scene import BattleScene
        return BattleScene(self.slot_index, level_type, level_number)

    def back_to_town(self):
        print("⬅ Zurück zur Stadt")
        from scenes.town_scene import TownScene
        return TownScene(self.slot_index)

    # --------------------------------------------------------
    # Update
    # --------------------------------------------------------
    def update(self, events):
        for e in events:
            for btn in self.buttons:
                result = btn.handle_event(e)
                if result:
                    return result

    # --------------------------------------------------------
    # Draw
    # --------------------------------------------------------
    def draw(self, screen):
        screen.fill((40, 40, 60))

        # Titel
        title = FONT.render("Level Auswahl", True, (255, 255, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

        # Kategorien-Labels
        feld_label = FONT.render("Feld", True, (200, 255, 200))
        cave_label = FONT.render("Cave", True, (200, 200, 255))

        center_x = WIDTH // 2
        label_y = 120
        screen.blit(
            feld_label,
            (center_x - 200 - feld_label.get_width() // 2, label_y)
        )
        screen.blit(
            cave_label,
            (center_x + 200 - cave_label.get_width() // 2, label_y)
        )

        # Buttons zeichnen
        for btn in self.buttons:
            btn.draw(screen)
