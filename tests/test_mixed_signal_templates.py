import unittest
from pathlib import Path

from scripts.run_ngspice import render_template
from scripts.spec_io import flatten_for_template, load_spec


class MixedSignalTemplateTest(unittest.TestCase):
    def test_comparator_template_renders(self):
        spec = load_spec("specs/comparator.yaml")
        rendered = render_template(
            Path("circuits/comparator/testbenches/comparator_tran.spice.in"),
            flatten_for_template(spec),
        )

        self.assertIn(".include", rendered)
        self.assertIn("XCOMP vin out vdd 0 static_comparator", rendered)
        self.assertIn(".measure tran delay_s", rendered)

    def test_chain_template_renders_with_absolute_includes(self):
        spec = load_spec("specs/opamp_comparator_chain.yaml")
        rendered = render_template(
            Path("circuits/opamp_comparator_chain/testbenches/chain_tran.spice.in"),
            flatten_for_template(spec),
        )

        self.assertIn("circuits/ota/schematic/ota_5t.spice", rendered)
        self.assertIn("circuits/comparator/schematic/static_comparator.spice", rendered)
        self.assertIn("XOPAMP sensor ref amp_out vdd 0 bias ota_5t", rendered)
        self.assertIn("XCOMP amp_out dout vdd 0 static_comparator", rendered)
        self.assertIn(".measure tran decision_delay_s", rendered)


if __name__ == "__main__":
    unittest.main()
