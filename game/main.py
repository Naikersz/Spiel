"""
Main entry point for Spiel game
Интегрирован с новой системой инициализации
"""
import warnings
import os
import sys

# Добавляем родительскую директорию в путь для корректных импортов
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Suppress pkg_resources deprecation warning from pygame BEFORE importing pygame
# Фильтруем все предупреждения о pkg_resources (deprecated API)
PKG_RESOURCES_PATTERN = ".*pkg_resources.*"
warnings.filterwarnings("ignore", category=UserWarning, message=PKG_RESOURCES_PATTERN)
warnings.filterwarnings("ignore", message=PKG_RESOURCES_PATTERN)
warnings.filterwarnings("ignore", category=DeprecationWarning, message=PKG_RESOURCES_PATTERN)
# Также подавляем через переменную окружения для pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

from game.core.game_launcher import GameLauncher

def main():
    """Main game loop"""
    # Определяем базовый путь (на уровень выше папки game)
    base_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    # Создаем и запускаем лаунчер
    launcher = GameLauncher(base_path)
    launcher.run()

if __name__ == "__main__":
    main()

