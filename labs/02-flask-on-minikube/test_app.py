import unittest

from app import app


class AppTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_returns_greeting(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Hello from Flask", resp.data)

    def test_healthz(self):
        resp = self.client.get("/healthz")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), {"status": "ok"})

    def test_whoami_has_pod_name(self):
        resp = self.client.get("/whoami")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get_json()["pod"])


if __name__ == "__main__":
    unittest.main()
