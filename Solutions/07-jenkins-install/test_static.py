"""Static checks for the Lab 7 files (standard library only).

They verify structure and safety properties of the text. They do not build the
image, install plugins or start Jenkins; that needs Docker.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).parent


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


class GroovyTests(unittest.TestCase):
    def setUp(self):
        self.text = read("init.groovy.d/01-admin-user.groovy")

    def test_braces_and_parens_balanced(self):
        for open_, close in ("{}", "()"):
            self.assertEqual(self.text.count(open_), self.text.count(close))

    def test_reads_credentials_from_environment(self):
        self.assertIn("JENKINS_ADMIN_PASSWORD", self.text)
        self.assertIn("JENKINS_ADMIN_USER", self.text)

    def test_fails_closed_without_password(self):
        self.assertRegex(self.text, r"if \(!adminPassword\)[\s\S]*throw")

    def test_anonymous_read_disabled(self):
        self.assertIn("setAllowAnonymousRead(false)", self.text)

    def test_account_creation_is_idempotent(self):
        self.assertIn("getUser(adminUser) == null", self.text)

    def test_no_hardcoded_password(self):
        self.assertNotRegex(self.text, r"createAccount\([^)]*['\"][^'\"]+['\"]\s*\)")


class DockerfileTests(unittest.TestCase):
    def setUp(self):
        self.text = read("Dockerfile")

    def test_wizard_disabled(self):
        self.assertIn("-Djenkins.install.runSetupWizard=false", self.text)

    def test_plugins_and_init_script_copied(self):
        self.assertIn("jenkins-plugin-cli --plugin-file", self.text)
        self.assertIn("init.groovy.d", self.text)

    def test_pinned_lts_tag(self):
        self.assertRegex(self.text, r"FROM jenkins/jenkins:lts-jdk\d+")


class PluginsTests(unittest.TestCase):
    def test_entries_are_valid_ids(self):
        entries = [l.strip() for l in read("plugins.txt").splitlines()
                   if l.strip() and not l.startswith("#")]
        self.assertGreaterEqual(len(entries), 3)
        for e in entries:
            self.assertRegex(e, r"^[a-z0-9-]+(:[\w.\-]+)?$")
        self.assertIn("workflow-aggregator", entries)
        self.assertIn("git", entries)


class ComposeTests(unittest.TestCase):
    def setUp(self):
        self.text = read("docker-compose.yml")

    def test_password_required(self):
        self.assertIn("JENKINS_ADMIN_PASSWORD:?", self.text)

    def test_port_bound_to_loopback(self):
        self.assertIn('"127.0.0.1:${JENKINS_PORT:-8080}:8080"', self.text)

    def test_agent_port_not_published(self):
        self.assertNotRegex(self.text, r'(?m)^\s*-\s*"[^"]*50000:50000"')

    def test_named_volume_for_jenkins_home(self):
        self.assertIn("jenkins_home:/var/jenkins_home", self.text)
        self.assertRegex(self.text, r"(?m)^volumes:\n\s+jenkins_home:")

    def test_healthcheck_defined(self):
        self.assertIn("healthcheck:", self.text)

    def test_no_tabs(self):
        self.assertNotIn("\t", self.text)


class SecretsTests(unittest.TestCase):
    def test_env_example_only_has_placeholder(self):
        self.assertIn("JENKINS_ADMIN_PASSWORD=change-me", read(".env.example"))

    def test_no_literal_passwords_in_scripts_or_compose(self):
        for rel in ("deploy.sh", "verify.sh", "cleanup.sh", "docker-compose.yml"):
            for line in read(rel).splitlines():
                if re.search(r"PASSWORD\s*[:=]\s*[A-Za-z0-9]{6,}\s*$", line) and "unused" not in line:
                    self.fail(f"possible literal password in {rel}: {line.strip()}")


if __name__ == "__main__":
    unittest.main()
