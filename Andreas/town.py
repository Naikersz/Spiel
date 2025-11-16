# import pygame

# # Falls du globale Assets benötigst, kannst du sie hier laden
# try:
#     TOWN_BG = pygame.image.load("game.aw/assets/town/background.png")
# except:
#     TOWN_BG = None
#     print("⚠️ Town-Hintergrund nicht gefunden.")


# def draw_town(screen):
#     """Zeichnet die Town-Szene auf das Pygame-Fenster."""

#     if TOWN_BG:
#         screen.blit(TOWN_BG, (0, 0))
#     else:
#         screen.fill((80, 120, 80))  # Fallback-Farbe

#     # Beispiel: Gebäude anzeigen
#     # pygame.draw.rect(screen, (200, 200, 50), (100, 200, 200, 200))
#     # pygame.draw.rect(screen, (180, 80, 50), (400, 200, 200, 200))


# def update_town(events):
#     """Verarbeitet Klicks und Eingaben in der Town-Szene."""

#     for event in events:
#         if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
#             mx, my = pygame.mouse.get_pos()

#             # Beispiel: Klick auf Schmiede
#             # if pygame.Rect(100, 200, 200, 200).collidepoint(mx, my):
#             #     print("🛠 Betrete Schmiede")

#             # Beispiel: Klick auf Taverne
#             # if pygame.Rect(400, 200, 200, 200).collidepoint(mx, my):
#             #     print("🍺 Betrete Taverne")

""""""""""""

import pygame

# ------------------------------------------------------------
# Hintergrund laden (optional)
# ------------------------------------------------------------
try:
    TOWN_BG = pygame.image.load("game.aw/assets/town/background.png")
except:
    TOWN_BG = None
    print("⚠️ Town-Hintergrund nicht gefunden.")


# ------------------------------------------------------------
# Button-Unterstützung aus main.py importieren
# ------------------------------------------------------------
from main import Button, FONT, WIDTH, HEIGHT


# ------------------------------------------------------------
# Town Buttons (Inventar / Schmied / Shop / Kampf)
# ------------------------------------------------------------
town_buttons = []


def create_town_buttons():
    """Erzeugt die Buttons der Town-Szene."""
    global town_buttons
    town_buttons = []

    w, h = 220, 60
    x = WIDTH - w - 40
    start_y = 150
    gap = 80

    # -------- Button-Callbacks -------- #

    def open_inventory():
        print("📦 Inventar geöffnet!")

    def open_smith():
        print("🛠 Schmied geöffnet!")

    def open_shop():
        print("🛒 Shop geöffnet!")

    def start_fight():
        print("⚔️ Kampf gestartet!")

    # -------- Buttons erzeugen -------- #

    town_buttons.append(Button("Inventar", x, start_y + gap * 0, w, h, open_inventory))
    town_buttons.append(Button("Schmied",  x, start_y + gap * 1, w, h, open_smith))
    town_buttons.append(Button("Shop",     x, start_y + gap * 2, w, h, open_shop))
    town_buttons.append(Button("Kampf",    x, start_y + gap * 3, w, h, start_fight))


# ------------------------------------------------------------
# DRAW
# ------------------------------------------------------------
def draw_town(screen):
    """Zeichnet die Town-Szene und Buttons."""

    if TOWN_BG:
        screen.blit(TOWN_BG, (0, 0))
    else:
        screen.fill((80, 120, 80))  # Fallback-Hintergrund

    title = FONT.render("Town", True, (255, 255, 255))
    screen.blit(title, (40, 40))

    # Buttons zeichnen
    for btn in town_buttons:
        btn.draw(screen)


# ------------------------------------------------------------
# UPDATE
# ------------------------------------------------------------
def update_town(events):
    """Verarbeitet Button-Events."""
    for event in events:
        for btn in town_buttons:
            btn.handle_event(event)
