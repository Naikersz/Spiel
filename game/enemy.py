# game/enemy.py
import pygame
from .character import ModularCharacter

class Enemy(ModularCharacter):
    def __init__(self, x: int, y: int, player_ref):
        super().__init__(x, y)
        self.player = player_ref
        self.speed = 1.5
        self.attack_range = 80
        self.attack_cooldown = 0
        self.max_cooldown = 1.5
        self.hp = 50
        self.max_hp = 50
        self.patrol_points = [(200, 200), (600, 400)]
        self.current_patrol = 0
        self.state = "patrol"

        self.layers.clear()
        self.visible_layers.clear()
        self.load_default_layers()

    def load_default_layers(self):
        from .character import CharacterLayer  # ← Импортируем здесь

        layers = [
            ("body", "game/assets/sprites/body/bodies/male/bodySkeleton.png", 10),
            ("head", "game/assets/sprites/head/heads/enemies/headSkeleton.png", 50),
            ("scimitar", "game/assets/sprites/weapons/scimitarwWalk.png", 40),
            ("scimitar_attack", "game/assets/sprites/weapons/scimitarSlash.png", 41),
        ]
        for name, path, z in layers:
            self.layers[name] = CharacterLayer(path, name, z_pos=z)
        self.visible_layers = {"body", "head", "scimitar"}

    def update(self, dt: float, player):
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        dist = ((player.x - self.x)**2 + (player.y - self.y)**2)**0.5

        self.state = "chase" if dist < 200 else "patrol"
        self.visible_layers = {"body", "head", "scimitar_attack"} if self.current_animation == "attack" else {"body", "head", "scimitar"}

        if (self.state == "chase" and dist < self.attack_range and 
            self.attack_cooldown <= 0 and self.current_animation != "attack"):
            self.current_animation = "attack"
            self.current_frame = 0
            self.attack_cooldown = self.max_cooldown

        if self.current_animation != "attack":
            dx = dy = 0
            if self.state == "chase":
                dx = 1 if player.x > self.x else -1 if player.x < self.x else 0
                dy = 1 if player.y > self.y else -1 if player.y < self.y else 0
                norm = max((dx**2 + dy**2)**0.5, 1)
                dx, dy = dx / norm * self.speed, dy / norm * self.speed
                self.move(int(dx), int(dy))
            elif self.state == "patrol":
                tx, ty = self.patrol_points[self.current_patrol]
                dx, dy = tx - self.x, ty - self.y
                dist_to = max((dx**2 + dy**2)**0.5, 1)
                if dist_to < 20:
                    self.current_patrol = (self.current_patrol + 1) % 2
                else:
                    self.move(int(dx / dist_to * self.speed), int(dy / dist_to * self.speed))

        if self.current_animation == "attack" and self.current_frame == 3:
            player.take_damage(15)

        super().update(dt)

    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, (255, 0, 0), (self.x-32, self.y-64, 64, 64), 3)
        super().draw(screen)