import unittest

from scripts.agent_loop import generated_candidates, override_strings, score_evaluation


class AgentLoopTest(unittest.TestCase):
    def test_generated_candidates_include_balanced_tradeoff(self):
        spec = {
            "bias_tail_v": 0.68,
            "devices": {
                "mn_in": {"w_um": 10.8, "l_um": 0.7},
                "mp_load": {"l_um": 0.7},
            },
        }
        baseline = {
            "results": [
                {"score": {"misses": {"dc_gain_db": 0.02}}},
                {"score": {"misses": {"unity_gain_hz": 0.2}}},
            ]
        }

        candidates = generated_candidates(spec, baseline)

        self.assertIn(
            [
                "bias_tail_v=0.7",
                "devices.mn_in.l_um=1.05",
                "devices.mn_in.w_um=15.12",
                "devices.mp_load.l_um=1.05",
            ],
            [override_strings(candidate) for candidate in candidates],
        )

    def test_score_evaluation_prefers_passing_result(self):
        passing = score_evaluation(
            {
                "summary": {"pass": True, "passed_count": 4, "failed_count": 0, "errored_count": 0},
                "results": [{"score": {"misses": {}}, "measures": {"power_w": 2e-5}}],
            }
        )
        failing = score_evaluation(
            {
                "summary": {"pass": False, "passed_count": 3, "failed_count": 1, "errored_count": 0},
                "results": [{"score": {"misses": {"unity_gain_hz": 0.2}}, "measures": {"power_w": 2e-5}}],
            }
        )

        self.assertTrue(passing["pass"])
        self.assertLess(passing["score"], failing["score"])


if __name__ == "__main__":
    unittest.main()
