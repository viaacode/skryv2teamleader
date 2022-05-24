#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/services/document_service.py
#
#   DocumentService, handle document webhook events
#


class DocumentService:
    def __init__(self, common_clients):
        self.tlc = common_clients.teamleader
        self.org_ids = common_clients.org_ids
        self.slack = common_clients.slack

    def postadres(self):
        return self.document.document.value['adres_en_contactgegevens']['postadres']

    def handle_event(self, document_body):
        self.body = document_body
        self.document = self.body.document
        self.dossier = self.body.dossier

        print("handle_event document label=", self.document.definitionLabel)
        if self.body.action == 'updated':
            print("adres=", self.postadres())
