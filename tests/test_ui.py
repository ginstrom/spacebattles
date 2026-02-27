import unittest
from unittest.mock import MagicMock, patch
import pygame
from src.ui.map import Map
from src.models.ship import Ship
from src.models.weapon import Weapon

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
        
        self.player = Ship("Player", 100, 100, [Weapon("Laser", (10, 20), 1, 100, 0, 5)])
        self.cpu = Ship("CPU", 100, 100, [Weapon("Laser", (10, 20), 1, 100, 0, 5)])

    @patch('src.ui.map.draw_enemy_icon')
    @patch('src.ui.map.draw_player_icon')
    @patch('pygame.draw.circle')
    @patch('pygame.draw.line')
    @patch('pygame.draw.rect')
    def test_map_draw(self, mock_rect, mock_line, mock_circle, mock_player_icon, mock_enemy_icon):
        self.map_obj.draw(
            self.mock_surf, 800, self.player, self.cpu, "player", None, 
            self.mock_font, self.mock_small_font
        )
        
        # Verify clip was set and unset
        clip_args = [call.args[0] for call in self.mock_surf.set_clip.call_args_list]
        self.assertTrue(any(isinstance(c, pygame.Rect) and c.width == 800 and c.height == 700 for c in clip_args if c is not None))
        self.assertIn(None, clip_args)
        
        # Verify stars were drawn
        self.mock_surf.set_at.assert_called_with((10, 10), (255, 255, 255))
        # Note: circle call might fail if mock_circle is not properly patched for the call in map.py
        # because map.py imports pygame.draw.circle.
        
        # Verify icons were drawn
        mock_enemy_icon.assert_called_once()
        mock_player_icon.assert_called_once()

    @patch('pygame.draw.polygon')
    def test_draw_enemy_icon(self, mock_polygon):
        from src.ui.elements import draw_enemy_icon
        draw_enemy_icon(self.mock_surf, 100, 100, 64)
        self.assertEqual(mock_polygon.call_count, 2)

    @patch('pygame.draw.circle')
    @patch('pygame.draw.line')
    def test_draw_player_icon(self, mock_line, mock_circle):
        from src.ui.elements import draw_player_icon
        draw_player_icon(self.mock_surf, 100, 100, 64)
        self.assertEqual(mock_circle.call_count, 3)
        mock_line.assert_called_once()

    @patch('pygame.draw.rect')
    def test_draw_info_card_player(self, mock_rect):
        from src.ui.elements import draw_info_card
        from src.constants import PHASE_FIRE
        
        weapon_buttons = {}
        ui_elements = {}
        detail_toggles = {}
        expanded = set()
        rect = pygame.Rect(10, 10, 200, 300)

        draw_info_card(
            self.mock_surf, rect, self.mock_font, self.player, True, True, 
            PHASE_FIRE, None, weapon_buttons, ui_elements, detail_toggles, expanded
        )
        
        self.assertIn(0, weapon_buttons)
        self.assertIn("end_turn", ui_elements)
        self.assertTrue(mock_rect.called)

    @patch('pygame.draw.rect')
    def test_draw_info_card_cpu(self, mock_rect):
        from src.ui.elements import draw_info_card
        from src.constants import PHASE_FIRE
        
        weapon_buttons = {}
        ui_elements = {}
        detail_toggles = {}
        expanded = set()
        rect = pygame.Rect(10, 10, 200, 300)

        draw_info_card(
            self.mock_surf, rect, self.mock_font, self.cpu, False, False, 
            PHASE_FIRE, None, weapon_buttons, ui_elements, detail_toggles, expanded
        )
        
        self.assertEqual(len(weapon_buttons), 1) # CPU has 1 weapon
        self.assertEqual(len(detail_toggles), 1)
        self.assertEqual(len(ui_elements), 0) # CPU has no "End Turn" button
        self.assertTrue(mock_rect.called)

    @patch('pygame.draw.rect')
    def test_draw_info_card_stacked(self, mock_rect):
        from src.ui.elements import draw_info_card
        from src.constants import PHASE_FIRE
        
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
            self.mock_surf, rect, self.mock_font, ship, True, True, 
            PHASE_FIRE, None, weapon_buttons, ui_elements, detail_toggles, expanded
        )
        
        self.assertIn(0, weapon_buttons)
        self.assertIn(1, weapon_buttons)

if __name__ == "__main__":
    unittest.main()
