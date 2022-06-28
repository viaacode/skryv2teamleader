#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   tests/unit/test_milestone_service.py
#

import pytest
import uuid
import requests_mock
import json

from app.comm.webhook_scheduler import WebhookScheduler
from app.clients.slack_client import SlackClient
from app.clients.skryv_client import SkryvClient
from app.clients.teamleader_client import TeamleaderClient
from app.clients.common_clients import CommonClients
from app.models.milestone_body import MilestoneBody
from app.models.document_body import DocumentBody

from mock_teamleader_client import MockTlClient
from mock_ldap_client import MockLdapClient
from mock_slack_wrapper import MockSlackWrapper
from mock_redis_cache import MockRedisCache

from testing_config import tst_app_config


class TestMilestoneService:
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

        return CommonClients(
            TeamleaderClient(
                tst_app_config(),
                MockRedisCache()
            ),
            MockLdapClient(),
            slack_client,
            SkryvClient(tst_app_config()),
            MockRedisCache()
        )

    @pytest.mark.asyncio
    async def test_milestone_akkoord(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        ms = open("tests/fixtures/milestone/milestone_opstart.json", "r")
        test_milestone = MilestoneBody.parse_raw(ms.read())
        ms.close()
        res = await ws.execute_webhook('milestone_event', test_milestone)
        assert res == 'milestone event is handled'

    @pytest.mark.asyncio
    async def test_milestone_geen_opstart(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        ms = open("tests/fixtures/milestone/milestone_geen_opstart.json", "r")
        test_milestone = MilestoneBody.parse_raw(ms.read())
        ms.close()
        res = await ws.execute_webhook('milestone_event', test_milestone)
        assert res == 'milestone event is handled'

    @pytest.mark.asyncio
    async def test_milestone_later(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        ms = open("tests/fixtures/milestone/milestone_later.json", "r")
        test_milestone = MilestoneBody.parse_raw(ms.read())
        ms.close()
        res = await ws.execute_webhook('milestone_event', test_milestone)
        assert res == 'milestone event is handled'

        # check intentieverklaring  is pending status
        tlc = mock_clients.teamleader
        assert tlc.method_called('update_company')

        updated_company = tlc.last_method_called()['update_company']
        assert 'pending' in str(updated_company['custom_fields'])
        assert 'ingevuld' not in str(updated_company['custom_fields'])

    @pytest.mark.asyncio
    async def test_milestone_geen_interesse(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        ms = open("tests/fixtures/milestone/milestone_geen_interesse.json", "r")
        test_milestone = MilestoneBody.parse_raw(ms.read())
        ms.close()
        res = await ws.execute_webhook('milestone_event', test_milestone)
        assert res == 'milestone event is handled'

        # check intentieverklaring  is pending status
        tlc = mock_clients.teamleader
        assert tlc.method_called('update_company')

        updated_company = tlc.last_method_called()['update_company']
        assert 'ingevuld' in str(updated_company['custom_fields'])
        assert 'pending' not in str(updated_company['custom_fields'])

    @pytest.mark.asyncio
    async def test_milestone_interesse(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        ms = open("tests/fixtures/milestone/milestone_interesse.json", "r")
        test_milestone = MilestoneBody.parse_raw(ms.read())
        ms.close()
        res = await ws.execute_webhook('milestone_event', test_milestone)
        assert res == 'milestone event is handled'

        tlc = mock_clients.teamleader
        assert tlc.method_called('update_company')

        # check intentieverklaring  is pending status
        updated_company = tlc.last_method_called()['update_company']
        assert 'pending' in str(updated_company['custom_fields'])
        assert 'ingevuld' not in str(updated_company['custom_fields'])

    @pytest.mark.asyncio
    async def test_milestone_swo(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        ms = open("tests/fixtures/milestone/milestone_swo_akkoord.json", "r")
        test_milestone = MilestoneBody.parse_raw(ms.read())
        ms.close()
        res = await ws.execute_webhook('milestone_event', test_milestone)
        assert res == 'milestone event is handled'

    @pytest.mark.asyncio
    async def test_milestone_missing_external_id(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        ms = open("tests/fixtures/milestone/milestone_opstart.json", "r")
        test_milestone = MilestoneBody.parse_raw(ms.read())
        test_milestone.dossier.externalId = None
        ms.close()
        res = await ws.execute_webhook('milestone_event', test_milestone)
        assert res == 'milestone event is handled'

    @pytest.mark.asyncio
    async def test_milestone_briefing(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        ms = open("tests/fixtures/milestone/milestone_opstart.json", "r")
        test_milestone = MilestoneBody.parse_raw(ms.read())
        test_milestone.dossier.dossierDefinition = uuid.UUID(
            'ffb5c880-8301-4d15-bbe9-edaa6d59c4f6'
        )
        ms.close()
        res = await ws.execute_webhook('milestone_event', test_milestone)
        assert res == 'milestone event is handled'

    @pytest.mark.asyncio
    async def test_milestone_some_contacts_sync(self, mock_clients):

        ws = WebhookScheduler()
        ws.start(mock_clients)

        # send a document event, so mocked redis stores it for
        # actual milestone call
        doc = open("tests/fixtures/document/updated_example.json", "r")
        test_doc = DocumentBody.parse_raw(doc.read())
        doc.close()
        res = await ws.execute_webhook('document_event', test_doc)
        assert res == 'document event is handled'

        ms = open("tests/fixtures/milestone/milestone_opstart.json", "r")
        test_milestone = MilestoneBody.parse_raw(ms.read())
        ms.close()

        res = await ws.execute_webhook('milestone_event', test_milestone)
        assert res == 'milestone event is handled'

        tlc = mock_clients.teamleader
        assert tlc.method_called('update_company')

    @pytest.mark.asyncio
    async def test_milestone_contacts_and_adresses_sync(self, mock_clients):

        ws = WebhookScheduler()
        ws.start(mock_clients)

        # send a document event, so mocked redis stores it for
        # actual milestone call
        doc = open("tests/fixtures/document/update_contacts_itv.json", "r")
        test_doc = DocumentBody.parse_raw(doc.read())
        doc.close()
        res = await ws.execute_webhook('document_event', test_doc)
        assert res == 'document event is handled'

        ms = open("tests/fixtures/milestone/milestone_opstart.json", "r")
        test_milestone = MilestoneBody.parse_raw(ms.read())
        ms.close()

        res = await ws.execute_webhook('milestone_event', test_milestone)
        assert res == 'milestone event is handled'

        tlc = mock_clients.teamleader
        last_tlc_call = tlc.last_method_called()
        assert 'update_company' in last_tlc_call
        updated_company = last_tlc_call['update_company']

        assert updated_company['name'] == 'Testorganisatie voor Walter'
        # update: we behouden van teamleader org_type ipv de skryv waarde te nemen
        # assert 'CUL - erfgoedbibliotheek' in str(updated_company)  # value van skryv
        assert 'CUL - museum (erkend)' in str(updated_company)

        # facturatienaam is set on adresses
        assert 'AGB Walter' in str(updated_company['addresses'])

        # check some adresses
        assert 'straat 1234' in str(updated_company['addresses'])
        assert 'Facturatiestraat 12' in str(updated_company['addresses'])
        assert 'Leveringsstraat 12' in str(updated_company['addresses'])

        # check intentieverklaring value
        assert 'ingevuld' in str(updated_company['custom_fields'])
        assert 'pending' not in str(updated_company['custom_fields'])

        assert 'BE' in updated_company['vat_number']
        assert '0644.450.38' in updated_company['vat_number']

    @pytest.mark.asyncio
    async def test_milestone_error_in_contacts(self, mock_client_requests, requests_mock):
        API_URL = 'https://api.teamleader.eu'

        ws = WebhookScheduler()
        ws.start(mock_client_requests)

        with open("tests/fixtures/teamleader/custom_fields.json") as f:
            custom_fields = json.loads(f.read())

        requests_mock.get(
            f'{API_URL}/customFieldDefinitions.list',
            json={'data': custom_fields}
        )

        # send a document event, so mocked redis stores it for
        # actual milestone call
        doc = open("tests/fixtures/document/update_contacts_itv.json", "r")
        test_doc = DocumentBody.parse_raw(doc.read())
        doc.close()
        res = await ws.execute_webhook('document_event', test_doc)
        assert res == 'document event is handled'

        ms = open("tests/fixtures/milestone/milestone_opstart.json", "r")
        test_milestone = MilestoneBody.parse_raw(ms.read())
        ms.close()

        company_id = '1b2ab41a-7f59-103b-8cd4-1fcdd5140767'
        with open("tests/fixtures/teamleader/test_company.json") as f:
            test_company = json.loads(f.read())

        requests_mock.get(
            f'{API_URL}/companies.info?id={company_id}',
            json={'data': test_company}
        )

        with open("tests/fixtures/teamleader/test_contacts.json") as f:
            test_contacts = json.loads(f.read())

        contact_filter = f'company_id%5D={company_id}&page%5Bnumber%5D=1&page%5Bsize%5D=20'
        requests_mock.get(
            f'{API_URL}/contacts.list?filter%5B{contact_filter}',
            json={'data': test_contacts}
        )

        with open("tests/fixtures/teamleader/test_contact_administratie.json") as f:
            test_contact_administratie = json.loads(f.read())

        requests_mock.get(
            f'{API_URL}/contacts.info?id=93a20358-4b37-071f-8975-bde813530b50',
            json={'data': test_contact_administratie}
        )

        with open("tests/fixtures/teamleader/test_contact_directie.json") as f:
            test_contact_directie = json.loads(f.read())

        requests_mock.get(
            f'{API_URL}/contacts.info?id=03d32499-4a3d-0be9-bd79-424bf3530b4e',
            json={'data': test_contact_directie}
        )

        with open("tests/fixtures/teamleader/test_contact_extra1.json") as f:
            test_contact_extra1 = json.loads(f.read())

        requests_mock.get(
            f'{API_URL}/contacts.info?id=bf924044-c14e-053e-8077-df6f83530b51',
            json={'data': test_contact_extra1}
        )

        with open("tests/fixtures/teamleader/test_contact_extra2.json") as f:
            test_contact_extra2 = json.loads(f.read())

        requests_mock.get(
            f'{API_URL}/contacts.info?id=0db5a988-59b6-056b-9c75-767943548544',
            json={'data': test_contact_extra2}
        )

        # simulate error in contact update:
        requests_mock.post(
            f'{API_URL}/contacts.update',
            body='some contact error here',
            status_code=400
        )

        requests_mock.post(
            f'{API_URL}/contacts.updateCompanyLink',
            body='some update company link error',
            status_code=400
        )

        requests_mock.post(
            f'{API_URL}/companies.update',
            json={'data': 'success'}
        )

        res = await ws.execute_webhook('milestone_event', test_milestone)
        assert res == 'milestone event is handled'

        # TODO: simulate cases when contacts is empty

        # TODO: simulate bad VAT number

        # TODO: simulate bad email or missing email

        # TODO: simulate bad last_name

        # TODO: write errors to slack in case of 400 errors (and validate this happens)
