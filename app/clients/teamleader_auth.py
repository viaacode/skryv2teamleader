#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/clients/teamleader_auth.py
#
#   TeamleaderAuth model class to store and load
#   teamleader oauth tokens. right now 2 modes of operation are
#   used if redis_cache is not passed we use a pickle file to store
#   tokens. In qas+production we pass in a RedisCache instance and then
#   we store the tokens in redis using REDIS_URL env var
#

import os
import pickle
from app.clients.redis_cache import RedisCache


class TeamleaderAuth():
    """Acts as a client to query and modify information from and to database"""

    def __init__(self, tl_config: dict, redis_cache: RedisCache = None):
        self.redis = None
        if redis_cache:
            self.token_key = 'teamleader_auth_tokens'
            self.redis = redis_cache
        else:
            self.token_file = tl_config.get('token_file', 'auth_tokens.pkl')

    def save(self, code='', auth_token='', refresh_token=''):
        token_data = {
            'code': code,
            'token': auth_token,
            'refresh_token': refresh_token
        }

        if self.redis:
            print(f"Saving tokens in REDIS key: {self.token_key}")
            self.redis.save(self.token_key, token_data)
        else:
            print(f"Saving tokens in pickle file: {self.token_file}")
            tfile = open(self.token_file, "wb")
            pickle.dump(token_data, tfile)
            tfile.close()

    def read(self):
        if self.redis:
            token_data = self.redis.load(self.token_key)
            print(f"Read tokens from REDIS key: {self.token_key}")
        else:
            tfile = open(self.token_file, "rb")
            token_data = pickle.load(tfile)
            tfile.close()
            print(f"Read tokens from pickle file: {self.token_file}")

        return token_data['code'], token_data['token'], token_data['refresh_token']

    def reset(self):
        try:
            if self.redis:
                self.redis.delete(self.token_key)
            else:
                os.remove(self.token_file)
        except FileNotFoundError:
            pass

    def tokens_available(self):
        if self.redis:
            res = self.redis.get(self.token_key)
            return res is not None
        else:
            return os.path.isfile(self.token_file)
