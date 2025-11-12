import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
clock = pygame.time.Clock()

# Загрузка sprite sheet (поместите player_spritesheet.png в папку с кодом)
# Пример: 4 кадра по 64x64 пикселя в ряд
spritesheet = pygame.image.load("game/images/player.png").convert_alpha()
frame_width, frame_height = 64, 64  # Размер одного кадра
frames = [] 

# Извлечение кадров из sprite sheet (горизонтальная строка, 4 кадра)
for i in range(6):
    rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
    frame = spritesheet.subsurface(rect)
    frames.append(frame)

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = frames[0]
        self.rect = self.image.get_rect(center=(400, 300))
        self.frame_index = 0
        self.animation_speed = 0.2  # Скорость анимации
        self.anim_counter = 0

    def update(self):
        # Логика движения (пример: WASD)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] or keys[pygame.K_s] or keys[pygame.K_a] or keys[pygame.K_d]:
            self.anim_counter += 1
            if self.anim_counter > 1 / self.animation_speed:
                self.frame_index = (self.frame_index + 1) % len(frames)
                self.image = frames[self.frame_index]
                self.anim_counter = 0
        else:
            self.image = frames[0]  # Стоячая поза

        # Движение
        if keys[pygame.K_a]: self.rect.x -= 5
        if keys[pygame.K_d]: self.rect.x += 5
        if keys[pygame.K_w]: self.rect.y -= 5
        if keys[pygame.K_s]: self.rect.y += 5

player = Player()
all_sprites = pygame.sprite.Group(player)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.VIDEORESIZE:
            screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

    all_sprites.update()

    screen.fill((50, 50, 100))
    all_sprites.draw(screen)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()