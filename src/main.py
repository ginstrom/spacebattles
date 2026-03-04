"""
The entry point for the real-time Ship Duel application.
Initializes the game engine and the ScreenManager.
"""
import logging
import os
import sys
from pathlib import Path

import pygame
from src.constants import WIDTH, HEIGHT, FPS
from src.core.screen_manager import ScreenManager
from src.screens.menu_screen import MenuScreen


def configure_logging(log_path: str | Path = "spacebattle.log") -> Path:
    resolved_path = Path(log_path).resolve()
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s %(message)s",
        handlers=[
            logging.FileHandler(resolved_path, mode="w", encoding="utf-8"),
            logging.StreamHandler(sys.stderr),
        ],
        force=True,
    )
    logging.getLogger(__name__).info("logging initialized: %s", resolved_path)
    return resolved_path


def build_game() -> tuple[ScreenManager, pygame.time.Clock]:
    pygame.init()
    if hasattr(pygame.key, "stop_text_input"):
        pygame.key.stop_text_input()
    windowed = os.getenv("SPACEBATTLE_WINDOWED", "0") == "1"
    screen_flags = 0 if windowed else pygame.FULLSCREEN
    screen = pygame.display.set_mode((WIDTH, HEIGHT), screen_flags)
    pygame.display.set_caption("Ship Duel")
    clock = pygame.time.Clock()

    manager = ScreenManager(screen)
    manager.set_screen(MenuScreen)
    return manager, clock


def run_game_loop(manager: ScreenManager, clock: pygame.time.Clock) -> None:
    while manager.running:
        dt = clock.tick(FPS)
        manager.handle_events()
        manager.update(dt)
        manager.draw()


def main() -> None:
    configure_logging()
    manager, clock = build_game()
    try:
        run_game_loop(manager, clock)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
