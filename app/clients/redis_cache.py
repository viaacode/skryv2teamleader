#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/clients/redis_cache.py
#

import json
import redis


class RedisCache:
    def __init__(self) -> str:
        self.redis_cache = None

    def create_connection(self, redis_url):
        self.redis_cache = redis.Redis.from_url(redis_url)

    # async def _get(self, key) -> str:
    #     return await self.redis_cache.get(key)

    def get(self, key):
        return self.redis_cache.get(key)

    def set(self, key, value):
        self.redis_cache.set(key, value)

    def delete(self, key):
        self.redis_cache.delete(key)

    def close(self):
        self.redis_cache.close()

    def save(self, key, dictvalue):
        self.set(key, json.dumps(dictvalue))

    def load(self, key):
        return json.loads(self.get(key))


redis_cache = RedisCache()
