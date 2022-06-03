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

from testing_config import tst_app_config


class TestScheduler:
    @pytest.fixture
    def mock_clients(self):
        slack_client = SlackClient(tst_app_config())
        slack_client.slack_wrapper = MockSlackWrapper()

        return CommonClients(
            MockTlClient(),
            MockLdapClient(),
            slack_client
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
    async def test_milestone_akkoord(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        ms = open("tests/fixtures/milestone/milestone_akkoord.json", "r")
        test_milestone = MilestoneBody.parse_raw(ms.read())
        ms.close()
        res = await ws.execute_webhook('milestone_event', test_milestone)
        assert res == 'milestone event is handled'

    @pytest.mark.asyncio
    async def test_milestone_akkoord_missing_external_id(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        ms = open("tests/fixtures/milestone/milestone_akkoord.json", "r")
        test_milestone = MilestoneBody.parse_raw(ms.read())
        test_milestone.dossier.externalId = None
        ms.close()
        res = await ws.execute_webhook('milestone_event', test_milestone)
        assert res == 'milestone event is handled'

    @pytest.mark.asyncio
    async def test_milestone_briefing(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        ms = open("tests/fixtures/milestone/milestone_akkoord.json", "r")
        test_milestone = MilestoneBody.parse_raw(ms.read())
        test_milestone.dossier.dossierDefinition = uuid.UUID(
            'ffb5c880-8301-4d15-bbe9-edaa6d59c4f6'
        )
        ms.close()
        res = await ws.execute_webhook('milestone_event', test_milestone)
        assert res == 'milestone event is handled'

    @pytest.mark.asyncio
    async def test_document_update(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        doc = open("tests/fixtures/document/updated_example.json", "r")
        test_doc = DocumentBody.parse_raw(doc.read())
        doc.close()
        res = await ws.execute_webhook('document_event', test_doc)
        assert res == 'document event is handled'

    @pytest.mark.asyncio
    async def test_document_update_addendum(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        doc = open("tests/fixtures/document/updated_addendums.json", "r")
        test_doc = DocumentBody.parse_raw(doc.read())
        doc.close()
        res = await ws.execute_webhook('document_event', test_doc)
        assert res == 'document event is handled'

    @pytest.mark.asyncio
    async def test_document_briefing(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        doc = open("tests/fixtures/document/updated_addendums.json", "r")
        test_doc = DocumentBody.parse_raw(doc.read())
        test_doc.dossier.dossierDefinition = uuid.UUID(
            'ffb5c880-8301-4d15-bbe9-edaa6d59c4f6'
        )
        doc.close()
        res = await ws.execute_webhook('document_event', test_doc)
        assert res == 'document event is handled'

    @pytest.mark.asyncio
    async def test_create_document_with_valid_or_id(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        doc = open("tests/fixtures/document/updated_addendums.json", "r")
        test_doc = DocumentBody.parse_raw(doc.read())
        test_doc.action = 'created'
        doc.close()
        res = await ws.execute_webhook('document_event', test_doc)
        assert res == 'document event is handled'

    @pytest.mark.asyncio
    async def test_document_create_without_or_id(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        doc = open("tests/fixtures/document/created_example.json", "r")
        test_doc = DocumentBody.parse_raw(doc.read())
        doc.close()
        res = await ws.execute_webhook('document_event', test_doc)
        assert res == 'document event is handled'

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
