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

    def test_derives_current_mirror_operating_point_values(self):
        text = """
        vdd                              1.800000e+00
        ref                              6.393686e-01
        vdd#branch                       -1.00000e-05
        vout#branch                      -1.09545e-05
        """

        measures = parse_measure_text(text)

        self.assertEqual(measures["power_w"], 1.8e-05)
        self.assertEqual(measures["vref_v"], 0.6393686)
        self.assertEqual(measures["iout_a"], 1.09545e-05)


if __name__ == "__main__":
    unittest.main()
