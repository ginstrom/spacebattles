import unittest
from unittest.mock import MagicMock, patch
import pygame
from src.screens.battle_screen import BattleScreen
from src.core.screen_manager import ScreenManager
from src.constants import PLAYER_TURN, CPU_TURN, PHASE_FIRE, PHASE_END


class TestScreens(unittest.TestCase):
    def setUp(self):
        self.mock_surface = MagicMock(spec=pygame.Surface)
        self.manager = ScreenManager(self.mock_surface)

        with patch('pygame.font.SysFont') as mock_sysfont:
            mock_font = MagicMock(spec=pygame.font.Font)
            mock_font.get_linesize.return_value = 20
            mock_font.size.return_value = (50, 20)
            mock_text_surf = MagicMock(spec=pygame.Surface)
            mock_text_surf.get_width.return_value = 50
            mock_text_surf.get_height.return_value = 20
            mock_font.render.return_value = mock_text_surf
            mock_sysfont.return_value = mock_font

            self.screen = BattleScreen(self.manager)

    @patch('pygame.time.get_ticks')
    def test_battle_screen_init(self, mock_get_ticks):
        self.assertEqual(self.screen.turn, PLAYER_TURN)
        self.assertEqual(self.screen.phase, PHASE_FIRE)
        self.assertIsNone(self.screen.winner)

    @patch('pygame.time.get_ticks')
    def test_handle_event_weapon_click(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        # Setup a fake button rect for index 0
        self.screen.weapon_buttons = {0: pygame.Rect(100, 100, 50, 50)}

        event = MagicMock()
        event.type = pygame.MOUSEBUTTONDOWN
        event.button = 1
        event.pos = (125, 125)

        with patch(
            'src.systems.combat.CombatSystem.execute_attack'
        ) as mock_attack:
            mock_attack.return_value = (True, 50)
            self.screen.handle_event(event)

            mock_attack.assert_called_once()
            # Phase remains FIRE in multi-fire mode until End Turn is clicked
            self.assertEqual(self.screen.phase, PHASE_FIRE)
            self.assertIn("fired", self.screen.message)
            self.assertIsNotNone(self.screen.attack_animation)
            self.assertEqual(
                self.screen.attack_animation["color"], (230, 80, 80))

    @patch('pygame.time.get_ticks')
    def test_handle_event_end_turn(self, mock_get_ticks):
        mock_get_ticks.return_value = 1000
        self.screen.phase = PHASE_END
        self.screen.ui_elements = {"end_turn": pygame.Rect(100, 100, 50, 50)}

        event = MagicMock()
        event.type = pygame.MOUSEBUTTONDOWN
        event.button = 1
        event.pos = (125, 125)

        self.screen.handle_event(event)
        self.assertEqual(self.screen.turn, CPU_TURN)
        self.assertEqual(self.screen.phase, PHASE_FIRE)
        self.assertEqual(self.screen.cpu_fire_at_ms,
                         1000 + self.screen.CPU_DELAY_MS)

    @patch('pygame.time.get_ticks')
    def test_cpu_update(self, mock_get_ticks):
        self.screen.turn = CPU_TURN
        self.screen.phase = PHASE_FIRE
        self.screen.cpu_fire_at_ms = 1000
        mock_get_ticks.return_value = 2000  # Past delay

        with patch(
            'src.systems.combat.CombatSystem.execute_attack'
        ) as mock_attack:
            mock_attack.return_value = (True, 40)
            self.screen.update(16)

            mock_attack.assert_called_once()
            self.assertEqual(self.screen.phase, PHASE_END)
            self.assertIsNotNone(self.screen.attack_animation)
            self.assertEqual(
                self.screen.attack_animation["color"], (230, 80, 80))

    @patch('pygame.draw.rect')
    @patch('pygame.draw.line')
    @patch('pygame.time.get_ticks')
    def test_draw_renders_attack_animation(
        self, mock_get_ticks, mock_line, mock_rect
    ):
        self.screen.attack_animation = {
            "color": (230, 80, 80),
            "start": (100, 100),
            "end": (200, 200),
            "started_at_ms": 1000,
            "duration_ms": 240,
        }
        mock_get_ticks.return_value = 1100
        mock_surf = MagicMock(spec=pygame.Surface)
        with patch.object(self.screen.map, 'draw'):
            self.screen.draw(mock_surf)
        self.assertTrue(mock_line.called)

    @patch('pygame.draw.rect')
    @patch('pygame.draw.line')
    @patch('pygame.time.get_ticks')
    def test_draw_expires_attack_animation(
        self, mock_get_ticks, mock_line, mock_rect
    ):
        self.screen.attack_animation = {
            "color": (230, 80, 80),
            "start": (100, 100),
            "end": (200, 200),
            "started_at_ms": 1000,
            "duration_ms": 240,
        }
        mock_get_ticks.return_value = 1300
        mock_surf = MagicMock(spec=pygame.Surface)
        with patch.object(self.screen.map, 'draw'):
            self.screen.draw(mock_surf)
        self.assertIsNone(self.screen.attack_animation)

    @patch('pygame.time.get_ticks')
    def test_restart(self, mock_get_ticks):
        self.screen.winner = "Computer"
        event = MagicMock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_r

        self.screen.handle_event(event)
        self.assertIsNone(self.screen.winner)
        self.assertEqual(self.screen.turn, PLAYER_TURN)

    @patch('pygame.draw.rect')
    @patch('pygame.draw.line')
    def test_draw(self, mock_line, mock_rect):
        mock_surf = MagicMock(spec=pygame.Surface)
        with patch.object(self.screen.map, 'draw') as mock_map_draw:
            self.screen.draw(mock_surf)
            mock_surf.fill.assert_called_once()
            mock_map_draw.assert_called_once()
            self.assertTrue(mock_surf.blit.called)

    @patch('pygame.draw.rect')
    def test_draw_collapsed(self, mock_rect):
        mock_surf = MagicMock(spec=pygame.Surface)
        self.screen.panel_expanded = False
        with patch.object(self.screen.map, 'draw') as mock_map_draw:
            self.screen.draw(mock_surf)
            mock_surf.fill.assert_called_once()
            mock_map_draw.assert_called_once()
            self.assertTrue(mock_surf.blit.called)

    @patch('pygame.time.get_ticks')
    def test_handle_event_toggle_panel(self, mock_get_ticks):
        self.assertTrue(self.screen.panel_expanded)
        event = MagicMock()
        event.type = pygame.MOUSEBUTTONDOWN
        event.button = 1
        event.pos = self.screen.toggle_tab_rect.center

        self.screen.handle_event(event)
        self.assertFalse(self.screen.panel_expanded)

    @patch('pygame.time.get_ticks')
    def test_cpu_update_no_weapons(self, mock_get_ticks):
        self.screen.turn = CPU_TURN
        self.screen.phase = PHASE_FIRE
        self.screen.cpu_fire_at_ms = 1000
        mock_get_ticks.return_value = 2000

        # Drain CPU weapons
        for w in self.screen.cpu.weapons:
            w.charges = 0
            w.current_cooldown = 10  # Also make sure they are on cooldown

        self.screen.update(16)
        self.assertEqual(self.screen.phase, PHASE_END)
        self.assertIn("no weapons left", self.screen.message)

    @patch('pygame.draw.rect')
    @patch('pygame.draw.line')
    def test_draw_winner(self, mock_line, mock_rect):
        self.screen.winner = "Player"
        mock_surf = MagicMock(spec=pygame.Surface)
        with patch.object(self.screen.map, 'draw'):
            self.screen.draw(mock_surf)
            # Check blit for overlay and text blitting
            self.assertTrue(mock_surf.blit.called)


if __name__ == "__main__":
    unittest.main()
