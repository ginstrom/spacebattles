"""
Global constants for the game, including window dimensions, colors,
turn states, and UI layout parameters.
"""
import pygame

WIDTH, HEIGHT = 900, 700
FPS = 60

BG = (15, 18, 26)
PANEL_BG = (28, 34, 50)
PANEL_BORDER = (55, 70, 110)
WHITE = (240, 240, 240)
GRAY = (120, 120, 120)
GREEN = (80, 220, 120)
RED = (230, 80, 80)
BLUE = (90, 160, 255)
YELLOW = (245, 220, 90)

PLAYER_TURN = "player"
CPU_TURN = "cpu"

PHASE_FIRE = "fire"
PHASE_END = "end"

PANEL_W = 320
TAB_W = 22
TAB_H = 64
PANEL_PAD = 14
MSG_H = 68
