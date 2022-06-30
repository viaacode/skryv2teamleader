#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   tests/unit/test_redis_cache.py
#

import pytest
import uuid
import requests_mock

from app.clients.redis_cache import RedisCache
from testing_config import tst_app_config


class MockedRedis:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = value

    def expire(self, key, seconds):
        print("expiring in seconds=", seconds)
        self.data[key] = None  # expire immediately

    def delete(self, key):
        self.data[key] = None

    def close(self):
        self.data = {}


class TestRedisCache:
    @pytest.fixture
    def redmock(self):
        rc = RedisCache()
        rc.create_connection('redis://mocked')
        rc.redis_cache = MockedRedis()
        return rc

    def test_get_call(self, redmock):
        res = redmock.get('some_key')
        assert res is None

    def test_set_call(self, redmock):
        redmock.set('some_key', 'some_value')
        res = redmock.get('some_key')
        assert res is 'some_value'

    def test_auto_expire(self, redmock):
        redmock.set('some_key', 'some_value')
        redmock.auto_expire('some_key')
        res = redmock.get('some_key')
        assert res is None

    def test_delete(self, redmock):
        redmock.set('some_key', 'some_value')
        redmock.delete('some_key')
        res = redmock.get('some_key')
        assert res is None

    def test_close(self, redmock):
        redmock.set('some_key', 'some_value')
        redmock.close()
        res = redmock.get('some_key')
        assert res is None
