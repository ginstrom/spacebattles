"""
Base class for all modular screens in the game, providing a
consistent interface for event handling, updates, and drawing.
"""
import pygame


class BaseScreen:
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager

    def handle_event(self, event: pygame.event.Event):
        pass

    def update(self, dt: int):
        pass

    def draw(self, surface: pygame.Surface):
        pass
