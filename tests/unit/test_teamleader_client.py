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
from datetime import datetime

from app.clients.teamleader_client import TeamleaderClient, TeamleaderAuthError
from testing_config import tst_app_config
from tests.unit.mock_redis_cache import MockRedisCache


class TestTeamleaderClient:
    API_URL = 'https://api.teamleader.eu'
    AUTH_URL = 'https://app.teamleader.eu'

    @pytest.fixture
    def tlc(self):
        tlc_fast = TeamleaderClient(
            tst_app_config(),
            MockRedisCache()
        )
        # switch off rate limiting for fast tests
        tlc_fast.RATE_LIMIT = 0.0

        return tlc_fast

    def test_authcode_callback_bad_state(self, tlc, requests_mock):
        test_code = 'code1234'
        test_state = 'bad_state'
        res = tlc.authcode_callback(test_code, test_state)
        assert res['status'] == 'code rejected'
        assert tlc.code != 'code1234'

    def test_authcode_callback_invalid_response(self, tlc, requests_mock):
        requests_mock.post(
            'https://app.teamleader.eu/oauth2/access_token',
            text='wrong code used',
            status_code=400
        )

        test_code = 'code1234'
        test_state = 'test_secret_code_state'
        res = tlc.authcode_callback(test_code, test_state)
        assert res['error'] == 'code rejected: wrong code used'

    def test_authcode_callback(self, tlc, requests_mock):
        test_code = 'code1234'
        test_state = 'test_secret_code_state'

        requests_mock.post(
            'https://app.teamleader.eu/oauth2/access_token',
            json={
                'access_token': 'new_test_access_token',
                'refresh_token': 'new_test_refresh_token'
            }
        )
        res = tlc.authcode_callback(test_code, test_state)
        assert res['status'] == 'code accepted'
        assert tlc.code == 'code1234'
        assert tlc.token == 'new_test_access_token'
        assert tlc.refresh_token == 'new_test_refresh_token'

    def test_oauth_check(self, tlc, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/customFieldDefinitions.list?page%5Bnumber%5D=1&page%5Bsize%5D=1',
            json={'data': []}
        )
        result = tlc.oauth_check()
        assert result['status'] == 'ok'

    def test_oauth_check_expired(self, tlc, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/customFieldDefinitions.list?page%5Bnumber%5D=1&page%5Bsize%5D=1',
            json={'data': []},
            status_code=401
        )
        requests_mock.post(
            'https://app.teamleader.eu/oauth2/access_token',
            json={},
            status_code=400
        )
        result = tlc.oauth_check()
        assert result['status'] != "ok"
        assert 'authorization_refresh_link' in result

    def test_get_company(self, tlc, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/companies.info?id=company_uuid',
            json={'data': {}}
        )

        result = tlc.get_company('company_uuid')
        assert result == {}

    def test_get_company_unauthorized(self, tlc, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/companies.info?id=company_uuid',
            json={'data': {}},
            status_code=401
        )

        requests_mock.post(
            f'{self.AUTH_URL}/oauth2/access_token',
            json={
                'access_token': 'test_access',
                'refresh_token': 'test_refresh',
            },
            status_code=401
        )

        with pytest.raises(TeamleaderAuthError):
            result = tlc.get_company('company_uuid')
            assert result == {}

    def test_get_company_refresh_token_needed(self, tlc, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/companies.info?id=company_uuid',
            [
                {'json': {'data': {}}, 'status_code': 401},
                {'json': {'data': {}}, 'status_code': 200}
            ]
        )

        requests_mock.post(
            f'{self.AUTH_URL}/oauth2/access_token',
            json={
                'access_token': 'test_access',
                'refresh_token': 'test_refresh',
            },
            status_code=200
        )

        result = tlc.get_company('company_uuid')
        assert result == {}

    def test_get_company_error_response_raises(self, tlc, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/companies.info?id=company_uuid',
            [
                {'json': {'data': {}}, 'status_code': 400},
            ]
        )

        with pytest.raises(ValueError):
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

    def test_update_company_with_empty_response(self, tlc, requests_mock):
        with open("tests/fixtures/teamleader/company_updated_addendums.json") as f:
            mock_company = json.loads(f.read())

        requests_mock.post(
            f'{self.API_URL}/companies.update',
            json={'data': mock_company},
            status_code=204
        )

        result = tlc.update_company(mock_company)
        assert result is None

    def test_update_company_when_refresh_token_needed(self, tlc, requests_mock):
        with open("tests/fixtures/teamleader/company_updated_addendums.json") as f:
            mock_company = json.loads(f.read())

        requests_mock.post(
            f'{self.API_URL}/companies.update',
            [
                {'json': {'data': 'some error'}, 'status_code': 401},
                {'json': {'data': mock_company}, 'status_code': 200}
            ]
        )

        requests_mock.post(
            f'{self.AUTH_URL}/oauth2/access_token',
            json={
                'access_token': 'test_access',
                'refresh_token': 'test_refresh',
            },
            status_code=200
        )

        result = tlc.update_company(mock_company)
        assert result['name'] == 'S.M.A.K.'

    def test_update_company_validation_error(self, tlc, requests_mock):
        with open("tests/fixtures/teamleader/company_updated_addendums.json") as f:
            mock_company = json.loads(f.read())

        requests_mock.post(
            f'{self.API_URL}/companies.update',
            json={'data': mock_company},
            status_code=400
        )

        with pytest.raises(ValueError):
            result = tlc.update_company(mock_company)
            assert result is None

    def test_update_company_unauthorized_raised(self, tlc, requests_mock):
        with open("tests/fixtures/teamleader/company_updated_addendums.json") as f:
            mock_company = json.loads(f.read())

        requests_mock.post(
            f'{self.API_URL}/companies.update',
            [
                {'json': {'data': 'some error'}, 'status_code': 401},
                {'json': {'data': mock_company}, 'status_code': 401}
            ]
        )

        requests_mock.post(
            f'{self.AUTH_URL}/oauth2/access_token',
            json={
                'access_token': 'test_access',
                'refresh_token': 'test_refresh',
            },
            status_code=401
        )

        with pytest.raises(TeamleaderAuthError):
            result = tlc.update_company(mock_company)
            assert result == ''

    def test_list_companies(self, tlc, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/companies.list',
            json={'data': []}
        )

        result = tlc.list_companies()
        assert result == []

    def test_list_companies_with_since(self, tlc, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/companies.list',
            json={'data': []}
        )

        result = tlc.list_companies(1, 20, datetime.now())
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

        with pytest.raises(TeamleaderAuthError):
            result = tlc.list_contacts()
            assert result is None

    def test_list_contacts_other_error(self, tlc, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/contacts.list',
            json={'data': []},
            status_code=400
        )

        with pytest.raises(ValueError):
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

    def test_list_business_types(self, tlc, requests_mock):
        with open('tests/fixtures/teamleader/business_types.json') as f:
            business_types = json.loads(f.read())

        requests_mock.get(
            f'{self.API_URL}/businessTypes.list',
            json={'data': business_types}
        )

        result = tlc.list_business_types()
        assert len(result) > 10

    def test_secure_route_without_jwt(self, tlc, requests_mock):
        tlc.webhook_jwt = None
        res = tlc.secure_route('some url')
        assert res == 'some url'

    def test_migrate_uuid(self, tlc, requests_mock):
        old_id = '56061444'
        resource_type = 'contact'
        mapped_uuid = '6f9a8f80-5779-08fd-b57b-91a6d3576e04'
        requests_mock.get(
            f'{self.API_URL}/migrate.id?id={old_id}&type={resource_type}',
            json={'data': {'id': mapped_uuid}}
        )
        contact_uuid = tlc.get_migrate_uuid(resource_type, old_id)
        assert contact_uuid == mapped_uuid

    def test_migrate_uuid_needs_auth_refresh(self, tlc, requests_mock):
        old_id = '56061444'
        resource_type = 'contact'
        mapped_uuid = '6f9a8f80-5779-08fd-b57b-91a6d3576e04'
        requests_mock.get(
            f'{self.API_URL}/migrate.id?id={old_id}&type={resource_type}',
            [
                {'json': {'data': {'id': mapped_uuid}}, 'status_code': 401},
                {'json': {'data': {'id': mapped_uuid}}, 'status_code': 200}
            ]
        )

        requests_mock.post(
            f'{self.AUTH_URL}/oauth2/access_token',
            json={
                'access_token': 'test_access',
                'refresh_token': 'test_refresh',
            },
            status_code=200
        )

        contact_uuid = tlc.get_migrate_uuid(resource_type, old_id)
        assert contact_uuid == mapped_uuid

    def test_migrate_uuid_failed_auth_refresh(self, tlc, requests_mock):
        old_id = '56061444'
        resource_type = 'contact'
        mapped_uuid = '6f9a8f80-5779-08fd-b57b-91a6d3576e04'
        requests_mock.get(
            f'{self.API_URL}/migrate.id?id={old_id}&type={resource_type}',
            [
                {'json': {'data': {'id': mapped_uuid}}, 'status_code': 401},
                {'json': {'data': {'id': mapped_uuid}}, 'status_code': 401}
            ]
        )

        requests_mock.post(
            f'{self.AUTH_URL}/oauth2/access_token',
            json={
                'access_token': 'test_access',
                'refresh_token': 'test_refresh',
            },
            status_code=400
        )

        with pytest.raises(TeamleaderAuthError):
            contact_uuid = tlc.get_migrate_uuid(resource_type, old_id)
            assert contact_uuid is None

    def test_migrate_uuid_not_found(self, tlc, requests_mock):
        old_id = '56061444'
        resource_type = 'contact'
        mapped_uuid = '6f9a8f80-5779-08fd-b57b-91a6d3576e04'
        requests_mock.get(
            f'{self.API_URL}/migrate.id?id={old_id}&type={resource_type}',
            json={},
            status_code=404
        )
        contact_uuid = tlc.get_migrate_uuid(resource_type, old_id)
        assert contact_uuid is None
