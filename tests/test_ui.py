import unittest
from unittest.mock import MagicMock, patch
import pygame
from src.ui.map import Map
from src.models.ship import Ship
from src.models.weapon import Weapon
from src.constants import HEIGHT


class TestUI(unittest.TestCase):
    def setUp(self):
        self.stars = [(10, 10, 255, 1), (20, 20, 200, 3)]
        self.map_obj = Map(self.stars)
        self.mock_surf = MagicMock(spec=pygame.Surface)
        self.mock_font = MagicMock(spec=pygame.font.Font)
        self.mock_small_font = MagicMock(spec=pygame.font.Font)

        # Mock render to return a surface with some dimensions
        mock_rendered_text = MagicMock(spec=pygame.Surface)
        mock_rendered_text.get_rect.return_value = pygame.Rect(0, 0, 50, 20)
        mock_rendered_text.get_height.return_value = 20
        mock_rendered_text.get_width.return_value = 50
        self.mock_small_font.render.return_value = mock_rendered_text
        self.mock_font.render.return_value = mock_rendered_text
        self.mock_font.get_linesize.return_value = 20

        self.player = Ship("Player", 100, 100, [
                           Weapon("Laser", (10, 20), 1, 100, 0, 5)],
                           x=400.0, y=HEIGHT * 3 / 4, heading=0.0)
        self.cpu = Ship("CPU", 100, 100, [
                        Weapon("Laser", (10, 20), 1, 100, 0, 5),
                        Weapon("Laser", (10, 20), 1, 100, 0, 5),
                        Weapon("Laser", (10, 20), 1, 100, 0, 5)],
                        x=400.0, y=HEIGHT / 4, heading=180.0)

    @patch('src.ui.map.draw_enemy_icon')
    @patch('src.ui.map.draw_player_icon')
    @patch('pygame.draw.circle')
    @patch('pygame.draw.line')
    @patch('pygame.draw.rect')
    def test_map_draw(
            self,
            mock_rect,
            mock_line,
            mock_circle,
            mock_player_icon,
            mock_enemy_icon):
        self.map_obj.draw(
            self.mock_surf, 800, self.player, self.cpu, True, None,
            self.mock_font, self.mock_small_font
        )

        # Verify clip was set and unset
        clip_args = [call.args[0]
                     for call in self.mock_surf.set_clip.call_args_list]
        self.assertTrue(
            any(
                isinstance(c, pygame.Rect)
                and c.width == 800
                and c.height == HEIGHT
                for c in clip_args
                if c is not None
            )
        )
        self.assertIn(None, clip_args)

        # Verify stars were drawn
        self.mock_surf.set_at.assert_called_with((10, 10), (255, 255, 255))
        # Note: circle call might fail if mock_circle is not properly patched.
        # because map.py imports pygame.draw.circle.

        # Verify icons were drawn
        mock_enemy_icon.assert_called_once()
        mock_player_icon.assert_called_once()
        self.assertEqual(mock_enemy_icon.call_args[0][4], self.cpu.heading)
        self.assertEqual(mock_player_icon.call_args[0][4], self.player.heading)

    @patch('src.ui.map.draw_player_icon')
    @patch('pygame.draw.line')
    def test_map_draw_ghost_route(self, mock_line, mock_player_icon):
        waypoints = [(500.0, 600.0), (600.0, 650.0)]
        test_surface = pygame.Surface((800, HEIGHT))
        self.mock_small_font.render.return_value = pygame.Surface((50, 20))
        self.map_obj.draw(
            test_surface,
            800,
            self.player,
            self.cpu,
            False,
            None,
            self.mock_font,
            self.mock_small_font,
            waypoints,
        )

        # Regular player icon + ghost icon render.
        self.assertGreaterEqual(mock_player_icon.call_count, 2)
        self.assertTrue(mock_line.called)

    @patch('src.ui.map.draw_enemy_icon')
    @patch('src.ui.map.draw_player_icon')
    @patch('pygame.draw.circle')
    @patch('pygame.draw.line')
    @patch('pygame.draw.rect')
    def test_map_draw_does_not_render_ship_hp_bars(
        self,
        mock_rect,
        mock_line,
        mock_circle,
        mock_player_icon,
        mock_enemy_icon,
    ):
        self.map_obj.draw(
            self.mock_surf, 800, self.player, self.cpu, True, None,
            self.mock_font, self.mock_small_font
        )

        background_bar_rects = [
            call for call in mock_rect.call_args_list if call.args[1] == (60, 60, 80)
        ]
        self.assertEqual(background_bar_rects, [])

    @patch('pygame.draw.polygon')
    def test_draw_enemy_icon(self, mock_polygon):
        from src.ui.elements import draw_enemy_icon
        with patch("src.ui.elements.get_enemy_icon_surface", return_value=None):
            draw_enemy_icon(self.mock_surf, 100, 100, 64)
        self.assertEqual(mock_polygon.call_count, 2)

    @patch('pygame.transform.rotate')
    def test_draw_enemy_icon_uses_sprite_when_available(self, mock_rotate):
        from src.ui.elements import draw_enemy_icon
        icon = pygame.Surface((64, 64), pygame.SRCALPHA)
        mock_rotate.return_value = icon
        with patch("src.ui.elements.get_enemy_icon_surface", return_value=icon):
            draw_enemy_icon(self.mock_surf, 100, 100, 64)

        mock_rotate.assert_called_once_with(icon, -0.0)
        self.mock_surf.blit.assert_called_once()

    @patch('pygame.transform.rotate')
    def test_draw_enemy_icon_applies_heading_rotation(self, mock_rotate):
        from src.ui.elements import draw_enemy_icon
        icon = pygame.Surface((64, 64), pygame.SRCALPHA)
        mock_rotate.return_value = icon
        with patch("src.ui.elements.get_enemy_icon_surface", return_value=icon):
            draw_enemy_icon(self.mock_surf, 100, 100, 64, heading_deg=90.0)

        mock_rotate.assert_called_once_with(icon, -90.0)

    @patch('pygame.draw.circle')
    @patch('pygame.draw.line')
    def test_draw_player_icon(self, mock_line, mock_circle):
        from src.ui.elements import draw_player_icon
        with patch("src.ui.elements.get_player_icon_surface", return_value=None):
            draw_player_icon(self.mock_surf, 100, 100, 64)
        self.assertEqual(mock_circle.call_count, 3)
        mock_line.assert_called_once()

    @patch('pygame.draw.rect')
    def test_draw_info_card_player(self, mock_rect):
        from src.ui.elements import draw_info_card

        weapon_buttons = {}
        ui_elements = {}
        detail_toggles = {}
        expanded = set()
        rect = pygame.Rect(10, 10, 200, 300)

        draw_info_card(
            self.mock_surf,
            rect,
            self.mock_font,
            self.player,
            True,
            True,
            None,
            weapon_buttons,
            ui_elements,
            detail_toggles,
            expanded)

        self.assertIn(0, weapon_buttons)
        self.assertEqual(len(ui_elements), 0)
        self.assertTrue(mock_rect.called)

    @patch('pygame.draw.rect')
    def test_draw_info_card_cpu(self, mock_rect):
        from src.ui.elements import draw_info_card
        from src.constants import BLUE

        weapon_buttons = {}
        ui_elements = {}
        detail_toggles = {}
        expanded = set()
        rect = pygame.Rect(10, 10, 200, 300)

        draw_info_card(
            self.mock_surf,
            rect,
            self.mock_font,
            self.cpu,
            False,
            True,
            None,
            weapon_buttons,
            ui_elements,
            detail_toggles,
            expanded)

        self.assertEqual(len(weapon_buttons), 3)  # CPU has 3 weapons
        self.assertEqual(len(detail_toggles), 3)
        self.assertEqual(len(ui_elements), 0)  # CPU has no "End Turn" button
        self.assertTrue(mock_rect.called)

        # CPU active weapon should use the same active color affordance.
        cpu_weapon_button = weapon_buttons[0]
        self.assertTrue(
            any(
                call.args[1] == BLUE and call.args[2] == cpu_weapon_button
                for call in mock_rect.call_args_list
            )
        )

    @patch('pygame.draw.rect')
    def test_draw_info_card_stacked(self, mock_rect):
        from src.ui.elements import draw_info_card

        weapon_buttons = {}
        ui_elements = {}
        detail_toggles = {}
        expanded = set()
        rect = pygame.Rect(10, 10, 200, 300)

        # Mock font methods
        self.mock_font.get_linesize.return_value = 20
        mock_text_surf = MagicMock(spec=pygame.Surface)
        mock_text_surf.get_width.return_value = 50
        mock_text_surf.get_height.return_value = 20
        self.mock_font.render.return_value = mock_text_surf

        ship = Ship("Test", 100, 100, [
            Weapon("W1", (10, 10), 1, 100),
            Weapon("W2", (10, 10), 1, 100)
        ])

        draw_info_card(
            self.mock_surf,
            rect,
            self.mock_font,
            ship,
            True,
            True,
            None,
            weapon_buttons,
            ui_elements,
            detail_toggles,
            expanded)

        self.assertIn(0, weapon_buttons)
        self.assertIn(1, weapon_buttons)

    @patch('pygame.draw.rect')
    def test_draw_info_card_shows_seconds_cooldown(self, mock_rect):
        from src.ui.elements import draw_info_card

        weapon_buttons = {}
        ui_elements = {}
        detail_toggles = {}
        expanded = {0}
        rect = pygame.Rect(10, 10, 200, 300)
        self.player.weapons[0].current_cooldown_seconds = 3.4

        draw_info_card(
            self.mock_surf,
            rect,
            self.mock_font,
            self.player,
            True,
            True,
            None,
            weapon_buttons,
            ui_elements,
            detail_toggles,
            expanded)

        render_texts = [call.args[0] for call in self.mock_font.render.call_args_list]
        self.assertTrue(any("(3.4s)" in text for text in render_texts))
        self.assertTrue(any("Cooldown: 5.0s" in text for text in render_texts))


if __name__ == "__main__":
    unittest.main()
