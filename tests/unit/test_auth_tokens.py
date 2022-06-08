#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   tests/unit/test_auth_tokens.py
#

from app.clients.teamleader_auth import TeamleaderAuth
from mock_redis_cache import MockRedisCache

class TestTeamleaderAuth:
    def test_token_saving(self):
        ta = TeamleaderAuth({'token_file': 'test_tokens.pkl'}, MockRedisCache())
        ta.reset()
        assert ta.tokens_available() is False

        ta.save('somecode', 'some_auth', 'some_refresh')
        assert ta.tokens_available()
        assert ta.read() == ('somecode', 'some_auth', 'some_refresh')

        ta.reset()
        assert ta.tokens_available() is False
