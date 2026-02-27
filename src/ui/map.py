"""
Handles the rendering of the battle map, including the starfield
and the visual positioning of ships.
"""
import pygame
from src.constants import (
    BLUE,
    CPU_TURN,
    HEIGHT,
    PANEL_BORDER,
    PLAYER_TURN,
    WHITE,
)
from src.utils.helpers import hp_color
from src.ui.elements import draw_enemy_icon, draw_player_icon
from src.models.ship import Ship


class Map:
    def __init__(self, stars: list[tuple[int, int, int, int]]):
        self.stars = stars

    def draw(
        self,
        surf: pygame.Surface,
        map_w: int,
        player: Ship,
        cpu: Ship,
        turn: str,
        winner: str | None,
        font: pygame.font.Font,
        small_font: pygame.font.Font,
    ) -> None:
        clip_rect = pygame.Rect(0, 0, map_w, HEIGHT)
        surf.set_clip(clip_rect)

        for sx, sy, brightness, size in self.stars:
            if sx < map_w:
                c = (brightness, brightness, brightness)
                if size <= 1:
                    surf.set_at((sx, sy), c)
                else:
                    pygame.draw.circle(surf, c, (sx, sy), size // 2)

        surf.set_clip(None)
        pygame.draw.line(surf, PANEL_BORDER, (map_w, 0), (map_w, HEIGHT), 1)

        # CPU
        cpu_cx = map_w // 2
        cpu_cy = HEIGHT // 4
        icon_size = 64
        if turn == CPU_TURN and winner is None:
            pygame.draw.circle(surf, BLUE, (cpu_cx, cpu_cy),
                               icon_size // 2 + 10, 2)
        draw_enemy_icon(surf, cpu_cx, cpu_cy, icon_size)
        name_surf = small_font.render(cpu.name, True, WHITE)
        surf.blit(name_surf, name_surf.get_rect(
            centerx=cpu_cx, top=cpu_cy + icon_size // 2 + 12))
        bar_w = 100
        bar_h = 8
        bar_x = cpu_cx - bar_w // 2
        bar_y = cpu_cy + icon_size // 2 + 12 + name_surf.get_height() + 4
        pygame.draw.rect(surf, (60, 60, 80), (bar_x, bar_y,
                         bar_w, bar_h), border_radius=4)
        fill_w = int(bar_w * max(0, cpu.hp) /
                     cpu.max_hp) if cpu.max_hp > 0 else 0
        if fill_w > 0:
            pygame.draw.rect(surf, hp_color(cpu.hp, cpu.max_hp),
                             (bar_x, bar_y, fill_w, bar_h), border_radius=4)

        # Player
        player_cx = map_w // 2
        player_cy = HEIGHT * 3 // 4
        if turn == PLAYER_TURN and winner is None:
            pygame.draw.circle(
                surf, BLUE, (player_cx, player_cy), icon_size // 2 + 10, 2)
        draw_player_icon(surf, player_cx, player_cy, icon_size)
        p_name_surf = small_font.render(player.name, True, WHITE)
        p_name_rect = p_name_surf.get_rect(
            centerx=player_cx, bottom=player_cy - icon_size // 2 - 12)
        surf.blit(p_name_surf, p_name_rect)
        p_bar_y = p_name_rect.top - bar_h - 4
        p_bar_x = player_cx - bar_w // 2
        pygame.draw.rect(surf, (60, 60, 80),
                         (p_bar_x, p_bar_y, bar_w, bar_h), border_radius=4)
        p_fill_w = int(bar_w * max(0, player.hp) /
                       player.max_hp) if player.max_hp > 0 else 0
        if p_fill_w > 0:
            pygame.draw.rect(
                surf,
                hp_color(player.hp, player.max_hp),
                (p_bar_x,
                 p_bar_y,
                 p_fill_w,
                 bar_h),
                border_radius=4)
