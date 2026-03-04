"""
Reusable UI components for the game, including ship icons,
info cards, and health bars.
"""
import math
from pathlib import Path
import pygame
from src.constants import (
    PANEL_BG,
    PANEL_BORDER,
    BLUE,
    GRAY,
    WHITE,
)
from src.utils.helpers import hp_color
from src.models.ship import Ship

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_PLAYER_ICON_PATH = _PROJECT_ROOT / "assets/images/ships/player_default.png"
_ENEMY_ICON_PATH = _PROJECT_ROOT / "assets/images/ships/computer_default.png"
_ICON_CACHE: dict[tuple[str, int], pygame.Surface | None] = {}


def _load_icon_surface(path: Path, size: int) -> pygame.Surface | None:
    key = (str(path), size)
    if key in _ICON_CACHE:
        return _ICON_CACHE[key]

    if not path.exists():
        _ICON_CACHE[key] = None
        return None

    try:
        loaded = pygame.image.load(str(path))
        _ICON_CACHE[key] = pygame.transform.smoothscale(loaded, (size, size))
    except pygame.error:
        _ICON_CACHE[key] = None
    return _ICON_CACHE[key]


def get_enemy_icon_surface(size: int) -> pygame.Surface | None:
    return _load_icon_surface(_ENEMY_ICON_PATH, size)


def get_player_icon_surface(size: int) -> pygame.Surface | None:
    return _load_icon_surface(_PLAYER_ICON_PATH, size)


def draw_enemy_icon(
    surf: pygame.Surface,
    cx: int,
    cy: int,
    size: int,
    heading_deg: float = 0.0,
) -> None:
    icon = get_enemy_icon_surface(size)
    if icon is not None:
        rotated_icon = pygame.transform.rotate(icon, -heading_deg)
        surf.blit(rotated_icon, rotated_icon.get_rect(center=(cx, cy)))
        return

    half = size // 2
    points = [
        (0.0, -float(half)),
        (-float(half), float(half)),
        (float(half), float(half)),
    ]
    theta = math.radians(heading_deg)
    sin_t = math.sin(theta)
    cos_t = math.cos(theta)
    rotated_points = [
        (
            int(round(cx + px * cos_t - py * sin_t)),
            int(round(cy + px * sin_t + py * cos_t)),
        )
        for px, py in points
    ]
    pygame.draw.polygon(surf, (90, 130, 200), rotated_points)
    pygame.draw.polygon(surf, PANEL_BORDER, rotated_points, 2)


