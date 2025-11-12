import pygame
import sys
import os

pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Анимация из Sprite Sheet")
clock = pygame.time.Clock()
FPS, ANIM_SPEED = 60, 6  # 6 кадров/сек

# Класс SpriteSheet (вставьте из шага 2)
class SpriteSheet:
    def __init__(self, filename):
        self.sheet = pygame.image.load("game/images/p1_walk.png").convert_alpha()  # Загрузка с прозрачностью

    def get_image(self, x, y, width, height):
        """Вырезает один кадр по координатам (x,y) размером w x h"""
        rect = pygame.Rect(x, y, width, height)
        image = pygame.Surface(rect.size).convert_alpha()
        image.blit(self.sheet, (0, 0), rect)
        return image

    def load_strip(self, rect, count, colorkey=None):
        """Вырезает горизонтальную полосу: rect=(x,y,w,h), count=кол-во кадров"""
        images = []
        for i in range(count):
            images.append(self.get_image(rect[0] + i * rect[2], rect[1], rect[2], rect[3]))
        return images

    def load_grid(self, start_x, start_y, width, height, cols, rows):
        """Вырезает сетку: cols столбцов, rows строк"""
        frames = []
        for row in range(rows):
            for col in range(cols):
                x = start_x + col * width
                y = start_y + row * height
                frames.append(self.get_image(x, y, width, height))
        return frames
    
# Загрузка
spritesheet = SpriteSheet("images/p1_walk.png")  # Ваш файл

# Вырезаем кадры ходьбы вправо (полоса: start=(0,0), w=66, h=90, 8 кадров)
walk_right = spritesheet.load_strip((0, 0, 66, 90), 8)

# Для left: зеркалим
walk_left = [pygame.transform.flip(img, True, False) for img in walk_right]

idle = walk_right[0]

# Переменные игрока (как раньше)
player_x, player_y = 100, SCREEN_HEIGHT - 100
player_speed = 5
anim_index, anim_timer = 0, 0
is_moving, direction = False, "right"

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Управление (стрелки)
    keys = pygame.key.get_pressed()
    is_moving = False
    if keys[pygame.K_LEFT]:
        player_x -= player_speed
        direction = "left"
        is_moving = True
    if keys[pygame.K_RIGHT]:
        player_x += player_speed
        direction = "right"
        is_moving = True
    player_x = max(0, min(SCREEN_WIDTH - 66, player_x))  # Границы

    # Анимация
    if is_moving:
        anim_timer += 1
        if anim_timer > FPS // ANIM_SPEED:
            anim_timer = 0
            anim_index = (anim_index + 1) % len(walk_right)

    # Отрисовка
    screen.fill((0, 100, 200))
    current_frame = walk_left[anim_index] if is_moving and direction == "left" else \
                    walk_right[anim_index] if is_moving else idle
    screen.blit(current_frame, (player_x, player_y))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()