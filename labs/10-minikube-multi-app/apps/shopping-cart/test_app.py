import unittest

from app import create_app
from cart_store import MemoryStore


class BrokenStore(MemoryStore):
    def ping(self):
        return False


class CartTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app(MemoryStore()).test_client()

    def test_cart_starts_empty(self):
        self.assertEqual(self.client.get("/cart").get_json(), {"items": [], "count": 0})

    def test_post_adds_item_and_returns_201(self):
        resp = self.client.post("/cart", json={"item": "Laptop"})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.get_json(), {"added": "Laptop", "count": 1})
        self.assertEqual(self.client.get("/cart").get_json()["items"], ["Laptop"])

    def test_item_is_trimmed(self):
        self.client.post("/cart", json={"item": "  Pen  "})
        self.assertEqual(self.client.get("/cart").get_json()["items"], ["Pen"])

    def test_invalid_bodies_are_rejected(self):
        for body in ({}, {"item": ""}, {"item": "   "}, {"item": 5}, {"other": "x"}):
            self.assertEqual(self.client.post("/cart", json=body).status_code, 400, body)
        self.assertEqual(self.client.post("/cart", data="not json").status_code, 400)
        self.assertEqual(self.client.post("/cart", json=["Laptop"]).status_code, 400)

    def test_overlong_item_rejected(self):
        self.assertEqual(self.client.post("/cart", json={"item": "x" * 101}).status_code, 400)

    def test_delete_clears_cart(self):
        self.client.post("/cart", json={"item": "Pen"})
        self.assertEqual(self.client.delete("/cart").status_code, 204)
        self.assertEqual(self.client.get("/cart").get_json()["count"], 0)

    def test_health_ok_and_livez(self):
        self.assertEqual(self.client.get("/health").status_code, 200)
        self.assertEqual(self.client.get("/livez").status_code, 200)

    def test_not_ready_when_store_down_but_still_alive(self):
        client = create_app(BrokenStore()).test_client()
        self.assertEqual(client.get("/health").status_code, 503)
        self.assertEqual(client.get("/livez").status_code, 200)

    def test_pod_header(self):
        self.assertTrue(self.client.get("/cart").headers["X-Served-By"])


if __name__ == "__main__":
    unittest.main()
