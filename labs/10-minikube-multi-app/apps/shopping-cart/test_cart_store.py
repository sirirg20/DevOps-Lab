"""Tests for cart_store (standard library only, no Flask or Redis needed)."""
import unittest

from cart_store import MemoryStore, RedisStore, build_store


class FakeRedis:
    """Just enough of redis.Redis for RedisStore; can return bytes like the real client."""

    def __init__(self, as_bytes=False, healthy=True):
        self.data = {}
        self.as_bytes = as_bytes
        self.healthy = healthy

    def rpush(self, key, value):
        self.data.setdefault(key, []).append(value)

    def lrange(self, key, start, end):
        values = self.data.get(key, [])
        return [v.encode() if self.as_bytes else v for v in values]

    def delete(self, key):
        self.data.pop(key, None)

    def ping(self):
        if not self.healthy:
            raise ConnectionError("down")
        return True


class StoreContract:
    """Behaviour every store must have."""

    def make(self):
        raise NotImplementedError

    def test_starts_empty(self):
        self.assertEqual(self.make().items(), [])

    def test_add_keeps_order(self):
        store = self.make()
        for item in ("a", "b", "c"):
            store.add(item)
        self.assertEqual(store.items(), ["a", "b", "c"])

    def test_clear(self):
        store = self.make()
        store.add("x")
        store.clear()
        self.assertEqual(store.items(), [])

    def test_ping(self):
        self.assertTrue(self.make().ping())


class MemoryStoreTests(StoreContract, unittest.TestCase):
    def make(self):
        return MemoryStore()

    def test_items_returns_a_copy(self):
        store = MemoryStore()
        store.add("x")
        store.items().append("y")
        self.assertEqual(store.items(), ["x"])


class RedisStoreTests(StoreContract, unittest.TestCase):
    def make(self):
        return RedisStore(FakeRedis())

    def test_decodes_bytes(self):
        store = RedisStore(FakeRedis(as_bytes=True))
        store.add("pen")
        self.assertEqual(store.items(), ["pen"])

    def test_two_replicas_sharing_one_redis_see_the_same_cart(self):
        shared = FakeRedis()
        replica_a, replica_b = RedisStore(shared), RedisStore(shared)
        replica_a.add("book")
        self.assertEqual(replica_b.items(), ["book"])

    def test_two_memory_replicas_disagree(self):
        """The problem the Redis store exists to solve."""
        replica_a, replica_b = MemoryStore(), MemoryStore()
        replica_a.add("book")
        self.assertNotEqual(replica_a.items(), replica_b.items())

    def test_ping_false_when_redis_down(self):
        self.assertFalse(RedisStore(FakeRedis(healthy=False)).ping())


class BuildStoreTests(unittest.TestCase):
    def test_memory_without_redis_host(self):
        self.assertIsInstance(build_store({}), MemoryStore)


if __name__ == "__main__":
    unittest.main()
