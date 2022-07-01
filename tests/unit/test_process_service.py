#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   tests/unit/test_process_service.py
#

import pytest
import uuid
import requests_mock
import json

from app.comm.webhook_scheduler import WebhookScheduler
from app.clients.slack_client import SlackClient
from app.clients.skryv_client import SkryvClient
from app.clients.common_clients import CommonClients
from app.clients.teamleader_client import TeamleaderClient
from app.models.process_body import ProcessBody
from app.models.document_body import DocumentBody
from app.services.document_service import DocumentService
from app.services.process_service import ProcessService

from mock_teamleader_client import MockTlClient
from mock_ldap_client import MockLdapClient, UNKNOWN_OR_ID, UNMAPPED_OR_ID
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

    def teamleader_fixture(self, json_file):
        f = open(f"tests/fixtures/teamleader/{json_file}")
        data = json.loads(f.read())
        f.close()
        return data

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
        assert res == 'process event is handled'

    @pytest.mark.asyncio
    async def test_process_ended_empty_addendums(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        doc = open("tests/fixtures/document/updated_addendums.json", "r")
        test_doc = DocumentBody.parse_raw(doc.read())
        doc.close()
        test_doc.document.document.value['te_ondertekenen_documenten'] = []
        res = await ws.execute_webhook('document_event', test_doc)
        assert res == 'document event is handled'

        proc = open("tests/fixtures/process/process_ended.json", "r")
        test_process = ProcessBody.parse_raw(proc.read())
        proc.close()
        res = await ws.execute_webhook('process_event', test_process)
        assert res == 'process event is handled'

    @pytest.mark.asyncio
    async def test_process_missing_document(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        proc = open("tests/fixtures/process/process_ended.json", "r")
        test_process = ProcessBody.parse_raw(proc.read())
        proc.close()
        res = await ws.execute_webhook('process_event', test_process)
        assert res == 'process event is handled'

    @pytest.mark.asyncio
    async def test_process_ended_unknown_org(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        doc = open("tests/fixtures/document/updated_addendums.json", "r")
        test_doc = DocumentBody.parse_raw(doc.read())
        doc.close()
        test_doc.dossier.externalId = UNKNOWN_OR_ID
        res = await ws.execute_webhook('document_event', test_doc)
        assert res == 'document event is handled'

        proc = open("tests/fixtures/process/process_ended.json", "r")
        test_process = ProcessBody.parse_raw(proc.read())
        proc.close()
        test_process.dossier.externalId = UNKNOWN_OR_ID
        res = await ws.execute_webhook('process_event', test_process)
        assert res == 'process event is handled'

    @pytest.mark.asyncio
    async def test_process_unknown_action(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        proc = open("tests/fixtures/process/process_ended.json", "r")
        test_process = ProcessBody.parse_raw(proc.read())
        test_process.action = "something else"
        proc.close()
        res = await ws.execute_webhook('process_event', test_process)
        assert res == 'process event is handled'

    def test_process_call_company_not_found(self, mock_client_requests, requests_mock):
        API_URL = 'https://api.teamleader.eu'

        # send a document event, so mocked redis stores it for
        # actual milestone call
        requests_mock.get(
            f'{API_URL}/customFieldDefinitions.list',
            json={'data': self.teamleader_fixture('custom_fields.json')}
        )

        doc = open("tests/fixtures/document/update_contacts_itv.json", "r")
        test_doc = DocumentBody.parse_raw(doc.read())
        doc.close()
        ds = DocumentService(mock_client_requests)

        # remove some values to trigger edge case handling
        test_doc.document.document.value.pop('adres_en_contactgegevens')
        test_doc.document.document.value.pop('bedrijfsvorm')

        ds.handle_event(test_doc)

        company_id = '1b2ab41a-7f59-103b-8cd4-1fcdd5140767'
        test_company = self.teamleader_fixture('test_company.json')
        # remove some keys so that we trigger edge cases
        test_company.pop('addresses')
        test_company.pop('emails')
        test_company.pop('telephones')

        # simulate company not found in teamleader
        requests_mock.get(
            f'{API_URL}/companies.info?id={company_id}',
            json={'data': None},
            status_code=404
        )

        proc = open("tests/fixtures/process/process_ended.json", "r")
        test_process = ProcessBody.parse_raw(proc.read())
        proc.close()

        ps = ProcessService(mock_client_requests)
        ps.handle_event(test_process)

        assert 'companies.update' not in requests_mock.last_request.url

    def test_process_call_update_failed(self, mock_client_requests, requests_mock):
        API_URL = 'https://api.teamleader.eu'

        # send a document event, so mocked redis stores it for
        # actual milestone call
        requests_mock.get(
            f'{API_URL}/customFieldDefinitions.list',
            json={'data': self.teamleader_fixture('custom_fields.json')}
        )

        doc = open("tests/fixtures/document/update_contacts_itv.json", "r")
        test_doc = DocumentBody.parse_raw(doc.read())
        doc.close()
        ds = DocumentService(mock_client_requests)

        # remove some values to trigger edge case handling
        test_doc.document.document.value.pop('adres_en_contactgegevens')
        test_doc.document.document.value.pop('bedrijfsvorm')

        ds.handle_event(test_doc)

        company_id = '1b2ab41a-7f59-103b-8cd4-1fcdd5140767'
        test_company = self.teamleader_fixture('test_company.json')
        # remove some keys so that we trigger edge cases
        test_company.pop('addresses')
        test_company.pop('emails')
        test_company.pop('telephones')
        requests_mock.get(
            f'{API_URL}/companies.info?id={company_id}',
            json={'data': test_company}
        )

        # make update fail with errorcode 400
        requests_mock.post(
            f'{API_URL}/companies.update',
            [
                {'json': {'data': 'some failure in saving'}, 'status_code': 400},
            ]
        )

        proc = open("tests/fixtures/process/process_ended.json", "r")
        test_process = ProcessBody.parse_raw(proc.read())
        proc.close()

        ps = ProcessService(mock_client_requests)
        ps.handle_event(test_process)

        assert 'companies.update' in requests_mock.last_request.url
