#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   tests/unit/test_skryv_base_service.py
#

import pytest
import uuid

from app.clients.common_clients import CommonClients
from app.models.process_body import ProcessBody
from app.models.document_body import DocumentBody
from app.clients.slack_client import SlackClient
from app.clients.skryv_client import SkryvClient

from mock_teamleader_client import MockTlClient
from mock_ldap_client import MockLdapClient
from mock_slack_wrapper import MockSlackWrapper
from mock_redis_cache import MockRedisCache

from testing_config import tst_app_config

from app.services.skryv_base import SkryvBase


class TestSkryvBaseService:
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

    def test_invalid_cp_status_is_ignored(self, mock_clients):
        sb = SkryvBase()
        sb.tlc = mock_clients.teamleader
        sb.read_configuration()

        test_company = {'custom_fields': []}
        updated_company = sb.set_cp_status(test_company, 'something invalid')
        assert len(test_company['custom_fields']) == 0

    def test_valid_cp_status(self, mock_clients):
        sb = SkryvBase()
        sb.tlc = mock_clients.teamleader
        sb.read_configuration()

        test_company = {'custom_fields': []}
        updated_company = sb.set_cp_status(test_company, 'pending')
        assert len(test_company['custom_fields']) > 0
        assert updated_company['custom_fields'][0]['value'] == 'pending'

    def test_invalid_intentieverklaring_ignored(self, mock_clients):
        sb = SkryvBase()
        sb.tlc = mock_clients.teamleader
        sb.read_configuration()

        test_company = {'custom_fields': []}
        updated_company = sb.set_intentieverklaring(
            test_company, 'something invalid')
        assert len(test_company['custom_fields']) == 0

    def test_valid_intentieverklaring(self, mock_clients):
        sb = SkryvBase()
        sb.tlc = mock_clients.teamleader
        sb.read_configuration()

        test_company = {'custom_fields': []}
        updated_company = sb.set_intentieverklaring(test_company, 'ingevuld')
        assert len(test_company['custom_fields']) > 0
        assert updated_company['custom_fields'][0]['value'] == 'ingevuld'

    def test_invalid_addenda(self, mock_clients):
        sb = SkryvBase()
        sb.tlc = mock_clients.teamleader
        sb.read_configuration()

        test_company = {'custom_fields': []}
        updated_company = sb.set_swo_addenda(test_company, 'something invalid')
        assert len(test_company['custom_fields']) == 0

    def test_existing_addenda(self, mock_clients):
        sb = SkryvBase()
        sb.tlc = mock_clients.teamleader
        sb.read_configuration()

        addenda_values = ['addenda1', 'addenda2']
        test_company = {
            'custom_fields': [
                {
                    "definition": {
                        "type": "customFieldDefinition",
                        "id": "30aa7f48-8915-0a13-8853-4c04fee6bb11"
                    },
                    "value": addenda_values
                }
            ]
        }
        company_addenda = sb.get_existing_addenda(test_company)
        assert company_addenda == addenda_values
