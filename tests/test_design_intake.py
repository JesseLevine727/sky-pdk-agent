import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.design_intake import (
    build_plan,
    load_catalog,
    load_intent,
    scaffold_directories,
    write_markdown_report,
)


class DesignIntakeTest(unittest.TestCase):
    def test_builds_opamp_comparator_plan(self):
        intent = load_intent("intents/opamp_comparator_chain.yaml")
        catalog = load_catalog("templates/analog_blocks.yaml")

        plan = build_plan(intent, catalog)

        self.assertEqual("sky-pdk-agent.design_plan.v1", plan["schema"])
        self.assertEqual("opamp_comparator_chain", plan["design"])
        self.assertEqual("templates/analog_blocks.yaml", plan["catalog_path"])
        self.assertEqual("ota_frontend_static_cmos_comparator", plan["topology"])
        self.assertEqual(
            ["opamp", "comparator", "opamp_comparator_chain"],
            [block["name"] for block in plan["blocks"]],
        )
        self.assertIn("specs/comparator.yaml", plan["planned_paths"])
        self.assertIn("make eval-opamp-comparator-chain", plan["acceptance"]["commands"])
        self.assertEqual([True, True, True], [match["matched"] for match in plan["template_matches"]])
        comparator = next(match for match in plan["template_matches"] if match["kind"] == "static_cmos_comparator")
        self.assertTrue(comparator["supports"]["schematic_eval"])
        self.assertTrue(comparator["supports"]["layout"])
        self.assertEqual("make signoff-comparator", comparator["commands"]["signoff"])

    def test_writes_report_and_scaffolds_directories(self):
        intent = load_intent("intents/opamp_comparator_chain.yaml")
        catalog = load_catalog("templates/analog_blocks.yaml")
        plan = build_plan(intent, catalog)

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = write_markdown_report(plan, root / "reports" / "design_plan.md")
            created = scaffold_directories(plan, root)
            json_path = root / "reports" / "design_plan.json"
            json_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            report_text = report.read_text(encoding="utf-8")
            json_text = json_path.read_text(encoding="utf-8")

        self.assertIn("# Design Intake Plan", report_text)
        self.assertIn("## Template Coverage", report_text)
        self.assertIn("opamp.out", report_text)
        self.assertTrue(any(path.name == ".gitkeep" for path in created))
        self.assertIn("static_cmos_comparator", json_text)


if __name__ == "__main__":
    unittest.main()
