from app.clients.redis_cache import RedisCache
# import json


class MockRedisCache(RedisCache):
    def __init__(self) -> str:
        self.redis_cache = {}

    def create_connection(self, redis_url):
        print(
            f"mocked redis cache, using in memory cache instead of {redis_url}")

    def get(self, key):
        return self.redis_cache.get(key)

    def set(self, key, value):
        self.redis_cache[key] = value

    def delete(self, key):
        if self.redis_cache.get(key):
            self.redis_cache.pop(key)

    def close(self):
        print("mocked redis cache closing")
        # self.redis_cache = {}

    # the save_document and other methods remain unchanged/reused from the actual redis cache
    # we only needed to override the above methods to make a 'fakeredis'
