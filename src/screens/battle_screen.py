"""
The main battle screen implementation, managing real-time combat
flow, player interaction, and CPU logic.
"""
import logging
import math
import pygame
import random
from src.core.base_screen import BaseScreen
from src.constants import *
from src.models.ship import Ship
from src.models.weapon import Weapon
from src.utils.helpers import make_stars, wrap_text
from src.ui.map import Map
from src.ui.elements import draw_info_card
from src.systems.combat import CombatSystem

_log = logging.getLogger(__name__)


class BattleScreen(BaseScreen):
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        if hasattr(pygame.key, "stop_text_input"):
            pygame.key.stop_text_input()
        self.screen_w, self.screen_h = self._screen_size()
        self.font = pygame.font.SysFont(None, 28)
        self.big_font = pygame.font.SysFont(None, 44)
        self.small_font = pygame.font.SysFont(None, 22)

        self.available_weapons = Weapon.load_weapons("data/weapons.yaml")
        self.map_world_w = int((self.screen_w - PANEL_W) * 3)
        self.map_world_h = int(self.screen_h * 3)
        self.map_view_x = (self.map_world_w - (self.screen_w - PANEL_W)) / 2.0
        self.map_view_y = (self.map_world_h - self.screen_h) / 2.0
        self.player, self.cpu = self._make_game()
        star_count = max(150, (self.map_world_w * self.map_world_h) // 10000)
        self.map = Map(make_stars(star_count, self.map_world_w, self.map_world_h))

        self.is_paused = True
        self.message = "Paused. Press Space to start."
        self.winner = None

        self.cpu_fire_at_ms = None
        self.CPU_DELAY_MS = 900
        self.ATTACK_ANIM_MS = 240
        self.CPU_TRAIL_DISTANCE_PX = SHIP_ICON_SIZE * 2.0
        self.MIN_SHIP_SEPARATION_PX = SHIP_ICON_SIZE * 1.2
        self.CPU_HEADING_FOLLOW_MIN_MS = 1000
        self.CPU_HEADING_FOLLOW_MAX_MS = 3000

        self.weapon_buttons = {}
        self.weapon_detail_toggles = {}
        self.expanded_weapons = set()
        self.cpu_weapon_buttons = {}
        self.cpu_weapon_detail_toggles = {}
        self.cpu_expanded_weapons = set()
        self.ui_elements = {}
        self.panel_expanded = True
        self.attack_animation = None
        self.game_time_ms: int = 0
        self.toggle_tab_rect = pygame.Rect(
            self.screen_w - TAB_W, self.screen_h // 2 - TAB_H // 2, TAB_W, TAB_H)
        self.turn_left_held = False
        self.turn_right_held = False
        self.waypoints: list[tuple[float, float]] = []
        self.queued_player_attacks: list[int] = []
        self.cpu_follow_heading_deg = self.player.heading
        self.cpu_pending_follow_heading_deg: float | None = None
        self.cpu_follow_heading_apply_at_ms = 0
        self.map_dragging = False
        self.map_drag_last_pos: tuple[int, int] | None = None
        self.pause_menu_visible = False

    def _screen_size(self) -> tuple[int, int]:
        if hasattr(self.screen_manager, "screen") and hasattr(self.screen_manager.screen, "get_size"):
            w, h = self.screen_manager.screen.get_size()
            if isinstance(w, int) and isinstance(h, int) and w > 0 and h > 0:
                return w, h
        return WIDTH, HEIGHT

    def _current_map_width(self):
        return self.screen_w - PANEL_W if self.panel_expanded else self.screen_w

    @staticmethod
    def _is_key_physically_pressed(key_code: int) -> bool:
        try:
            return bool(pygame.key.get_pressed()[key_code])
        except (IndexError, TypeError, pygame.error):
            return False

    @staticmethod
    def _current_mods() -> int:
        try:
            return pygame.key.get_mods()
        except pygame.error:
            return 0

    def _is_map_point(self, pos):
        x, y = pos
        return 0 <= x <= self._current_map_width() and 0 <= y <= self.screen_h

    def _screen_to_world(self, pos: tuple[int, int]) -> tuple[float, float]:
        return float(pos[0]) + self.map_view_x, float(pos[1]) + self.map_view_y

    def _clamp_map_view(self) -> None:
        map_w = self._current_map_width()
        max_x = max(0.0, float(self.map_world_w - map_w))
        max_y = max(0.0, float(self.map_world_h - self.screen_h))
        self.map_view_x = max(0.0, min(max_x, self.map_view_x))
        self.map_view_y = max(0.0, min(max_y, self.map_view_y))

    def _enforce_minimum_ship_separation(self) -> None:
        dx = self.player.x - self.cpu.x
        dy = self.player.y - self.cpu.y
        dist = math.hypot(dx, dy)
        if dist >= self.MIN_SHIP_SEPARATION_PX:
            return
        if dist <= 1e-6:
            dx, dy, dist = 1.0, 0.0, 1.0
        nx = dx / dist
        ny = dy / dist
        push = (self.MIN_SHIP_SEPARATION_PX - dist) / 2.0

        self.player.x += nx * push
        self.player.y += ny * push
        self.cpu.x -= nx * push
        self.cpu.y -= ny * push

        self.player.x = max(0.0, min(float(self.map_world_w), self.player.x))
        self.player.y = max(0.0, min(float(self.map_world_h), self.player.y))
        self.cpu.x = max(0.0, min(float(self.map_world_w), self.cpu.x))
        self.cpu.y = max(0.0, min(float(self.map_world_h), self.cpu.y))

    @staticmethod
    def _heading_delta_deg(a: float, b: float) -> float:
        return abs((a - b + 180.0) % 360.0 - 180.0)

    def _update_cpu_follow_heading_delay(self, now_ms: int) -> None:
        current_heading = self.player.heading % 360.0
        if self.cpu_pending_follow_heading_deg is None:
            if self._heading_delta_deg(current_heading, self.cpu_follow_heading_deg) > 0.1:
                self.cpu_pending_follow_heading_deg = current_heading
                self.cpu_follow_heading_apply_at_ms = now_ms + random.randint(
                    self.CPU_HEADING_FOLLOW_MIN_MS, self.CPU_HEADING_FOLLOW_MAX_MS
                )
        else:
            if self._heading_delta_deg(current_heading, self.cpu_pending_follow_heading_deg) > 0.1:
                self.cpu_pending_follow_heading_deg = current_heading
                self.cpu_follow_heading_apply_at_ms = now_ms + random.randint(
                    self.CPU_HEADING_FOLLOW_MIN_MS, self.CPU_HEADING_FOLLOW_MAX_MS
                )
            elif now_ms >= self.cpu_follow_heading_apply_at_ms:
                self.cpu_follow_heading_deg = self.cpu_pending_follow_heading_deg
                self.cpu_pending_follow_heading_deg = None

    def _finish_game(self, winner: str) -> None:
        self.winner = winner
        result_message = "Computer wins!" if winner == "Computer" else "Player wins!"
        from src.screens.menu_screen import MenuScreen
        self.screen_manager.set_screen(MenuScreen, result_message=result_message)

    def _pause_menu_buttons(self) -> dict[str, dict[str, pygame.Rect | str | tuple[int, int, int]]]:
        menu_w = 300
        menu_h = 180
        menu_x = self.screen_w // 2 - menu_w // 2
        menu_y = self.screen_h // 2 - menu_h // 2
        btn_w = 220
        btn_h = 48
        btn_x = self.screen_w // 2 - btn_w // 2
        resume_y = menu_y + 50
        quit_y = resume_y + btn_h + 16
        return {
            "menu_rect": {"rect": pygame.Rect(menu_x, menu_y, menu_w, menu_h)},
            "resume": {
                "rect": pygame.Rect(btn_x, resume_y, btn_w, btn_h),
                "text": "RESUME",
                "color": BLUE,
            },
            "quit": {
                "rect": pygame.Rect(btn_x, quit_y, btn_w, btn_h),
                "text": "QUIT",
                "color": RED,
            },
        }

    def _set_pause_menu_visible(self, visible: bool, now: int) -> None:
        self.pause_menu_visible = visible
        if visible:
            self.is_paused = True
            self.cpu_fire_at_ms = None
            self.message = "Paused. Select RESUME or QUIT."
        else:
            self.is_paused = False
            self.cpu_fire_at_ms = now + self.CPU_DELAY_MS
            self.message = "Battle running. Press Space to pause."

    def _fire_player_weapon(self, weapon_idx: int, now_ms: int) -> bool:
        if not (0 <= weapon_idx < len(self.player.weapons)):
            return False
        weapon = self.player.weapons[weapon_idx]
        if not weapon.can_fire():
            return False

        hit, dmg = CombatSystem.execute_attack(self.player, weapon, self.cpu)
        self._start_attack_animation(True, weapon.name, hit, now_ms)
        if hit:
            self.message = (
                f"You fired {weapon.name} "
                f"for {dmg} damage. "
                "Keep firing while weapons are ready."
            )
        else:
            self.message = (
                f"You fired {weapon.name} "
                "and MISSED. "
                "Keep firing while weapons are ready."
            )

        if self.cpu.is_dead():
            self._finish_game("Player")
        return True

    def _toggle_pause(self, now):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.message = "Paused. Press Space to resume."
            self.cpu_fire_at_ms = None
        else:
            self.message = "Battle running. Press Space to pause."
            self.cpu_fire_at_ms = now + self.CPU_DELAY_MS
        _log.info("T+%.3fs %s", self.game_time_ms / 1000, "paused" if self.is_paused else "unpaused")

    @staticmethod
    def _is_repeat_keydown(event) -> bool:
        repeat = getattr(event, "repeat", 0)
        if isinstance(repeat, bool):
            return repeat
        if isinstance(repeat, int):
            return repeat != 0
        return False

    def _make_game(self):
        # Create unique instances for each ship
        # To match the "From: [laser x 2] [ion beam x 1]" example:
        map_center_x = self.map_world_w / 2.0
        map_center_y = self.map_world_h / 2.0
        p_weapons = []
        laser = self.available_weapons["Laser"]
        ion = self.available_weapons["Ion Beam"]

        # Two lasers
        p_weapons.append(Weapon(laser.name, laser.damage_range,
                         laser.cooldown, laser.hit_chance, 0, laser.charges))
        p_weapons.append(Weapon(laser.name, laser.damage_range,
                         laser.cooldown, laser.hit_chance, 0, laser.charges))
        # One ion beam
        p_weapons.append(Weapon(ion.name, ion.damage_range,
                         ion.cooldown, ion.hit_chance, 0, ion.charges))

        c_weapons = []
        # Computer gets three lasers
        c_weapons.append(Weapon(laser.name, laser.damage_range,
                         laser.cooldown, laser.hit_chance, 0, laser.charges))
        c_weapons.append(Weapon(laser.name, laser.damage_range,
                         laser.cooldown, laser.hit_chance, 0, laser.charges))
        c_weapons.append(Weapon(laser.name, laser.damage_range,
                         laser.cooldown, laser.hit_chance, 0, laser.charges))

        player = Ship(
            name="Player",
            max_hp=750,
            hp=750,
            weapons=p_weapons,
            x=map_center_x,
            y=map_center_y + self.screen_h / 4.0,
            heading=0.0,
            rotation_speed_deg_s=45.0,
        )
        cpu = Ship(
            name="Computer",
            max_hp=500,
            hp=500,
            weapons=c_weapons,
            x=map_center_x,
            y=map_center_y - self.screen_h / 4.0,
            heading=180.0,
            rotation_speed_deg_s=25.0,
        )
        return player, cpu

    def handle_event(self, event):
        now = pygame.time.get_ticks()
        if self.winner is not None:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.player, self.cpu = self._make_game()
                self.is_paused = True
                self.message = "Paused. Press Space to start."
                self.winner = None
                self.cpu_fire_at_ms = None
                self.attack_animation = None
                self.game_time_ms = 0
                self.weapon_buttons.clear()
                self.weapon_detail_toggles.clear()
                self.expanded_weapons.clear()
                self.cpu_weapon_buttons.clear()
                self.cpu_weapon_detail_toggles.clear()
                self.cpu_expanded_weapons.clear()
                self.ui_elements.clear()
                self.turn_left_held = False
                self.turn_right_held = False
                self.waypoints.clear()
                self.queued_player_attacks.clear()
                self.cpu_follow_heading_deg = self.player.heading
                self.cpu_pending_follow_heading_deg = None
                self.cpu_follow_heading_apply_at_ms = 0
                self.map_dragging = False
                self.map_drag_last_pos = None
                self.pause_menu_visible = False
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if self.pause_menu_visible:
                return
            if self._is_repeat_keydown(event):
                return
            self._toggle_pause(now)
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.pause_menu_visible:
                self._set_pause_menu_visible(False, now)
            else:
                self._set_pause_menu_visible(True, now)
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_a:
            self.turn_left_held = True
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_d:
            self.turn_right_held = True
            return
        if event.type == pygame.KEYUP and event.key == pygame.K_a:
            self.turn_left_held = False
            return
        if event.type == pygame.KEYUP and event.key == pygame.K_d:
            self.turn_right_held = False
            return

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.map_dragging = False
            self.map_drag_last_pos = None
            return

        if event.type == pygame.MOUSEMOTION and self.map_dragging:
            if self.map_drag_last_pos is not None:
                dx = event.pos[0] - self.map_drag_last_pos[0]
                dy = event.pos[1] - self.map_drag_last_pos[1]
                self.map_view_x -= float(dx)
                self.map_view_y -= float(dy)
                self._clamp_map_view()
            self.map_drag_last_pos = event.pos
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.pause_menu_visible:
            buttons = self._pause_menu_buttons()
            if buttons["resume"]["rect"].collidepoint(event.pos):
                self._set_pause_menu_visible(False, now)
            elif buttons["quit"]["rect"].collidepoint(event.pos):
                from src.screens.menu_screen import MenuScreen
                self.screen_manager.set_screen(MenuScreen)
            return

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self._is_map_point(event.pos)
        ):
            mods = self._current_mods()
            pos = self._screen_to_world(event.pos)
            if mods & pygame.KMOD_CTRL:
                self.waypoints = [pos]
                if hasattr(pygame.key, "stop_text_input"):
                    pygame.key.stop_text_input()
                return
            if mods & pygame.KMOD_SHIFT:
                self.waypoints.append(pos)
                if hasattr(pygame.key, "stop_text_input"):
                    pygame.key.stop_text_input()
                return
            click_hits_ui = (
                self.toggle_tab_rect.collidepoint(event.pos)
                or any(r.collidepoint(event.pos) for r in self.weapon_buttons.values())
                or any(r.collidepoint(event.pos) for r in self.weapon_detail_toggles.values())
                or any(r.collidepoint(event.pos) for r in self.cpu_weapon_buttons.values())
                or any(r.collidepoint(event.pos) for r in self.cpu_weapon_detail_toggles.values())
            )
            if not click_hits_ui:
                self.map_dragging = True
                self.map_drag_last_pos = event.pos
                return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.toggle_tab_rect.collidepoint(pos):
                self.panel_expanded = not self.panel_expanded
                self._clamp_map_view()
                self.weapon_buttons.clear()
                self.weapon_detail_toggles.clear()
                self.cpu_weapon_buttons.clear()
                self.cpu_weapon_detail_toggles.clear()
                self.ui_elements.clear()
            else:
                # Check player weapon detail toggles
                for idx, toggle_rect in self.weapon_detail_toggles.items():
                    if toggle_rect.collidepoint(pos):
                        if idx in self.expanded_weapons:
                            self.expanded_weapons.remove(idx)
                        else:
                            self.expanded_weapons.add(idx)
                        return

                # Check CPU weapon detail toggles
                for idx, toggle_rect in self.cpu_weapon_detail_toggles.items():
                    if toggle_rect.collidepoint(pos):
                        if idx in self.cpu_expanded_weapons:
                            self.cpu_expanded_weapons.remove(idx)
                        else:
                            self.cpu_expanded_weapons.add(idx)
                        return

                if not self.is_paused:
                    for idx, btn_rect in self.weapon_buttons.items():
                        if btn_rect.collidepoint(pos):
                            fired = self._fire_player_weapon(idx, now)
                            if not fired:
                                if idx in self.queued_player_attacks:
                                    self.queued_player_attacks.remove(idx)
                                else:
                                    self.queued_player_attacks.append(idx)
                            break
                else:
                    for idx, btn_rect in self.weapon_buttons.items():
                        if btn_rect.collidepoint(pos):
                            if idx in self.queued_player_attacks:
                                self.queued_player_attacks.remove(idx)
                            else:
                                self.queued_player_attacks.append(idx)
                            break

    def update(self, dt):
        now = pygame.time.get_ticks()
        if self.winner is not None or self.is_paused:
            return

        self.game_time_ms += dt
        dt_seconds = dt / 1000.0
        for w in self.player.weapons:
            w.tick_seconds(dt_seconds)
        for w in self.cpu.weapons:
            w.tick_seconds(dt_seconds)

        left_pressed = self.turn_left_held or self._is_key_physically_pressed(pygame.K_a)
        right_pressed = self.turn_right_held or self._is_key_physically_pressed(pygame.K_d)
        manual_override = left_pressed or right_pressed
        if manual_override and self.waypoints:
            self.waypoints.clear()

        if left_pressed:
            self.player.heading -= self.player.rotation_speed_deg_s * dt_seconds
        elif right_pressed:
            self.player.heading += self.player.rotation_speed_deg_s * dt_seconds
        elif self.waypoints:
            waypoint = self.waypoints[0]
            wp_dx = waypoint[0] - self.player.x
            wp_dy = waypoint[1] - self.player.y
            if math.hypot(wp_dx, wp_dy) <= 12.0:
                self.waypoints.pop(0)
            else:
                target_heading = math.degrees(math.atan2(wp_dx, -wp_dy)) % 360.0
                delta = (target_heading - self.player.heading + 540.0) % 360.0 - 180.0
                max_turn = self.player.rotation_speed_deg_s * dt_seconds
                if delta > max_turn:
                    delta = max_turn
                elif delta < -max_turn:
                    delta = -max_turn
                self.player.heading = (self.player.heading + delta) % 360.0
        self.player.heading %= 360.0

        heading_rad = math.radians(self.player.heading)
        self.player.x += math.sin(heading_rad) * self.player.speed_px_s * dt_seconds
        self.player.y -= math.cos(heading_rad) * self.player.speed_px_s * dt_seconds
        self.player.x = max(0.0, min(float(self.map_world_w), self.player.x))
        self.player.y = max(0.0, min(float(self.map_world_h), self.player.y))

        if self.queued_player_attacks and self.winner is None:
            queued_idx = self.queued_player_attacks[0]
            if self._fire_player_weapon(queued_idx, now):
                self.queued_player_attacks.pop(0)
            if self.winner is not None:
                return

        self._update_cpu_follow_heading_delay(now)

        player_heading_rad = math.radians(self.cpu_follow_heading_deg)
        player_forward_x = math.sin(player_heading_rad)
        player_forward_y = -math.cos(player_heading_rad)
        target_x = self.player.x - player_forward_x * self.CPU_TRAIL_DISTANCE_PX
        target_y = self.player.y - player_forward_y * self.CPU_TRAIL_DISTANCE_PX

        player_dx = self.player.x - self.cpu.x
        player_dy = self.player.y - self.cpu.y
        if math.hypot(player_dx, player_dy) < self.MIN_SHIP_SEPARATION_PX * 1.5:
            side_sign = 1.0 if (player_dx * player_forward_y - player_dy * player_forward_x) >= 0 else -1.0
            side_x = -player_forward_y * (self.CPU_TRAIL_DISTANCE_PX * 0.5) * side_sign
            side_y = player_forward_x * (self.CPU_TRAIL_DISTANCE_PX * 0.5) * side_sign
            target_x = self.player.x + side_x
            target_y = self.player.y + side_y

        dx = target_x - self.cpu.x
        dy = target_y - self.cpu.y
        if dx != 0.0 or dy != 0.0:
            target_heading = math.degrees(math.atan2(dx, -dy)) % 360.0
            delta = (target_heading - self.cpu.heading + 540.0) % 360.0 - 180.0
            max_turn = self.cpu.rotation_speed_deg_s * dt_seconds
            if delta > max_turn:
                delta = max_turn
            elif delta < -max_turn:
                delta = -max_turn
            self.cpu.heading = (self.cpu.heading + delta) % 360.0

        cpu_heading_rad = math.radians(self.cpu.heading)
        self.cpu.x += math.sin(cpu_heading_rad) * self.cpu.speed_px_s * dt_seconds
        self.cpu.y -= math.cos(cpu_heading_rad) * self.cpu.speed_px_s * dt_seconds
        self.cpu.x = max(0.0, min(float(self.map_world_w), self.cpu.x))
        self.cpu.y = max(0.0, min(float(self.map_world_h), self.cpu.y))
        self._enforce_minimum_ship_separation()

        if self.cpu_fire_at_ms is not None and now >= self.cpu_fire_at_ms:
            available = [w for w in self.cpu.weapons if w.can_fire()]
            if available:
                weapon = random.choice(available)
                hit, dmg = CombatSystem.execute_attack(
                    self.cpu, weapon, self.player)
                self._start_attack_animation(
                    False, weapon.name, hit, now
                )
                if hit:
                    self.message = (
                        f"Computer fired {weapon.name} "
                        f"for {dmg} damage."
                    )
                else:
                    self.message = (
                        f"Computer fired {weapon.name} and MISSED."
                    )

                if self.player.is_dead():
                    self._finish_game("Computer")
                    return
            self.cpu_fire_at_ms = now + self.CPU_DELAY_MS

    def draw(self, screen):
        self.screen_w, self.screen_h = self._screen_size()
        screen.fill(BG)
        panel_x = self.screen_w - PANEL_W if self.panel_expanded else self.screen_w
        map_w = self.screen_w - PANEL_W if self.panel_expanded else self.screen_w

        self.map.draw(
            screen,
            map_w,
            self.player,
            self.cpu,
            (not self.is_paused),
            self.winner,
            self.font,
            self.small_font,
            self.waypoints,
            self.map_view_x,
            self.map_view_y,
        )
        self._draw_attack_animation(screen, map_w)

        if self.panel_expanded:
            self._draw_side_panel(screen, panel_x)
        else:
            self._draw_collapsed_bar(screen)

        self.toggle_tab_rect = self._draw_toggle_tab(screen, panel_x)

        if self.pause_menu_visible:
            self._draw_pause_menu_overlay(screen)

        if self.winner is not None:
            self._draw_winner_overlay(screen)

    def _start_attack_animation(self, player_fired, weapon_name, hit, now_ms):
        color = RED if weapon_name == "Laser" else YELLOW
        if player_fired:
            start = (self.player.x, self.player.y)
            target = (self.cpu.x, self.cpu.y)
        else:
            start = (self.cpu.x, self.cpu.y)
            target = (self.player.x, self.player.y)
        self.attack_animation = {
            "color": color,
            "start": start,
            "target": target,
            "missed": not hit,
            "started_at_ms": now_ms,
            "duration_ms": self.ATTACK_ANIM_MS,
        }

    def _beam_end_for_draw(self, start, target, missed, map_w):
        if not missed:
            return target

        sx, sy = start
        tx, ty = target
        dx = tx - sx
        dy = ty - sy

        candidates = []
        if dx != 0:
            for bx in (0, map_w):
                t = (bx - sx) / dx
                y = sy + t * dy
                if t > 1.0 and 0 <= y <= self.screen_h:
                    candidates.append((t, (int(round(bx)), int(round(y)))))
        if dy != 0:
            for by in (0, self.screen_h):
                t = (by - sy) / dy
                x = sx + t * dx
                if t > 1.0 and 0 <= x <= map_w:
                    candidates.append((t, (int(round(x)), int(round(by)))))

        if not candidates:
            return target
        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]

    def _draw_attack_animation(self, screen, map_w):
        if self.attack_animation is None:
            return

        now = pygame.time.get_ticks()
        elapsed = now - self.attack_animation["started_at_ms"]
        duration = self.attack_animation["duration_ms"]
        if elapsed >= duration:
            self.attack_animation = None
            return

        progress = max(0.0, min(1.0, elapsed / duration))
        beam_w = max(2, int(7 * (1.0 - progress)))
        start = (
            self.attack_animation["start"][0] - self.map_view_x,
            self.attack_animation["start"][1] - self.map_view_y,
        )
        target = (
            self.attack_animation["target"][0] - self.map_view_x,
            self.attack_animation["target"][1] - self.map_view_y,
        )

        old_clip = screen.get_clip()
        screen.set_clip(pygame.Rect(0, 0, map_w, self.screen_h))
        pygame.draw.line(
            screen,
            self.attack_animation["color"],
            start,
            self._beam_end_for_draw(
                start,
                target,
                self.attack_animation["missed"],
                map_w,
            ),
            beam_w,
        )
        screen.set_clip(old_clip)

    def _draw_side_panel(self, surf, panel_x):
        panel_rect = pygame.Rect(panel_x, 0, PANEL_W, self.screen_h)
        pygame.draw.rect(surf, PANEL_BG, panel_rect)
        pygame.draw.line(surf, PANEL_BORDER, (panel_x, 0),
                         (panel_x, self.screen_h), 1)

        inner_x = panel_x + PANEL_PAD
        inner_w = PANEL_W - 2 * PANEL_PAD
        remaining_h = self.screen_h - 2 * PANEL_PAD - MSG_H
        card_h = remaining_h // 2 - PANEL_PAD // 2

        cpu_card_rect = pygame.Rect(inner_x, PANEL_PAD, inner_w, card_h)
        msg_y = cpu_card_rect.bottom + PANEL_PAD // 2
        msg_rect = pygame.Rect(inner_x, msg_y, inner_w, MSG_H)
        player_card_rect = pygame.Rect(
            inner_x, msg_rect.bottom + PANEL_PAD // 2, inner_w, card_h)

        draw_info_card(
            surf,
            cpu_card_rect,
            self.font,
            self.cpu,
            False,
            (not self.is_paused),
            self.winner,
            self.cpu_weapon_buttons,
            self.ui_elements,
            self.cpu_weapon_detail_toggles,
            self.cpu_expanded_weapons,
        )

        # Message strip
        pygame.draw.rect(surf, (20, 24, 38), msg_rect, border_radius=8)
        pygame.draw.rect(surf, PANEL_BORDER, msg_rect, 1, border_radius=8)
        lines = wrap_text(self.small_font, self.message, inner_w - 12)
        line_h = self.small_font.get_linesize() + 2
        text_y = msg_rect.y + (msg_rect.height - len(lines) * line_h) // 2
        for line in lines:
            line_surf = self.small_font.render(line, True, WHITE)
            surf.blit(line_surf, (msg_rect.x + 8, text_y))
            text_y += line_h

        draw_info_card(
            surf,
            player_card_rect,
            self.font,
            self.player,
            True,
            (not self.is_paused),
            self.winner,
            self.weapon_buttons,
            self.ui_elements,
            self.weapon_detail_toggles,
            self.expanded_weapons,
            set(self.queued_player_attacks),
        )

    def _draw_collapsed_bar(self, screen):
        bar_h = 40
        overlay = pygame.Surface((self.screen_w, bar_h), pygame.SRCALPHA)
        overlay.fill((10, 12, 22, 200))
        screen.blit(overlay, (0, self.screen_h - bar_h))
        msg_surf = self.small_font.render(self.message, True, WHITE)
        screen.blit(msg_surf, msg_surf.get_rect(
            center=(self.screen_w // 2, self.screen_h - bar_h // 2)))

    def _draw_toggle_tab(self, surf, panel_x):
        if self.panel_expanded:
            tab_x = panel_x - TAB_W + 4
        else:
            tab_x = self.screen_w - TAB_W
        tab_y = self.screen_h // 2 - TAB_H // 2
        tab_rect = pygame.Rect(tab_x, tab_y, TAB_W, TAB_H)
        pygame.draw.rect(surf, PANEL_BG, tab_rect, border_radius=8)
        pygame.draw.rect(surf, PANEL_BORDER, tab_rect, 2, border_radius=8)
        arrow = ">>" if self.panel_expanded else "<<"
        arrow_surf = self.small_font.render(arrow, True, WHITE)
        surf.blit(arrow_surf, arrow_surf.get_rect(center=tab_rect.center))
        return tab_rect

    def _draw_winner_overlay(self, screen):
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        wtxt = self.big_font.render(f"{self.winner} wins!", True, WHITE)
        rtxt = self.font.render("Press R to restart", True, WHITE)
        screen.blit(wtxt, wtxt.get_rect(center=(self.screen_w // 2, self.screen_h // 2 - 20)))
        screen.blit(rtxt, rtxt.get_rect(center=(self.screen_w // 2, self.screen_h // 2 + 25)))

    def _draw_pause_menu_overlay(self, screen):
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        buttons = self._pause_menu_buttons()
        menu_rect = buttons["menu_rect"]["rect"]
        pygame.draw.rect(screen, PANEL_BG, menu_rect, border_radius=12)
        pygame.draw.rect(screen, PANEL_BORDER, menu_rect, 2, border_radius=12)

        title = self.font.render("PAUSED", True, WHITE)
        screen.blit(title, title.get_rect(center=(self.screen_w // 2, menu_rect.y + 26)))

        for key in ("resume", "quit"):
            btn = buttons[key]
            btn_rect = btn["rect"]
            pygame.draw.rect(screen, PANEL_BG, btn_rect, border_radius=10)
            pygame.draw.rect(screen, btn["color"], btn_rect, 2, border_radius=10)
            txt = self.small_font.render(btn["text"], True, WHITE)
            screen.blit(txt, txt.get_rect(center=btn_rect.center))
