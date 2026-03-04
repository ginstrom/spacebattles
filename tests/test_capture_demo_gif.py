import unittest
from unittest.mock import MagicMock, patch

from src.tools.capture_demo_gif import (
    CaptureConfig,
    build_ffmpeg_command,
    capture_demo_gif,
)


class TestCaptureDemoGif(unittest.TestCase):
    def test_build_ffmpeg_command_x11grab(self):
        cfg = CaptureConfig(
            duration=10,
            output="assets/demo/gameplay.gif",
            fps=20,
            display=":0.0",
            geometry="1280x720",
            startup_delay=1.5,
            game_command=("uv", "run", "python", "-m", "src.main"),
        )

        cmd = build_ffmpeg_command(cfg)

        self.assertEqual(cmd[0], "ffmpeg")
        self.assertIn("-f", cmd)
        self.assertIn("x11grab", cmd)
        self.assertIn("-video_size", cmd)
        self.assertIn("1280x720", cmd)
        self.assertIn("-i", cmd)
        self.assertIn(":0.0", cmd)
        self.assertIn("-t", cmd)
        self.assertIn("10", cmd)
        self.assertEqual(cmd[-1], "assets/demo/gameplay.gif")

    @patch("src.tools.capture_demo_gif.time.sleep")
    @patch("src.tools.capture_demo_gif.subprocess.run")
    @patch("src.tools.capture_demo_gif.subprocess.Popen")
    def test_capture_demo_gif_runs_and_stops_game(
        self,
        mock_popen,
        mock_run,
        mock_sleep,
    ):
        game_proc = MagicMock()
        game_proc.poll.return_value = None
        mock_popen.return_value = game_proc

        cfg = CaptureConfig(
            duration=10,
            output="assets/demo/gameplay.gif",
            fps=20,
            display=":0.0",
            geometry="1280x720",
            startup_delay=1.0,
            game_command=("uv", "run", "python", "-m", "src.main"),
        )

        capture_demo_gif(cfg)

        mock_popen.assert_called_once_with(cfg.game_command)
        self.assertGreaterEqual(mock_sleep.call_count, 1)
        mock_run.assert_called_once()
        game_proc.terminate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
