#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/services/webhook_service.py
#
#   WebhookService handles listing, creating and deleting all webhooks
#
from app.clients.skryv_client import SkryvClient


class WebhookService:

    def __init__(self, teamleader_client):
        # self.tlc = teamleader_client
        self.sc = SkryvClient()

    def list_webhooks(self):
        return {
            'registered_webhooks': self.sc.list_webhooks(),
            'webhook_url': self.sc.webhook_url
        }

    def update_webhooks(self):
        # unregister all old existing webhooks and re-install new ones
        # we us list_webhooks because most likely token is changed now
        existing_webhooks = self.sc.list_webhooks()
        for hook in existing_webhooks:
            self.sc.remove_webhook(hook)

        self.create_webhooks()
        return {'status': f'webhooks to {self.sc.webhook_url} updated'}

    def create_webhooks(self):
        # add skryv webhooks
        self.sc.register_webhook(
            f'{self.sc.webhook_url}/skryv/document',
            'document'
        )
        self.sc.register_webhook(
            f'{self.sc.webhook_url}/skryv/process',
            'process'
        )
        self.sc.register_webhook(
            f'{self.sc.webhook_url}/skryv/milestone',
            'milestone'
        )

        return {'status': f'webhooks to {self.sc.webhook_url} created'}

    def delete_webhooks(self):
        # remove skryv webhooks
        self.sc.remove_webhook(f'{self.sc.webhook_url}/skryv/milestone')
        self.sc.remove_webhook(f'{self.sc.webhook_url}/skryv/process')
        self.sc.remove_webhook(f'{self.sc.webhook_url}/skryv/document')

        return {'status': f'webhooks to {self.sc.webhook_url} deleted'}
