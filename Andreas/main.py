import pygame
import sys
import os
import json
from typing import List

from town import draw_town, update_town
import town  # funktioniert schon

pygame.init()

# ---------------------------------------------------
# PATHS
# ---------------------------------------------------
BASE_PATH = os.path.abspath(os.path.dirname(__file__))
SAVE_ROOT = os.path.join(BASE_PATH, "save")
SAVE_SLOTS = ["save1", "save2", "save3"]
ASSET_ICON_PATH = os.path.join(BASE_PATH, "assets", "icons")

# ---------------------------------------------------
# WINDOW
# ---------------------------------------------------
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game")

clock = pygame.time.Clock()

# ---------------------------------------------------
# FONTS
# ---------------------------------------------------
FONT_BIG = pygame.font.Font(None, 70)
FONT = pygame.font.Font(None, 40)
FONT_SMALL = pygame.font.Font(None, 26)

# ---------------------------------------------------
# CLASS ICON PATHS
# ---------------------------------------------------
CLASS_ICONS = {
    "warrior": os.path.join(ASSET_ICON_PATH, "warrior.png"),
    "mage": os.path.join(ASSET_ICON_PATH, "mage.png"),
    "rogue": os.path.join(ASSET_ICON_PATH, "rogue.png"),
    "paladin": os.path.join(ASSET_ICON_PATH, "paladin.png"),
}


# ---------------------------------------------------
# BUTTON
# ---------------------------------------------------
class Button:
    def __init__(self, text, x, y, w, h, callback):
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)
        self.callback = callback
        self.is_pressed = False

    def draw(self, surface):
        mouse = pygame.mouse.get_pos()

        color = (120, 120, 120) if self.rect.collidepoint(mouse) else (80, 80, 80)
        pygame.draw.rect(surface, color, self.rect, border_radius=10)

        txt = FONT.render(self.text, True, (255, 255, 255))
        surface.blit(txt, (self.rect.centerx - txt.get_width() // 2,
                           self.rect.centery - txt.get_height() // 2))

    def handle_event(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.rect.collidepoint(ev.pos):
                self.is_pressed = True

        if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            if self.is_pressed and self.rect.collidepoint(ev.pos):
                self.callback()
            self.is_pressed = False


# ---------------------------------------------------
# LOAD ICON
# ---------------------------------------------------
def load_icon_for_class(class_id):
    path = CLASS_ICONS.get(class_id, None)
    if not path or not os.path.exists(path):
        surf = pygame.Surface((64, 64))
        surf.fill((150, 150, 150))
        return surf

    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.smoothscale(img, (64, 64))


# ---------------------------------------------------
# LOAD HEROES FROM SLOT
# ---------------------------------------------------
def load_heroes_from_save_slot(slot_path) -> List[dict]:
    heroes_dir = os.path.join(slot_path, "heroes")

    if not os.path.exists(heroes_dir):
        return []

    heroes = []
    for file in sorted(os.listdir(heroes_dir)):
        if file.endswith(".json"):
            with open(os.path.join(heroes_dir, file), "r") as f:
                hero = json.load(f)

            hero["name"] = hero.get("name", "Unknown")
            hero["level"] = hero.get("level", 1)
            hero["class_id"] = hero.get("class_id", "warrior")
            hero["icon_surf"] = load_icon_for_class(hero["class_id"])

            heroes.append(hero)

    return heroes[:4]


# ---------------------------------------------------
# CREATE LOAD MENU
# ---------------------------------------------------
def create_load_menu():
    buttons = []
    data = []

    x = 100
    y = 150
    width = 700
    height = 140
    spacing = 160

    for i, slot in enumerate(SAVE_SLOTS):
        slot_path = os.path.join(SAVE_ROOT, slot)
        heroes = load_heroes_from_save_slot(slot_path)
        data.append(heroes)

        def make_cb(index=i):
            return lambda: enter_town(index)

        btn = Button(f"{i+1}.", x, y + i * spacing, width, height, make_cb())
        buttons.append(btn)

    return buttons, data


# ---------------------------------------------------
# DRAW SINGLE SAVE SLOT
# ---------------------------------------------------
def draw_save_slot(surface, btn, heroes):
    r = btn.rect

    pygame.draw.rect(surface, (60, 60, 60), r, border_radius=10)
    pygame.draw.rect(surface, (30, 30, 30), (r.x + 6, r.y + 6, r.width - 12, r.height - 12), border_radius=8)

    # slot number
    surface.blit(FONT.render(btn.text, True, (200, 200, 200)), (r.x + 10, r.y + 10))

    if not heroes:
        surface.blit(FONT.render("Keine Helden vorhanden", True, (180, 180, 180)), (r.x + 80, r.y + 40))
        return

    offset_y = r.y + 10
    for hero in heroes:
        surface.blit(hero["icon_surf"], (r.x + 70, offset_y))

        name_txt = FONT.render(hero["name"], True, (255, 255, 255))
        lvl_txt = FONT_SMALL.render(f"Level {hero['level']}", True, (200, 200, 200))

        surface.blit(name_txt, (r.x + 150, offset_y + 5))
        surface.blit(lvl_txt, (r.x + 150, offset_y + 45))

        offset_y += 70


# ---------------------------------------------------
# SCREENS
# ---------------------------------------------------
current_screen = "main_menu"


def enter_town(slot_index):
    global current_screen
    current_screen = "town"


# MAIN MENU BUTTONS
def main_menu_buttons():
    x = WIDTH // 2 - 150
    w = 300
    h = 60
    start_y = 180
    gap = 90

    def go_load():
        global current_screen, load_buttons, save_slots_data
        load_buttons, save_slots_data = create_load_menu()
        current_screen = "load_menu"

    return [
        Button("Spiel starten", x, start_y + gap * 0, w, h, lambda: enter_town(-1)),
        Button("Spiel laden", x, start_y + gap * 1, w, h, go_load),
        Button("Optionen", x, start_y + gap * 2, w, h, lambda: None),
        Button("Beenden", x, start_y + gap * 3, w, h, lambda: sys.exit())
    ]


main_buttons = main_menu_buttons()
load_buttons, save_slots_data = create_load_menu()


# ---------------------------------------------------
# RENDER FUNCTIONS
# ---------------------------------------------------
def draw_main_menu(surface, events):
    surface.fill((30, 30, 30))

    title = FONT_BIG.render("Hauptmenü", True, (255, 255, 255))
    surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

    for btn in main_buttons:
        btn.draw(surface)
        for ev in events:
            btn.handle_event(ev)


def draw_load_menu(surface, events):
    surface.fill((25, 25, 25))

    title = FONT_BIG.render("Spielstand laden", True, (255, 255, 255))
    surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))

    for i, btn in enumerate(load_buttons):
        btn.draw(surface)
        draw_save_slot(surface, btn, save_slots_data[i])
        for ev in events:
            btn.handle_event(ev)


# ---------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------
while True:
    events = pygame.event.get()

    for ev in events:
        if ev.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    if current_screen == "main_menu":
        draw_main_menu(screen, events)

    elif current_screen == "load_menu":
        draw_load_menu(screen, events)

    elif current_screen == "town":
        draw_town(screen)
        update_town(events)

    pygame.display.flip()
    clock.tick(60)
