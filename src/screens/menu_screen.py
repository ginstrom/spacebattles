"""
A reusable menu screen for startup and game-over states.
"""
import logging
import os
import pygame

from src.constants import WIDTH, HEIGHT, PANEL_BG, PANEL_BORDER, WHITE, BLUE, RED
from src.core.base_screen import BaseScreen
from src.screens.battle_screen import BattleScreen

_log = logging.getLogger(__name__)


class MenuScreen(BaseScreen):
    def __init__(self, screen_manager, result_message=None):
        super().__init__(screen_manager)
        self.big_font = pygame.font.SysFont(None, 72)
        self.font = pygame.font.SysFont(None, 44)
        self.small_font = pygame.font.SysFont(None, 28)

        self.result_message = result_message
        self.title = "SHIP DUEL" if not result_message else "BATTLE OVER"
        self.screen_w, self.screen_h = self._screen_size()

        self.buttons = {}
        self._setup_buttons()

    def update(self, dt):
        if os.getenv("SPACEBATTLE_DEMO_SCRIPT", "0") == "1" and self.result_message is None:
            self.screen_manager.set_screen(BattleScreen)

    def _screen_size(self) -> tuple[int, int]:
        if hasattr(self.screen_manager, "screen") and hasattr(self.screen_manager.screen, "get_size"):
            w, h = self.screen_manager.screen.get_size()
            if isinstance(w, int) and isinstance(h, int) and w > 0 and h > 0:
                return w, h
        return WIDTH, HEIGHT

    def _setup_buttons(self):
        btn_w, btn_h = 240, 60
        btn_x = self.screen_w // 2 - btn_w // 2

        new_game_y = self.screen_h // 2 + 20
        self.buttons["new_game"] = {
            "rect": pygame.Rect(btn_x, new_game_y, btn_w, btn_h),
            "text": "NEW GAME",
            "color": BLUE,
        }

        quit_y = new_game_y + 80
        self.buttons["quit"] = {
            "rect": pygame.Rect(btn_x, quit_y, btn_w, btn_h),
            "text": "QUIT",
            "color": RED,
        }

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.buttons["new_game"]["rect"].collidepoint(pos):
                _log.info("starting new game")
                self.screen_manager.set_screen(BattleScreen)
            elif self.buttons["quit"]["rect"].collidepoint(pos):
                _log.info("quitting game")
                self.screen_manager.quit()

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.screen_manager.set_screen(BattleScreen)
            elif event.key == pygame.K_ESCAPE:
                self.screen_manager.quit()

    def draw(self, screen):
        screen.fill((15, 18, 26))
        self.screen_w, self.screen_h = self._screen_size()

        title_surf = self.big_font.render(self.title, True, WHITE)
        screen.blit(title_surf, title_surf.get_rect(center=(self.screen_w // 2, self.screen_h // 2 - 180)))

        if self.result_message:
            color = (230, 80, 80) if "Computer" in self.result_message else (80, 220, 120)
            res_surf = self.font.render(self.result_message, True, color)
            screen.blit(res_surf, res_surf.get_rect(center=(self.screen_w // 2, self.screen_h // 2 - 80)))

        for btn in self.buttons.values():
            pygame.draw.rect(screen, PANEL_BG, btn["rect"], border_radius=12)
            pygame.draw.rect(screen, btn["color"], btn["rect"], 2, border_radius=12)
            txt_surf = self.small_font.render(btn["text"], True, WHITE)
            screen.blit(txt_surf, txt_surf.get_rect(center=btn["rect"].center))
