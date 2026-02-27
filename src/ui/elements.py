"""
Reusable UI components for the game, including ship icons,
info cards, and health bars.
"""
import pygame
from src.constants import (
    PANEL_BG,
    PANEL_BORDER,
    BLUE,
    GRAY,
    GREEN,
    PHASE_END,
    PHASE_FIRE,
    WHITE,
)
from src.utils.helpers import hp_color, wrap_text
from src.models.ship import Ship


def draw_enemy_icon(surf: pygame.Surface, cx: int, cy: int, size: int) -> None:
    half = size // 2
    points = [
        (cx, cy + half),
        (cx - half, cy - half),
        (cx + half, cy - half),
    ]
    pygame.draw.polygon(surf, (90, 130, 200), points)
    pygame.draw.polygon(surf, PANEL_BORDER, points, 2)


def draw_player_icon(
        surf: pygame.Surface,
        cx: int,
        cy: int,
        size: int) -> None:
    half = size // 2
    pygame.draw.circle(surf, (180, 110, 70), (cx, cy), half)
    pygame.draw.circle(surf, PANEL_BORDER, (cx, cy), half, 2)
    head_r = max(4, size // 9)
    head_cy = cy - half // 3
    pygame.draw.circle(surf, WHITE, (cx, head_cy), head_r)
    body_top = head_cy + head_r
    body_bot = cy + half // 3
    pygame.draw.line(surf, WHITE, (cx, body_top), (cx, body_bot), 2)


def draw_info_card(
    surf: pygame.Surface,
    rect: pygame.Rect,
    font: pygame.font.Font,
    ship: Ship,
    is_player: bool,
    active_turn: bool,
    phase: str,
    winner: str | None,
    weapon_buttons_out: dict[int, pygame.Rect],
    ui_elements_out: dict[str, pygame.Rect],
    weapon_detail_toggles_out: dict[int, pygame.Rect],
    expanded_weapons: set[int],
) -> None:
    border_color = BLUE if (active_turn and winner is None) else PANEL_BORDER
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
    pygame.draw.rect(surf, (50, 55, 75),
                     (tx, ty, bar_w, bar_h), border_radius=5)
    fill_w = int(bar_w * max(0, ship.hp) /
                 ship.max_hp) if ship.max_hp > 0 else 0
    if fill_w > 0:
        pygame.draw.rect(
            surf, hp_color(ship.hp, ship.max_hp),
            (tx, ty, fill_w, bar_h), border_radius=5,
        )
    ty += bar_h + 4

    hp_str = f"HP: {ship.hp} / {ship.max_hp}"
    hp_surf = font.render(hp_str, True, hp_color(ship.hp, ship.max_hp))
    surf.blit(hp_surf, (tx, ty))
    ty += line_h + 6

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
        is_weapon_active = (
            active_turn
            and phase == PHASE_FIRE
            and w.can_fire()
            and winner is None
        )
        can_fire_now = (
            is_player
            and is_weapon_active
        )
        color = BLUE if is_weapon_active else (50, 55, 75)
        text_color = WHITE if (
            can_fire_now or not is_player) else (160, 160, 160)

        label = w.name
        if w.current_cooldown > 0:
            label += f" ({w.current_cooldown})"
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
                f"Cooldown: {w.cooldown} (turns)",
                f"Damage: {w.damage_range[0]} - {w.damage_range[1]}",
                f"Hit %: {w.hit_chance}%"
            ]
            for d_line in details:
                d_surf = font.render(d_line, True, (200, 200, 200))
                surf.blit(d_surf, (tx + 16, ty))
                ty += font.get_linesize()
            ty += 4

    if is_player:
        ty += 8
        et_label = "End Turn"
        et_enabled = active_turn and winner is None  # Can always end turn
        et_color = GREEN if et_enabled else GRAY
        et_text_color = WHITE if et_enabled else (160, 160, 160)

        et_surf = font.render(et_label, True, et_text_color)
        et_w = et_surf.get_width() + 32
        et_rect = pygame.Rect(tx, ty, et_w, btn_h)
        pygame.draw.rect(surf, et_color, et_rect, border_radius=8)
        pygame.draw.rect(surf, (30, 30, 45), et_rect, 1, border_radius=8)
        surf.blit(et_surf, (tx + 16, ty + (btn_h - et_surf.get_height()) // 2))
        ui_elements_out["end_turn"] = et_rect
