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

    # reset_comapany is only used for testing on qas or dev
    # it clears all flags and removes all related contacts, use with caution!
    def reset_company(self, or_id):
        # we clear all values here FOR DEBUGGING !!!!
        print(
            f"DEBUG RESET COMPANY CALLED! teamleader company or-id = {or_id}")

        ldap_org = self.ldap.find_company(or_id)
        if not ldap_org:
            print(
                f"company with OR-id {or_id} not found for process {self.action}")
            self.slack.no_ldap_entry_found(self.dossier)
            return

        company_id = ldap_org['x-be-viaa-externalUUID'].value
        company = self.tlc.get_company(company_id)

        # clear all flags and addenda set by milestones or process service
        company = self.set_cp_status(company, 'nee')
        company = self.set_intentieverklaring(company, None)
        company = self.set_toestemming_start(company, False)
        company = self.set_swo(company, False)
        company = self.set_swo_addenda(company, [])

        self.tlc.update_company(company)

        # also remove all contacts
        existing_contacts = self.tlc.company_contacts(company_id)
        for ec in existing_contacts:
            self.tlc.delete_contact(ec['id'])

    def save_cp_updated_document(self, document_body):
        if self.action != 'updated':
            print(
                "skipping document {self.action}, waiting for document 'updated' action...")
            return

        # store updated document in redis for a following milestone or process webhook:
        print(
            f"saving document {self.dossier.id} in redis for organization {self.or_id}")
        self.redis.save_document(document_body)

        # TODO: only uncomment reset_company for debugging purposes, after release this
        # can be removed/deprecated including entire reset_company method above
        # self.reset_company(self.or_id)

    def handle_event(self, document_body: DocumentBody):
        body = document_body
        self.action = body.action
        self.document = body.document
        self.dossier = body.dossier
        self.or_id = self.dossier.externalId

        # enkel behandeling type dossier 'contentpartner', skip briefing en anderen
        if self.dossier.dossierDefinition != self.SKRYV_DOSSIER_CP_ID:
            print(
                f"{self.dossier.dossierDefinition} is not a content partner document, skip event")

            return

        if(self.or_id):
            self.save_cp_updated_document(document_body)
        else:
            self.slack.external_id_empty(self.dossier)
