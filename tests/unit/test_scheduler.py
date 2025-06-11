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
from app.clients.skryv_client import SkryvClient
from app.clients.common_clients import CommonClients
from app.models.process_body import ProcessBody
from app.models.milestone_body import MilestoneBody
from app.models.document_body import DocumentBody

from mock_teamleader_client import MockTlClient
from mock_ldap_client import MockLdapClient
from mock_redis_cache import MockRedisCache

from testing_config import tst_app_config


class TestScheduler:
    @pytest.mark.asyncio
    async def test_invalid_webhook(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)
        res = await ws.execute_webhook('something_bad', 'some_id')
        assert res is None

    @pytest.mark.asyncio
    async def test_scheduling(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)
        assert ws.webhook_queue.empty()

        doc = open("tests/fixtures/document/updated_addendums.json", "r")
        test_doc = DocumentBody.parse_raw(doc.read())
        doc.close()

        ws.schedule('document_event', test_doc)
        assert not ws.webhook_queue.empty()

        await ws.webhook_processing()
        assert ws.webhook_queue.empty()
