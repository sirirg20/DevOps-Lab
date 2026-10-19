"""Where the cart lives. In memory for local runs, in Redis when running on the cluster.

A cart kept in each replica's own memory shows a different cart depending on
which replica answers. Sharing it through Redis makes every replica agree.
"""


class MemoryStore:
    def __init__(self):
        self._items = []

    def items(self):
        return list(self._items)

    def add(self, item):
        self._items.append(item)

    def clear(self):
        self._items.clear()

    def ping(self):
        return True


class RedisStore:
    """Cart stored as a Redis list. `client` is a redis.Redis (or a compatible fake)."""

    def __init__(self, client, key="cart"):
        self.client = client
        self.key = key

    def items(self):
        return [i.decode() if isinstance(i, bytes) else i
                for i in self.client.lrange(self.key, 0, -1)]

    def add(self, item):
        self.client.rpush(self.key, item)

    def clear(self):
        self.client.delete(self.key)

    def ping(self):
        try:
            return bool(self.client.ping())
        except Exception:
            return False


def build_store(env):
    """Pick the store from environment variables (REDIS_HOST, REDIS_PORT)."""
    host = env.get("REDIS_HOST")
    if not host:
        return MemoryStore()
    import redis  # imported here so local runs and tests do not need the package

    client = redis.Redis(host=host, port=int(env.get("REDIS_PORT", "6379")),
                         socket_timeout=2, socket_connect_timeout=2, decode_responses=True)
    return RedisStore(client)
