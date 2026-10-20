"""Static sanity checks on the AppArmor profile text.

These do NOT load the profile into a kernel; they only catch typos and
accidental removal of the rules the lab depends on. Real enforcement is
checked by check_restrictions.py on a Linux host with AppArmor.
"""
import pathlib
import re
import unittest

PROFILE = pathlib.Path(__file__).parent / "profile" / "lab5-restricted"


class ProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = PROFILE.read_text(encoding="utf-8")
        cls.rules = [
            line.strip()
            for line in cls.text.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]

    def test_profile_name(self):
        self.assertRegex(self.text, r"(?m)^profile lab5-restricted\b")

    def test_braces_balanced(self):
        self.assertEqual(self.text.count("{"), self.text.count("}"))

    def test_rules_end_with_comma(self):
        for rule in self.rules:
            if rule.startswith(("#include", "profile ")) or rule == "}":
                continue
            self.assertTrue(rule.endswith(","), f"missing trailing comma: {rule!r}")

    def test_required_denies_present(self):
        for expected in (
            "deny /etc/passwd r,",
            "deny /var/** wklx,",
            "deny /bin/** mx,",
            "deny /usr/bin/** mx,",
            "deny capability sys_admin,",
            "deny mount,",
        ):
            self.assertIn(expected, self.rules)

    def test_python_interpreter_dir_not_denied(self):
        self.assertFalse(any(re.match(r"deny /usr/local/", r) for r in self.rules))

    def test_network_allowed(self):
        self.assertIn("network inet stream,", self.rules)


if __name__ == "__main__":
    unittest.main()
