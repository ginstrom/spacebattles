import unittest
from unittest.mock import MagicMock, patch
import pygame
from src.core.screen_manager import ScreenManager
from src.core.base_screen import BaseScreen


class TestCore(unittest.TestCase):
    def setUp(self):
        self.mock_surface = MagicMock(spec=pygame.Surface)
        self.manager = ScreenManager(self.mock_surface)

    def test_set_screen(self):
        class MockScreen(BaseScreen):
            def __init__(self, manager, param=None):
                super().__init__(manager)
                self.param = param

        self.manager.set_screen(MockScreen, param="test")
        self.assertIsInstance(self.manager.current_screen, MockScreen)
        self.assertEqual(self.manager.current_screen.param, "test")

    @patch('pygame.event.get')
    def test_handle_events_quit(self, mock_event_get):
        mock_event = MagicMock()
        mock_event.type = pygame.QUIT
        mock_event_get.return_value = [mock_event]

        self.manager.handle_events()
        self.assertFalse(self.manager.running)

    @patch('pygame.event.get')
    def test_handle_events_delegation(self, mock_event_get):
        mock_screen = MagicMock(spec=BaseScreen)
        self.manager.current_screen = mock_screen

        mock_event = MagicMock()
        mock_event.type = pygame.KEYDOWN
        mock_event_get.return_value = [mock_event]

        self.manager.handle_events()
        mock_screen.handle_event.assert_called_with(mock_event)

    def test_update(self):
        mock_screen = MagicMock(spec=BaseScreen)
        self.manager.current_screen = mock_screen
        self.manager.update(16)
        mock_screen.update.assert_called_with(16)

    @patch('pygame.display.flip')
    def test_draw(self, mock_flip):
        mock_screen = MagicMock(spec=BaseScreen)
        self.manager.current_screen = mock_screen
        self.manager.draw()
        mock_screen.draw.assert_called_with(self.mock_surface)
        mock_flip.assert_called_once()

    def test_quit(self):
        self.assertTrue(self.manager.running)
        self.manager.quit()
        self.assertFalse(self.manager.running)

    def test_base_screen_methods(self):
        base = BaseScreen(self.manager)
        # These should do nothing but should be callable
        base.handle_event(MagicMock())
        base.update(16)
        base.draw(self.mock_surface)


if __name__ == "__main__":
    unittest.main()
