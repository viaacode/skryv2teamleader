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

    def auto_expire(self, key):
        # auto expire stale documents after a few minutes
        # because document webhook is called right before
        # milestone and process end. this should be fine
        expiry_minutes = 5
        self.redis_cache.expire(key, 60*expiry_minutes)

    def delete(self, key):
        self.redis_cache.delete(key)

    def close(self):
        self.redis_cache.close()

    def save(self, key, dictvalue):
        self.set(key, json.dumps(dictvalue))

    def save_document(self, document):
        # we need to be able to lookup using dossier id
        key = 'dossier_{}'.format(document.dossier.id)
        self.set(key, json.dumps(document.json()))
        self.auto_expire(key)

    def load_document(self, dossier_id):
        # use a dossier id, to get last saved document
        key = 'dossier_{}'.format(dossier_id)
        dossier_data = self.get(key)
        if dossier_data:
            return json.loads(dossier_data)

    def load(self, key):
        return json.loads(self.get(key))


redis_cache = RedisCache()
