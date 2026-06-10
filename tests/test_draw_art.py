import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import draw_art


class StartDateParsingTests(unittest.TestCase):
    def test_accepts_sunday_start_date(self) -> None:
        self.assertEqual(draw_art._parse_start_date("2026-06-07"), date(2026, 6, 7))

    def test_rejects_non_sunday_start_date(self) -> None:
        with patch("builtins.print") as mocked_print:
            with self.assertRaises(SystemExit) as raised:
                draw_art._parse_start_date("2026-06-10")

        self.assertEqual(raised.exception.code, 1)
        self.assertIn("must be a Sunday", mocked_print.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
