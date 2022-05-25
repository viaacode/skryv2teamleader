#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/services/process_service.py
#
#   ProcessService, handle process webhook events
#

from app.models.process_body import ProcessBody


class ProcessService:
    def __init__(self, common_clients):
        self.tlc = common_clients.teamleader
        self.org_ids = common_clients.org_ids
        self.slack = common_clients.slack

    def teamleader_update(self):
        print(
            "process teamleader update: id={} organization_id={} definition={}".format(
                self.process.id,
                self.or_id,
                self.process.processDefinitionKey
            )
        )

    def handle_event(self, process_body: ProcessBody):
        self.body = process_body
        self.dossier = self.body.dossier
        self.process = self.body.process
        self.action = self.body.action
        self.or_id = self.dossier.externalId

        if(self.or_id):
            self.teamleader_update()
        else:
            print(
                "skipping process {self.process.id} because or_id is missing")
