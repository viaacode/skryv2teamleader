#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   tests/unit/test_teamleader_client.py
#

import pytest
import requests_mock
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

    def test_get_company(self, tlc, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/companies.info?id=company_uuid',
            json={'data': {}}
        )
        result = tlc.get_company('company_uuid')
        assert result == {}

    def test_get_contact(self, tlc, requests_mock):
        requests_mock.get(
            f'{self.API_URL}/contacts.info?id=some_contact_uuid',
            json={'data': {'id': 'mocked_contact_id'}}
        )
        result = tlc.get_contact('some_contact_uuid')
        assert result['id'] == 'mocked_contact_id'

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
