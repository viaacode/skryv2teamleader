#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/clients/skryv_client.py
#
#   Manage webhooks at skryv.com, for now we only make a list
#   to show what webhooks are expected, but we don't have actual
#   skryv-api access so we can't implement register/remove webhooks
#


class SkryvClient:
    def __init__(self, app_config: dict):
        env_params = app_config['skryv']
        self.webhook_url = env_params['webhook_url']

    def list_webhooks(self):
        return [
            f'{self.webhook_url}/skryv/process',
            f'{self.webhook_url}/skryv/document',
            f'{self.webhook_url}/skryv/milestone',
        ]
