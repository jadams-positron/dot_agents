from pathlib import Path
import unittest

SKILLS = Path(__file__).resolve().parents[2]
ROOT = SKILLS.parent


class PolicyTests(unittest.TestCase):
    def test_superpowers_is_an_unchanged_dependency(self):
        rollout = (ROOT / "docs/work-gh-issues-rollout.md").read_text()
        self.assertIn("consume-only", rollout)
        self.assertIn("coctostan/pi-superpowers", rollout)
        self.assertNotIn("jadams-positron/pi-superpowers", rollout)
        self.assertNotIn("<verified-superpowers-source-path>", rollout)

    def test_owned_callers_define_compatibility_instead_of_inventing_upstream_modes(self):
        reference = SKILLS / "change-control/references/upstream-skills.md"
        self.assertTrue(reference.is_file(), "owned compatibility rules must not require an upstream patch")
        text = reference.read_text()
        for term in ("executing-plans", "receiving-code-review", "writing-plans", "finishing-a-development-branch", "consume-only", "required_now", "report and wait"):
            self.assertIn(term, text)
        self.assertIn("does not add a mode", text)
        self.assertIn("explicit user restrictions", text)
        for name in ("change-control", "work-issue", "work-gh-issues"):
            policy = (SKILLS / name / "SKILL.md").read_text()
            self.assertIn("upstream-skills.md", policy, name)


if __name__ == "__main__":
    unittest.main()
