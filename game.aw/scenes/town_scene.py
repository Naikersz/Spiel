import pygame
from ui.button import Button
from ui.fonts import FONT
from core.constants import WIDTH, HEIGHT



class TownScene:
    def __init__(self, slot_index):
        self.slot_index = slot_index
        self.buttons = []
        self.create_buttons()

        try:
            self.TOWN_BG = pygame.image.load("assets/town/background.png")
        except:
            self.TOWN_BG = None

    # --------------------------------------------------------
    # Buttons erzeugen
    # --------------------------------------------------------
    def create_buttons(self):
        w, h = 220, 60
        x = WIDTH - w - 40
        start_y = 150
        gap = 80

        self.buttons = [
            Button("Inventar",      x, start_y + gap * 0, w, h, self.inventory),
            Button("Schmied",       x, start_y + gap * 1, w, h, self.smith),
            Button("Shop",          x, start_y + gap * 2, w, h, self.shop),
            Button("Kampf",         x, start_y + gap * 3, w, h, self.fight),
            Button("Spiel beenden", x, start_y + gap * 4, w, h, self.exit_to_menu)
        ]

    # --------------------------------------------------------
    # Button-Callbacks
    # --------------------------------------------------------
    def inventory(self):
        from scenes.inventory_scene import InventoryScene

        return InventoryScene(self.slot_index)

    def smith(self):
        print("🛠 Schmied geöffnet!")

    def shop(self):
        print("🛒 Shop geöffnet!")

    def fight(self):
        print("⚔️ Kampf gestartet!")
        from scenes.level_selection_scene import LevelSelectionScene
        return LevelSelectionScene(self.slot_index)

    def exit_to_menu(self):
        print("⬅ Zurück zum Hauptmenü")
        from scenes.main_menu import MainMenu   # <- WICHTIG: Import hier, nicht oben!
        return MainMenu()
    # <<--- Szenenwechsel

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
        if self.TOWN_BG:
            screen.blit(self.TOWN_BG, (0, 0))
        else:
            screen.fill((80, 120, 80))

        title = FONT.render("Town", True, (255, 255, 255))
        screen.blit(title, (40, 40))

        for btn in self.buttons:
            btn.draw(screen)
