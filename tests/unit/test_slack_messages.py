#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   tests/unit/test_slack_messages.py
#

import pytest
from app.clients.slack_client import SlackClient
from mock_slack_wrapper import MockSlackWrapper
from testing_config import tst_app_config
import uuid


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
        slack_client = SlackClient(tst_app_config())
        slack_client.slack_wrapper = MockSlackWrapper()
        return slack_client

    def test_start_server(self, slack):
        slack.server_started_message()
        assert slack.slack_wrapper.method_called('create_message')

    def test_no_ldap_entry_found(self, slack):
        slack.no_ldap_entry_found(DossierMock())
        assert slack.slack_wrapper.method_called('create_message')

    def test_company_not_found(self, slack):
        slack.company_not_found(uuid.uuid4(), 'OR-testid')
        assert slack.slack_wrapper.method_called('create_message')

    # these are already covered with other tests
    # def test_empty_last_name()
    # def test_external_id_empty()
