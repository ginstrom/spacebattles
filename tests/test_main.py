import logging
import tempfile
import unittest
import os
from pathlib import Path
from unittest.mock import patch
import pygame

from src.main import configure_logging, build_game, build_capture_ffmpeg_command
from src.constants import WIDTH, HEIGHT


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
        mock_set_mode.assert_called_once_with((WIDTH, HEIGHT), pygame.FULLSCREEN)

    @patch.dict(os.environ, {"SPACEBATTLE_WINDOWED": "1"})
    @patch("src.main.pygame.time.Clock")
    @patch("src.main.pygame.display.set_caption")
    @patch("src.main.pygame.display.set_mode")
    @patch("src.main.pygame.init")
    @patch("src.main.ScreenManager.set_screen")
    def test_build_game_uses_windowed_mode_when_enabled(
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
        mock_set_mode.assert_called_once_with((WIDTH, HEIGHT), 0)

    def test_build_capture_ffmpeg_command_uses_rawvideo_stdin(self):
        cmd = build_capture_ffmpeg_command(
            width=WIDTH,
            height=HEIGHT,
            fps=20,
            caption="Image #1: Demo",
            output_path="assets/demo/gameplay.gif",
        )
        self.assertEqual(cmd[0], "ffmpeg")
        self.assertIn("rawvideo", cmd)
        self.assertIn("rgb24", cmd)
        self.assertIn("-", cmd)
        self.assertIn("-filter_complex", cmd)
        self.assertIn("drawtext", " ".join(cmd))


if __name__ == "__main__":
    unittest.main()
