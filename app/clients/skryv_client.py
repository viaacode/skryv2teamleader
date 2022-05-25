#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/clients/skryv_client.py
#
#   Manage webhooks at skryv.com
#


class SkryvClient:
    def __init__(self):
        self.webhook_url = 'skryv_webhook_url'

    def register_webhook(self, url, event):
        print("TODO: add skryv api call to create url=", url, 'for event=', event)

    def remove_webhook(self, url):
        print("TODO: api call to skryv to remove webhook url=", url)

    def list_webhooks(self):
        return [
            f'{self.webhook_url}/skryv/process',
            f'{self.webhook_url}/skryv/document',
            f'{self.webhook_url}/skryv/milestone',
        ]
