#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   tests/unit/test_slack_messages.py
#

import pytest
import uuid

from app.clients.slack_client import SlackClient

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
    def test_start_server(self, slack):
        slack.server_started_message()
        slack._post_to_webhook.assert_called()

    def test_no_ldap_entry_found(self, slack):
        slack.no_ldap_entry_found(DossierMock())
        slack._post_to_webhook.assert_called()

    def test_company_not_found(self, slack):
        slack.company_not_found(uuid.uuid4(), "OR-testid")
        slack._post_to_webhook.assert_called()

    def test_duplicate_message_filter(self, slack):
        slack.company_not_found("company_id", "or_id")
        slack.company_not_found("company_id", "or_id")
        slack.company_not_found("company_id", "or_id")
        slack._post_to_webhook.assert_called_once()

    def test_dev_only_prints_debug_message(self, slack):
        slack.env = "DEV"
        slack.teamleader_auth_error("SomeService", "some_error")
        slack._post_to_webhook.assert_not_called()

    @pytest.mark.skip()
    def test_connection_error(self):
        app_config = tst_app_config()
        app_config["environment"] = "QAS"
        slack_client = SlackClient(app_config)
        # trigger api error
        slack_client.server_started_message()

    # these are already covered with other tests:
    # slack.test_empty_last_name()
    # slack.test_external_id_empty()
    # slack.update_company_failed(company_id, error, dossier)
    # slack.invalid_ondertekenprocess(dossier_id, error)
