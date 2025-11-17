import pygame
from ui.fonts import FONT

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
                return self.callback()
            self.is_pressed = False

        return None
