import sys
import unittest
from pathlib import Path

from scripts.signoff_block import ALL_STAGES, build_plan, paths_for, selected_stages
from scripts.spec_io import load_spec


class SignoffBlockTest(unittest.TestCase):
    def test_builds_ota_signoff_plan_from_spec(self):
        spec_path = Path("specs/ota.yaml")
        spec = load_spec(spec_path)

        plan = build_plan(spec_path, spec, selected_stages("all"))

        self.assertEqual([stage.name for stage in plan], ALL_STAGES)
        self.assertEqual(plan[0].command[:2], [sys.executable, "scripts/render_ota_cell.py"])
        self.assertIn("scripts/run_magic_drc.sh", plan[3].command)
        self.assertIn("scripts/run_netgen_lvs.sh", plan[5].command)
        self.assertTrue(any("postlayout_eval.md" in str(path) for path in plan[-1].evidence))

    def test_uses_flow_paths_for_ota_reports(self):
        spec_path = Path("specs/ota.yaml")
        spec = load_spec(spec_path)

        paths = paths_for(spec_path, spec)

        self.assertEqual(paths["lvs_report"], Path("circuits/ota/reports/lvs_ota.md"))
        self.assertEqual(paths["postlayout_report"], Path("circuits/ota/reports/postlayout_eval.md"))


if __name__ == "__main__":
    unittest.main()
