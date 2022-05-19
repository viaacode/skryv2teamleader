#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/clients/slack_client.py
#
#   To easily post slack messages on channel: #skryvbot
#

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


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
            print(f"DEBUG MODE: slack_message = {slack_text}")
            return

        try:
            if slack_text == self.previous_message:
                print(
                    f"Skipping send of duplicate slack message: {slack_text}")
                return

            self.client.chat_postMessage(
                channel=self.channel,
                text=slack_text
            )

            self.previous_message = slack_text

        except SlackApiError as e:
            print(
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

    def missing_email(self, contact):
        self.create_message(
            f"""Contact {contact['first_name']} {contact['last_name']}
            heeft geen e-mailadres, gelieve dit in teamleader aan te passen:
            {contact['web_url']}
            """
        )
    
