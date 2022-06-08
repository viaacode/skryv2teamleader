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

    def doc_postadres(self):
        dvals = self.document.document.value
        if 'adres_en_contactgegevens' in dvals:
            return dvals['adres_en_contactgegevens']['postadres']

    # we use this temporarely for testing, however
    # this needs to be done at a different moment, we
    # store the dossier here, and then set these in
    # either a process ended event for SWO.
    # or a milestone for ITV
    # see : https://meemoo.atlassian.net/wiki/spaces/IK/pages/818086103/contract.meemoo.be+en+Teamleader+skryv2crm

    def status_update(self, company):
        # TODO: remove this, this is just to easier debug teamleader propagation,
        # we clear all values here FOR DEBUGGING !!!!

        company = self.set_cp_status(company, 'nee')
        company = self.set_intentieverklaring(company, 'pending')
        company = self.set_toestemming_start(company, False)
        company = self.set_swo(company, False)
        company = self.set_swo_addenda(company, [])

        return company

    # opmerking
    # Binnen dossier "Briefing" heb je 1 proces met 1 document denk ik
    # Binnen dossier "Contentpartner" heb je 3 processen met meerdere documenten
    # Briefing-dossier is veel eenvoudiger dan Contentpartner
    # or id for testing: "OR-np1wh8z"

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

        # enkel behandeling type dossier 'contentpartner'
        if self.dossier.dossierDefinition != self.SKRYV_DOSSIER_CP_ID:
            print(
                f"{self.dossier.dossierDefinition} is not a content partner document, skip event")

            return

        if self.action == 'created':
            print("skipping document create, waiting for update...")
            return

        if self.action == 'updated':
            self.redis.save_document(self.body)
            tl_company = self.tlc.get_company(company_id)
            print("adres=", self.doc_postadres())
            tl_company = self.status_update(tl_company)
            self.tlc.update_company(tl_company)
            print(f"updated teamleader company {company_id}")

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
