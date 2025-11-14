# game/engine.py
import pygame
from .character import ModularCharacter
from .enemy import Enemy

class SimpleGame:
    def __init__(self):
        pygame.init()  # ← ИНИЦИАЛИЗАЦИЯ ЗДЕСЬ!
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Spiel - LPC Анимации")
        self.clock = pygame.time.Clock()
        self.running = True
        self.player = ModularCharacter(400, 300)
        self.enemies = [Enemy(100, 200, self.player)]

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: self.player.toggle_clothing("hut", "head")
                elif event.key == pygame.K_2: self.player.toggle_clothing("leather_armor", "body")
                elif event.key == pygame.K_3: self.player.toggle_clothing("gloves")
                elif event.key == pygame.K_4: self.player.toggle_clothing("pants")
                elif event.key == pygame.K_5: self.player.toggle_clothing("boots")
                elif event.key == pygame.K_6: self.player.toggle_clothing("mantal")
                elif event.key == pygame.K_7: self.player.toggle_clothing("cuffs")
                elif event.key == pygame.K_SPACE:
                    self.player.current_frame = (self.player.current_frame + 1) % 9

    def update(self):
        dt = self.clock.tick(60) / 1000.0
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * 3
        dy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * 3
        self.player.move(dx, dy)
        for enemy in self.enemies:
            enemy.update(dt, self.player)
        self.player.update(dt)

    def draw(self):
        self.screen.fill((30, 50, 40))
        cell = 64
        for x in range(0, self.screen_width, cell):
            pygame.draw.line(self.screen, (70, 70, 100), (x, 0), (x, self.screen_height), 1)
        for y in range(0, self.screen_height, cell):
            pygame.draw.line(self.screen, (70, 70, 100), (0, y), (self.screen_width, y), 1)

        self.player.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)

        hp_ratio = self.player.hp / self.player.max_hp
        pygame.draw.rect(self.screen, (100, 0, 0), (10, 70, 100, 10))
        pygame.draw.rect(self.screen, (0, 200, 0), (10, 70, 100 * hp_ratio, 10))
        pygame.display.flip()

    def run(self):
        print("=" * 60)
        print("LPC АНИМАЦИИ: 9 кадров ходьбы, 6 — атака")
        print("1-7: одежда | SPACE: кадр | WASD: ходьба")
        print("=" * 60)
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
        pygame.quit()