#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   tests/unit/test_milestone_service.py
#

import pytest
import uuid

from app.comm.webhook_scheduler import WebhookScheduler
from app.clients.slack_client import SlackClient
from app.clients.skryv_client import SkryvClient
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
