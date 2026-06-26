import unittest

from scripts.parse_measures import parse_measure_text


class ParseMeasuresTest(unittest.TestCase):
    def test_parses_standard_ngspice_measure_lines(self):
        text = """
        dc_gain_db = 4.215e+01
        unity_gain_hz = 6.7e6
        phase_margin_deg = 61.2
        """

        measures = parse_measure_text(text)

        self.assertAlmostEqual(measures["dc_gain_db"], 42.15)
        self.assertAlmostEqual(measures["unity_gain_hz"], 6.7e6)
        self.assertAlmostEqual(measures["phase_margin_deg"], 61.2)


if __name__ == "__main__":
    unittest.main()

