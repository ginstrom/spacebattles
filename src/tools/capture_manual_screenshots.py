"""Generate deterministic screenshots for the player manual."""

from __future__ import annotations

import argparse
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pygame

from src.constants import PANEL_W
from src.main import build_game
from src.screens.battle_screen import BattleScreen


@dataclass(frozen=True)
class ManualScreenshotConfig:
    output_dir: str = "docs/images/manual"


@dataclass(frozen=True)
class ManualShot:
    filename: str
    setup: Callable[[BattleScreen], None]
    settle_frames: int = 2


def screenshot_filenames() -> list[str]:
    return [
        "battle-overview.png",
        "waypoint-planning.png",
        "combat-fire-exchange.png",
        "weapon-arc-preview.png",
        "zoomed-map.png",
        "distance-falloff-details.png",
    ]


def _reset_scene(screen: BattleScreen) -> None:
    screen.player, screen.cpu = screen._make_game()
    screen.is_paused = True
    screen.message = "Paused. Press Space to start."
    screen.winner = None
    screen.cpu_fire_at_ms = None
    screen.attack_animation = None
    screen.game_time_ms = 0
    screen.waypoints.clear()
    screen.waypoint_undo_stack.clear()
    screen.waypoint_redo_stack.clear()
    screen.queued_player_attacks.clear()
    screen.turn_left_held = False
    screen.turn_right_held = False
    screen.panel_expanded = True
    screen.weapon_buttons.clear()
    screen.weapon_detail_toggles.clear()
    screen.expanded_weapons.clear()
    screen.cpu_weapon_buttons.clear()
    screen.cpu_weapon_detail_toggles.clear()
    screen.cpu_expanded_weapons.clear()
    screen.hovered_player_weapon_idx = None
    screen.ui_elements.clear()
    screen.map_zoom = screen.default_map_zoom
    screen.map_view_x = (screen.map_world_w - (screen.screen_w - PANEL_W)) / 2.0
    screen.map_view_y = (screen.map_world_h - screen.screen_h) / 2.0
    screen._clamp_map_view()
    screen.map_dragging = False
    screen.map_drag_last_pos = None
    screen.pause_menu_visible = False
    screen.demo_script_enabled = False
    screen.demo_cursor_screen_pos = None


def _setup_overview(screen: BattleScreen) -> None:
    _reset_scene(screen)
    screen.message = "Paused. Press Space to start."


def _setup_waypoint_planning(screen: BattleScreen) -> None:
    _reset_scene(screen)
    x, y = screen.player.x, screen.player.y
    screen.waypoints = [
        (x + (screen.map_world_w * 0.06), y - (screen.map_world_h * 0.06)),
        (x + (screen.map_world_w * 0.12), y - (screen.map_world_h * 0.11)),
    ]
    screen.message = "Paused. Waypoint route preview is visible."


def _setup_combat_fire(screen: BattleScreen) -> None:
    _reset_scene(screen)
    screen.is_paused = False
    screen.message = "Battle running. Press Space to pause."
    screen._start_attack_animation(True, "Laser", True, pygame.time.get_ticks())


def _setup_weapon_arc_preview(screen: BattleScreen) -> None:
    _reset_scene(screen)
    screen.is_paused = False
    screen.message = "Battle running. Weapon arc preview shown."
    screen.weapon_buttons[0] = pygame.Rect(0, 0, 1, 1)
    screen.hovered_player_weapon_idx = 0


def _setup_zoomed_map(screen: BattleScreen) -> None:
    _reset_scene(screen)
    center = (screen._current_map_width() // 2, screen.screen_h // 2)
    screen._apply_zoom_at_cursor(1.0, center)
    screen._apply_zoom_at_cursor(1.0, center)
    screen.message = "Zoomed map view centered at cursor."


def _setup_distance_falloff(screen: BattleScreen) -> None:
    _reset_scene(screen)
    screen.cpu_expanded_weapons.add(2)
    screen.message = "Expanded weapon details include distance falloff stats."


def _shots() -> list[ManualShot]:
    return [
        ManualShot("battle-overview.png", _setup_overview),
        ManualShot("waypoint-planning.png", _setup_waypoint_planning),
        ManualShot("combat-fire-exchange.png", _setup_combat_fire),
        ManualShot("weapon-arc-preview.png", _setup_weapon_arc_preview, settle_frames=3),
        ManualShot("zoomed-map.png", _setup_zoomed_map),
        ManualShot("distance-falloff-details.png", _setup_distance_falloff),
    ]


def _step_frames(manager, dt_ms: int = 16, count: int = 1) -> None:
    for _ in range(max(1, count)):
        pygame.event.pump()
        manager.update(dt_ms)
        manager.draw()


def capture_manual_screenshots(cfg: ManualScreenshotConfig) -> list[Path]:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ["SPACEBATTLE_WINDOWED"] = "1"

    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    random.seed(7)
    manager, _clock = build_game()
    manager.set_screen(BattleScreen)
    if not isinstance(manager.current_screen, BattleScreen):
        raise RuntimeError("expected BattleScreen after setup")

    battle = manager.current_screen
    _step_frames(manager, count=2)
    saved_paths: list[Path] = []
    for shot in _shots():
        shot.setup(battle)
        _step_frames(manager, count=shot.settle_frames)
        output_path = output_dir / shot.filename
        pygame.image.save(manager.screen, str(output_path))
        saved_paths.append(output_path)

    pygame.quit()
    return saved_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture documentation screenshots from deterministic scenes.")
    parser.add_argument("--output-dir", default="docs/images/manual")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = ManualScreenshotConfig(output_dir=args.output_dir)
    capture_manual_screenshots(cfg)


if __name__ == "__main__":
    main()
