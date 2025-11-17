import os
import pygame

pygame.init()

# ---------------------------------------------------
# PATHS
# ---------------------------------------------------
BASE_PATH = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
SAVE_ROOT = os.path.join(BASE_PATH, "save")
SAVE_SLOTS = ["save1", "save2", "save3"]

ASSET_ICON_PATH = os.path.join(BASE_PATH, "assets", "icons")

# ---------------------------------------------------
# WINDOW
# ---------------------------------------------------
WIDTH, HEIGHT = 900, 600
