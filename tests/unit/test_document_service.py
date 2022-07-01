#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   tests/unit/test_document_service.py
#

import pytest
import uuid
import requests_mock
import json

from app.comm.webhook_scheduler import WebhookScheduler
from app.clients.teamleader_client import TeamleaderClient
from app.clients.slack_client import SlackClient
from app.clients.skryv_client import SkryvClient
from app.clients.common_clients import CommonClients
from app.models.document_body import DocumentBody
from app.services.document_service import DocumentService

from mock_teamleader_client import MockTlClient
from mock_ldap_client import MockLdapClient
from mock_slack_wrapper import MockSlackWrapper
from mock_redis_cache import MockRedisCache

from testing_config import tst_app_config


class TestDocumentService:
    @pytest.fixture
    def mock_clients(self):
        slack_client = SlackClient(tst_app_config())
        slack_client.slack_wrapper = MockSlackWrapper()

        return CommonClients(
            MockTlClient(),
            MockLdapClient(),
            slack_client,
            SkryvClient(tst_app_config()),
            MockRedisCache()
        )

    @pytest.fixture
    def mock_client_requests(self):
        slack_client = SlackClient(tst_app_config())
        slack_client.slack_wrapper = MockSlackWrapper()

        tlc = TeamleaderClient(
            tst_app_config(),
            MockRedisCache()
        )
        # switch off rate limiting for fast tests
        tlc.RATE_LIMIT = 0.0

        return CommonClients(
            tlc,
            MockLdapClient(),
            slack_client,
            SkryvClient(tst_app_config()),
            MockRedisCache()
        )

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

        doc = open("tests/fixtures/document/updated_example.json", "r")
        test_doc = DocumentBody.parse_raw(doc.read())
        doc.close()
        test_doc.dossier.externalId = None
        res = await ws.execute_webhook('document_event', test_doc)
        assert res == 'document event is handled'

    def test_document_service_with_unauthorized_teamleader_api(self, mock_client_requests, requests_mock):
        API_URL = 'https://api.teamleader.eu'

        requests_mock.get(
            f'{API_URL}/customFieldDefinitions.list',
            json={'data': []},
            status_code=401
        )

        requests_mock.post(
            'https://app.teamleader.eu/oauth2/access_token',
            json={},
            status_code=401
        )

        doc = open("tests/fixtures/document/update_contacts_itv.json", "r")
        test_doc = DocumentBody.parse_raw(doc.read())
        doc.close()
        ds = DocumentService(mock_client_requests)
        ds.handle_event(test_doc)

        assert '/oauth2/access_token' in requests_mock.last_request.url
