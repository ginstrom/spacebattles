"""
Manager for handling screen transitions and delegating game loop
responsibilities to the active screen.
"""
import pygame


class ScreenManager:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.current_screen = None
        self.running = True

    def set_screen(self, screen_class, **kwargs):
        self.current_screen = screen_class(self, **kwargs)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if self.current_screen:
                self.current_screen.handle_event(event)

    def update(self, dt: int):
        if self.current_screen:
            self.current_screen.update(dt)

    def draw(self):
        if self.current_screen:
            self.current_screen.draw(self.screen)
        pygame.display.flip()

    def quit(self):
        self.running = False
