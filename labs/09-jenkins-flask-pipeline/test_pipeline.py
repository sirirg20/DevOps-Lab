"""Tests for the Lab 9 pipeline pieces that can run without Jenkins, Docker or Flask.

Standard library plus bash/tar/curl. They run the ci/ scripts for real (package,
deploy and prune, app start/stop, smoke test against a stand-in HTTP server),
render the job XML, and check the Jenkinsfile and files structurally. They do
not run Jenkins, so stage execution and the Flask tests are not covered here.
"""
import ast
import http.server
import os
import pathlib
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import threading
import unittest
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).parent
BASH = shutil.which("bash")
needs_bash = unittest.skipUnless(BASH, "bash not available")


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def sh(script, *args, env=None, check=True):
    full = dict(os.environ)
    full.update(env or {})
    # POSIX-style script path: with backslashes, `dirname "$0"` inside the script breaks.
    return subprocess.run([BASH, (ROOT / script).as_posix(), *map(str, args)], env=full,
                          capture_output=True, text=True, check=check)


def posix(path):
    return pathlib.Path(path).as_posix()


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@needs_bash
class PackageTests(unittest.TestCase):
    def test_package_contains_only_runtime_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            sh("ci/package.sh", "5", posix(tmp))
            with tarfile.open(pathlib.Path(tmp) / "flask-app-5.tar.gz") as tar:
                names = sorted(tar.getnames())
                version = tar.extractfile("VERSION").read().decode().strip()
        self.assertEqual(names, ["VERSION", "app.py", "requirements.txt"])
        self.assertEqual(version, "5")

    def test_package_requires_version(self):
        self.assertNotEqual(sh("ci/package.sh", check=False).returncode, 0)


