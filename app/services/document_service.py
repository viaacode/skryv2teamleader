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
    def __init__(self, document_body):
        self.body = document_body
        self.document = self.body.document
        self.dossier = self.body.dossier

    def postadres(self):
        return self.document.document.value['adres_en_contactgegevens']['postadres']

    def handle_event(self):
        print("in document handling label=", self.document.definitionLabel)
        if self.body.action == 'updated':
            print("adres=", self.postadres())
