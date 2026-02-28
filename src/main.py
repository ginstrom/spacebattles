"""
The entry point for the real-time Ship Duel application.
Initializes the game engine and the ScreenManager.
"""
import pygame
from src.constants import WIDTH, HEIGHT, FPS
from src.core.screen_manager import ScreenManager
from src.screens.battle_screen import BattleScreen


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Ship Duel")
    clock = pygame.time.Clock()

    manager = ScreenManager(screen)
    manager.set_screen(BattleScreen)

    while manager.running:
        dt = clock.tick(FPS)
        manager.handle_events()
        manager.update(dt)
        manager.draw()

    pygame.quit()


if __name__ == "__main__":
    main()
