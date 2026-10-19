import socket
import unittest
from unittest import mock

from app import app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_about(self):
        data = self.client.get("/about").get_json()
        self.assertEqual(data["service"], "flask-api")
        self.assertEqual(data["port"], 5001)

    def test_health(self):
        self.assertEqual(self.client.get("/health").get_json(), {"status": "ok"})

    def test_deps_ok_when_reachable(self):
        with mock.patch("app.socket.gethostbyname", return_value="172.18.0.2"), \
             mock.patch("app.socket.create_connection") as conn:
            conn.return_value.__enter__.return_value = object()
            resp = self.client.get("/deps")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get_json()["ok"])

    def test_deps_503_when_name_does_not_resolve(self):
        with mock.patch("app.socket.gethostbyname", side_effect=socket.gaierror("unknown host")):
            resp = self.client.get("/deps")
        self.assertEqual(resp.status_code, 503)
        body = resp.get_json()
        self.assertFalse(body["ok"])
        self.assertFalse(body["dependencies"]["db"]["resolved"])

    def test_deps_503_when_connection_refused(self):
        with mock.patch("app.socket.gethostbyname", return_value="172.18.0.2"), \
             mock.patch("app.socket.create_connection", side_effect=ConnectionRefusedError("refused")):
            resp = self.client.get("/deps")
        self.assertEqual(resp.status_code, 503)
        self.assertTrue(resp.get_json()["dependencies"]["cache"]["resolved"])


if __name__ == "__main__":
    unittest.main()
