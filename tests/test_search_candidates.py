import unittest

from scripts.search_candidates import candidate_overrides, override_strings
from scripts.spec_io import load_spec


class SearchCandidatesTest(unittest.TestCase):
    def test_generates_profile_candidates(self):
        spec = load_spec("specs/ota.yaml")

        candidates = candidate_overrides(spec, "quick")

        self.assertEqual(len(candidates), 6)
        self.assertIn({"devices.mp_load.w_um": 26, "devices.mn_in.w_um": 15.12}, candidates)

    def test_override_strings_are_stable(self):
        rendered = override_strings({"b": 2.0, "a": True})

        self.assertEqual(rendered, ["a=true", "b=2"])


if __name__ == "__main__":
    unittest.main()
