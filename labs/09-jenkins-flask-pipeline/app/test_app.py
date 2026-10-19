import tempfile
import unittest
from pathlib import Path
from unittest import mock

import app as app_module


class AppTests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.create_app().test_client()

    def test_index(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data.decode(), "Hello from the Flask pipeline!\n")

    def test_health(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), {"status": "ok"})

    def test_version_defaults_to_dev_without_version_file(self):
        with mock.patch.object(app_module, "VERSION_FILE", Path("/nonexistent/VERSION")):
            self.assertEqual(self.client.get("/version").get_json(), {"version": "dev"})

    def test_version_reads_version_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            version_file = Path(tmp) / "VERSION"
            version_file.write_text("42\n", encoding="utf-8")
            with mock.patch.object(app_module, "VERSION_FILE", version_file):
                self.assertEqual(self.client.get("/version").get_json(), {"version": "42"})

    def test_unknown_route_is_404(self):
        self.assertEqual(self.client.get("/nope").status_code, 404)


if __name__ == "__main__":
    unittest.main()
