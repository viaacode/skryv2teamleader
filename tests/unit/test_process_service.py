#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   tests/unit/test_process_service.py
#

import pytest
import uuid

from app.comm.webhook_scheduler import WebhookScheduler
from app.clients.slack_client import SlackClient
from app.clients.common_clients import CommonClients
from app.models.process_body import ProcessBody
from app.models.document_body import DocumentBody

from mock_teamleader_client import MockTlClient
from mock_ldap_client import MockLdapClient
from mock_slack_wrapper import MockSlackWrapper
from mock_redis_cache import MockRedisCache

from testing_config import tst_app_config


class TestProcessService:
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
    async def test_process_created_event(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        proc = open("tests/fixtures/process/process_created.json", "r")
        test_process = ProcessBody.parse_raw(proc.read())
        proc.close()
        res = await ws.execute_webhook('process_event', test_process)
        assert res == 'process event is handled'

    @pytest.mark.asyncio
    async def test_process_created_briefing(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        proc = open("tests/fixtures/process/process_created.json", "r")
        test_process = ProcessBody.parse_raw(proc.read())
        test_process.dossier.dossierDefinition = uuid.UUID(
            'ffb5c880-8301-4d15-bbe9-edaa6d59c4f6'
        )
        proc.close()
        res = await ws.execute_webhook('process_event', test_process)
        assert res == 'process event is handled'

    @pytest.mark.asyncio
    async def test_process_created_without_external_id(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        proc = open("tests/fixtures/process/process_created.json", "r")
        test_process = ProcessBody.parse_raw(proc.read())
        test_process.dossier.externalId = None
        proc.close()
        res = await ws.execute_webhook('process_event', test_process)
        assert res == 'process event is handled'

    @pytest.mark.asyncio
    async def test_process_ended(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        doc = open("tests/fixtures/document/updated_addendums.json", "r")
        test_doc = DocumentBody.parse_raw(doc.read())
        doc.close()
        res = await ws.execute_webhook('document_event', test_doc)
        assert res == 'document event is handled'

        proc = open("tests/fixtures/process/process_ended.json", "r")
        test_process = ProcessBody.parse_raw(proc.read())
        proc.close()
        res = await ws.execute_webhook('process_event', test_process)
        # TODO check that updated_addendums document is properly found here!
        assert res == 'process event is handled'
