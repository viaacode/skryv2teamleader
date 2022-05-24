#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/services/process_service.py
#
#   ProcessService, handle process webhook events
#


class ProcessService:
    def __init__(self, process_body):
        self.body = process_body
        self.dossier = self.body.dossier
        self.process = self.body.process
        self.action = self.body.action

    def handle_event(self):
        print("handling process id={} organization_id={}".format(
                self.process.id,
                self.dossier.externalId
            )
        )
