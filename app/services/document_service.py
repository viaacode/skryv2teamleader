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
        self.ldap = common_clients.ldap
        self.slack = common_clients.slack

    def postadres(self):
        return self.document.document.value['adres_en_contactgegevens']['postadres']

    def teamleader_update(self):
        print(
            "document teamleader update: organization_id={}, document label={}, action={}".format(
                self.or_id,
                self.document.definitionLabel,
                self.action
            )
        )

        ldap_org = self.ldap.find_company(self.or_id)
        if not ldap_org:
            self.slack.no_ldap_entry_found(self.dossier)
            return

        tl_org_uuid = ldap_org['x-be-viaa-externalUUID'].value

        print("TODO: updated teamleader organization with uuid=", tl_org_uuid)

        if self.action == 'updated':
            print("adres=", self.postadres())

    def handle_event(self, document_body: DocumentBody):
        self.body = document_body
        self.action = self.body.action
        self.document = self.body.document
        self.dossier = self.body.dossier
        self.or_id = self.dossier.externalId

        if(self.or_id):
            self.teamleader_update()
        else:
            self.slack.external_id_empty(self.dossier)
