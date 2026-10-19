import unittest

from app import PRODUCTS, create_app


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_products_lists_three_items(self):
        resp = self.client.get("/products")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), PRODUCTS)
        self.assertEqual(len(PRODUCTS), 3)

    def test_every_product_has_expected_fields(self):
        for product in PRODUCTS:
            self.assertEqual(set(product), {"id", "name", "price"})

    def test_pod_header_present(self):
        self.assertTrue(self.client.get("/products").headers["X-Served-By"])

    def test_health(self):
        self.assertEqual(self.client.get("/health").get_json(), {"status": "ok"})

    def test_post_not_allowed(self):
        self.assertEqual(self.client.post("/products").status_code, 405)


if __name__ == "__main__":
    unittest.main()
