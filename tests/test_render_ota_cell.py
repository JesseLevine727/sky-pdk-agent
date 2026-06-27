import unittest

from scripts.render_ota_cell import render_ota_cell
from scripts.spec_io import load_spec


class RenderOtaCellTest(unittest.TestCase):
    def test_renders_parameterized_ota_subcircuit(self):
        spec = load_spec("specs/ota.yaml")

        rendered = render_ota_cell(spec)

        self.assertIn(".subckt ota_5t inp inn out vdd vss bias", rendered)
        self.assertIn("MN_IN_W=15.12", rendered)
        self.assertIn("MP_LOAD_W=26", rendered)
        self.assertIn("XMN_INP outn inp tail vss sky130_fd_pr__nfet_01v8", rendered)
        self.assertIn("XMP_MIRROR out outn vdd vdd sky130_fd_pr__pfet_01v8", rendered)
        self.assertIn(".ends ota_5t", rendered)


if __name__ == "__main__":
    unittest.main()
