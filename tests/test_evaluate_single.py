import tempfile
import unittest
from pathlib import Path

from scripts.evaluate_single import write_report


class EvaluateSingleTest(unittest.TestCase):
    def test_writes_single_testbench_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.md"

            write_report(
                report,
                "specs/example.yaml",
                "tb.spice.in",
                Path("runs/example"),
                {"iout_a": 1.0e-5},
                {"pass": True, "misses": {}},
            )

            text = report.read_text(encoding="utf-8")
            self.assertIn("Overall: PASS", text)
            self.assertIn("`iout_a`", text)


if __name__ == "__main__":
    unittest.main()
