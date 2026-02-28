import unittest
from unittest.mock import MagicMock
from src.utils.helpers import hp_color, make_stars, wrap_text
from src.constants import GREEN, YELLOW, RED, WIDTH, HEIGHT


class TestUtils(unittest.TestCase):
    def test_hp_color_green(self):
        self.assertEqual(hp_color(100, 100), GREEN)
        self.assertEqual(hp_color(41, 100), GREEN)

    def test_hp_color_yellow(self):
        self.assertEqual(hp_color(40, 100), YELLOW)
        self.assertEqual(hp_color(21, 100), YELLOW)

    def test_hp_color_red(self):
        self.assertEqual(hp_color(20, 100), RED)
        self.assertEqual(hp_color(0, 100), RED)

    def test_hp_color_zero_max_hp(self):
        self.assertEqual(hp_color(0, 0), RED)

    def test_make_stars(self):
        stars = make_stars(10)
        self.assertEqual(len(stars), 10)
        for x, y, b, s in stars:
            self.assertTrue(0 <= x <= WIDTH)
            self.assertTrue(0 <= y <= HEIGHT)
            self.assertTrue(120 <= b <= 255)  # Brightness
            self.assertTrue(1 <= s <= 3)     # Size

    def test_wrap_text(self):
        mock_font = MagicMock()
        # Mock font.size to return width based on string length for simplicity
        mock_font.size.side_effect = lambda s: (len(s) * 10, 20)

        text = "this is a test text"
        # max_w = 40 means max 4 characters per line
        lines = wrap_text(mock_font, text, 40)
        self.assertEqual(lines, ["this", "is a", "test", "text"])

    def test_wrap_text_empty(self):
        mock_font = MagicMock()
        mock_font.size.return_value = (0, 0)
        self.assertEqual(wrap_text(mock_font, "", 100), [""])


if __name__ == "__main__":
    unittest.main()
