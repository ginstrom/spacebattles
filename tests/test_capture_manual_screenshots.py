import unittest
from unittest.mock import patch

from src.tools.capture_manual_screenshots import (
    ManualScreenshotConfig,
    parse_args,
    screenshot_filenames,
)


class TestCaptureManualScreenshots(unittest.TestCase):
    def test_parse_args_uses_expected_defaults(self):
        with patch("sys.argv", ["capture_manual_screenshots"]):
            args = parse_args()
        self.assertEqual(args.output_dir, "docs/images/manual")

    def test_screenshot_filenames_cover_core_and_advanced_features(self):
        names = screenshot_filenames()
        self.assertEqual(
            names,
            [
                "battle-overview.png",
                "waypoint-planning.png",
                "combat-fire-exchange.png",
                "weapon-arc-preview.png",
                "zoomed-map.png",
                "distance-falloff-details.png",
            ],
        )

    def test_config_defaults_match_cli_defaults(self):
        cfg = ManualScreenshotConfig()
        self.assertEqual(cfg.output_dir, "docs/images/manual")


if __name__ == "__main__":
    unittest.main()
