"""Tests for Lab 8 that need no Jenkins or Docker (standard library + bash).

They render the job config with render_job.sh and check the resulting XML, run
the sample-repo helper against a temporary directory, and check safety
properties of the files. They do not talk to Jenkins.
"""
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).parent
BASH = shutil.which("bash")


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def render(**env):
    full = {k: v for k, v in os.environ.items() if k not in ("REPO_URL", "BRANCH", "POLL_SCM_SPEC")}
    full.update(env)
    out = subprocess.run([BASH, str(ROOT / "render_job.sh")], env=full,
                         capture_output=True, text=True, check=True)
    return out.stdout


@unittest.skipUnless(BASH, "bash not available")
class RenderTests(unittest.TestCase):
    def test_defaults_produce_wellformed_xml(self):
        root = ET.fromstring(render())
        self.assertEqual(root.tag, "project")
        self.assertEqual(root.find(".//hudson.plugins.git.UserRemoteConfig/url").text,
                         "file:///sample-repo")
        self.assertEqual(root.find(".//hudson.plugins.git.BranchSpec/name").text, "*/main")
        self.assertEqual(list(root.find("triggers")), [])

    def test_no_unreplaced_placeholders(self):
        self.assertNotRegex(render(POLL_SCM_SPEC="H/5 * * * *"), r"@[A-Z_]+@")
        self.assertNotRegex(render(), r"@[A-Z_]+@")

    def test_custom_repo_and_branch(self):
        root = ET.fromstring(render(REPO_URL="https://github.com/me/devops-sample-code.git",
                                    BRANCH="*/develop"))
        self.assertEqual(root.find(".//hudson.plugins.git.UserRemoteConfig/url").text,
                         "https://github.com/me/devops-sample-code.git")
        self.assertEqual(root.find(".//hudson.plugins.git.BranchSpec/name").text, "*/develop")

    def test_special_characters_are_escaped_not_corrupting(self):
        url = "https://example.com/r.git?a=1&b=2|x"
        root = ET.fromstring(render(REPO_URL=url))
        self.assertEqual(root.find(".//hudson.plugins.git.UserRemoteConfig/url").text, url)

    def test_poll_trigger_added_when_requested(self):
        root = ET.fromstring(render(POLL_SCM_SPEC="H/2 * * * *"))
        self.assertEqual(root.find("triggers/hudson.triggers.SCMTrigger/spec").text, "H/2 * * * *")

    def test_parameter_and_build_step(self):
        root = ET.fromstring(render())
        self.assertEqual(root.find(".//hudson.model.StringParameterDefinition/name").text, "GREETEE")
        command = root.find(".//hudson.tasks.Shell/command").text
        self.assertIn('bash hello-world.sh "$GREETEE"', command)

    def test_build_history_is_bounded(self):
        self.assertEqual(ET.fromstring(render()).find(".//numToKeep").text, "10")


@unittest.skipUnless(BASH and shutil.which("git"), "bash and git required")
class SampleRepoTests(unittest.TestCase):
    def test_helper_creates_repo_and_never_needs_a_remote(self):
        with tempfile.TemporaryDirectory() as tmp:
            lab = pathlib.Path(tmp) / "lab"
            shutil.copytree(ROOT, lab, ignore=shutil.ignore_patterns(".work", "__pycache__"))
            run = lambda *a: subprocess.run([BASH, str(lab / "make_sample_repo.sh"), *a],
                                            capture_output=True, text=True, check=True).stdout
            run()
            repo = lab / ".work" / "devops-sample-code"
            self.assertTrue((repo / "hello-world.sh").is_file())
            run("--new-commit")
            log = subprocess.run(["git", "-C", str(repo), "log", "--oneline"],
                                 capture_output=True, text=True, check=True).stdout
            self.assertEqual(len(log.strip().splitlines()), 2)
            remotes = subprocess.run(["git", "-C", str(repo), "remote"],
                                     capture_output=True, text=True, check=True).stdout
            self.assertEqual(remotes.strip(), "")


class SafetyTests(unittest.TestCase):
    def test_no_script_pushes_anywhere(self):
        for rel in ("deploy.sh", "verify.sh", "create_job.sh", "make_sample_repo.sh",
                    "cleanup.sh", "render_job.sh", "lib.sh"):
            text = read(rel)
            self.assertNotIn("git push", text, rel)
            self.assertNotIn("remote add", text, rel)

    def test_compose_requires_password_and_binds_loopback(self):
        text = read("docker-compose.yml")
        self.assertIn("JENKINS_ADMIN_PASSWORD:?", text)
        self.assertIn('"127.0.0.1:${JENKINS_PORT:-8080}:8080"', text)
        self.assertIn(":/sample-repo:ro", text)

    def test_init_script_fails_closed(self):
        text = read("init.groovy.d/01-admin-user.groovy")
        self.assertRegex(text, r"if \(!adminPassword\)[\s\S]*throw")
        self.assertIn("setAllowAnonymousRead(false)", text)

    def test_wizard_disabled_and_git_plugin_installed(self):
        self.assertIn("-Djenkins.install.runSetupWizard=false", read("Dockerfile"))
        self.assertIn("\ngit\n", read("plugins.txt"))

    def test_env_example_has_only_placeholder(self):
        self.assertIn("JENKINS_ADMIN_PASSWORD=change-me", read(".env.example"))

    def test_work_dir_is_ignored(self):
        self.assertIn(".work/", read(".gitignore"))


if __name__ == "__main__":
    unittest.main()
