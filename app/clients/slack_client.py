#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/clients/slack_client.py
#
#   To easily post slack messages on channel: #crmbot
#

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from app.models.dossier import Dossier
from viaa.configuration import ConfigParser
from viaa.observability import logging

config = ConfigParser()
logger = logging.get_logger(__name__, config=config)


class SlackWrapper:
    """Publishing slack messages, this wrapper can be mocked easily in tests"""

    def __init__(self, token, channel, env="TST"):
        self.token = token
        self.channel = channel
        self.client = WebClient(token=self.token)
        self.env = env
        self.previous_message = ''

    def create_message(self, message):
        slack_text = f"({self.env}) {message}"

        if self.env == 'DEV' or self.env == 'TST':
            logger.info(f"DEBUG MODE: slack_message = {slack_text}")
            return

        try:
            if slack_text == self.previous_message:
                logger.warning(
                    f"Skipping send of duplicate slack message: {slack_text}"
                )
                return

            self.client.chat_postMessage(
                channel=self.channel,
                text=slack_text
            )

            self.previous_message = slack_text

        except SlackApiError as e:
            logger.error(
                f"SLACK ERROR: {e.response['error']} => Please check config.yml and .env"
            )


class SlackClient:
    def __init__(self, app_config: dict):
        self.cfg = app_config
        self.slack_wrapper = SlackWrapper(
            self.cfg['slack']['token'],
            self.cfg['slack']['channel'],
            self.cfg.get('environment')
        )

    def create_message(self, message):
        self.slack_wrapper.create_message(message)

    def server_started_message(self):
        webhook_url = self.cfg['skryv']['webhook_url']
        self.create_message(
            f'Skryv2Teamleader started. webhook_url = {webhook_url}'
        )

    def external_id_empty(self, dossier: Dossier):
        self.create_message(f"ExternalId is empty in document: {dossier}")

    def no_ldap_entry_found(self, dossier: Dossier):
        msg = 'No LDAP entry found with Attribute'
        self.create_message(
            "{} o={} for dossier {} with label {}".format(
                msg,
                dossier.externalId,
                dossier.id,
                dossier.label
            )
        )

    def company_not_found(self, company_id, or_id):
        msg = 'Company UUID: {} with OR_ID: {} not found in Teamleader'.format(
            company_id,
            or_id
        )
        self.create_message(msg)

    def empty_last_name(self, company, contact):
        company_url = 'https://focus.teamleader.eu/company_detail.php?id={}'.format(
            company['id']
        )

        msg_part1 = f"Contact found with empty last_name, setting last_name = {contact['last_name']}"
        msg_part2 = f'and linking to company in teamleader: {company_url}'
        last_name_warning = f'{msg_part1} {msg_part2}'

        self.create_message(last_name_warning)
