import unittest
import os
from unittest.mock import MagicMock, patch
import math
import pygame
from src.screens.battle_screen import BattleScreen
from src.screens.menu_screen import MenuScreen
from src.core.screen_manager import ScreenManager
from src.constants import WIDTH, HEIGHT, PANEL_W, TAB_W, TAB_H
from src.models.ship import Ship


class TestScreens(unittest.TestCase):
    def setUp(self):
        self.mock_surface = MagicMock(spec=pygame.Surface)
        self.mock_surface.get_size.return_value = (WIDTH, HEIGHT)
        self.manager = ScreenManager(self.mock_surface)

        with patch("pygame.font.SysFont") as mock_sysfont:
            mock_font = MagicMock(spec=pygame.font.Font)
            mock_font.get_linesize.return_value = 20
            mock_font.size.return_value = (50, 20)
            mock_text_surf = MagicMock(spec=pygame.Surface)
            mock_text_surf.get_width.return_value = 50
            mock_text_surf.get_height.return_value = 20
            mock_font.render.return_value = mock_text_surf
            mock_sysfont.return_value = mock_font
            self.screen = BattleScreen(self.manager)

        self.map_center_x = (WIDTH - PANEL_W) // 2
        self.cpu_y = HEIGHT // 4
        self.player_y = HEIGHT * 3 // 4

    def test_battle_screen_uses_runtime_surface_dimensions(self):
        dynamic_w, dynamic_h = 1920, 1080
        dynamic_surface = MagicMock(spec=pygame.Surface)
        dynamic_surface.get_size.return_value = (dynamic_w, dynamic_h)
        manager = ScreenManager(dynamic_surface)

        with patch("pygame.font.SysFont") as mock_sysfont:
            mock_font = MagicMock(spec=pygame.font.Font)
            mock_font.get_linesize.return_value = 20
            mock_font.size.return_value = (50, 20)
            mock_text_surf = MagicMock(spec=pygame.Surface)
            mock_text_surf.get_width.return_value = 50
            mock_text_surf.get_height.return_value = 20
            mock_font.render.return_value = mock_text_surf
            mock_sysfont.return_value = mock_font
            screen = BattleScreen(manager)

        self.assertEqual(screen.map_world_w, int((dynamic_w - PANEL_W) * 3))
        self.assertEqual(screen.map_world_h, int(dynamic_h * 3))
        self.assertEqual(
            screen.toggle_tab_rect,
            pygame.Rect(dynamic_w - TAB_W, dynamic_h // 2 - TAB_H // 2, TAB_W, TAB_H),
        )

    def test_menu_screen_uses_runtime_surface_dimensions_for_button_layout(self):
        dynamic_w, dynamic_h = 1920, 1080
        dynamic_surface = MagicMock(spec=pygame.Surface)
        dynamic_surface.get_size.return_value = (dynamic_w, dynamic_h)
        manager = ScreenManager(dynamic_surface)

        with patch("pygame.font.SysFont") as mock_sysfont:
            mock_sysfont.return_value = MagicMock(spec=pygame.font.Font)
            screen = MenuScreen(manager)

        new_game_rect = screen.buttons["new_game"]["rect"]
        self.assertEqual(new_game_rect.centerx, dynamic_w // 2)
        self.assertEqual(new_game_rect.y, dynamic_h // 2 + 20)

    @patch.dict(os.environ, {"SPACEBATTLE_DEMO_SCRIPT": "1"})
    def test_menu_screen_auto_starts_battle_in_demo_mode(self):
        with patch("pygame.font.SysFont") as mock_sysfont:
            mock_sysfont.return_value = MagicMock(spec=pygame.font.Font)
            screen = MenuScreen(self.manager)
        with patch.object(self.manager, "set_screen") as mock_set_screen:
            screen.update(16)
            mock_set_screen.assert_called_once()

    def _mouse_event(self, x=125, y=125):
        event = MagicMock()
        event.type = pygame.MOUSEBUTTONDOWN
        event.button = 1
        event.pos = (x, y)
        return event

    @staticmethod
    def _wheel_event(y):
        event = MagicMock()
        event.type = pygame.MOUSEWHEEL
        event.y = y
        return event

    @staticmethod
    def _key_event(key, mod=0):
        event = MagicMock()
        event.type = pygame.KEYDOWN
        event.key = key
        event.mod = mod
        event.repeat = 0
        return event

    class _PressedState:
        def __init__(self, pressed_keys):
            self.pressed_keys = pressed_keys

        def __getitem__(self, key):
            return self.pressed_keys.get(key, 0)

    @patch("pygame.time.get_ticks")
    def test_battle_screen_init_paused(self, mock_get_ticks):
        self.assertTrue(self.screen.is_paused)
        self.assertIn("Paused", self.screen.message)
        self.assertIsNone(self.screen.winner)

    @patch.dict(os.environ, {"SPACEBATTLE_DEMO_SCRIPT": "1"})
    @patch("pygame.time.get_ticks")
    def test_demo_script_unpauses_sets_waypoint_and_fires(self, mock_get_ticks):
        mock_get_ticks.side_effect = [0, 700, 950, 1250, 1550, 2100]

        with patch("pygame.font.SysFont") as mock_sysfont:
            mock_font = MagicMock(spec=pygame.font.Font)
            mock_font.get_linesize.return_value = 20
            mock_font.size.return_value = (50, 20)
            mock_text_surf = MagicMock(spec=pygame.Surface)
            mock_text_surf.get_width.return_value = 50
            mock_text_surf.get_height.return_value = 20
            mock_font.render.return_value = mock_text_surf
            mock_sysfont.return_value = mock_font
            screen = BattleScreen(self.manager)

        with patch.object(screen, "_fire_player_weapon", return_value=True) as mock_fire:
            screen.update(16)
            screen.update(16)
            screen.update(16)
            screen.update(16)
            screen.update(16)
            screen.update(16)

        self.assertFalse(screen.is_paused)
        self.assertEqual(len(screen.waypoints), 2)
        self.assertIsNotNone(screen.demo_cursor_screen_pos)
        mock_fire.assert_called()

    @patch("pygame.key.stop_text_input")
    def test_battle_screen_stops_text_input_for_ime(self, mock_stop_text_input):
        with patch("pygame.font.SysFont") as mock_sysfont:
            mock_font = MagicMock(spec=pygame.font.Font)
            mock_font.get_linesize.return_value = 20
            mock_font.size.return_value = (50, 20)
            mock_text_surf = MagicMock(spec=pygame.Surface)
            mock_text_surf.get_width.return_value = 50
            mock_text_surf.get_height.return_value = 20
            mock_font.render.return_value = mock_text_surf
            mock_sysfont.return_value = mock_font
            _ = BattleScreen(self.manager)
        mock_stop_text_input.assert_called_once()

    @patch("pygame.time.get_ticks")
    def test_battle_screen_initial_ship_spatial_state(self, mock_get_ticks):
        map_center_x = self.screen.map_world_w / 2.0
        map_center_y = self.screen.map_world_h / 2.0
        self.assertEqual(self.screen.player.x, map_center_x)
        self.assertEqual(self.screen.player.y, map_center_y + HEIGHT / 4.0)
        self.assertEqual(self.screen.player.heading, 0.0)
        self.assertEqual(self.screen.cpu.x, map_center_x)
        self.assertEqual(self.screen.cpu.y, map_center_y - HEIGHT / 4.0)
        self.assertEqual(self.screen.cpu.heading, 180.0)

    def test_cpu_loadout_includes_hell_beam(self):
        self.assertEqual(len(self.screen.cpu.weapons), 3)
        weapon_names = [w.name for w in self.screen.cpu.weapons]
        self.assertEqual(weapon_names.count("Laser"), 2)
        self.assertIn("Hell Beam", weapon_names)
        hell_beam = next(w for w in self.screen.cpu.weapons if w.name == "Hell Beam")
        self.assertEqual(hell_beam.cooldown, 3)

    def test_player_loadout_includes_protom_beam(self):
        self.assertEqual([w.name for w in self.screen.player.weapons], ["Laser", "Laser", "Protom Beam"])
        self.assertEqual(self.screen.player.weapons[2].cooldown, 6)

    def test_ship_weapon_mount_config_applies_facing_and_arc(self):
        self.screen.ship_configs["player"]["weapons"] = [
            {"name": "Laser", "facing_deg": 45},
            {"name": "Laser", "facing_deg": 315, "firing_arc_deg": 150},
            {"name": "Ion Beam", "facing_deg": 180},
        ]

        player, _ = self.screen._make_game()
        self.assertEqual(len(player.weapons), 3)
        self.assertEqual([w.facing_deg for w in player.weapons], [45.0, 315.0, 180.0])
        self.assertEqual(player.weapons[0].firing_arc_deg, 120.0)
        self.assertEqual(player.weapons[1].firing_arc_deg, 150.0)
        self.assertEqual(player.weapons[2].firing_arc_deg, 60.0)

    def test_ship_profiles_are_loaded_from_config(self):
        self.assertEqual(self.screen.player.name, "Alliance cruiser")
        self.assertEqual(self.screen.player.max_hp, 750)
        self.assertEqual(self.screen.player.hp, 750)
        self.assertEqual(self.screen.player.hull_max_hp, 750)
        self.assertEqual(self.screen.player.hull_hp, 750)
        self.assertEqual(self.screen.player.shield_max_hp, 120)
        self.assertEqual(len(self.screen.player.shields), 6)
        self.assertEqual(self.screen.player.shields, [120, 120, 100, 120, 120, 110])
        self.assertIn("weapons", self.screen.player.systems)
        self.assertEqual(
            self.screen.player.systems["weapons"]["max"],
            len(self.screen.player.weapons),
        )
        self.assertEqual(self.screen.cpu.name, "Gorlach cruiser")
        self.assertEqual(self.screen.cpu.max_hp, 500)
        self.assertEqual(self.screen.cpu.hp, 500)
        self.assertEqual(self.screen.cpu.hull_max_hp, 500)
        self.assertEqual(self.screen.cpu.hull_hp, 500)
        self.assertEqual(self.screen.cpu.shield_max_hp, 90)
        self.assertEqual(len(self.screen.cpu.shields), 6)
        self.assertEqual(self.screen.cpu.shields, [90, 90, 90, 75, 90, 90])
        self.assertIn("weapons", self.screen.cpu.systems)

    def test_make_game_uses_configured_shield_values(self):
        self.screen.ship_configs["player"]["shield_max_hp"] = 120
        self.screen.ship_configs["player"]["shields"] = [10, 20, 30, 40, 50, 60]
        self.screen.ship_configs["computer"]["shield_max_hp"] = 80
        self.screen.ship_configs["computer"]["shields"] = [80, 70, 60, 50, 40, 30]

        player, cpu = self.screen._make_game()

        self.assertEqual(player.shield_max_hp, 120)
        self.assertEqual(player.shields, [10, 20, 30, 40, 50, 60])
        self.assertEqual(cpu.shield_max_hp, 80)
        self.assertEqual(cpu.shields, [80, 70, 60, 50, 40, 30])

    def test_make_game_defaults_shields_when_config_missing(self):
        self.screen.ship_configs["player"].pop("shield_max_hp", None)
        self.screen.ship_configs["player"].pop("shields", None)
        self.screen.ship_configs["computer"].pop("shield_max_hp", None)
        self.screen.ship_configs["computer"].pop("shields", None)

        player, cpu = self.screen._make_game()

        self.assertEqual(player.shield_max_hp, 100)
        self.assertEqual(player.shields, [100] * 6)
        self.assertEqual(cpu.shield_max_hp, 100)
        self.assertEqual(cpu.shields, [100] * 6)

    def test_player_turn_rate_is_faster_than_cpu(self):
        self.assertLess(self.screen.player.rotation_speed_deg_s, 90.0)
        self.assertLess(self.screen.cpu.rotation_speed_deg_s, self.screen.player.rotation_speed_deg_s)
        self.assertAlmostEqual(
            self.screen.player.rotation_speed_deg_s / self.screen.cpu.rotation_speed_deg_s,
            2.0,
            places=2,
        )

    def test_ship_spatial_defaults(self):
        ship = Ship("Test", 100, 100, [])
        self.assertEqual(ship.x, 0.0)
        self.assertEqual(ship.y, 0.0)
        self.assertEqual(ship.heading, 0.0)
        self.assertEqual(ship.speed_px_s, HEIGHT / 20.0)
        self.assertEqual(ship.rotation_speed_deg_s, 90.0)

    @patch("pygame.time.get_ticks")
    def test_space_toggles_pause(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        event = MagicMock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_SPACE

        self.screen.handle_event(event)
        self.assertFalse(self.screen.is_paused)
        self.assertEqual(self.screen.cpu_fire_at_ms, 1000 + self.screen.CPU_DELAY_MS)

        # Second press toggles back to paused.
        self.screen.handle_event(event)
        self.assertTrue(self.screen.is_paused)
        self.assertIsNone(self.screen.cpu_fire_at_ms)

    @patch("pygame.time.get_ticks")
    def test_escape_opens_pause_menu_overlay_and_pauses(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        self.screen.is_paused = False
        event = MagicMock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_ESCAPE

        self.screen.handle_event(event)
        self.assertTrue(self.screen.is_paused)
        self.assertTrue(self.screen.pause_menu_visible)
        self.assertIsNone(self.screen.cpu_fire_at_ms)

    @patch("pygame.time.get_ticks")
    def test_pause_menu_resume_button_unpauses(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        self.screen.pause_menu_visible = True
        self.screen.is_paused = True
        buttons = self.screen._pause_menu_buttons()
        resume_rect = buttons["resume"]["rect"]
        event = self._mouse_event(resume_rect.centerx, resume_rect.centery)

        self.screen.handle_event(event)
        self.assertFalse(self.screen.pause_menu_visible)
        self.assertFalse(self.screen.is_paused)
        self.assertEqual(self.screen.cpu_fire_at_ms, 1000 + self.screen.CPU_DELAY_MS)

    @patch("pygame.time.get_ticks")
    def test_pause_menu_quit_button_returns_to_menu(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        self.screen.pause_menu_visible = True
        self.screen.is_paused = True
        buttons = self.screen._pause_menu_buttons()
        quit_rect = buttons["quit"]["rect"]
        event = self._mouse_event(quit_rect.centerx, quit_rect.centery)

        with patch.object(self.manager, "set_screen") as mock_set_screen:
            self.screen.handle_event(event)
            mock_set_screen.assert_called_once()

    @patch("pygame.time.get_ticks")
    def test_handle_event_weapon_click_ignored_while_paused(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        self.screen.weapon_buttons = {0: pygame.Rect(100, 100, 50, 50)}

        with patch("src.systems.combat.CombatSystem.execute_attack") as mock_attack:
            self.screen.handle_event(self._mouse_event())
            mock_attack.assert_not_called()

    @patch("pygame.time.get_ticks")
    def test_handle_event_weapon_click_when_running(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        self.screen.is_paused = False
        self.screen.weapon_buttons = {0: pygame.Rect(100, 100, 50, 50)}
        self.screen.player.x = 321.0
        self.screen.player.y = 654.0
        self.screen.cpu.x = 210.0
        self.screen.cpu.y = 123.0

        with patch("src.systems.combat.CombatSystem.execute_attack") as mock_attack:
            mock_attack.return_value = (True, 50)
            self.screen.handle_event(self._mouse_event())
            mock_attack.assert_called_once()
            self.assertIn("fired", self.screen.message)
            self.assertIsNotNone(self.screen.attack_animation)
            self.assertEqual(self.screen.attack_animation["start"], (321.0, 654.0))
            self.assertEqual(self.screen.attack_animation["target"], (210.0, 123.0))

    @patch("pygame.time.get_ticks")
    def test_handle_event_weapon_click_when_running_queues_if_on_cooldown(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        self.screen.is_paused = False
        self.screen.weapon_buttons = {0: pygame.Rect(100, 100, 50, 50)}
        self.screen.player.weapons[0].current_cooldown_seconds = 2.0

        with patch("src.systems.combat.CombatSystem.execute_attack") as mock_attack:
            self.screen.handle_event(self._mouse_event())
            mock_attack.assert_not_called()
            self.assertEqual(self.screen.queued_player_attacks, [0])

    @patch("pygame.time.get_ticks")
    def test_handle_event_weapon_click_when_running_queues_if_target_out_of_arc(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        self.screen.is_paused = False
        self.screen.weapon_buttons = {0: pygame.Rect(100, 100, 50, 50)}
        self.screen.player.heading = 0.0
        self.screen.player.weapons[0].firing_arc_deg = 60.0
        self.screen.cpu.x = self.screen.player.x
        self.screen.cpu.y = self.screen.player.y + 250.0

        with patch("src.systems.combat.CombatSystem.execute_attack") as mock_attack:
            self.screen.handle_event(self._mouse_event())
            mock_attack.assert_not_called()
            self.assertEqual(self.screen.queued_player_attacks, [0])

    @patch("pygame.time.get_ticks")
    def test_handle_event_weapon_click_when_running_unqueues_if_already_queued(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        self.screen.is_paused = False
        self.screen.weapon_buttons = {0: pygame.Rect(100, 100, 50, 50)}
        self.screen.player.weapons[0].current_cooldown_seconds = 2.0
        self.screen.queued_player_attacks = [0]

        with patch("src.systems.combat.CombatSystem.execute_attack") as mock_attack:
            self.screen.handle_event(self._mouse_event())
            mock_attack.assert_not_called()
            self.assertEqual(self.screen.queued_player_attacks, [])

    @patch("pygame.time.get_ticks")
    def test_handle_event_weapon_click_queues_while_paused(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        self.screen.is_paused = True
        panel_x = WIDTH - PANEL_W + 10
        self.screen.weapon_buttons = {0: pygame.Rect(panel_x, 100, 50, 50)}

        with patch("src.systems.combat.CombatSystem.execute_attack") as mock_attack:
            self.screen.handle_event(self._mouse_event(panel_x + 5, 110))
            mock_attack.assert_not_called()
            self.assertEqual(self.screen.queued_player_attacks, [0])

    @patch("pygame.time.get_ticks")
    def test_update_paused_does_not_tick_or_cpu_fire(self, mock_get_ticks):
        self.screen.is_paused = True
        self.screen.player.weapons[0].current_cooldown_seconds = 5.0
        self.screen.cpu_fire_at_ms = 1000
        mock_get_ticks.return_value = 2000

        with patch("src.systems.combat.CombatSystem.execute_attack") as mock_attack:
            self.screen.update(500)
            self.assertEqual(self.screen.player.weapons[0].current_cooldown_seconds, 5.0)
            mock_attack.assert_not_called()

    @patch("pygame.time.get_ticks")
    def test_update_running_ticks_cooldowns(self, mock_get_ticks):
        self.screen.is_paused = False
        self.screen.player.weapons[0].current_cooldown_seconds = 1.0
        mock_get_ticks.return_value = 1000
        self.screen.update(500)
        self.assertAlmostEqual(self.screen.player.weapons[0].current_cooldown_seconds, 0.5)

    @patch("pygame.time.get_ticks")
    def test_cpu_update_running_fires(self, mock_get_ticks):
        self.screen.is_paused = False
        self.screen.cpu_fire_at_ms = 1000
        mock_get_ticks.return_value = 2000
        self.screen.player.x = 330.0
        self.screen.player.y = 700.0
        self.screen.cpu.x = 450.0
        self.screen.cpu.y = 140.0

        with patch("src.systems.combat.CombatSystem.execute_attack") as mock_attack:
            mock_attack.return_value = (True, 40)
            self.screen.update(16)
            mock_attack.assert_called_once()
            self.assertIsNotNone(self.screen.attack_animation)
            self.assertEqual(self.screen.attack_animation["start"], (self.screen.cpu.x, self.screen.cpu.y))
            self.assertEqual(self.screen.attack_animation["target"], (self.screen.player.x, self.screen.player.y))
            self.assertEqual(self.screen.cpu_fire_at_ms, 2000 + self.screen.CPU_DELAY_MS)

    @patch("pygame.time.get_ticks")
    def test_update_fires_queued_weapon_when_running(self, mock_get_ticks):
        self.screen.is_paused = False
        self.screen.cpu_fire_at_ms = None
        self.screen.queued_player_attacks = [0]
        mock_get_ticks.return_value = 2000

        with patch("src.systems.combat.CombatSystem.execute_attack") as mock_attack:
            mock_attack.return_value = (True, 40)
            self.screen.update(16)
            mock_attack.assert_called_once()
            self.assertEqual(self.screen.queued_player_attacks, [])

    @patch("pygame.time.get_ticks")
    def test_update_keeps_queued_weapon_until_target_enters_firing_arc(self, mock_get_ticks):
        self.screen.is_paused = False
        self.screen.cpu_fire_at_ms = None
        self.screen.player.speed_px_s = 0.0
        self.screen.cpu.speed_px_s = 0.0
        self.screen.queued_player_attacks = [0]
        self.screen.player.weapons[0].firing_arc_deg = 60.0
        self.screen.player.heading = 0.0
        self.screen.cpu.x = self.screen.player.x
        self.screen.cpu.y = self.screen.player.y + 250.0
        mock_get_ticks.return_value = 2000

        with patch("src.systems.combat.CombatSystem.execute_attack") as mock_attack:
            mock_attack.return_value = (True, 40)
            self.screen.update(16)
            mock_attack.assert_not_called()
            self.assertEqual(self.screen.queued_player_attacks, [0])

            self.screen.player.heading = 180.0
            self.screen.update(16)
            mock_attack.assert_called_once()
            self.assertEqual(self.screen.queued_player_attacks, [])

    @patch("pygame.time.get_ticks")
    def test_cpu_does_not_fire_when_player_out_of_arc(self, mock_get_ticks):
        self.screen.is_paused = False
        self.screen.cpu_fire_at_ms = 1000
        self.screen.cpu.rotation_speed_deg_s = 0.0
        self.screen.cpu.heading = 0.0
        for weapon in self.screen.cpu.weapons:
            weapon.firing_arc_deg = 60.0
        mock_get_ticks.return_value = 2000

        with patch("src.systems.combat.CombatSystem.execute_attack") as mock_attack:
            self.screen.update(16)
            mock_attack.assert_not_called()

    def test_target_arc_uses_weapon_facing_offset(self):
        weapon = self.screen.player.weapons[0]
        weapon.firing_arc_deg = 60.0
        self.screen.player.heading = 0.0
        self.screen.cpu.x = self.screen.player.x

        weapon.facing_deg = 180.0
        self.screen.cpu.y = self.screen.player.y + 250.0
        self.assertTrue(
            self.screen._is_target_in_weapon_arc(self.screen.player, self.screen.cpu, weapon)
        )

        self.screen.cpu.y = self.screen.player.y - 250.0
        self.assertFalse(
            self.screen._is_target_in_weapon_arc(self.screen.player, self.screen.cpu, weapon)
        )

    @patch("pygame.draw.rect")
    @patch("pygame.draw.line")
    @patch("pygame.time.get_ticks")
    def test_draw_renders_attack_animation(self, mock_get_ticks, mock_line, mock_rect):
        self.screen.map_view_x = 0.0
        self.screen.map_view_y = 0.0
        self.screen.attack_animation = {
            "color": (230, 80, 80),
            "start": (100, 100),
            "target": (200, 200),
            "missed": False,
            "started_at_ms": 1000,
            "duration_ms": 240,
        }
        mock_get_ticks.return_value = 1100
        mock_surf = MagicMock(spec=pygame.Surface)
        with patch.object(self.screen.map, "draw"):
            self.screen.draw(mock_surf)
        self.assertTrue(mock_line.called)

    @patch("pygame.draw.rect")
    @patch("pygame.draw.line")
    @patch("pygame.time.get_ticks")
    def test_draw_miss_extends_beam_to_screen_edge(self, mock_get_ticks, mock_line, mock_rect):
        self.screen.map_view_x = 0.0
        self.screen.map_view_y = 0.0
        self.screen.attack_animation = {
            "color": (230, 80, 80),
            "start": (450, 525),
            "target": (450, 175),
            "missed": True,
            "started_at_ms": 1000,
            "duration_ms": 240,
        }
        mock_get_ticks.return_value = 1100
        mock_surf = MagicMock(spec=pygame.Surface)
        with patch.object(self.screen.map, "draw"):
            self.screen.draw(mock_surf)

        red_beam_calls = [c for c in mock_line.call_args_list if c.args[1] == (230, 80, 80)]
        self.assertTrue(red_beam_calls)
        self.assertEqual(red_beam_calls[-1].args[3], (450, 0))

    @patch("pygame.draw.line")
    @patch("pygame.draw.arc")
    def test_draw_weapon_arc_preview_shows_when_hovering_weapon_card(self, mock_arc, mock_line):
        self.screen.hovered_player_weapon_idx = 0
        self.screen.panel_expanded = True
        self.screen.weapon_buttons = {0: pygame.Rect(WIDTH - PANEL_W + 20, 100, 80, 32)}
        self.screen.player.weapons[0].firing_arc_deg = 120.0

        render_surface = pygame.Surface((WIDTH, HEIGHT))
        self.screen._draw_weapon_arc_preview(render_surface, WIDTH - PANEL_W)

        self.assertTrue(mock_arc.called)
        self.assertTrue(mock_line.called)

    @patch("pygame.time.get_ticks")
    def test_space_works_when_keyup_lost(self, mock_get_ticks):
        """Space must toggle even if the preceding KEYUP was lost (SDL2/focus quirk)."""
        mock_get_ticks.return_value = 1000
        event = MagicMock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_SPACE

        # First press: unpause
        self.screen.handle_event(event)
        self.assertFalse(self.screen.is_paused)

        # Second press WITHOUT a KEYUP in between (simulates SDL2/focus quirk
        # where KEYUP is lost). With the edge-trigger guard removed, the toggle
        # still fires correctly.
        self.screen.handle_event(event)
        self.assertTrue(self.screen.is_paused)

    @patch("pygame.time.get_ticks")
    def test_restart(self, mock_get_ticks):
        self.screen.winner = "Computer"
        event = MagicMock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_r
        self.screen.handle_event(event)
        self.assertIsNone(self.screen.winner)
        self.assertTrue(self.screen.is_paused)

    @patch("pygame.time.get_ticks")
    def test_game_time_accumulates_when_running(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        self.screen.is_paused = False
        self.screen.game_time_ms = 0
        self.screen.update(500)
        self.screen.update(500)
        self.assertEqual(self.screen.game_time_ms, 1000)

    @patch("pygame.time.get_ticks")
    def test_game_time_frozen_when_paused(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        self.screen.is_paused = True
        self.screen.game_time_ms = 0
        self.screen.update(500)
        self.assertEqual(self.screen.game_time_ms, 0)

    @patch("pygame.time.get_ticks")
    def test_toggle_pause_logs_state(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        self.screen.game_time_ms = 12345

        with patch("src.screens.battle_screen._log") as mock_log:
            event = MagicMock()
            event.type = pygame.KEYDOWN
            event.key = pygame.K_SPACE

            self.screen.handle_event(event)   # unpause
            self.screen.handle_event(event)   # pause

            self.assertEqual(mock_log.info.call_count, 2)
            first_args = mock_log.info.call_args_list[0].args
            second_args = mock_log.info.call_args_list[1].args
            self.assertIn("unpaused", first_args)
            self.assertIn("paused", second_args)
            self.assertAlmostEqual(first_args[1], 12.345)

    @patch("pygame.time.get_ticks")
    def test_space_ignores_key_repeat(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000

        first_event = MagicMock()
        first_event.type = pygame.KEYDOWN
        first_event.key = pygame.K_SPACE
        first_event.repeat = 0

        repeat_event = MagicMock()
        repeat_event.type = pygame.KEYDOWN
        repeat_event.key = pygame.K_SPACE
        repeat_event.repeat = 1

        self.screen.handle_event(first_event)
        self.assertFalse(self.screen.is_paused)

        # Repeated KEYDOWN while key is held should not toggle pause again.
        self.screen.handle_event(repeat_event)
        self.assertFalse(self.screen.is_paused)

    @patch("pygame.time.get_ticks")
    def test_update_running_moves_player_forward(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        self.screen.is_paused = False
        start_x = self.screen.player.x
        start_y = self.screen.player.y
        self.screen.update(1000)
        self.assertEqual(self.screen.player.x, start_x)
        self.assertEqual(self.screen.player.y, start_y - self.screen.player.speed_px_s)

    @patch("pygame.time.get_ticks")
    def test_update_running_turns_with_a_and_d(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        self.screen.is_paused = False

        a_down = MagicMock()
        a_down.type = pygame.KEYDOWN
        a_down.key = pygame.K_a
        self.screen.handle_event(a_down)
        self.screen.update(1000)
        self.assertEqual(self.screen.player.heading, 360.0 - self.screen.player.rotation_speed_deg_s)

        a_up = MagicMock()
        a_up.type = pygame.KEYUP
        a_up.key = pygame.K_a
        self.screen.handle_event(a_up)

        d_down = MagicMock()
        d_down.type = pygame.KEYDOWN
        d_down.key = pygame.K_d
        self.screen.handle_event(d_down)
        self.screen.update(1000)
        self.assertEqual(self.screen.player.heading, 0.0)

    @patch("pygame.time.get_ticks")
    def test_update_clamps_player_within_map_bounds(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        self.screen.is_paused = False
        self.screen.player.x = -5.0
        self.screen.player.y = 1.0
        self.screen.player.heading = 0.0
        self.screen.update(1000)

        self.assertEqual(self.screen.player.x, 0.0)
        self.assertEqual(self.screen.player.y, 0.0)

    @patch("pygame.time.get_ticks")
    def test_cpu_rotates_toward_player(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        self.screen.is_paused = False
        self.screen.cpu_fire_at_ms = None
        self.screen.cpu.heading = 0.0
        self.screen.player.speed_px_s = 0.0
        self.screen.player.x = self.screen.cpu.x + 100.0
        self.screen.player.y = self.screen.cpu.y

        self.screen.update(1000)
        self.assertEqual(self.screen.cpu.heading, self.screen.cpu.rotation_speed_deg_s)

    @patch("pygame.time.get_ticks")
    def test_cpu_moves_forward_when_running(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        self.screen.is_paused = False
        self.screen.cpu_fire_at_ms = None
        self.screen.cpu.heading = 180.0
        start_y = self.screen.cpu.y

        self.screen.update(1000)
        self.assertEqual(self.screen.cpu.y, start_y + self.screen.cpu.speed_px_s)

    @patch("pygame.time.get_ticks")
    def test_paused_map_click_adds_waypoint(self, mock_get_ticks):
        event = MagicMock()
        event.type = pygame.MOUSEBUTTONDOWN
        event.button = 1
        event.pos = (100, 100)
        with patch("pygame.key.get_mods", return_value=0):
            self.screen.handle_event(event)
        self.assertEqual(self.screen.waypoints, [])

    @patch("pygame.time.get_ticks")
    def test_paused_shift_click_adds_waypoint(self, mock_get_ticks):
        event = MagicMock()
        event.type = pygame.MOUSEBUTTONDOWN
        event.button = 1
        event.pos = (100, 100)
        with patch("pygame.key.get_mods", return_value=pygame.KMOD_SHIFT):
            self.screen.handle_event(event)
        self.assertEqual(self.screen.waypoints, [self.screen._screen_to_world((100, 100))])

    @patch("pygame.time.get_ticks")
    def test_paused_ctrl_click_replaces_waypoints(self, mock_get_ticks):
        self.screen.waypoints = [(10.0, 20.0), (30.0, 40.0)]
        event = MagicMock()
        event.type = pygame.MOUSEBUTTONDOWN
        event.button = 1
        event.pos = (200, 220)
        with patch("pygame.key.get_mods", return_value=pygame.KMOD_CTRL):
            self.screen.handle_event(event)
        self.assertEqual(self.screen.waypoints, [self.screen._screen_to_world((200, 220))])

    @patch("pygame.time.get_ticks")
    def test_unpaused_shift_click_adds_waypoint(self, mock_get_ticks):
        self.screen.is_paused = False
        self.screen.waypoints = [self.screen._screen_to_world((50, 60))]
        event = MagicMock()
        event.type = pygame.MOUSEBUTTONDOWN
        event.button = 1
        event.pos = (100, 110)
        with patch("pygame.key.get_mods", return_value=pygame.KMOD_SHIFT):
            self.screen.handle_event(event)
        self.assertEqual(
            self.screen.waypoints,
            [self.screen._screen_to_world((50, 60)), self.screen._screen_to_world((100, 110))],
        )

    @patch("pygame.time.get_ticks")
    def test_unpaused_ctrl_click_replaces_waypoints(self, mock_get_ticks):
        self.screen.is_paused = False
        self.screen.waypoints = [self.screen._screen_to_world((10, 20)), self.screen._screen_to_world((30, 40))]
        event = MagicMock()
        event.type = pygame.MOUSEBUTTONDOWN
        event.button = 1
        event.pos = (150, 170)
        with patch("pygame.key.get_mods", return_value=pygame.KMOD_CTRL):
            self.screen.handle_event(event)
        self.assertEqual(self.screen.waypoints, [self.screen._screen_to_world((150, 170))])

    @patch("pygame.key.get_mods", return_value=pygame.KMOD_CTRL)
    @patch("pygame.mouse.get_pos", return_value=(140, 160))
    def test_draw_ctrl_preview_uses_cursor_waypoint_only(self, _mock_mouse_pos, _mock_mods):
        self.screen.waypoints = [self.screen._screen_to_world((50, 60))]
        with (
            patch.object(self.screen.map, "draw") as mock_map_draw,
            patch.object(self.screen, "_draw_attack_animation"),
            patch.object(self.screen, "_draw_side_panel"),
            patch.object(self.screen, "_draw_toggle_tab", return_value=self.screen.toggle_tab_rect),
            patch.object(self.screen, "_draw_demo_cursor"),
        ):
            self.screen.draw(self.mock_surface)
        self.assertEqual(mock_map_draw.call_args.args[8], [self.screen._screen_to_world((140, 160))])

    @patch("pygame.key.get_mods", return_value=pygame.KMOD_SHIFT)
    @patch("pygame.mouse.get_pos", return_value=(220, 260))
    def test_draw_shift_preview_appends_cursor_waypoint_when_route_exists(self, _mock_mouse_pos, _mock_mods):
        first = self.screen._screen_to_world((80, 90))
        self.screen.waypoints = [first]
        with (
            patch.object(self.screen.map, "draw") as mock_map_draw,
            patch.object(self.screen, "_draw_attack_animation"),
            patch.object(self.screen, "_draw_side_panel"),
            patch.object(self.screen, "_draw_toggle_tab", return_value=self.screen.toggle_tab_rect),
            patch.object(self.screen, "_draw_demo_cursor"),
        ):
            self.screen.draw(self.mock_surface)
        self.assertEqual(
            mock_map_draw.call_args.args[8],
            [first, self.screen._screen_to_world((220, 260))],
        )

    @patch("pygame.time.get_ticks")
    def test_ctrl_z_ctrl_y_undo_redo_waypoints(self, mock_get_ticks):
        click_a = self._mouse_event(100, 100)
        click_b = self._mouse_event(160, 180)
        with patch("pygame.key.get_mods", return_value=pygame.KMOD_CTRL):
            self.screen.handle_event(click_a)
        with patch("pygame.key.get_mods", return_value=pygame.KMOD_SHIFT):
            self.screen.handle_event(click_b)
        expected_a = self.screen._screen_to_world((100, 100))
        expected_b = self.screen._screen_to_world((160, 180))
        self.assertEqual(self.screen.waypoints, [expected_a, expected_b])

        self.screen.handle_event(self._key_event(pygame.K_z, pygame.KMOD_CTRL))
        self.assertEqual(self.screen.waypoints, [expected_a])

        self.screen.handle_event(self._key_event(pygame.K_z, pygame.KMOD_CTRL))
        self.assertEqual(self.screen.waypoints, [])

        self.screen.handle_event(self._key_event(pygame.K_y, pygame.KMOD_CTRL))
        self.assertEqual(self.screen.waypoints, [expected_a])

        self.screen.handle_event(self._key_event(pygame.K_y, pygame.KMOD_CTRL))
        self.assertEqual(self.screen.waypoints, [expected_a, expected_b])

    @patch("pygame.time.get_ticks")
    def test_new_waypoint_edit_clears_redo_stack(self, mock_get_ticks):
        with patch("pygame.key.get_mods", return_value=pygame.KMOD_CTRL):
            self.screen.handle_event(self._mouse_event(100, 100))
        with patch("pygame.key.get_mods", return_value=pygame.KMOD_SHIFT):
            self.screen.handle_event(self._mouse_event(130, 140))
        self.screen.handle_event(self._key_event(pygame.K_z, pygame.KMOD_CTRL))
        with patch("pygame.key.get_mods", return_value=pygame.KMOD_SHIFT):
            self.screen.handle_event(self._mouse_event(200, 210))
        expected = [
            self.screen._screen_to_world((100, 100)),
            self.screen._screen_to_world((200, 210)),
        ]
        self.assertEqual(self.screen.waypoints, expected)

        self.screen.handle_event(self._key_event(pygame.K_y, pygame.KMOD_CTRL))
        self.assertEqual(self.screen.waypoints, expected)

    @patch("pygame.time.get_ticks")
    def test_map_drag_pans_viewport(self, mock_get_ticks):
        self.screen.map_view_x = 600.0
        self.screen.map_view_y = 500.0

        down_event = MagicMock()
        down_event.type = pygame.MOUSEBUTTONDOWN
        down_event.button = 1
        down_event.pos = (200, 200)
        with patch("pygame.key.get_mods", return_value=0):
            self.screen.handle_event(down_event)

        move_event = MagicMock()
        move_event.type = pygame.MOUSEMOTION
        move_event.pos = (230, 245)
        self.screen.handle_event(move_event)

        self.assertEqual(self.screen.map_view_x, 570.0)
        self.assertEqual(self.screen.map_view_y, 455.0)

    @patch("pygame.time.get_ticks")
    def test_map_drag_clamps_viewport_bounds(self, mock_get_ticks):
        max_x = float(self.screen.map_world_w - self.screen._current_map_width())
        max_y = float(self.screen.map_world_h - HEIGHT)
        self.screen.map_view_x = max_x
        self.screen.map_view_y = max_y

        down_event = MagicMock()
        down_event.type = pygame.MOUSEBUTTONDOWN
        down_event.button = 1
        down_event.pos = (300, 300)
        with patch("pygame.key.get_mods", return_value=0):
            self.screen.handle_event(down_event)

        move_event = MagicMock()
        move_event.type = pygame.MOUSEMOTION
        move_event.pos = (0, 0)
        self.screen.handle_event(move_event)

        self.assertEqual(self.screen.map_view_x, max_x)
        self.assertEqual(self.screen.map_view_y, max_y)

    def test_map_zoom_defaults_to_one_with_expected_limits(self):
        self.assertEqual(self.screen.map_zoom, 1.0)
        self.assertEqual(self.screen.default_map_zoom, 1.0)
        self.assertEqual(self.screen.min_map_zoom, 0.5)
        self.assertEqual(self.screen.max_map_zoom, 2.5)

    @patch("pygame.mouse.get_pos", return_value=(200, 220))
    @patch("pygame.time.get_ticks")
    def test_mousewheel_zoom_is_centered_on_cursor(self, mock_get_ticks, _mock_mouse_pos):
        mock_get_ticks.return_value = 1000
        self.screen.map_view_x = 400.0
        self.screen.map_view_y = 300.0
        before = self.screen._screen_to_world((200, 220))

        self.screen.handle_event(self._wheel_event(1))

        after = self.screen._screen_to_world((200, 220))
        self.assertGreater(self.screen.map_zoom, 1.0)
        self.assertAlmostEqual(before[0], after[0], places=4)
        self.assertAlmostEqual(before[1], after[1], places=4)

    @patch("pygame.mouse.get_pos", return_value=(220, 240))
    @patch("pygame.time.get_ticks")
    def test_mousewheel_zoom_clamps_to_min_and_max(self, mock_get_ticks, _mock_mouse_pos):
        mock_get_ticks.return_value = 1000
        self.screen.map_zoom = self.screen.max_map_zoom

        self.screen.handle_event(self._wheel_event(1))
        self.assertEqual(self.screen.map_zoom, self.screen.max_map_zoom)

        self.screen.map_zoom = self.screen.min_map_zoom
        self.screen.handle_event(self._wheel_event(-1))
        self.assertEqual(self.screen.map_zoom, self.screen.min_map_zoom)

    @patch("pygame.time.get_ticks")
    def test_screen_to_world_respects_zoom(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        self.screen.map_view_x = 300.0
        self.screen.map_view_y = 200.0
        self.screen.map_zoom = 2.0

        wx, wy = self.screen._screen_to_world((100, 60))
        self.assertEqual(wx, 350.0)
        self.assertEqual(wy, 230.0)

    @patch("pygame.time.get_ticks")
    def test_virtual_map_allows_movement_beyond_visible_width(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        self.screen.is_paused = False
        self.screen.cpu_fire_at_ms = None
        self.screen.player.speed_px_s = 200.0
        self.screen.player.heading = 90.0
        self.screen.player.x = self.screen.map_view_x + self.screen._current_map_width() - 5.0
        self.screen.player.y = self.screen.map_view_y + HEIGHT / 2.0

        self.screen.update(1000)
        self.assertGreater(self.screen.player.x, self.screen.map_view_x + self.screen._current_map_width())
        self.assertLessEqual(self.screen.player.x, self.screen.map_world_w)

    @patch("pygame.time.get_ticks")
    def test_waypoint_autopilot_turns_toward_next_point(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        self.screen.is_paused = False
        self.screen.player.speed_px_s = 0.0
        self.screen.player.heading = 0.0
        self.screen.waypoints = [(self.screen.player.x + 100.0, self.screen.player.y)]

        self.screen.update(1000)
        self.assertEqual(self.screen.player.heading, self.screen.player.rotation_speed_deg_s)

    @patch("pygame.time.get_ticks")
    def test_waypoint_removed_when_reached(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        self.screen.is_paused = False
        self.screen.player.speed_px_s = 0.0
        self.screen.waypoints = [(self.screen.player.x + 1.0, self.screen.player.y + 1.0)]

        self.screen.update(16)
        self.assertEqual(self.screen.waypoints, [])

    @patch("pygame.time.get_ticks")
    def test_manual_steering_clears_waypoints(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        self.screen.is_paused = False
        self.screen.waypoints = [(100.0, 100.0)]
        self.screen.turn_left_held = True

        self.screen.update(16)
        self.assertEqual(self.screen.waypoints, [])

    @patch("pygame.key.get_pressed")
    @patch("pygame.time.get_ticks")
    def test_polled_keyboard_input_clears_waypoints(self, mock_get_ticks, mock_get_pressed):
        mock_get_ticks.return_value = 1000
        mock_get_pressed.return_value = self._PressedState({pygame.K_a: 1})
        self.screen.is_paused = False
        self.screen.waypoints = [(120.0, 120.0)]
        self.screen.turn_left_held = False
        self.screen.turn_right_held = False

        self.screen.update(16)
        self.assertEqual(self.screen.waypoints, [])

    @patch("pygame.time.get_ticks")
    def test_ships_can_overlap_when_chasing(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        self.screen.is_paused = False
        self.screen.cpu_fire_at_ms = None
        self.screen.player.speed_px_s = 0.0
        self.screen.cpu.speed_px_s = 0.0
        self.screen.player.x = 600.0
        self.screen.player.y = 450.0
        self.screen.cpu.x = 602.0
        self.screen.cpu.y = 450.0

        self.screen.update(16)
        distance = math.hypot(self.screen.player.x - self.screen.cpu.x, self.screen.player.y - self.screen.cpu.y)
        self.assertAlmostEqual(distance, 2.0, places=6)

    @patch("random.randint")
    @patch("pygame.time.get_ticks")
    def test_cpu_follow_heading_applies_after_delay(self, mock_get_ticks, mock_randint):
        self.screen.is_paused = False
        self.screen.cpu_fire_at_ms = None
        self.screen.player.speed_px_s = 0.0
        self.screen.cpu.speed_px_s = 0.0
        self.screen.player.heading = 0.0
        self.screen.cpu_follow_heading_deg = 0.0
        self.screen.cpu_pending_follow_heading_deg = None
        mock_randint.return_value = 2000

        mock_get_ticks.return_value = 1000
        self.screen.player.heading = 90.0
        self.screen.update(16)
        self.assertEqual(self.screen.cpu_follow_heading_deg, 0.0)
        self.assertEqual(self.screen.cpu_follow_heading_apply_at_ms, 3000)

        mock_get_ticks.return_value = 2500
        self.screen.update(16)
        self.assertEqual(self.screen.cpu_follow_heading_deg, 0.0)

        mock_get_ticks.return_value = 3000
        self.screen.update(16)
        self.assertEqual(self.screen.cpu_follow_heading_deg, 90.0)

    @patch("pygame.time.get_ticks")
    def test_winner_transitions_to_menu_screen(self, mock_get_ticks):
        mock_get_ticks.return_value = 2000
        self.screen.is_paused = False
        self.screen.cpu_fire_at_ms = 1000
        self.screen.player.hull_hp = 10
        def lethal_cpu_attack(*args, **kwargs):
            self.screen.player.hull_hp = 0
            return (True, 20)

        with patch("src.systems.combat.CombatSystem.execute_attack", side_effect=lethal_cpu_attack):
            with patch.object(self.manager, "set_screen") as mock_set_screen:
                self.screen.update(16)
                mock_set_screen.assert_called_once()


if __name__ == "__main__":
    unittest.main()
