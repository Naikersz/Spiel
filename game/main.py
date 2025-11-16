"""
Main entry point for Spiel game
"""
import warnings
import os

# Suppress pkg_resources deprecation warning from pygame BEFORE importing pygame
warnings.filterwarnings("ignore", category=UserWarning, message=".*pkg_resources.*")
warnings.filterwarnings("ignore", message=".*pkg_resources.*")

import pygame
from game.menu_system import MenuManager, GameState

def main():
    """Main game loop"""
    pygame.init()
    
    # Fullscreen mode
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Spiel - Roguelike Adventure")
    clock = pygame.time.Clock()
    
    # Initialize menu system
    menu_manager = MenuManager(screen)
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            
            # Handle menu events
            action = menu_manager.handle_event(event)
            if action:
                if action == "quit_game":
                    running = False
                    break
                else:
                    menu_manager.handle_action(action)
        
        # Update menu
        menu_manager.update(dt)
        
        # Draw menu
        menu_manager.draw()
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()

