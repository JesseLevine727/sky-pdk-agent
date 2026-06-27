import unittest

from scripts.spec_io import flatten_for_template, load_spec


class SpecIoTest(unittest.TestCase):
    def test_flattens_schematic_cell_context(self):
        spec = load_spec("specs/ota.yaml")

        params = flatten_for_template(spec)

        self.assertEqual(params["schematic_cell_name"], "ota_5t")
        self.assertTrue(params["schematic_cell_netlist"].endswith("circuits/ota/schematic/ota_5t.spice"))


if __name__ == "__main__":
    unittest.main()
