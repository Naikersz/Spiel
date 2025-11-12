import pygame
from game.scenes.character_creation import CharacterCreationScene
pygame.init()
screen = pygame.display.set_mode((800, 600))
scene = CharacterCreationScene(screen)
clock = pygame.time.Clock()
running = True
while running:
    events = pygame.event.get()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    scene.handle_events(events)
    scene.render()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()