def draw_player_icon(
        surf: pygame.Surface,
        cx: int,
        cy: int,
        size: int,
        heading_deg: float = 0.0) -> None:
    icon = get_player_icon_surface(size)
    if icon is None:
        icon = pygame.Surface((size, size), pygame.SRCALPHA)
        half = size // 2
        icx = size // 2
        icy = size // 2
        pygame.draw.circle(icon, (180, 110, 70), (icx, icy), half)
        pygame.draw.circle(icon, PANEL_BORDER, (icx, icy), half, 2)
        head_r = max(4, size // 9)
        head_cy = icy - half // 3
        pygame.draw.circle(icon, WHITE, (icx, head_cy), head_r)
        body_top = head_cy + head_r
        body_bot = icy + half // 3
        pygame.draw.line(icon, WHITE, (icx, body_top), (icx, body_bot), 2)

    rotated_icon = pygame.transform.rotate(icon, -heading_deg)
    surf.blit(rotated_icon, rotated_icon.get_rect(center=(cx, cy)))


def draw_info_card(
    surf: pygame.Surface,
    rect: pygame.Rect,
    font: pygame.font.Font,
    ship: Ship,
    is_player: bool,
    is_running: bool,
    winner: str | None,
    weapon_buttons_out: dict[int, pygame.Rect],
    ui_elements_out: dict[str, pygame.Rect],
    weapon_detail_toggles_out: dict[int, pygame.Rect],
    expanded_weapons: set[int],
    queued_weapon_indices: set[int] | None = None,
) -> None:
    border_color = BLUE if (is_running and winner is None) else PANEL_BORDER
    pygame.draw.rect(surf, PANEL_BG, rect, border_radius=12)
    pygame.draw.rect(surf, border_color, rect, 2, border_radius=12)

    pad = 12
    tx = rect.x + pad
    ty = rect.y + pad
    content_w = rect.width - 2 * pad
    line_h = font.get_linesize() + 2

    name_surf = font.render(ship.name, True, WHITE)
    surf.blit(name_surf, (tx, ty))
    ty += line_h + 4

    bar_h = 10
    bar_w = content_w
    pygame.draw.rect(surf, (50, 55, 75), (tx, ty, bar_w, bar_h), border_radius=5)
    fill_w = int(bar_w * max(0, ship.hull_hp) / ship.hull_max_hp) if ship.hull_max_hp > 0 else 0
    if fill_w > 0:
        pygame.draw.rect(
            surf, hp_color(ship.hull_hp, ship.hull_max_hp),
            (tx, ty, fill_w, bar_h), border_radius=5,
        )
    ty += bar_h + 4

    hull_str = f"Hull: {ship.hull_hp} / {ship.hull_max_hp}"
    hp_surf = font.render(hull_str, True, hp_color(ship.hull_hp, ship.hull_max_hp))
    surf.blit(hp_surf, (tx, ty))
    ty += line_h + 6

    shields = list(ship.shields[:6]) if ship.shields else [0] * 6
    while len(shields) < 6:
        shields.append(0)
    shield_max = max(1, int(ship.shield_max_hp))
    shield_cols = 3
    shield_col_w = content_w // shield_cols
    for idx, value in enumerate(shields):
        row = idx // shield_cols
        col = idx % shield_cols
        sx = tx + col * shield_col_w
        sy = ty + row * line_h
        shield_label = f"S{idx + 1}: {value}/{shield_max}"
        shield_color = hp_color(value, shield_max)
        shield_surf = font.render(shield_label, True, shield_color)
        surf.blit(shield_surf, (sx, sy))
    ty += (2 * line_h) + 6

    weapons_label = font.render("Weapons:", True, GRAY)
    surf.blit(weapons_label, (tx, ty))
    ty += line_h

    weapon_buttons_out.clear()
    weapon_detail_toggles_out.clear()
    ui_elements_out.clear()
    btn_h = line_h + 8
    btn_gap = 6

    for i, w in enumerate(ship.weapons):
        # Main weapon button
        # Player can fire; CPU uses the same active/inactive visual affordance.
        is_queued = (
            is_player
            and queued_weapon_indices is not None
            and i in queued_weapon_indices
            and winner is None
        )
        is_weapon_active = (
            is_running
            and w.can_fire()
            and winner is None
        )
        can_fire_now = (
            is_player
            and is_weapon_active
        )
        color = BLUE if is_weapon_active else (50, 55, 75)
        if is_queued:
            color = (210, 140, 55)
        text_color = WHITE if (
            can_fire_now or not is_player) else (160, 160, 160)
        if is_queued:
            text_color = WHITE

        label = f"[Q] {w.name}" if is_queued else w.name
        if w.current_cooldown_seconds > 0:
            label += f" ({w.current_cooldown_seconds:.1f}s)"
        elif w.charges is not None:
            label += f" ({w.charges})"

        btn_surf = font.render(label, True, text_color)
        # Reserve space for the ">>" affordance on the right
        affordance_w = 30
        btn_w = content_w - affordance_w - 4

        btn_rect = pygame.Rect(tx, ty, btn_w, btn_h)
        pygame.draw.rect(surf, color, btn_rect, border_radius=8)
        pygame.draw.rect(surf, (30, 30, 45), btn_rect, 1, border_radius=8)
        surf.blit(
            btn_surf,
            (tx + 12, ty + (btn_h - btn_surf.get_height()) // 2),
        )
        weapon_buttons_out[i] = btn_rect

        # Details affordance
        aff_rect = pygame.Rect(tx + btn_w + 4, ty, affordance_w, btn_h)
        pygame.draw.rect(surf, (40, 45, 60), aff_rect, border_radius=8)
        pygame.draw.rect(surf, PANEL_BORDER, aff_rect, 1, border_radius=8)

        aff_text = "<<" if i in expanded_weapons else ">>"
        aff_surf = font.render(aff_text, True, WHITE)
        surf.blit(aff_surf, aff_surf.get_rect(center=aff_rect.center))
        weapon_detail_toggles_out[i] = aff_rect

        ty += btn_h + btn_gap

        # Expanded details
        if i in expanded_weapons:
            details = [
                f"Cooldown: {w.cooldown_seconds:.1f}s",
                f"Damage: {w.damage_range[0]} - {w.damage_range[1]}",
                f"Hit %: {w.hit_chance}%"
            ]
            for d_line in details:
                d_surf = font.render(d_line, True, (200, 200, 200))
                surf.blit(d_surf, (tx + 16, ty))
                ty += font.get_linesize()
            ty += 4
