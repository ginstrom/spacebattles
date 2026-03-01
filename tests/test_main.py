import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.main import configure_logging, build_game


class TestMainLogging(unittest.TestCase):
    def setUp(self):
        self.root = logging.getLogger()
        self.original_handlers = list(self.root.handlers)
        self.original_level = self.root.level

    def tearDown(self):
        for handler in list(self.root.handlers):
            handler.close()
            self.root.removeHandler(handler)
        for handler in self.original_handlers:
            self.root.addHandler(handler)
        self.root.setLevel(self.original_level)

    def test_configure_logging_overrides_preconfigured_root_handlers(self):
        logging.basicConfig(level=logging.WARNING)

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "spacebattle.log"
            configure_logging(log_path)

            logging.getLogger("src.screens.battle_screen").info("T+0.000s unpaused")

            contents = log_path.read_text(encoding="utf-8")
            self.assertIn("T+0.000s unpaused", contents)

    @patch("src.main.pygame.time.Clock")
    @patch("src.main.pygame.display.set_caption")
    @patch("src.main.pygame.display.set_mode")
    @patch("src.main.pygame.init")
    @patch("src.main.ScreenManager.set_screen")
    def test_build_game_starts_on_menu_screen(
        self,
        mock_set_screen,
        mock_init,
        mock_set_mode,
        mock_set_caption,
        mock_clock_cls,
    ):
        mock_surface = unittest.mock.MagicMock()
        mock_set_mode.return_value = mock_surface
        mock_clock = unittest.mock.MagicMock()
        mock_clock_cls.return_value = mock_clock

        manager, clock = build_game()

        self.assertIs(clock, mock_clock)
        self.assertIsNotNone(manager)
        self.assertEqual(mock_set_screen.call_args[0][0].__name__, "MenuScreen")


if __name__ == "__main__":
    unittest.main()
