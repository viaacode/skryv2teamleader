#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/clients/slack_client.py
#
#   To easily post slack messages on channel #skryvbot
#

import json
from urllib.request import urlopen, Request

from viaa.configuration import ConfigParser
from viaa.observability import logging

from app.models.dossier import Dossier

config = ConfigParser()
logger = logging.get_logger(__name__, config=config)


class SlackClient:
    """Publish slack messages."""

    def __init__(self, app_config: dict):
        """
        Configuring a different channel to post to is not possible.  The
        channel is bound to the webhook URL, which is set in the Slack app at
        https://api.slack.com/apps/A091BFFRZ7A/
        """
        self.cfg = app_config
        self.env = app_config.get("environment") or "TST"
        self.webhook = app_config["slack"]["webhook"]
        self.previous_message = ""

    def _post_to_webhook(self, contents):
        """
        POST to the Slack webhook.

        Parameters:
            contents -- dict containing the message contents, with the `text'
                        key containing the main message body
        """
        request = Request(
            url=self.webhook,
            headers={"Content-Type": "application/json"},
            data=json.dumps(contents).encode("utf-8"),
        )
        response = urlopen(request)
        if response.status == 200:
            logger.debug("successfully sent Slack message")
        else:
            logger.error(f"failed to send Slack message: {response.status}")

    def create_message(self, message):
        slack_text = f"({self.env}) {message}"
        try:
            if slack_text == self.previous_message:
                logger.info(f"Skipping send of duplicate slack message: {slack_text}")
                return
            if self.env == "DEV" or self.env == "TST":
                print(f"\nSLACK WEBHOOK: {self.webhook} \nSLACK MSG: {slack_text}\n")
            else:
                self._post_to_webhook({"text": slack_text})
            self.previous_message = slack_text
        except Exception as e:
            logger.error(f"SLACK ERROR: {e}")

    def server_started_message(self):
        webhook_url = self.cfg["skryv"]["webhook_url"]
        self.create_message(f"Skryv2Teamleader started. webhook_url = {webhook_url}")

    def external_id_empty(self, dossier: Dossier):
        msg = "ExternalId is empty in skryv dossier_id: {} contentpartner: {}".format(dossier.id, dossier.label)
        self.create_message(msg)

    def no_ldap_entry_found(self, dossier: Dossier):
        msg = "No LDAP entry found with Attribute"
        self.create_message(
            "{} o={} for dossier {} with label {}".format(msg, dossier.externalId, dossier.id, dossier.label)
        )

    def company_not_found(self, company_id, or_id):
        msg = "Company UUID: {} with OR_ID: {} not found in Teamleader".format(company_id, or_id)
        self.create_message(msg)

    def empty_last_name(self, company, contact):
        company_url = "https://focus.teamleader.eu/company_detail.php?id={}".format(company["id"])

        msg_part1 = f"Contact found with empty last_name {contact.get('id')}.\n"
        msg_part2 = f"Setting last_name to {contact.get('last_name')} \n"
        msg_part3 = f"and linking to company in teamleader: {company_url}"
        last_name_warning = f"{msg_part1} {msg_part2} {msg_part3}"

        self.create_message(last_name_warning)

    def update_contact_failed(self, contact, company_id, error):
        company_link = "https://focus.teamleader.eu/company_detail.php?id={}".format(company_id)

        contact_link = "https://focus.teamleader.eu/contact_detail.php?id={}".format(contact.get("id"))

        msg = "Teamleader error: {} when updating contact {}\n on company {}".format(error, contact_link, company_link)
        self.create_message(msg)

    def add_contact_failed(self, contact, company_id, error):
        company_link = "https://focus.teamleader.eu/company_detail.php?id={}".format(company_id)

        msg = "Teamleader error: {} when adding new contact {}\n on company {}".format(
            error, f"{contact.get('first_name')} {contact.get('last_name')}", company_link
        )
        self.create_message(msg)

    def update_company_failed(self, company_id, error, dossier):
        company_link = "https://focus.teamleader.eu/company_detail.php?id={}".format(company_id)
        msg = "Teamleader error {} when updating company {}".format(error, company_link)

        msg = f"{msg}\n contentpartner: {dossier.label}\n skryv_id: {dossier.id}"

        self.create_message(msg)

    def teamleader_auth_error(self, service_name, error):
        msg = "Teamleader API authentication error in {} : {}. {}.".format(
            service_name, error, "Use the /health/oauth route to update tokens with a authorization_refresh_link"
        )
        self.create_message(msg)

    def invalid_ondertekenproces(self, dossier, error):
        msg = "Errors in ondertekenproces for Skryv {} {} parsing error: {}".format(
            f"contentpartner={dossier.label}", f"dossier_id={dossier.id}", error
        )
        self.create_message(msg)

    def invalid_milestone_dossier(self, dossier, error):
        msg = "Error in dossier during handling of milestone for Skryv {} {} parsing error: {}".format(
            f"contentpartner={dossier.label}", f"dossier_id={dossier.id}", error
        )
        self.create_message(msg)
