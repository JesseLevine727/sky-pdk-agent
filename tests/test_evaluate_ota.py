import unittest

from scripts.evaluate_ota import (
    evaluation_cases,
    override_args,
    overrides_to_mapping,
    summarize_results,
)


class EvaluateOtaTest(unittest.TestCase):
    def test_evaluation_cases_from_mapping_are_named(self):
        spec = {
            "evaluation": {
                "cases": {
                    "nominal tt": {
                        "description": "Nominal",
                        "overrides": {"simulation.corner": "tt", "supply_v": 1.8},
                    }
                }
            }
        }

        cases = evaluation_cases(spec)

        self.assertEqual(cases[0]["name"], "nominal_tt")
        self.assertEqual(cases[0]["overrides"]["simulation.corner"], "tt")

    def test_override_args_are_stable(self):
        args = override_args({"supply_v": 1.8, "simulation.corner": "tt"})

        self.assertEqual(args, ["--set", "simulation.corner=tt", "--set", "supply_v=1.8"])

    def test_override_args_render_booleans_and_nulls(self):
        args = override_args({"enabled": True, "none_value": None})

        self.assertEqual(args, ["--set", "enabled=true", "--set", "none_value=null"])

    def test_overrides_to_mapping_parses_scalars(self):
        parsed = overrides_to_mapping(["supply_v=1.8", "enabled=true"])

        self.assertEqual(parsed["supply_v"], 1.8)
        self.assertTrue(parsed["enabled"])

    def test_summarize_results_counts_pass_fail_and_error(self):
        summary = summarize_results(
            [
                {"returncode": 0, "score": {"pass": True}},
                {"returncode": 0, "score": {"pass": False}},
                {"returncode": 1, "score": {}},
            ]
        )

        self.assertEqual(summary["case_count"], 3)
        self.assertEqual(summary["passed_count"], 1)
        self.assertEqual(summary["failed_count"], 1)
        self.assertEqual(summary["errored_count"], 1)
        self.assertFalse(summary["pass"])


if __name__ == "__main__":
    unittest.main()
