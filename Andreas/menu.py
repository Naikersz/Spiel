import pygame
import sys

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mein Spiel")

FONT = pygame.font.Font(None, 48)

# Button-Klasse
class Button:
    def __init__(self, text, x, y, w, h, callback):
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)
        self.callback = callback
        self.base_color = (70, 70, 70)
        self.hover_color = (120, 120, 120)

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.base_color
        pygame.draw.rect(surface, color, self.rect, border_radius=12)

        text_surface = FONT.render(self.text, True, (255, 255, 255))
        surface.blit(
            text_surface,
            (self.rect.centerx - text_surface.get_width() // 2,
             self.rect.centery - text_surface.get_height() // 2)
        )

    def check_click(self):
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            if pygame.mouse.get_pressed()[0]:
                self.callback()


# --- Callback-Funktionen ---
def start_game():
    print("Neues Spiel wird gestartet...")

def load_game():
    print("Spielstand wird geladen...")

def open_options():
    print("Optionen werden geöffnet...")

def quit_game():
    pygame.quit()
    sys.exit()


# --- Buttons erstellen ---
button_width = 300
button_height = 60
x = WIDTH // 2 - button_width // 2
start_y = 200
gap = 80

buttons = [
    Button("Spiel starten", x, start_y + gap * 0, button_width, button_height, start_game),
    Button("Spiel laden",   x, start_y + gap * 1, button_width, button_height, load_game),
    Button("Optionen",      x, start_y + gap * 2, button_width, button_height, open_options),
    Button("Beenden",       x, start_y + gap * 3, button_width, button_height, quit_game),
]


# -----------------------------
# Hauptloop
# -----------------------------
clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quit_game()

    screen.fill((30, 30, 30))

    for btn in buttons:
        btn.draw(screen)
        if pygame.mouse.get_pressed()[0]:
            btn.check_click()

    pygame.display.flip()
    clock.tick(60)
