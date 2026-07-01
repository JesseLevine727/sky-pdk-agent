import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.generate_comparator_magic_layout import render_manifest, render_tcl, write_manifest
from scripts.render_comparator_cell import render_cell
from scripts.spec_io import load_spec


class ComparatorPhysicalTest(unittest.TestCase):
    def test_renders_comparator_cell_from_spec(self):
        spec = load_spec("specs/comparator.yaml")

        rendered = render_cell(spec)

        self.assertIn(".subckt static_comparator vin out vdd vss", rendered)
        self.assertIn("MN_W=1", rendered)
        self.assertIn("MP_W=2.5", rendered)
        self.assertIn("XMN out vin vss vss sky130_fd_pr__nfet_01v8", rendered)
        self.assertIn("XMP out vin vdd vdd sky130_fd_pr__pfet_01v8", rendered)

    def test_renders_comparator_layout_tcl_and_manifest(self):
        spec = load_spec("specs/comparator.yaml")

        tcl = render_tcl(spec)
        manifest = render_manifest(
            spec,
            Path("circuits/comparator/layout/magic"),
            Path("circuits/comparator/layout/magic/static_comparator_seed.tcl"),
            Path("circuits/comparator/layout/magic/static_comparator.mag"),
        )

        self.assertIn("load static_comparator -force", tcl)
        self.assertIn("magic::gencell sky130::sky130_fd_pr__nfet_01v8 XMN", tcl)
        self.assertIn("magic::gencell sky130::sky130_fd_pr__pfet_01v8 XMP", tcl)
        self.assertIn("# net vin", tcl)
        self.assertIn("make_pin out 8.000 6.000 1", tcl)
        self.assertEqual("static_comparator", manifest["cell"])
        self.assertEqual(["vin", "out", "vdd", "vss"], manifest["pin_order"])
        self.assertEqual(2, len(manifest["devices"]))
        self.assertIn("vdd", manifest["route_nets"])

    def test_writes_comparator_layout_manifest_json(self):
        spec = load_spec("specs/comparator.yaml")

        with TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir)
            manifest_path = write_manifest(
                spec,
                out_dir,
                out_dir / "static_comparator_seed.tcl",
                out_dir / "static_comparator_layout_manifest.json",
            )

            text = manifest_path.read_text(encoding="utf-8")

        self.assertIn("sky-pdk-agent.layout_manifest.v1", text)
        self.assertIn("static_comparator", text)


if __name__ == "__main__":
    unittest.main()
