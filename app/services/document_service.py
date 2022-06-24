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

from viaa.configuration import ConfigParser
from viaa.observability import logging

config = ConfigParser()
logger = logging.get_logger(__name__, config=config)


class DocumentService(SkryvBase):
    def __init__(self, common_clients):
        self.tlc = common_clients.teamleader
        self.ldap = common_clients.ldap
        self.slack = common_clients.slack
        self.redis = common_clients.redis
        self.read_configuration()

    def save_cp_updated_document(self, document_body):
        if self.action != 'updated':
            logger.info(
                f"skipping document {self.action}, waiting for document 'updated' action..."
            )
            return

        # store updated document in redis for a following milestone or process webhook:
        logger.info(
            f"saving document {self.dossier.id} in redis for organization {self.or_id}"
        )
        self.redis.save_document(document_body)
        # self.reset_company(self.or_id)  # debugging: clear all fields and contacts

    def handle_event(self, document_body: DocumentBody):
        body = document_body
        self.action = body.action
        self.document = body.document
        self.dossier = body.dossier
        self.or_id = self.dossier.externalId

        # enkel behandeling type dossier 'contentpartner', skip briefing en anderen
        if self.dossier.dossierDefinition != self.SKRYV_DOSSIER_CP_ID:
            logger.info(
                f"{self.dossier.dossierDefinition} is not a CP document, skip event"
            )
            return

        if(self.or_id):
            self.save_cp_updated_document(document_body)
        else:
            self.slack.external_id_empty(self.dossier)

    # def reset_company(self, or_id):
    #     # we clear all values here FOR DEBUGGING !!!!
    #     print(
    #         f"DEBUG RESET COMPANY CALLED! teamleader company or-id = {or_id}")

    #     ldap_org = self.ldap.find_company(or_id)
    #     if not ldap_org:
    #         print(
    #             f"company with OR-id {or_id} not found for process {self.action}")
    #         self.slack.no_ldap_entry_found(self.dossier)
    #         return

    #     company_id = ldap_org['x-be-viaa-externalUUID'].value
    #     company = self.tlc.get_company(company_id)

    #     # clear all flags and addenda set by milestones or process service
    #     company = self.set_cp_status(company, 'nee')
    #     company = self.set_intentieverklaring(company, None)
    #     company = self.set_toestemming_start(company, False)
    #     company = self.set_swo(company, False)
    #     company = self.set_swo_addenda(company, [])

    #     self.tlc.update_company(company)

    #     # also remove all contacts
    #     existing_contacts = self.tlc.company_contacts(company_id)
    #     for ec in existing_contacts:
    #         self.tlc.delete_contact(ec['id'])