@needs_bash
class DeployTests(unittest.TestCase):
    def deploy_all(self, tmp, versions, keep):
        dist, root = posix(pathlib.Path(tmp) / "dist"), posix(pathlib.Path(tmp) / "root")
        for v in versions:
            sh("ci/package.sh", v, dist)
            sh("ci/deploy.sh", f"{dist}/flask-app-{v}.tar.gz", root, keep, env={"SKIP_VENV": "1"})
        return pathlib.Path(root)

    def test_switches_current_and_prunes_old_releases(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.deploy_all(tmp, [7, 8, 9, 10], keep=2)
            self.assertEqual(sorted(p.name for p in (root / "releases").iterdir()), ["10", "9"])
            self.assertEqual((root / "current" / "VERSION").read_text().strip(), "10")

    def test_numeric_ordering_not_lexical(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.deploy_all(tmp, [2, 9, 10, 11], keep=2)
            self.assertEqual(sorted(p.name for p in (root / "releases").iterdir()), ["10", "11"])

    def test_redeploying_same_version_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.deploy_all(tmp, [3, 3], keep=3)
            self.assertEqual([p.name for p in (root / "releases").iterdir()], ["3"])
            self.assertEqual((root / "current" / "app.py").is_file(), True)

    def test_rejects_invalid_keep_and_missing_tarball(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = posix(pathlib.Path(tmp) / "root")

            def code(tarball, keep):
                return sh("ci/deploy.sh", tarball, root, keep, check=False).returncode

            self.assertEqual(code("x.tar.gz", "abc"), 2)
            self.assertEqual(code("x.tar.gz", "0"), 2)
            self.assertEqual(code("missing.tar.gz", "2"), 1)

    def test_rejects_package_without_app(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = pathlib.Path(tmp) / "flask-app-1.tar.gz"
            (pathlib.Path(tmp) / "x.txt").write_text("x")
            with tarfile.open(bad, "w:gz") as tar:
                tar.add(pathlib.Path(tmp) / "x.txt", arcname="x.txt")
            r = sh("ci/deploy.sh", posix(bad), posix(pathlib.Path(tmp) / "root"), "2",
                   env={"SKIP_VENV": "1"}, check=False)
            self.assertEqual(r.returncode, 1)
            self.assertIn("no app.py", r.stderr)


@needs_bash
class RunAppTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = posix(self.tmp.name)
        self.port = free_port()
        py = sys.executable
        self.env = {
            "DEPLOY_ROOT": self.root,
            "APP_DIR": self.root,
            "APP_PORT": str(self.port),
            "APP_CMD": f"{posix(py)} -m http.server {self.port} --bind 127.0.0.1",
        }

    def tearDown(self):
        sh("ci/run_app.sh", "stop", env=self.env, check=False)
        self.tmp.cleanup()

    def listening(self):
        with socket.socket() as s:
            s.settimeout(0.5)
            return s.connect_ex(("127.0.0.1", self.port)) == 0

    def wait_listening(self, want, seconds=10):
        import time
        end = time.time() + seconds
        while time.time() < end:
            if self.listening() == want:
                return True
            time.sleep(0.2)
        return False

    def test_start_status_stop_lifecycle(self):
        sh("ci/run_app.sh", "start", env=self.env)
        self.assertTrue(self.wait_listening(True), "app never started listening")
        self.assertEqual(sh("ci/run_app.sh", "status", env=self.env).returncode, 0)
        self.assertTrue((pathlib.Path(self.tmp.name) / "app.pid").is_file())

        sh("ci/run_app.sh", "stop", env=self.env)
        self.assertTrue(self.wait_listening(False), "app still listening after stop")
        self.assertFalse((pathlib.Path(self.tmp.name) / "app.pid").exists())
        self.assertEqual(sh("ci/run_app.sh", "status", env=self.env, check=False).returncode, 3)

    def test_second_start_is_refused(self):
        sh("ci/run_app.sh", "start", env=self.env)
        self.assertNotEqual(sh("ci/run_app.sh", "start", env=self.env, check=False).returncode, 0)

    def test_stop_is_safe_when_not_running(self):
        self.assertEqual(sh("ci/run_app.sh", "stop", env=self.env).returncode, 0)

    def test_command_that_exits_immediately_is_reported(self):
        env = dict(self.env, APP_CMD="false")
        r = sh("ci/run_app.sh", "start", env=env, check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("exited immediately", r.stderr)
        self.assertFalse((pathlib.Path(self.tmp.name) / "app.pid").exists())


class FakeApp:
    """Stand-in HTTP server so smoke_test.sh can be tested without Flask."""

    def __init__(self, routes):
        outer = routes

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path in outer:
                    body = outer[self.path].encode()
                    self.send_response(200)
                else:
                    body = b"missing"
                    self.send_response(404)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


GOOD = {
    "/": "Hello from the Flask pipeline!\n",
    "/health": '{"status": "ok"}\n',
    "/version": '{"version": "12"}\n',
}


@needs_bash
class SmokeTestTests(unittest.TestCase):
    fast = {"SMOKE_RETRIES": "2", "SMOKE_DELAY": "0"}

    def run_smoke(self, routes, **extra_env):
        app = FakeApp(routes)
        try:
            return sh("ci/smoke_test.sh", app.url, env=dict(self.fast, **extra_env), check=False)
        finally:
            app.close()

    def test_passes_against_healthy_app(self):
        r = self.run_smoke(GOOD)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("SMOKE TEST PASSED", r.stdout)

    def test_checks_expected_version(self):
        self.assertEqual(self.run_smoke(GOOD, EXPECTED_VERSION="12").returncode, 0)
        r = self.run_smoke(GOOD, EXPECTED_VERSION="13")
        self.assertEqual(r.returncode, 1)
        self.assertIn("version is 13", r.stderr)

    def test_fails_when_health_is_not_ok(self):
        r = self.run_smoke(dict(GOOD, **{"/health": '{"status": "down"}'}))
        self.assertEqual(r.returncode, 1)
        self.assertIn("health reports ok", r.stderr)

    def test_fails_when_endpoint_missing(self):
        routes = {k: v for k, v in GOOD.items() if k != "/version"}
        self.assertEqual(self.run_smoke(routes).returncode, 1)

    def test_fails_when_nothing_is_listening(self):
        port = free_port()
        r = sh("ci/smoke_test.sh", f"http://127.0.0.1:{port}", env=self.fast, check=False)
        self.assertEqual(r.returncode, 1)


@needs_bash
class RenderTests(unittest.TestCase):
    def render(self, **env):
        base = {k: v for k, v in os.environ.items()
                if k not in ("REPO_URL", "BRANCH", "SCRIPT_PATH", "POLL_SCM_SPEC")}
        base.update(env)
        out = subprocess.run([BASH, (ROOT / "render_job.sh").as_posix()], env=base,
                             capture_output=True, text=True, check=True)
        return out.stdout

    def test_defaults(self):
        root = ET.fromstring(self.render())
        self.assertEqual(root.tag, "flow-definition")
        self.assertEqual(root.find(".//url").text, "file:///repo-src")
        self.assertEqual(root.find(".//branches//name").text, "*/main")
        self.assertEqual(root.find(".//scriptPath").text,
                         "labs/09-jenkins-flask-pipeline/Jenkinsfile")
        self.assertEqual(list(root.find("triggers")), [])

    def test_no_unreplaced_tokens(self):
        for text in (self.render(), self.render(POLL_SCM_SPEC="H/5 * * * *")):
            self.assertNotRegex(text, r"@[A-Z_]+@")

    def test_special_characters_survive(self):
        url = "https://example.com/r.git?a=1&b=2|x"
        self.assertEqual(ET.fromstring(self.render(REPO_URL=url)).find(".//url").text, url)

    def test_poll_trigger(self):
        root = ET.fromstring(self.render(POLL_SCM_SPEC="H/5 * * * *"))
        self.assertEqual(root.find("triggers/hudson.triggers.SCMTrigger/spec").text, "H/5 * * * *")


class JenkinsfileTests(unittest.TestCase):
    def setUp(self):
        self.text = read("Jenkinsfile")

    def test_braces_balanced(self):
        self.assertEqual(self.text.count("{"), self.text.count("}"))
        self.assertEqual(self.text.count("("), self.text.count(")"))

    def test_stages_in_order(self):
        self.assertEqual(re.findall(r"stage\('([^']+)'\)", self.text),
                         ["Prepare", "Build", "Lint", "Test", "Package", "Deploy", "Smoke test"])

    def test_deploy_stages_are_conditional(self):
        self.assertEqual(self.text.count("when { expression { return params.DEPLOY } }"), 2)

    def test_app_is_always_stopped(self):
        smoke = self.text.split("stage('Smoke test')")[1]
        self.assertRegex(smoke, r"post\s*\{\s*always\s*\{[\s\S]*run_app\.sh stop")

    def test_reports_and_artifacts_published(self):
        self.assertIn("junit testResults: 'reports/junit.xml'", self.text)
        self.assertIn("archiveArtifacts artifacts: 'dist/*.tar.gz'", self.text)

    def test_every_ci_script_it_calls_exists_and_is_used(self):
        called = set(re.findall(r"ci/([a-z_]+\.sh)", self.text))
        self.assertEqual(called, {"package.sh", "deploy.sh", "run_app.sh", "smoke_test.sh"})
        for name in called:
            self.assertTrue((ROOT / "ci" / name).is_file(), name)

    def test_no_embedded_credentials(self):
        self.assertNotRegex(self.text, r"(?i)(password|token|secret)\s*[:=]\s*['\"]\w+")


class AppSourceTests(unittest.TestCase):
    """Stand-in for flake8 (not installed): syntax, line length, whitespace."""

    def python_files(self):
        return [p for p in (ROOT / "app").glob("*.py")] + [ROOT / "test_pipeline.py"]

    def test_parse_and_style(self):
        for path in self.python_files():
            text = path.read_text(encoding="utf-8")
            ast.parse(text, filename=str(path))
            for n, line in enumerate(text.splitlines(), 1):
                self.assertLessEqual(len(line), 100, f"{path.name}:{n} too long")
                self.assertEqual(line, line.rstrip(), f"{path.name}:{n} trailing whitespace")
                self.assertNotIn("\t", line, f"{path.name}:{n} tab")

    def test_requirements_pinned(self):
        for rel in ("app/requirements.txt", "app/requirements-dev.txt"):
            for line in read(rel).splitlines():
                if line.strip() and not line.startswith("-r"):
                    self.assertRegex(line, r"^[A-Za-z0-9_.-]+==\d", f"{rel}: unpinned {line!r}")

    def test_dev_requirements_include_runtime_ones(self):
        self.assertIn("-r requirements.txt", read("app/requirements-dev.txt"))


class SafetyTests(unittest.TestCase):
    def test_compose_requires_password_and_binds_loopback(self):
        text = read("docker-compose.yml")
        self.assertIn("JENKINS_ADMIN_PASSWORD:?", text)
        self.assertIn('"127.0.0.1:${JENKINS_PORT:-8080}:8080"', text)
        self.assertIn("../..:/repo-src:ro", text)

    def test_init_script_fails_closed(self):
        text = read("jenkins/init.groovy.d/01-admin-user.groovy")
        self.assertRegex(text, r"if \(!adminPassword\)[\s\S]*throw")
        self.assertIn("setAllowAnonymousRead(false)", text)

    def test_jenkins_image_has_python_and_wizard_off(self):
        text = read("jenkins/Dockerfile")
        self.assertIn("python3-venv", text)
        self.assertIn("-Djenkins.install.runSetupWizard=false", text)

    def test_plugins_cover_pipeline_git_junit(self):
        entries = [line.strip() for line in read("jenkins/plugins.txt").splitlines()
                   if line.strip() and not line.startswith("#")]
        for needed in ("workflow-aggregator", "git", "junit"):
            self.assertIn(needed, entries)

    def test_nothing_pushes_to_a_remote(self):
        for path in list(ROOT.glob("*.sh")) + list((ROOT / "ci").glob("*.sh")):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("git push", text, path.name)
            self.assertNotIn("remote add", text, path.name)

    def test_env_example_only_placeholder_and_build_output_ignored(self):
        self.assertIn("JENKINS_ADMIN_PASSWORD=change-me", read(".env.example"))
        ignored = read(".gitignore")
        for entry in (".venv/", "dist/", "reports/"):
            self.assertIn(entry, ignored)


if __name__ == "__main__":
    unittest.main()
