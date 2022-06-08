#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/services/document_service.py
#
#   DocumentService, handle document webhook events and
#   store updated_document in redis for later use in milestones and process events
#   This skips briefing type, only process the content partner dossiers
#   In case of errors, we use slack client to post messages on #skryvbot
#

from app.models.document_body import DocumentBody
from app.services.skryv_base import SkryvBase


class DocumentService(SkryvBase):
    def __init__(self, common_clients):
        self.tlc = common_clients.teamleader
        self.ldap = common_clients.ldap
        self.slack = common_clients.slack
        self.redis = common_clients.redis
        self.read_configuration()

    def reset_company_status(self, company_id):
        # we clear all values here FOR DEBUGGING !!!!
        company = self.tlc.get_company(company_id)

        company = self.set_cp_status(company, 'nee')
        company = self.set_intentieverklaring(company, None)  # clear it
        company = self.set_toestemming_start(company, False)
        company = self.set_swo(company, False)
        company = self.set_swo_addenda(company, [])  # clear addenda

        self.tlc.update_company(company)
        print(f"DEBUG reset_company_status called on company: {company['id']}")

    def teamleader_update(self):
        ldap_org = self.ldap.find_company(self.or_id)
        if not ldap_org:
            print(f"OR-id {self.or_id} not found for process {self.action}")
            self.slack.no_ldap_entry_found(self.dossier)
            return

        company_id = ldap_org['x-be-viaa-externalUUID'].value

        print(
            "document teamleader update: or-id={}, TL uuid={}, document label={}, action={}".format(
                self.or_id,
                company_id,
                self.document.definitionLabel,
                self.action
            )
        )

        # enkel behandeling type dossier 'contentpartner', skip briefing en anderen
        if self.dossier.dossierDefinition != self.SKRYV_DOSSIER_CP_ID:
            print(
                f"{self.dossier.dossierDefinition} is not a content partner document, skip event")

            return

        if self.action == 'created':
            print("skipping document create, waiting for update...")
            return

        # store any updated document in redis for later use in milestone or process webhooks:
        if self.action == 'updated':
            print(f"saving document {self.body.dossier.id} in redis")
            self.redis.save_document(self.body)

            # TODO: remove this, when releasing
            self.reset_company_status(company_id)

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
