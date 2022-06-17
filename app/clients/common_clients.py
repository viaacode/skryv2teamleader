#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/clients/common_clients.py
#
#   CommonClients shared by services and because of injection
#   it becomes easier to mock these in our unit tests
#

from app.clients.teamleader_client import TeamleaderClient
from app.clients.ldap_client import LdapClient
from app.clients.slack_client import SlackClient
from app.clients.skryv_client import SkryvClient
from app.clients.redis_cache import RedisCache
from dataclasses import dataclass


@dataclass
class CommonClients:
    teamleader: TeamleaderClient
    ldap: LdapClient
    slack: SlackClient
    skryv: SkryvClient
    redis: RedisCache


def construct_clients(app_cfg, redis_cache: RedisCache = None):
    return CommonClients(
        TeamleaderClient(app_cfg, redis_cache),
        LdapClient(app_cfg),
        SlackClient(app_cfg),
        SkryvClient(app_cfg),
        redis_cache
    )
