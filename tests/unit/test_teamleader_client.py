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
# import requests_mock
import httpretty

from app.clients.teamleader_client import TeamleaderClient
from testing_config import tst_app_config
from tests.unit.mock_redis_cache import MockRedisCache


class TestTeamleaderClient:
    API_URL = 'https://api.teamleader.eu'

    @pytest.fixture
    def tlc(self):
        teamleader_client = TeamleaderClient(
            tst_app_config(), MockRedisCache())
        return teamleader_client

    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_get_company(self, tlc):
        httpretty.register_uri(
            httpretty.GET,
            f'{self.API_URL}/companies.info?id=company_uuid',
            body=json.dumps({'data': {}}),
            content_type="text/json"
        )

        result = tlc.get_company('company_uuid')
        assert result == {}

    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_update_company(self, tlc):
        with open("tests/fixtures/teamleader/company_updated_addendums.json") as f:
            mock_company = json.loads(f.read())

        httpretty.register_uri(
            httpretty.POST,
            f'{self.API_URL}/companies.update',
            body=json.dumps({'data': mock_company}),
            content_type="text/json"
        )

        result = tlc.update_company(mock_company)
        assert result['id'] is not None
        assert result['name'] == 'S.M.A.K.'
        assert result['emails'][0]['type'] == 'primary'
        assert result['emails'][0]['email'] == 'info@smak.be'

    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_list_companies(self, tlc):
        httpretty.register_uri(
            httpretty.GET,
            f'{self.API_URL}/companies.list',
            body=json.dumps({'data': []}),
            content_type="text/json"
        )

        result = tlc.list_companies()
        assert result == []

    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_get_contact(self, tlc):
        httpretty.register_uri(
            httpretty.GET,
            f'{self.API_URL}/contacts.info?id=some_contact_uuid',
            body=json.dumps({'data': {'id': 'mocked_contact_id'}}),
            content_type="text/json"
        )

        result = tlc.get_contact('some_contact_uuid')
        assert result['id'] == 'mocked_contact_id'

    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_list_contacts(self, tlc):
        httpretty.register_uri(
            httpretty.GET,
            f'{self.API_URL}/contacts.list',
            body=json.dumps({'data': []}),
            content_type="text/json"
        )

        result = tlc.list_contacts()
        assert result == []

    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_list_contacts_auth_error(self, tlc):
        httpretty.register_uri(
            httpretty.GET,
            f'{self.API_URL}/contacts.list',
            body=json.dumps({'data': []}),
            content_type="text/json",
            status=401
        )

        # as this is 401, this triggers an access_token call
        access_token_response = {
            'access_token': 'teamleader_test_access_token',
            'refresh_token': 'teamleader_test_refresh_token'
        }
        httpretty.register_uri(
            httpretty.POST,
            'https://app.teamleader.eu/oauth2/access_token',
            body=json.dumps(access_token_response),
            content_type="text/json"
        )

        with pytest.raises(ValueError, match='401'):
            result = tlc.list_contacts()
            assert result is None

    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_add_contact(self, tlc):
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

        httpretty.register_uri(
            httpretty.POST,
            f'{self.API_URL}/contacts.add',
            body=json.dumps({'data': mock_contact}),
            content_type="text/json"
        )

        result = tlc.add_contact(mock_contact)

        assert result['id'] is not None
        assert result['first_name'] == mock_contact['first_name']
        assert result['last_name'] == mock_contact['last_name']
        assert result['custom_fields'][0]['id'] == 'some_custom_field_id'
        assert result['custom_fields'][0]['value'] == 'some custom value'

    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_update_contact(self, tlc):
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

        httpretty.register_uri(
            httpretty.POST,
            f'{self.API_URL}/contacts.update',
            body=json.dumps({'data': mock_contact}),
            content_type="text/json"
        )

        result = tlc.update_contact(mock_contact)

        assert result['id'] is not None
        assert result['first_name'] == mock_contact['first_name']
        assert result['last_name'] == mock_contact['last_name']
        __import__('pdb').set_trace()
        assert result['custom_fields'][0]['id'] == 'some_custom_field_id'
        assert result['custom_fields'][0]['value'] == 'some custom value'

    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_link_to_company(self, tlc):
        contact_link = {
            'id': 'test_contact_id',
            'company_id': 'test_company_id',
            'position': 'ceo',
            'decision_maker': True
        }

        httpretty.register_uri(
            httpretty.POST,
            f'{self.API_URL}/contacts.linkToCompany',
            body=json.dumps({'data': contact_link}),
            content_type="text/json"
        )

        result = tlc.link_to_company(contact_link)
        result['id'] is not None

    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_update_company_link(self, tlc):
        contact_link = {
            'id': 'test_contact_id',
            'company_id': 'test_company_id',
            'position': 'ceo',
            'decision_maker': True
        }

        httpretty.register_uri(
            httpretty.POST,
            f'{self.API_URL}/contacts.updateCompanyLink',
            body=json.dumps({'data': contact_link}),
            content_type="text/json"
        )

        result = tlc.update_company_link(contact_link)
        result['id'] is not None

    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_delete_contact(self, tlc):
        httpretty.register_uri(
            httpretty.POST,
            f'{self.API_URL}/contacts.delete',
            body=json.dumps({'data': {'id': 'test_contact_id'}}),
            content_type="text/json"
        )

        result = tlc.delete_contact('test_contact_id')
        assert result['id'] is not None

    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_company_contacts(self, tlc):
        COMPANY_ID = 'some_company_uuid'
        FIRST_PAGE = 'page%5Bnumber%5D=1&page%5Bsize%5D=20'

        httpretty.register_uri(
            httpretty.GET,
            '{}/contacts.list?filter%5Bcompany_id%5D={}&{}'.format(
                self.API_URL,
                COMPANY_ID,
                FIRST_PAGE
            ),
            body=json.dumps({'data': [{'id': 'company_contact_id'}]}),
            content_type="text/json"
        )

        httpretty.register_uri(
            httpretty.GET,
            f'{self.API_URL}/contacts.info?id=company_contact_id',
            body=json.dumps({'data': {'first_name': 'testcontact_firstname'}}),
            content_type="text/json"
        )

        result = tlc.company_contacts('some_company_uuid')
        assert len(result) == 1

    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_custom_field(self, tlc):
        httpretty.register_uri(
            httpretty.GET,
            f'{self.API_URL}/customFieldDefinitions.info?id=test_field_id',
            body=json.dumps({'data': {'id': 'field_id'}}),
            content_type="text/json"
        )

        result = tlc.get_custom_field('test_field_id')
        assert result['id'] == 'field_id'

    @httpretty.activate(verbose=True, allow_net_connect=False)
    def test_list_custom_fields(self, tlc):
        with open('tests/fixtures/custom_fields.json') as cf_file:
            custom_fields = json.loads(cf_file.read())

        httpretty.register_uri(
            httpretty.GET,
            f'{self.API_URL}/customFieldDefinitions.list',

            body=json.dumps({'data': custom_fields}),
            content_type="text/json"
        )

        result = tlc.list_custom_fields()
        assert len(result) >= 31
