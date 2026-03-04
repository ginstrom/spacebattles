import unittest
from unittest.mock import patch

from src.tools.capture_demo_gif import (
    CaptureConfig,
    capture_demo_gif,
)


class TestCaptureDemoGif(unittest.TestCase):
    @patch("src.tools.capture_demo_gif.subprocess.Popen")
    def test_capture_demo_gif_uses_capture_env(
        self,
        mock_popen,
    ):
        game_proc = unittest.mock.MagicMock()
        game_proc.wait.return_value = 0
        mock_popen.return_value = game_proc
        cfg = CaptureConfig(
            duration=10,
            output="assets/demo/gameplay.gif",
            fps=20,
            caption="Image #1: Demo",
            game_command=("uv", "run", "python", "-m", "src.main"),
        )

        capture_demo_gif(cfg)

        mock_popen.assert_called_once()
        _, game_kwargs = mock_popen.call_args_list[0]
        self.assertIn("env", game_kwargs)
        self.assertEqual(game_kwargs["env"]["SPACEBATTLE_DEMO_SCRIPT"], "1")
        self.assertEqual(game_kwargs["env"]["SPACEBATTLE_WINDOWED"], "1")
        self.assertEqual(game_kwargs["env"]["SPACEBATTLE_CAPTURE_GIF"], "1")
        self.assertEqual(game_kwargs["env"]["SPACEBATTLE_CAPTURE_DURATION"], "10")
        self.assertEqual(game_kwargs["env"]["SPACEBATTLE_CAPTURE_FPS"], "20")
        self.assertEqual(game_kwargs["env"]["SPACEBATTLE_CAPTURE_OUTPUT"], "assets/demo/gameplay.gif")
        self.assertEqual(game_kwargs["env"]["SPACEBATTLE_CAPTURE_CAPTION"], "Image #1: Demo")
        game_proc.wait.assert_called_once()


if __name__ == "__main__":
    unittest.main()
