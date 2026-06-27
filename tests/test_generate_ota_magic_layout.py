import unittest

from scripts.generate_ota_magic_layout import render_tcl
from scripts.spec_io import load_spec


class GenerateOtaMagicLayoutTest(unittest.TestCase):
    def test_renders_routed_pcell_seed(self):
        spec = load_spec("specs/ota.yaml")

        tcl = render_tcl(spec)

        self.assertIn("load ota_5t -force", tcl)
        self.assertIn("magic::gencell sky130::sky130_fd_pr__nfet_01v8 XMN_INP", tcl)
        self.assertIn("w 15.12 l 1.05 nf 1", tcl)
        self.assertIn("magic::gencell sky130::sky130_fd_pr__pfet_01v8 XMP_MIRROR", tcl)
        self.assertIn("proc draw_routes", tcl)
        self.assertIn("# net tail", tcl)
        self.assertIn("paint metal2", tcl)
        self.assertIn("paint via1", tcl)
        self.assertIn("make_pin bias -5.000 -25.000 5", tcl)


if __name__ == "__main__":
    unittest.main()
