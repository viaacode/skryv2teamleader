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
from urllib.error import URLError
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
        try:
            if slack_text == self.previous_message:
                logger.warning(
                    f"Skipping send of duplicate slack message: {slack_text}"
                )
                return

            if self.env == 'DEV' or self.env == 'TST':
                print(
                    f"\nSLACK CHANNEL: {self.channel} \nSLACK MSG: {slack_text}\n"
                )
                self.previous_message = slack_text
                return

            self.client.chat_postMessage(
                channel=self.channel,
                text=slack_text
            )

            self.previous_message = slack_text

        except (SlackApiError, URLError) as e:
            logger.error(
                f"SLACK ERROR: {e} => Please check config.yml and .env"
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
        msg = "ExternalId is empty in skryv dossier_id: {} contentpartner: {}".format(
            dossier.id,
            dossier.label
        )
        self.create_message(msg)

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

        msg_part1 = f"Contact found with empty last_name {contact.get('id')}.\n"
        msg_part2 = f"Setting last_name to {contact.get('last_name')} \n"
        msg_part3 = f"and linking to company in teamleader: {company_url}"
        last_name_warning = f'{msg_part1} {msg_part2} {msg_part3}'

        self.create_message(last_name_warning)

    def update_contact_failed(self, contact, company_id, error):
        company_link = 'https://focus.teamleader.eu/company_detail.php?id={}'.format(
            company_id
        )

        contact_link = 'https://focus.teamleader.eu/contact_detail.php?id={}'.format(
            contact.get('id')
        )

        msg = "Teamleader error: {} when updating contact {}\n on company {}".format(
            error,
            contact_link,
            company_link
        )
        self.create_message(msg)

    def add_contact_failed(self, contact, company_id, error):
        company_link = 'https://focus.teamleader.eu/company_detail.php?id={}'.format(
            company_id
        )

        msg = "Teamleader error: {} when adding new contact {}\n on company {}".format(
            error,
            f"{contact.get('first_name')} {contact.get('last_name')}",
            company_link
        )
        self.create_message(msg)

    def update_company_failed(self, company_id, error, dossier):
        company_link = 'https://focus.teamleader.eu/company_detail.php?id={}'.format(
            company_id
        )
        msg = "Teamleader error {} when updating company {}".format(
            error,
            company_link
        )

        msg = f"{msg}\n contentpartner: {dossier.label}\n skryv_id: {dossier.id}"

        self.create_message(msg)

    def teamleader_auth_error(self, service_name, error):
        msg = "Teamleader API authentication error in {} : {}. {}.".format(
            service_name,
            error,
            'Use the /health/oauth route to update tokens with a authorization_refresh_link'
        )
        self.create_message(msg)

    def invalid_ondertekenproces(self, dossier, error):
        msg = 'Errors in ondertekenproces for Skryv {} {} parsing error: {}'.format(
            f'contentpartner={dossier.label}',
            f'dossier_id={dossier.id}',
            error
        )
        self.create_message(msg)

    def invalid_milestone_dossier(self, dossier, error):
        msg = 'Error in dossier during handling of milestone for Skryv {} {} parsing error: {}'.format(
            f'contentpartner={dossier.label}',
            f'dossier_id={dossier.id}',
            error
        )
        self.create_message(msg)
