import pygame, sys

pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Персонаж из спрайт-листа RPG")
clock = pygame.time.Clock()
FPS = 60

# === КЛАСС ДЛЯ СПРАЙТ-ЛИСТА ===
class SpriteSheet:
    def __init__(self, filename):
        self.sheet = pygame.image.load(filename).convert_alpha()

    def get_image(self, x, y, width, height):
        image = pygame.Surface((width, height), pygame.SRCALPHA)
        image.blit(self.sheet, (0, 0), (x, y, width, height))
        return image

# === ПАРАМЕТРЫ СПРАЙТА ===
spritesheet = SpriteSheet("game/images/bodyMale.png")

SPRITE_SHEET_WIDTH, SPRITE_SHEET_HEIGHT = 576, 256  # если твой файл именно такого размера
cols, rows = 9, 4  # 8 кадров в строке, 4 направления
frame_w = SPRITE_SHEET_WIDTH // cols   # 72 px
frame_h = SPRITE_SHEET_HEIGHT // rows  # 64 px

# === ЗАГРУЖАЕМ ВСЕ КАДРЫ ===
frames = []
for row in range(rows):
    row_frames = []
    for col in range(cols):
        x = col * frame_w
        y = row * frame_h
        img = spritesheet.get_image(x, y, frame_w, frame_h)
        row_frames.append(img)
    frames.append(row_frames)

# === НАСТРОЙКИ ===
player_x, player_y = SCREEN_WIDTH//2, SCREEN_HEIGHT//2
player_speed = 4
direction = 2  # 0=вверх, 1=влево, 2=вниз, 3=вправо
frame_index = 0
walk_time = 0
ANIM_FPS = 10

# === ИГРОВОЙ ЦИКЛ ===
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    moving = False

    if keys[pygame.K_UP]:
        player_y -= player_speed
        direction = 0
        moving = True
    elif keys[pygame.K_DOWN]:
        player_y += player_speed
        direction = 2
        moving = True
    elif keys[pygame.K_LEFT]:
        player_x -= player_speed
        direction = 1
        moving = True
    elif keys[pygame.K_RIGHT]:
        player_x += player_speed
        direction = 3
        moving = True

    # === АНИМАЦИЯ ===
    if moving:
        walk_time += 1 / FPS
        frame_index = int(walk_time * ANIM_FPS) % len(frames[direction])
    else:
        frame_index = 0
        walk_time = 0

    # === ОТРИСОВКА ===
    screen.fill((120, 180, 250))
    current_frame = frames[direction][frame_index]
    screen.blit(current_frame, (player_x, player_y))
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
