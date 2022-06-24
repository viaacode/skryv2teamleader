#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/clients/teamleader_auth.py
#
#   TeamleaderAuth model class to store and load
#   teamleader oauth tokens.
#

import os
from app.clients.redis_cache import RedisCache
from viaa.configuration import ConfigParser
from viaa.observability import logging

config = ConfigParser()
logger = logging.get_logger(__name__, config=config)


class TeamleaderAuth():
    """Acts as a client to query and modify information from and to database"""

    def __init__(self, tl_config: dict, redis_cache: RedisCache = None):
        self.token_key = 'skryv_tl_auth_tokens'
        self.redis = redis_cache

    def save(self, code='', auth_token='', refresh_token=''):
        token_data = {
            'code': code,
            'token': auth_token,
            'refresh_token': refresh_token
        }

        logger.info(f"Saving tokens in REDIS key: {self.token_key}")
        self.redis.save(self.token_key, token_data)

    def read(self):
        token_data = self.redis.load(self.token_key)
        logger.info(f"Read tokens from REDIS key: {self.token_key}")
        return token_data['code'], token_data['token'], token_data['refresh_token']

    def reset(self):
        if self.redis:
            self.redis.delete(self.token_key)

    def tokens_available(self):
        if not self.redis:
            return False

        res = self.redis.get(self.token_key)
        return res is not None
