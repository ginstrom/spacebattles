"""
Utility functions for the game, including HP color calculation,
starfield generation, and text wrapping.
"""
import pygame
import random
from src.constants import GREEN, YELLOW, RED, WHITE, WIDTH, HEIGHT


def hp_color(hp: int, max_hp: int) -> tuple[int, int, int]:
    pct = hp / max_hp if max_hp > 0 else 0
    if pct > 0.4:
        return GREEN
    elif pct > 0.2:
        return YELLOW
    return RED


def make_stars(n: int = 150) -> list[tuple[int, int, int, int]]:
    stars = []
    for _ in range(n):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        brightness = random.randint(120, 255)
        size = random.randint(1, 3)
        stars.append((x, y, brightness, size))
    return stars


def wrap_text(font: pygame.font.Font, text: str, max_w: int) -> list[str]:
    words = text.split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if font.size(test)[0] <= max_w:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines if lines else [""]
