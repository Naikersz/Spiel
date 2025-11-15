import pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()
objects_img = pygame.image.load('game/assets/tiles/dungeonex.png').convert_alpha()

TILE_SIZE = 32
sprites = {
    'cauldron': objects_img.subsurface(pygame.Rect(34, 0, 29, 32)),  # ТВОЙ котёл!
}
game_map = [[0]*25 for _ in range(18)]  # пустая карта

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            col, row = mx // TILE_SIZE, my // TILE_SIZE
            game_map[row][col] = 1  # поставь стол по клику!

    screen.fill((30,30,40))
    
    # Рисуй map
    for row in range(18):
        for col in range(25):
            if game_map[row][col] == 1:
                screen.blit(sprites['cauldron'], (col*TILE_SIZE, row*TILE_SIZE))
                

    # МЫШЬ-ОТЛАДКА
    mx, my = pygame.mouse.get_pos()
    col, row = mx // TILE_SIZE, my // TILE_SIZE
    font = pygame.font.SysFont('arial', 20)
    screen.blit(font.render(f'Позиция: grid[{row}][{col}] px=({mx//TILE_SIZE*TILE_SIZE}, {my//TILE_SIZE*TILE_SIZE})', True, (255,255,0)), (10,10))
    
    pygame.display.flip()
    clock.tick(60)
pygame.quit()