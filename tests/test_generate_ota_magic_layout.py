import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.generate_ota_magic_layout import render_manifest, render_tcl, write_manifest
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

    def test_renders_layout_manifest(self):
        spec = load_spec("specs/ota.yaml")

        manifest = render_manifest(
            spec,
            Path("circuits/ota/layout/magic"),
            Path("circuits/ota/layout/magic/ota_5t_seed.tcl"),
            Path("circuits/ota/layout/magic/ota_5t.mag"),
        )

        self.assertEqual("sky-pdk-agent.layout_manifest.v1", manifest["schema"])
        self.assertEqual("ota_5t", manifest["cell"])
        self.assertEqual(
            ["inp", "inn", "out", "vdd", "vss", "bias"],
            manifest["pin_order"],
        )
        self.assertEqual("inp", manifest["pins"][0]["name"])
        self.assertEqual([23.5, -25.0], manifest["pins"][4]["origin_um"])
        self.assertEqual("XMP_DIODE", manifest["devices"][0]["instance"])
        self.assertEqual("mp_load", manifest["devices"][0]["spec_device"])
        self.assertIn("G", manifest["devices"][0]["ports_um"])
        self.assertIn("tail", manifest["route_nets"])
        self.assertIn("metal3", manifest["generated_layers"])
        self.assertEqual(
            "circuits/ota/layout/magic/ota_5t.mag",
            manifest["generated_files"]["magic_layout"],
        )

    def test_writes_layout_manifest_json(self):
        spec = load_spec("specs/ota.yaml")

        with TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir)
            manifest_path = write_manifest(
                spec,
                out_dir,
                out_dir / "ota_5t_seed.tcl",
                out_dir / "ota_5t_layout_manifest.json",
            )

            data = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual("ota_5t", data["cell"])
        self.assertEqual("scripts/generate_ota_magic_layout.py", data["generator"])
        self.assertEqual(5, len(data["devices"]))


if __name__ == "__main__":
    unittest.main()
