import pygame
import json
import os
import requests

pygame.init()

# ===== Настройки окна =====
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Персонаж с экипировкой")
clock = pygame.time.Clock()
FPS = 60

# ===== Создание папок =====
base_dir = "game"
folders = [
    "assets/body/bodies/male",
    "assets/head/heads/human/male",
    "assets/hat/cloth/leather_cap/adult",
    "data/raw",
    "data/processed",
    "src/utils",
    "docs"
]

for folder in folders:
    path = os.path.join(base_dir, folder)
    os.makedirs(path, exist_ok=True)

# ===== Загрузка JSON =====
json_path = os.path.join(base_dir, "players.json")
with open(json_path, "r") as f:
    char_data = json.load(f)

# ===== Функция для скачивания файлов =====
def download_file(url, save_path):
    if os.path.exists(save_path):
        return  # уже есть
    try:
        print(f"⬇️ Скачивание: {url}")
        r = requests.get(url)
        r.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(r.content)
        print(f"✅ Сохранено: {save_path}")
    except Exception as e:
        print(f"❌ Ошибка при скачивании {url}: {e}")

# ===== Скачивание слоев =====
for layer in char_data["layers"]:
    local_path = os.path.join(base_dir, "assets", layer["fileName"])
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    # Составляем URL на spritesheets
    # base_url + путь к файлу из JSON
    # Например: https://liberatedpixelcup.github.io/Universal-LPC-Spritesheet-Character-Generator/spritesheets/body/bodies/male/light.png
    url = char_data["spritesheets"] + layer["fileName"]
    download_file(url, local_path)

# ===== Загрузка слоев в Pygame =====
layers = []
for layer in char_data["layers"]:
    path = os.path.join(base_dir, "assets", layer["fileName"])
    if not os.path.exists(path):
        print(f"⚠️ Файл не найден: {path}")
        continue
    img = pygame.image.load(path).convert_alpha()
    layers.append({
        "image": img,
        "zPos": layer["zPos"],
        "name": layer["name"],
        "parentName": layer["parentName"],
        "animations": layer["supportedAnimations"]
    })

# Сортируем по zPos
layers.sort(key=lambda x: x["zPos"])

# ===== Функция отрисовки персонажа =====
def render_character(surface, x, y):
    for layer in layers:
        surface.blit(layer["image"], (x, y))

# ===== Простая анимация ходьбы =====
walk_frames = [0, 5, 0, -5]
walk_index = 0
walk_timer = 0

player_x, player_y = 300, 300
player_speed = 5

# ===== Основной цикл =====
running = True
while running:
    dt = clock.tick(FPS) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    moving = False
    if keys[pygame.K_LEFT]:
        player_x -= player_speed
        moving = True
    if keys[pygame.K_RIGHT]:
        player_x += player_speed
        moving = True

    if moving:
        walk_timer += dt
        if walk_timer > 0.2:
            walk_timer = 0
            walk_index = (walk_index + 1) % len(walk_frames)
    else:
        walk_index = 0

    screen.fill((100, 150, 200))
    render_character(screen, player_x, player_y + walk_frames[walk_index])
    pygame.display.flip()

pygame.quit()
