import re
import socket
import unittest
from unittest import mock

from app import app

ITEMS = ["Smartphone", "Shoes", "Headphones", "Laptop"]


class FlashSaleTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_homepage_fields(self):
        data = self.client.get("/").get_json()
        self.assertEqual(set(data), {"message", "pod", "ts"})
        self.assertEqual(data["message"], "Welcome to Big Sale!")
        self.assertEqual(data["pod"], socket.gethostname())
        self.assertIsInstance(data["ts"], float)

    def test_buy_uses_given_user(self):
        data = self.client.get("/buy?user=123").get_json()
        self.assertEqual(set(data), {"status", "item", "user", "served_by_pod", "time"})
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["user"], "123")
        self.assertIn(data["item"], ITEMS)

    def test_buy_generates_default_user(self):
        data = self.client.get("/buy").get_json()
        self.assertRegex(data["user"], r"^user\d+$")
        self.assertTrue(1 <= int(data["user"][4:]) <= 1000)

    def test_buy_reports_pod_and_time(self):
        with mock.patch("app.socket.gethostname", return_value="flashsale-rs-abcde"):
            data = self.client.get("/buy").get_json()
        self.assertEqual(data["served_by_pod"], "flashsale-rs-abcde")
        self.assertRegex(data["time"], r"^\d{2}:\d{2}:\d{2}$")

    def test_health(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(),
                         {"status": "healthy", "pod": socket.gethostname()})


if __name__ == "__main__":
    unittest.main()
