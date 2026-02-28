import logging
import tempfile
import unittest
from pathlib import Path

from src.main import configure_logging


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


if __name__ == "__main__":
    unittest.main()
