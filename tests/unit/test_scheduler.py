#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   tests/unit/test_scheduler.py
#

import pytest
import uuid

from app.comm.webhook_scheduler import WebhookScheduler
from app.clients.slack_client import SlackClient
from app.clients.common_clients import CommonClients
from app.models.process_body import ProcessBody
from app.models.milestone_body import MilestoneBody
from app.models.document_body import DocumentBody

from mock_teamleader_client import MockTlClient
from mock_ldap_client import MockLdapClient
from mock_slack_wrapper import MockSlackWrapper
from mock_redis_cache import MockRedisCache

from testing_config import tst_app_config


class TestScheduler:
    @pytest.fixture
    def mock_clients(self):
        slack_client = SlackClient(tst_app_config())
        slack_client.slack_wrapper = MockSlackWrapper()

        return CommonClients(
            MockTlClient(),
            MockLdapClient(),
            slack_client,
            MockRedisCache()
        )

    @pytest.mark.asyncio
    async def test_invalid_webhook(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)
        res = await ws.execute_webhook('something_bad', 'some_id')
        assert res is None

    def test_scheduling(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)
        assert ws.webhook_queue.empty()

        ws.schedule('document_event', 'some_data')
        assert not ws.webhook_queue.empty()
