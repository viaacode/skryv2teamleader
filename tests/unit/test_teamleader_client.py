#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   tests/unit/test_teamleader_client.py
#

import pytest
import uuid
import json
import requests_mock
from app.clients.teamleader_client import TeamleaderClient
from testing_config import tst_app_config
from tests.unit.mock_redis_cache import MockRedisCache


class TestTeamleaderClient:
    API_URL = 'https://api.teamleader.eu'

    @pytest.fixture
    def tlc(self):
        return TeamleaderClient(
            tst_app_config(),
            MockRedisCache()
        )

    def test_get_company(self, tlc, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/companies.info?id=company_uuid',
            json={'data': {}}
        )

        result = tlc.get_company('company_uuid')
        assert result == {}

    def test_update_company(self, tlc, requests_mock):
        with open("tests/fixtures/teamleader/company_updated_addendums.json") as f:
            mock_company = json.loads(f.read())

        requests_mock.post(
            f'{self.API_URL}/companies.update',
            json={'data': mock_company}
        )

        result = tlc.update_company(mock_company)

        assert result['id'] is not None
        assert result['name'] == 'S.M.A.K.'
        assert result['emails'][0]['type'] == 'primary'
        assert result['emails'][0]['email'] == 'info@smak.be'

    def test_list_companies(self, tlc, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/companies.list',
            json={'data': []}
        )

        result = tlc.list_companies()
        assert result == []

    def test_get_contact(self, tlc, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/contacts.info?id=some_contact_uuid',
            json={'data': {'id': 'mocked_contact_id'}}
        )

        result = tlc.get_contact('some_contact_uuid')
        assert result['id'] == 'mocked_contact_id'

    def test_list_contacts(self, tlc, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/contacts.list',
            json={'data': []}
        )

        result = tlc.list_contacts()
        assert result == []

    def test_list_contacts_auth_error(self, tlc, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/contacts.list',
            json={'data': []},
            status_code=401
        )

        # as this is 401, this triggers an access_token call
        access_token_response = {
            'access_token': 'teamleader_test_access_token',
            'refresh_token': 'teamleader_test_refresh_token'
        }
        requests_mock.post(
            'https://app.teamleader.eu/oauth2/access_token',
            json=access_token_response
        )

        with pytest.raises(ValueError, match='401'):
            result = tlc.list_contacts()
            assert result is None

    def test_add_contact(self, tlc, requests_mock):
        mock_contact = {
            'id': str(uuid.uuid4()),
            'first_name': 'test first name',
            'last_name': 'test create name',
            'custom_fields': [
                {
                    'id': 'some_custom_field_id',
                    'value': 'some custom value'
                }
            ]
        }

        requests_mock.post(
            f'{self.API_URL}/contacts.add',
            json={'data': mock_contact}
        )

        result = tlc.add_contact(mock_contact)

        assert result['id'] is not None
        assert result['first_name'] == mock_contact['first_name']
        assert result['last_name'] == mock_contact['last_name']
        assert result['custom_fields'][0]['id'] == 'some_custom_field_id'
        assert result['custom_fields'][0]['value'] == 'some custom value'

    def test_update_contact(self, tlc, requests_mock):
        # with update, the custom field format is a bit different
        # existing contact has definition->id, whereas update needs other format
        mock_contact = {
            'id': str(uuid.uuid4()),
            'first_name': 'test first name',
            'last_name': 'test last name',
            'custom_fields': [
                {
                    'definition': {
                        'id': 'some_custom_field_id'
                    },
                    'value': 'some custom value'
                }
            ]
        }

        requests_mock.post(
            f'{self.API_URL}/contacts.update',
            json={'data': mock_contact}
        )

        result = tlc.update_contact(mock_contact)
        assert result['id'] is not None
        assert result['first_name'] == mock_contact['first_name']
        assert result['last_name'] == mock_contact['last_name']
        assert result['custom_fields'][0]['id'] == 'some_custom_field_id'
        assert result['custom_fields'][0]['value'] == 'some custom value'

    def test_link_to_company(self, tlc, requests_mock):
        contact_link = {
            'id': 'test_contact_id',
            'company_id': 'test_company_id',
            'position': 'ceo',
            'decision_maker': True
        }

        requests_mock.post(
            f'{self.API_URL}/contacts.linkToCompany',
            json={'data': contact_link}
        )

        result = tlc.link_to_company(contact_link)
        assert result['id'] is not None

    def test_update_company_link(self, tlc, requests_mock):
        contact_link = {
            'id': 'test_contact_id',
            'company_id': 'test_company_id',
            'position': 'ceo',
            'decision_maker': True
        }

        requests_mock.post(
            f'{self.API_URL}/contacts.updateCompanyLink',
            json={'data': contact_link}
        )

        result = tlc.update_company_link(contact_link)
        assert result['id'] is not None

    def test_delete_contact(self, tlc, requests_mock):
        requests_mock.post(
            f'{self.API_URL}/contacts.delete',
            json={'data': {'id': 'test_contact_id'}}
        )

        result = tlc.delete_contact('test_contact_id')
        assert result['id'] is not None

    def test_company_contacts(self, tlc, requests_mock):
        COMPANY_ID = 'some_company_uuid'
        FIRST_PAGE = 'page%5Bnumber%5D=1&page%5Bsize%5D=20'
        requests_mock.get(
            '{}/contacts.list?filter%5Bcompany_id%5D={}&{}'.format(
                self.API_URL,
                COMPANY_ID,
                FIRST_PAGE
            ),
            json={'data': [{'id': 'company_contact_id'}]}
        )

        requests_mock.get(
            f'{self.API_URL}/contacts.info?id=company_contact_id',
            json={'data': {'first_name': 'testcontact_firstname'}}
        )

        result = tlc.company_contacts('some_company_uuid')
        assert len(result) == 1

    def test_custom_field(self, tlc, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/customFieldDefinitions.info?id=test_field_id',
            json={'data': {'id': 'field_id'}}
        )

        result = tlc.get_custom_field('test_field_id')
        assert result['id'] == 'field_id'

    def test_list_custom_fields(self, tlc, requests_mock):
        with open('tests/fixtures/teamleader/custom_fields.json') as cf_file:
            custom_fields = json.loads(cf_file.read())

        requests_mock.get(
            f'{self.API_URL}/customFieldDefinitions.list',
            json={'data': custom_fields}
        )

        result = tlc.list_custom_fields()
        assert len(result) >= 31
