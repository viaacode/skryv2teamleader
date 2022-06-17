#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/services/webhook_service.py
#
#   WebhookService handles listing webhooks
#
from app.clients.skryv_client import SkryvClient


class WebhookService:

    def __init__(self, teamleader_client):
        self.sc = SkryvClient()

    def list_webhooks(self):
        return {
            'registered_webhooks': self.sc.list_webhooks(),
            'webhook_url': self.sc.webhook_url
        }
