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
from app.clients.org_id_generator import OrgIdGenerator
from app.clients.slack_client import SlackClient
from app.clients.redis_cache import RedisCache
from dataclasses import dataclass, field


# TODO: bring ldap back here as we need to make a call in order
# to map or-id into a company uuid!


@dataclass
class CommonClients:
    teamleader: TeamleaderClient
    slack: SlackClient
    org_ids: OrgIdGenerator = field(default=None)


def construct_clients(app_cfg, redis_cache: RedisCache = None):
    return CommonClients(
        TeamleaderClient(app_cfg, redis_cache),
        SlackClient(app_cfg),
        OrgIdGenerator(app_cfg)
    )
