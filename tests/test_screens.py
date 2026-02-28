import unittest
from unittest.mock import MagicMock, patch
import pygame
from src.screens.battle_screen import BattleScreen
from src.core.screen_manager import ScreenManager
from src.constants import WIDTH, HEIGHT, PANEL_W


class TestScreens(unittest.TestCase):
    def setUp(self):
        self.mock_surface = MagicMock(spec=pygame.Surface)
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

    def _mouse_event(self, x=125, y=125):
        event = MagicMock()
        event.type = pygame.MOUSEBUTTONDOWN
        event.button = 1
        event.pos = (x, y)
        return event

    @patch("pygame.time.get_ticks")
    def test_battle_screen_init_paused(self, mock_get_ticks):
        self.assertTrue(self.screen.is_paused)
        self.assertIn("Paused", self.screen.message)
        self.assertIsNone(self.screen.winner)

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

        with patch("src.systems.combat.CombatSystem.execute_attack") as mock_attack:
            mock_attack.return_value = (True, 50)
            self.screen.handle_event(self._mouse_event())
            mock_attack.assert_called_once()
            self.assertIn("fired", self.screen.message)
            self.assertIsNotNone(self.screen.attack_animation)
            self.assertEqual(self.screen.attack_animation["start"], (self.map_center_x, self.player_y))
            self.assertEqual(self.screen.attack_animation["target"], (self.map_center_x, self.cpu_y))

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

        with patch("src.systems.combat.CombatSystem.execute_attack") as mock_attack:
            mock_attack.return_value = (True, 40)
            self.screen.update(16)
            mock_attack.assert_called_once()
            self.assertIsNotNone(self.screen.attack_animation)
            self.assertEqual(self.screen.attack_animation["start"], (self.map_center_x, self.cpu_y))
            self.assertEqual(self.screen.attack_animation["target"], (self.map_center_x, self.player_y))
            self.assertEqual(self.screen.cpu_fire_at_ms, 2000 + self.screen.CPU_DELAY_MS)

    @patch("pygame.draw.rect")
    @patch("pygame.draw.line")
    @patch("pygame.time.get_ticks")
    def test_draw_renders_attack_animation(self, mock_get_ticks, mock_line, mock_rect):
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


if __name__ == "__main__":
    unittest.main()
