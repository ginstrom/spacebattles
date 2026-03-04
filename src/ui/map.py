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
from src.ui.elements import draw_enemy_icon, draw_player_icon
from src.models.ship import Ship


class Map:
    def __init__(self, stars: list[tuple[int, int, int, int]]):
        self.stars = stars

    @staticmethod
    def _predict_turn_limited_route(
        player: Ship,
        waypoints: list[tuple[float, float]],
    ) -> list[tuple[float, float]]:
        if not waypoints:
            return []

        x = float(player.x)
        y = float(player.y)
        heading = player.heading % 360.0
        route: list[tuple[float, float]] = [(x, y)]

        dt_seconds = 0.12
        speed_step = max(1.0, float(player.speed_px_s) * dt_seconds)
        max_turn_step = max(0.1, float(player.rotation_speed_deg_s) * dt_seconds)
        reach_distance = max(10.0, speed_step * 1.5)
        max_iterations = 5000

        waypoint_idx = 0
        iterations = 0
        while waypoint_idx < len(waypoints) and iterations < max_iterations:
            iterations += 1
            tx, ty = waypoints[waypoint_idx]
            dx = tx - x
            dy = ty - y
            distance = math.hypot(dx, dy)

            if distance <= reach_distance:
                x = float(tx)
                y = float(ty)
                route.append((x, y))
                waypoint_idx += 1
                continue

            target_heading = math.degrees(math.atan2(dx, -dy)) % 360.0
            delta = (target_heading - heading + 540.0) % 360.0 - 180.0
            if delta > max_turn_step:
                delta = max_turn_step
            elif delta < -max_turn_step:
                delta = -max_turn_step
            heading = (heading + delta) % 360.0

            heading_rad = math.radians(heading)
            x += math.sin(heading_rad) * speed_step
            y -= math.cos(heading_rad) * speed_step
            route.append((x, y))

        if route[-1] != tuple(waypoints[-1]):
            route.append((float(waypoints[-1][0]), float(waypoints[-1][1])))
        return route

    def _draw_ghost_route(
        self,
        surf: pygame.Surface,
        player: Ship,
        waypoints: list[tuple[float, float]],
        view_x: float,
        view_y: float,
    ) -> None:
        if not waypoints:
            return

        route_color = (110, 180, 255)
        points = self._predict_turn_limited_route(player, waypoints)
        if len(points) < 2:
            return

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
                sx = int(x1 + seg_dx * t0 - view_x)
                sy = int(y1 + seg_dy * t0 - view_y)
                ex = int(x1 + seg_dx * t1 - view_x)
                ey = int(y1 + seg_dy * t1 - view_y)
                pygame.draw.line(surf, route_color, (sx, sy), (ex, ey), 2)

        final_x, final_y = waypoints[-1]
        ghost = pygame.Surface((SHIP_ICON_SIZE, SHIP_ICON_SIZE), pygame.SRCALPHA)
        draw_player_icon(ghost, SHIP_ICON_SIZE // 2, SHIP_ICON_SIZE // 2, SHIP_ICON_SIZE)
        ghost.set_alpha(110)
        surf.blit(
            ghost,
            (
                int(final_x - view_x - SHIP_ICON_SIZE // 2),
                int(final_y - view_y - SHIP_ICON_SIZE // 2),
            ),
        )

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
        view_x: float = 0.0,
        view_y: float = 0.0,
    ) -> None:
        map_h = surf.get_height()
        clip_rect = pygame.Rect(0, 0, map_w, map_h)
        surf.set_clip(clip_rect)

        for star_x, star_y, brightness, size in self.stars:
            sx = int(star_x - view_x)
            sy = int(star_y - view_y)
            if 0 <= sx < map_w and 0 <= sy < map_h:
                c = (brightness, brightness, brightness)
                if size <= 1:
                    surf.set_at((sx, sy), c)
                else:
                    pygame.draw.circle(surf, c, (sx, sy), size // 2)

        surf.set_clip(None)
        pygame.draw.line(surf, PANEL_BORDER, (map_w, 0), (map_w, map_h), 1)
        self._draw_ghost_route(surf, player, waypoints or [], view_x, view_y)

        # CPU
        cpu_cx = int(cpu.x - view_x)
        cpu_cy = int(cpu.y - view_y)
        icon_size = SHIP_ICON_SIZE
        if is_running and winner is None:
            pygame.draw.circle(surf, BLUE, (cpu_cx, cpu_cy),
                               icon_size // 2 + 10, 2)
        draw_enemy_icon(surf, cpu_cx, cpu_cy, icon_size, cpu.heading)
        name_surf = small_font.render(cpu.name, True, WHITE)
        surf.blit(name_surf, name_surf.get_rect(
            centerx=cpu_cx, top=cpu_cy + icon_size // 2 + 12))

        # Player
        player_cx = int(player.x - view_x)
        player_cy = int(player.y - view_y)
        if is_running and winner is None:
            pygame.draw.circle(
                surf, BLUE, (player_cx, player_cy), icon_size // 2 + 10, 2)
        draw_player_icon(surf, player_cx, player_cy, icon_size, player.heading)
        p_name_surf = small_font.render(player.name, True, WHITE)
        p_name_rect = p_name_surf.get_rect(
            centerx=player_cx, bottom=player_cy - icon_size // 2 - 12)
        surf.blit(p_name_surf, p_name_rect)
