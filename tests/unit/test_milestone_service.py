#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   tests/unit/test_milestone_service.py
#

import uuid
import requests_mock
import json
import pytest

from app.comm.webhook_scheduler import WebhookScheduler
from app.clients.slack_client import SlackClient
from app.clients.skryv_client import SkryvClient
from app.clients.teamleader_client import TeamleaderClient
from app.clients.common_clients import CommonClients
from app.models.milestone_body import MilestoneBody
from app.models.document_body import DocumentBody
from app.services.milestone_service import MilestoneService
from app.services.document_service import DocumentService

from mock_teamleader_client import MockTlClient
from mock_ldap_client import MockLdapClient, UNKNOWN_OR_ID
from mock_slack_wrapper import MockSlackWrapper
from mock_redis_cache import MockRedisCache

from testing_config import tst_app_config


class TestMilestoneService():
    API_URL = 'https://api.teamleader.eu'
    AUTH_URL = 'https://app.teamleader.eu'

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
    async def test_milestone_akkoord(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        ms = open("tests/fixtures/milestone/milestone_opstart.json", "r")
        test_milestone = MilestoneBody.parse_raw(ms.read())
        ms.close()
        res = await ws.execute_webhook('milestone_event', test_milestone)
        assert res == 'milestone event is handled'

    # we call the services directly here, allowing more fine grained testing
    def test_milestone_error_in_contacts(self, mock_client_requests, requests_mock):
        # send a document event, so mocked redis stores it for actual milestone call
        requests_mock.get(
            f'{self.API_URL}/customFieldDefinitions.list',
            json={'data': self.teamleader_fixture('custom_fields.json')},
            headers={'Content-Type': 'application/json', 'Connection': 'Close'}
        )

        doc = open("tests/fixtures/document/update_contacts_itv.json", "r")
        test_doc = DocumentBody.parse_raw(doc.read())
        doc.close()
        ds = DocumentService(mock_client_requests)
        ds.handle_event(test_doc)

        company_id = '1b2ab41a-7f59-103b-8cd4-1fcdd5140767'
        test_company = self.teamleader_fixture('test_company.json')
        requests_mock.get(
            f'{self.API_URL}/companies.info?id={company_id}',
            json={'data': test_company},
            headers={'Content-Type': 'application/json', 'Connection': 'Close'}
        )

        test_contacts = self.teamleader_fixture('test_contacts_adding.json')
        contact_filter = f'company_id%5D={company_id}&page%5Bnumber%5D=1&page%5Bsize%5D=20'
        requests_mock.get(
            f'{self.API_URL}/contacts.list?filter%5B{contact_filter}',
            json={'data': test_contacts},
            headers={'Content-Type': 'application/json', 'Connection': 'Close'}
        )

        tc_administratie = self.teamleader_fixture(
            'test_contact_administratie.json')
        requests_mock.get(
            f'{self.API_URL}/contacts.info?id=93a20358-4b37-071f-8975-bde813530b50',
            json={'data': tc_administratie},
            headers={'Content-Type': 'application/json', 'Connection': 'Close'}
        )

        tc_directie = self.teamleader_fixture('test_contact_directie.json')
        requests_mock.get(
            f'{self.API_URL}/contacts.info?id=03d32499-4a3d-0be9-bd79-424bf3530b4e',
            json={'data': tc_directie},
            headers={'Content-Type': 'application/json', 'Connection': 'Close'}
        )

        tc_extra1 = self.teamleader_fixture('test_contact_extra1.json')
        requests_mock.get(
            f'{self.API_URL}/contacts.info?id=bf924044-c14e-053e-8077-df6f83530b51',
            json={'data': tc_extra1},
            headers={'Content-Type': 'application/json', 'Connection': 'Close'}
        )

        # tc_extra2 = self.teamleader_fixture('test_contact_extra2.json')
        # requests_mock.get(
        #     f'{self.API_URL}/contacts.info?id=0db5a988-59b6-056b-9c75-767943548544',
        #     json={'data': tc_extra2}
        # )

        # simulate error in contact update:
        requests_mock.post(
            f'{self.API_URL}/contacts.update',
            json={'data': 'contact update error'},
            headers={'Content-Type': 'application/json',
                     'Connection': 'Close'},
            status_code=400
        )

        # simulate error in contact add:
        requests_mock.post(
            f'{self.API_URL}/contacts.add',
            json={'data': 'contact add error'},
            headers={'Content-Type': 'application/json',
                     'Connection': 'Close'},
            status_code=400
        )

        requests_mock.post(
            f'{self.API_URL}/contacts.updateCompanyLink',
            json={'data': 'company link error'},
            headers={'Content-Type': 'application/json',
                     'Connection': 'Close'},
            status_code=400
        )

        requests_mock.post(
            f'{self.API_URL}/companies.update',
            json={'data': 'success'},
            headers={'Content-Type': 'application/json', 'Connection': 'Close'}
        )

        opstart = open("tests/fixtures/milestone/milestone_opstart.json", "r")
        test_milestone = MilestoneBody.parse_raw(opstart.read())
        opstart.close()

        ms = MilestoneService(mock_client_requests)
        ms.handle_event(test_milestone)

        assert 'companies.update' in requests_mock.last_request.url
        company_updated = requests_mock.last_request.body

        # validate cp status is updated here
        assert '"afe9268c-c6dd-0053-bc5d-d4da5e723daa", "value": "ja"' in company_updated
        assert '"bcf9ceba-a988-0fc6-805f-9e087ea23dac", "value": "ingevuld"' in company_updated
        assert '"05cf38ba-2d6f-01fe-a85f-dd84aad23dae", "value": true' in company_updated
        assert '"1d0cc259-4b07-01b8-aa5b-100344423db0", "value": true' in company_updated

    def test_milestone_error_in_contacts_link(self, mock_client_requests, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/customFieldDefinitions.list',
            json={'data': self.teamleader_fixture('custom_fields.json')}
        )

        doc = open("tests/fixtures/document/update_contacts_itv.json", "r")
        test_doc = DocumentBody.parse_raw(doc.read())
        doc.close()
        ds = DocumentService(mock_client_requests)
        ds.handle_event(test_doc)

        company_id = '1b2ab41a-7f59-103b-8cd4-1fcdd5140767'
        test_company = self.teamleader_fixture('test_company.json')
        requests_mock.get(
            f'{self.API_URL}/companies.info?id={company_id}',
            json={'data': test_company}
        )

        test_contacts = self.teamleader_fixture('test_contacts_adding.json')
        contact_filter = f'company_id%5D={company_id}&page%5Bnumber%5D=1&page%5Bsize%5D=20'
        requests_mock.get(
            f'{self.API_URL}/contacts.list?filter%5B{contact_filter}',
            json={'data': test_contacts}
        )

        tc_administratie = self.teamleader_fixture(
            'test_contact_administratie.json')
        requests_mock.get(
            f'{self.API_URL}/contacts.info?id=93a20358-4b37-071f-8975-bde813530b50',
            json={'data': tc_administratie}
        )

        tc_directie = self.teamleader_fixture('test_contact_directie.json')
        requests_mock.get(
            f'{self.API_URL}/contacts.info?id=03d32499-4a3d-0be9-bd79-424bf3530b4e',
            json={'data': tc_directie}
        )

        tc_extra1 = self.teamleader_fixture('test_contact_extra1.json')
        requests_mock.get(
            f'{self.API_URL}/contacts.info?id=bf924044-c14e-053e-8077-df6f83530b51',
            json={'data': tc_extra1}
        )

        requests_mock.post(
            f'{self.API_URL}/contacts.update',
            json={'data': {'id': 'bf924044-c14e-053e-8077-df6f83530b51'}},
            status_code=200
        )

        requests_mock.post(
            f'{self.API_URL}/contacts.add',
            json={'data': {'id': 'bf924044-c14e-053e-8077-df6f83530b51'}},
            status_code=200
        )

        # error when linking
        requests_mock.post(
            f'{self.API_URL}/contacts.linkToCompany',
            json={'data': 'company link error'},
            status_code=400
        )

        # all ok when updating link
        requests_mock.post(
            f'{self.API_URL}/contacts.updateCompanyLink',
            json={'data': 'all ok'},
            status_code=200
        )

        requests_mock.post(
            f'{self.API_URL}/companies.update',
            json={'data': 'success'}
        )

        opstart = open("tests/fixtures/milestone/milestone_opstart.json", "r")
        test_milestone = MilestoneBody.parse_raw(opstart.read())
        opstart.close()

        ms = MilestoneService(mock_client_requests)
        ms.handle_event(test_milestone)

        assert 'companies.update' in requests_mock.last_request.url
        company_updated = requests_mock.last_request.body

        # validate cp status is updated here
        assert '"afe9268c-c6dd-0053-bc5d-d4da5e723daa", "value": "ja"' in company_updated
        assert '"bcf9ceba-a988-0fc6-805f-9e087ea23dac", "value": "ingevuld"' in company_updated
        assert '"05cf38ba-2d6f-01fe-a85f-dd84aad23dae", "value": true' in company_updated
        assert '"1d0cc259-4b07-01b8-aa5b-100344423db0", "value": true' in company_updated

    def test_milestone_edge_cases_1(self, mock_client_requests, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/customFieldDefinitions.list',
            json={'data': self.teamleader_fixture('custom_fields.json')}
        )

        doc = open("tests/fixtures/document/update_contacts_itv.json", "r")
        test_doc = DocumentBody.parse_raw(doc.read())
        doc.close()
        ds = DocumentService(mock_client_requests)

        # remove some values to trigger edge case handling
        ac = test_doc.document.document.value['adres_en_contactgegevens']
        ac.pop(
            'facturatieadres_verschillend_van_postadres'
        )
        ac.pop(
            'facturatie_emailadres'
        )
        ac.pop(
            'gegevens_directie'
        )
        ac.pop(
            'contactpersoon_dienstverlening'
        )
        ac['werkt_uw_organisatie_met_bestelbonnen_voor_de_facturatie']['selectedOption'] = 'nee'
        test_doc.document.document.value['bedrijfsvorm']['selectedOption'] = 'something invalid'

        ds.handle_event(test_doc)

        company_id = '1b2ab41a-7f59-103b-8cd4-1fcdd5140767'
        test_company = self.teamleader_fixture('test_company.json')
        # remove some keys so that we trigger edge cases
        test_company.pop('addresses')
        test_company.pop('emails')
        test_company.pop('telephones')
        requests_mock.get(
            f'{self.API_URL}/companies.info?id={company_id}',
            json={'data': test_company}
        )

        test_contacts = self.teamleader_fixture('test_contacts_adding.json')
        contact_filter = f'company_id%5D={company_id}&page%5Bnumber%5D=1&page%5Bsize%5D=20'
        requests_mock.get(
            f'{self.API_URL}/contacts.list?filter%5B{contact_filter}',
            json={'data': test_contacts}
        )

        tc_administratie = self.teamleader_fixture(
            'test_contact_administratie.json')

        requests_mock.get(
            f'{self.API_URL}/contacts.info?id=93a20358-4b37-071f-8975-bde813530b50',
            json={'data': tc_administratie}
        )

        tc_directie = self.teamleader_fixture('test_contact_directie.json')
        requests_mock.get(
            f'{self.API_URL}/contacts.info?id=03d32499-4a3d-0be9-bd79-424bf3530b4e',
            json={'data': tc_directie}
        )

        tc_extra1 = self.teamleader_fixture('test_contact_extra1.json')
        requests_mock.get(
            f'{self.API_URL}/contacts.info?id=bf924044-c14e-053e-8077-df6f83530b51',
            json={'data': tc_extra1}
        )

        requests_mock.post(
            f'{self.API_URL}/contacts.update',
            json={'data': {'id': 'bf924044-c14e-053e-8077-df6f83530b51'}},
            status_code=200
        )

        requests_mock.post(
            f'{self.API_URL}/contacts.add',
            json={'data': {'id': 'bf924044-c14e-053e-8077-df6f83530b51'}},
            status_code=200
        )

        # error when linking
        requests_mock.post(
            f'{self.API_URL}/contacts.linkToCompany',
            json={'data': 'company link error'},
            status_code=400
        )

        # all ok when updating link
        requests_mock.post(
            f'{self.API_URL}/contacts.updateCompanyLink',
            json={'data': 'all ok'},
            status_code=200
        )

        requests_mock.post(
            f'{self.API_URL}/companies.update',
            json={'data': 'success'}
        )

        opstart = open("tests/fixtures/milestone/milestone_opstart.json", "r")
        test_milestone = MilestoneBody.parse_raw(opstart.read())
        opstart.close()

        ms = MilestoneService(mock_client_requests)
        ms.handle_event(test_milestone)

        assert 'companies.update' in requests_mock.last_request.url
        company_updated = requests_mock.last_request.body

        # validate cp status is updated here
        assert '"afe9268c-c6dd-0053-bc5d-d4da5e723daa", "value": "ja"' in company_updated
        assert '"bcf9ceba-a988-0fc6-805f-9e087ea23dac", "value": "ingevuld"' in company_updated
        assert '"05cf38ba-2d6f-01fe-a85f-dd84aad23dae", "value": true' in company_updated
        assert '"1d0cc259-4b07-01b8-aa5b-100344423db0", "value": true' in company_updated

    def test_milestone_edge_cases_2(self, mock_client_requests, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/customFieldDefinitions.list',
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
            f'{self.API_URL}/companies.info?id={company_id}',
            json={'data': test_company}
        )

        test_contacts = self.teamleader_fixture('test_contacts_adding.json')
        contact_filter = f'company_id%5D={company_id}&page%5Bnumber%5D=1&page%5Bsize%5D=20'
        # make first update fail, but have vat still saved
        requests_mock.post(
            f'{self.API_URL}/companies.update',
            [
                {'json': {'data': 'some failure in saving'}, 'status_code': 400},
                {'json': {'data': 'vat saved ok'}, 'status_code': 200}
            ]
        )

        opstart = open("tests/fixtures/milestone/milestone_opstart.json", "r")
        test_milestone = MilestoneBody.parse_raw(opstart.read())
        opstart.close()

        ms = MilestoneService(mock_client_requests)
        ms.handle_event(test_milestone)

        assert 'companies.update' in requests_mock.last_request.url
        company_updated = requests_mock.last_request.body

        # validate cp status is updated here
        assert '"afe9268c-c6dd-0053-bc5d-d4da5e723daa", "value": "ja"' in company_updated
        assert '"bcf9ceba-a988-0fc6-805f-9e087ea23dac", "value": "ingevuld"' in company_updated
        assert '"05cf38ba-2d6f-01fe-a85f-dd84aad23dae", "value": true' in company_updated
        assert '"1d0cc259-4b07-01b8-aa5b-100344423db0", "value": true' in company_updated

    def test_milestone_company_not_found(self, mock_client_requests, requests_mock):
        # send a document event, so mocked redis stores it for
        # actual milestone call
        requests_mock.get(
            f'{self.API_URL}/customFieldDefinitions.list',
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
            f'{self.API_URL}/companies.info?id={company_id}',
            json={'data': None},
            status_code=404
        )

        # make first update fail, but have vat still saved
        requests_mock.post(
            f'{self.API_URL}/companies.update',
            [
                {'json': {'data': 'some failure in saving'}, 'status_code': 400},
                {'json': {'data': 'vat saved ok'}, 'status_code': 200}
            ]
        )

        opstart = open("tests/fixtures/milestone/milestone_opstart.json", "r")
        test_milestone = MilestoneBody.parse_raw(opstart.read())
        opstart.close()

        ms = MilestoneService(mock_client_requests)
        ms.handle_event(test_milestone)

        assert 'companies.update' not in requests_mock.last_request.url

    def test_milestone_edge_case_invalid_btw(self, mock_client_requests, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/customFieldDefinitions.list',
            json={'data': self.teamleader_fixture('custom_fields.json')}
        )

        doc = open("tests/fixtures/document/update_contacts_itv.json", "r")
        test_doc = DocumentBody.parse_raw(doc.read())
        doc.close()
        ds = DocumentService(mock_client_requests)

        # remove some values to trigger edge case handling
        ds.handle_event(test_doc)

        company_id = '1b2ab41a-7f59-103b-8cd4-1fcdd5140767'
        test_company = self.teamleader_fixture('test_company.json')
        # remove some keys so that we trigger edge cases
        test_company.pop('addresses')
        test_company.pop('emails')
        test_company.pop('telephones')
        requests_mock.get(
            f'{self.API_URL}/companies.info?id={company_id}',
            json={'data': test_company}
        )

        test_contacts = self.teamleader_fixture('test_contacts_adding.json')
        contact_filter = f'company_id%5D={company_id}&page%5Bnumber%5D=1&page%5Bsize%5D=20'
        requests_mock.get(
            f'{self.API_URL}/contacts.list?filter%5B{contact_filter}',
            json={'data': test_contacts}
        )

        tc_administratie = self.teamleader_fixture(
            'test_contact_administratie.json')
        requests_mock.get(
            f'{self.API_URL}/contacts.info?id=93a20358-4b37-071f-8975-bde813530b50',
            json={'data': tc_administratie}
        )

        tc_directie = self.teamleader_fixture('test_contact_directie.json')
        requests_mock.get(
            f'{self.API_URL}/contacts.info?id=03d32499-4a3d-0be9-bd79-424bf3530b4e',
            json={'data': tc_directie}
        )

        tc_extra1 = self.teamleader_fixture('test_contact_extra1.json')
        requests_mock.get(
            f'{self.API_URL}/contacts.info?id=bf924044-c14e-053e-8077-df6f83530b51',
            json={'data': tc_extra1}
        )

        requests_mock.post(
            f'{self.API_URL}/contacts.update',
            json={'data': {'id': 'bf924044-c14e-053e-8077-df6f83530b51'}},
            status_code=200
        )

        requests_mock.post(
            f'{self.API_URL}/contacts.add',
            json={'data': {'id': 'bf924044-c14e-053e-8077-df6f83530b51'}},
            status_code=200
        )

        # ok to add
        requests_mock.post(
            f'{self.API_URL}/contacts.linkToCompany',
            json={'data': 'company link error'},
            status_code=200
        )

        # all ok when updating link
        requests_mock.post(
            f'{self.API_URL}/contacts.updateCompanyLink',
            json={'data': 'all ok'},
            status_code=200
        )

        # make second update request with vat number fail
        requests_mock.post(
            f'{self.API_URL}/companies.update',
            [
                {'json': {'data': 'success'}, 'status_code': 200},
                {'json': {'data': 'vat failed'}, 'status_code': 400}
            ]
        )

        opstart = open("tests/fixtures/milestone/milestone_opstart.json", "r")
        test_milestone = MilestoneBody.parse_raw(opstart.read())
        opstart.close()

        ms = MilestoneService(mock_client_requests)
        ms.handle_event(test_milestone)

        assert 'companies.update' in requests_mock.last_request.url
        company_updated = requests_mock.last_request.body

        # validate cp status is updated here
        assert '"afe9268c-c6dd-0053-bc5d-d4da5e723daa", "value": "ja"' in company_updated
        assert '"bcf9ceba-a988-0fc6-805f-9e087ea23dac", "value": "ingevuld"' in company_updated
        assert '"05cf38ba-2d6f-01fe-a85f-dd84aad23dae", "value": true' in company_updated
        assert '"1d0cc259-4b07-01b8-aa5b-100344423db0", "value": true' in company_updated

    def test_facturatienaam_without_adresses(self, mock_client_requests, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/customFieldDefinitions.list',
            json={'data': self.teamleader_fixture('custom_fields.json')}
        )

        ms = MilestoneService(mock_client_requests)
        empty_company = {}
        updated_company = ms.set_facturatienaam(empty_company, "some name")

        assert updated_company['addresses'][0]['type'] == 'invoicing'
        assert updated_company['addresses'][0]['address']['addressee'] == 'some name'

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

        doc = open("tests/fixtures/document/updated_example.json", "r")
        test_doc = DocumentBody.parse_raw(doc.read())
        doc.close()
        res = await ws.execute_webhook('document_event', test_doc)
        assert res == 'document event is handled'

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

        doc = open("tests/fixtures/document/updated_example.json", "r")
        test_doc = DocumentBody.parse_raw(doc.read())
        doc.close()
        res = await ws.execute_webhook('document_event', test_doc)
        assert res == 'document event is handled'

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

        doc = open("tests/fixtures/document/updated_example.json", "r")
        test_doc = DocumentBody.parse_raw(doc.read())
        doc.close()
        res = await ws.execute_webhook('document_event', test_doc)
        assert res == 'document event is handled'

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
    async def test_milestone_with_unknown_org(self, mock_clients):
        ws = WebhookScheduler()
        ws.start(mock_clients)

        # send a document event, so mocked redis stores it for
        # actual milestone call
        doc = open("tests/fixtures/document/updated_example.json", "r")
        test_doc = DocumentBody.parse_raw(doc.read())
        test_doc.dossier.externalId = UNKNOWN_OR_ID
        doc.close()
        res = await ws.execute_webhook('document_event', test_doc)
        assert res == 'document event is handled'

        ms = open("tests/fixtures/milestone/milestone_opstart.json", "r")
        test_milestone = MilestoneBody.parse_raw(ms.read())
        test_milestone.dossier.externalId = UNKNOWN_OR_ID
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

    def test_milestone_service_unauthorized(self, mock_client_requests, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/customFieldDefinitions.list',
            json={'data': []},
            status_code=401
        )

        requests_mock.post(
            f'{self.AUTH_URL}/oauth2/access_token',
            json={},
            status_code=401
        )

        requests_mock.get(
            f'{self.API_URL}/companies.info?id=1b2ab41a-7f59-103b-8cd4-1fcdd5140767',
            json={},
            status_code=401
        )

        mf = open("tests/fixtures/milestone/milestone_opstart.json", "r")
        test_milestone = MilestoneBody.parse_raw(mf.read())
        mf.close()

        ms = MilestoneService(mock_client_requests)
        ms.handle_event(test_milestone)

        assert '/oauth2/access_token' in requests_mock.last_request.url

    def test_invalid_functie_category(self, mock_client_requests, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/customFieldDefinitions.list',
            json={'data': self.teamleader_fixture('custom_fields.json')}
        )

        ms = MilestoneService(mock_client_requests)
        mock_contact = {'id': 'some_test_id', 'custom_fields': []}
        result = ms.set_functie_category(
            mock_contact, 'some bad functie category')

        assert result['id'] == 'some_test_id'
        assert result['custom_fields'] == []

    def test_valid_functie_category(self, mock_client_requests, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/customFieldDefinitions.list',
            json={'data': self.teamleader_fixture('custom_fields.json')}
        )

        ms = MilestoneService(mock_client_requests)
        mock_contact = {'id': 'some_test_id', 'custom_fields': []}
        result = ms.set_functie_category(mock_contact, 'marcom')

        assert result['id'] == 'some_test_id'
        assert result['custom_fields'][0]['value'] == 'marcom'
