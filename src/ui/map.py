"""
Handles the rendering of the battle map, including the starfield
and the visual positioning of ships.
"""
import math
import pygame
from src.constants import (
    BLUE,
    HEIGHT,
    PANEL_BORDER,
    SHIP_ICON_SIZE,
    WHITE,
)
from src.utils.helpers import hp_color
from src.ui.elements import draw_enemy_icon, draw_player_icon
from src.models.ship import Ship


class Map:
    def __init__(self, stars: list[tuple[int, int, int, int]]):
        self.stars = stars

    def _draw_ghost_route(
        self,
        surf: pygame.Surface,
        player: Ship,
        waypoints: list[tuple[float, float]],
    ) -> None:
        if not waypoints:
            return

        route_color = (110, 180, 255)
        points = [(float(player.x), float(player.y)), *waypoints]

        for idx in range(len(points) - 1):
            x1, y1 = points[idx]
            x2, y2 = points[idx + 1]
            seg_dx = x2 - x1
            seg_dy = y2 - y1
            seg_len = math.hypot(seg_dx, seg_dy)
            if seg_len <= 0.0:
                continue
            dash_px = 12.0
            dash_count = max(1, int(seg_len // dash_px))
            for dash_idx in range(dash_count):
                if dash_idx % 2 != 0:
                    continue
                t0 = dash_idx / dash_count
                t1 = min(1.0, (dash_idx + 1) / dash_count)
                sx = int(x1 + seg_dx * t0)
                sy = int(y1 + seg_dy * t0)
                ex = int(x1 + seg_dx * t1)
                ey = int(y1 + seg_dy * t1)
                pygame.draw.line(surf, route_color, (sx, sy), (ex, ey), 2)

        final_x, final_y = waypoints[-1]
        ghost = pygame.Surface((SHIP_ICON_SIZE, SHIP_ICON_SIZE), pygame.SRCALPHA)
        draw_player_icon(ghost, SHIP_ICON_SIZE // 2, SHIP_ICON_SIZE // 2, SHIP_ICON_SIZE)
        ghost.set_alpha(110)
        surf.blit(
            ghost,
            (int(final_x - SHIP_ICON_SIZE // 2), int(final_y - SHIP_ICON_SIZE // 2)),
        )

        heading_rad = math.radians(player.heading)
        hx = int(player.x + math.sin(heading_rad) * 36.0)
        hy = int(player.y - math.cos(heading_rad) * 36.0)
        pygame.draw.line(surf, route_color, (int(player.x), int(player.y)), (hx, hy), 2)

    def draw(
        self,
        surf: pygame.Surface,
        map_w: int,
        player: Ship,
        cpu: Ship,
        is_running: bool,
        winner: str | None,
        font: pygame.font.Font,
        small_font: pygame.font.Font,
        waypoints: list[tuple[float, float]] | None = None,
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
        self._draw_ghost_route(surf, player, waypoints or [])

        # CPU
        cpu_cx = int(cpu.x)
        cpu_cy = int(cpu.y)
        icon_size = SHIP_ICON_SIZE
        if is_running and winner is None:
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
        player_cx = int(player.x)
        player_cy = int(player.y)
        if is_running and winner is None:
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
