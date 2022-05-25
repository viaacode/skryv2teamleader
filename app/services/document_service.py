#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/services/document_service.py
#
#   DocumentService, handle document webhook events
#

from app.models.document_body import DocumentBody


class DocumentService:
    def __init__(self, common_clients):
        self.tlc = common_clients.teamleader
        self.org_ids = common_clients.org_ids
        self.slack = common_clients.slack

    def postadres(self):
        return self.document.document.value['adres_en_contactgegevens']['postadres']

    def handle_event(self, document_body: DocumentBody):
        self.body = document_body
        self.document = self.body.document
        self.dossier = self.body.dossier
        self.organization_id = self.dossier.externalId

        print(
            "handling document: organization_id={}, document label={}, action={}".format(
                self.organization_id,
                self.document.definitionLabel,
                self.body.action
            )
        )

        if self.body.action == 'updated':
            print("adres=", self.postadres())
