import pygame
from core.constants import WIDTH, HEIGHT
from core.scene_manager import SceneManager
from scenes.main_menu import MainMenu
import os
from core.constants import SAVE_ROOT

os.makedirs(SAVE_ROOT, exist_ok=True)

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game")
clock = pygame.time.Clock()

manager = SceneManager(MainMenu())

while True:
    events = pygame.event.get()

    for e in events:
        if e.type == pygame.QUIT:
            pygame.quit()
            quit()

    manager.update(events)
    manager.draw(screen)

    pygame.display.flip()
    clock.tick(60)


