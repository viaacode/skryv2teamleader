#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/app.py
#
#   Main application handles skryv incoming webhooks and makes updates in
#   teamleader and sometimes creates slack messages
#
#   The same methods are also linked to a swagger ui / fastapi json api calls.
#   See api folder for the routers and routes in api.py and server.py where
#   this is instantiated
#

from viaa.configuration import ConfigParser
from viaa.observability import logging

#from app.services.company_service import CompanyService
#from app.services.contact_service import ContactService
from app.services.webhook_service import WebhookService
from app.clients.common_clients import construct_clients
from app.clients.redis_cache import redis_cache
from app.comm.webhook_scheduler import WebhookScheduler


# Initialize the logger and the configuration
config = ConfigParser()
logger = logging.get_logger(__name__, config=config)


class App:

    def __init__(self):
        self.clients = None
        self.whs = WebhookScheduler()
        self.redis_cache = redis_cache

    def start_clients(self, start_scheduler=True):
        logger.info("Starting teamleader, zendesk, slack clients...")
        if config.app_cfg['teamleader']['redis_url'] == 'DISABLED':
            self.clients = construct_clients(config.app_cfg)
        else:
            self.clients = construct_clients(config.app_cfg, self.redis_cache)

        if start_scheduler:
            self.whs.start(self.clients)

    def auth_callback(self, code, state):
        return self.clients.teamleader.authcode_callback(code, state)

    def proces_webhook(self, proces_event):
        logger.info(f"proces event: {proces_event}")
        # company = self.clients.teamleader.get_company(
        #     company_event.subject.id
        # )
        # self.whs.schedule('update_company_webhook', company)
        return {'status': 'proces event received and scheduled for handling'}

    def milestone_webhook(self, milestone_event):
        logger.info(f"milestone event: {milestone_vent}")
        # company = self.clients.teamleader.get_company(
        #     company_event.subject.id
        # )
        # self.whs.schedule('update_company_webhook', company)
        return {'status': 'milestone event received and scheduled for handling'}

    def document_webhook(self, document_event):
        logger.info(f"document event: {document_event}")
        # company = self.clients.teamleader.get_company(
        #     company_event.subject.id
        # )
        # self.whs.schedule('update_company_webhook', company)
        return {'status': 'document event received and scheduled for handling'}



    def list_webhooks(self):
        ws = WebhookService(self.clients.teamleader)
        return ws.list_webhooks()

    def create_webhooks(self):
        ws = WebhookService(self.clients.teamleader)
        return ws.create_webhooks()

    def update_webhooks(self):
        ws = WebhookService(self.clients.teamleader)
        return ws.update_webhooks()

    def delete_webhooks(self):
        ws = WebhookService(self.clients.teamleader)
        return ws.delete_webhooks()


main_app = App()
