#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   tests/unit/test_slack_messages.py
#

import pytest
import uuid
import requests_mock

from app.clients.slack_client import SlackClient
from mock_slack_wrapper import MockSlackWrapper
from testing_config import tst_app_config


class DossierMock:
    @property
    def externalId(self):
        return "OR-testid"

    @property
    def id(self):
        return uuid.uuid4()

    @property
    def label(self):
        return "Company that is not found in ldap"


class TestSlackMessages:
    @pytest.fixture
    def slack(self):
        # we set env to QAS so we call real chat_postMessage
        # but then mock this method to get full coverage without making real requests
        app_config = tst_app_config()
        app_config['environment'] = 'QAS'
        slack_client = SlackClient(app_config)
        slack_client.slack_wrapper.client = MockSlackWrapper()
        return slack_client

    def test_start_server(self, slack, requests_mock):
        slack.server_started_message()
        assert slack.slack_wrapper.client.method_called('chat_postMessage')

    def test_no_ldap_entry_found(self, slack, requests_mock):
        slack.no_ldap_entry_found(DossierMock())
        assert slack.slack_wrapper.client.method_called('chat_postMessage')

    def test_company_not_found(self, slack):
        slack.company_not_found(uuid.uuid4(), 'OR-testid')
        assert slack.slack_wrapper.client.method_called('chat_postMessage')

    def test_duplicate_message_filter(self, slack):
        slack.company_not_found('company_id', 'or_id')
        slack.company_not_found('company_id', 'or_id')
        slack.company_not_found('company_id', 'or_id')
        assert len(slack.slack_wrapper.client.all_method_calls()) == 1

    def test_dev_only_prints_debug_message(self, slack):
        slack.slack_wrapper.env = 'DEV'
        slack.teamleader_auth_error('SomeService', 'some_error')
        assert not slack.slack_wrapper.client.method_called('chat_postMessage')

    def test_connection_error(self):
        app_config = tst_app_config()
        app_config['environment'] = 'QAS'
        slack_client = SlackClient(app_config)
        # trigger api error
        slack_client.server_started_message()

    # these are already covered with other tests:
    # slack.test_empty_last_name()
    # slack.test_external_id_empty()
    # slack.update_company_failed(company_id, error, dossier)
    # slack.invalid_ondertekenprocess(dossier_id, error)
