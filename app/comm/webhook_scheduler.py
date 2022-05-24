#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/comm/webhook_scheduler.py
#       we queue the incomming webrequests
#       this fixes race conditions on ldap operations
#

import queue
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from viaa.configuration import ConfigParser
from viaa.observability import logging

# todo have other services here...
# from app.services.company_service import CompanyService
# from app.services.contact_service import ContactService

# Initialize the logger and the configuration
config = ConfigParser()
logger = logging.get_logger(__name__, config=config)


class WebhookScheduler:
    def __init__(self):
        self.clients = None
        self.webhook_queue = queue.Queue()
        self.queue_limit = 5        # nr of entries per scheduler iteration
        self.scheduler_interval = 1  # run webhook_processing every x seconds
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(
            self.webhook_processing,
            'interval', seconds=self.scheduler_interval
        )

    def start(self, clients):
        self.clients = clients
        self.scheduler.start()
        logger.info(
            "APScheduler started: interval seconds={} queue_limit={}".format(
                self.scheduler_interval,
                self.queue_limit
            )
        )

    def schedule(self, webhook, parameters):
        self.webhook_queue.put({
            "webhook": webhook,
            "params": parameters
        })

    async def execute_webhook(self, name, params):
        if name == 'process_event':
            logger.info(f"process event params={params}")
            # TODO: some service call here...
            return "process event result"
        elif name == 'milestone_event':
            logger.info(f"milestone event params={params}")
            print("milestone status=", params.milestone.status)
            # TODO: some service call here...
            return "milestione event result"
        elif name == 'document_event':
            logger.info(f"Document event params={params}")
            # TODO: some service call here...
            return "document event result"
        else:
            logger.warning(
                f"invalid webhook: {name} received with params: {params}")

    async def webhook_processing(self):
        for i in range(self.queue_limit):
            if not self.webhook_queue.empty():
                request_obj = self.webhook_queue.get_nowait()
                await self.execute_webhook(
                    request_obj['webhook'],
                    request_obj['params']
                )
