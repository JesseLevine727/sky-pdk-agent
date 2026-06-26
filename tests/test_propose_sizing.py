import unittest

from scripts.propose_sizing import propose
from scripts.spec_io import load_spec


class ProposeSizingTest(unittest.TestCase):
    def test_gain_and_bandwidth_misses_create_overrides(self):
        spec = load_spec("specs/ota.yaml")
        proposal = propose(
            spec,
            {
                "dc_gain_db": 32.0,
                "unity_gain_hz": 1.0e6,
                "phase_margin_deg": 70.0,
                "power_w": 1.0e-4,
            },
        )

        self.assertIn("devices.mn_in.l_um", proposal["overrides"])
        self.assertIn("devices.mp_load.l_um", proposal["overrides"])
        self.assertIn("devices.mn_in.w_um", proposal["overrides"])
        self.assertIn("bias_tail_v", proposal["overrides"])


if __name__ == "__main__":
    unittest.main()

