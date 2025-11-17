class SceneManager:
    def __init__(self, start_scene):
        self.current_scene = start_scene

    def update(self, events):
        next_scene = self.current_scene.update(events)
        if next_scene:
            self.current_scene = next_scene

    def draw(self, screen):
        self.current_scene.draw(screen)
