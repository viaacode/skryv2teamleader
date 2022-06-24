#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/services/process_service.py
#
#   ProcessService, handle process webhook events, we check for a secific
#   ended process. And if found. We fetch the last updated document associated
#   with this process and then set
#   cp_status = ja,
#   toestemming_start=True
#   swo = True
#   swo_addenda = mapped list from addenda inside the document into specific
#   array value. We use base class helper methods for this
#

from app.models.process_body import ProcessBody
from app.models.document_body import DocumentBody
from app.services.skryv_base import SkryvBase
from pydantic import ValidationError

from viaa.configuration import ConfigParser
from viaa.observability import logging

config = ConfigParser()
logger = logging.get_logger(__name__, config=config)


class ProcessService(SkryvBase):
    def __init__(self, common_clients):
        self.tlc = common_clients.teamleader
        self.ldap = common_clients.ldap
        self.slack = common_clients.slack
        self.redis = common_clients.redis
        self.read_configuration()

    def get_addendums(self, document_body):
        dvals = document_body.document.document.value
        if 'te_ondertekenen_documenten' in dvals:
            tod = dvals['te_ondertekenen_documenten']
            if 'addendum' in tod:
                return tod['addendum']

    def addendums_update(self, company, document):
        tl_swo_map = {
            'Aanduiding contentpartners (koepel)': 'Aanduiding contentpartners (koepel)',
            'Protocol voor de elektronische mededeling van persoonsgegevens (GDPR)': 'GDPR protocol',
            'Overeenkomst voor de bescherming van persoonsgegevens (GDPR)': 'GDPR overeenkomst',
            'Dienstverlening inzake de digitalisering en ontsluiting van kunstwerken, erfgoedobjecten of topstukken': 'Dienstverlening kunstwerken erfgoedobjecten topstukken',  # noqa: E501
            'Specifieke voorwaarden': 'Specifieke voorwaarden',
            'Topstukkenaddendum': 'Topstukkenaddendum'
        }

        addendums = self.get_addendums(document)
        if not addendums:
            logger.info("no new, addendums found in document")
            return company

        # keep existing addenda from previous process
        tl_addendums = self.get_existing_addenda(company)
        logger.info(f"existing company swo_addenda = {tl_addendums}")

        for ad in addendums:
            ad_naam = tl_swo_map.get(ad['naam']['Specifieke addenda'])
            if ad_naam and ad_naam not in tl_addendums:
                tl_addendums.append(
                    ad_naam
                )

        logger.info(f"merged company swo_addenda = {tl_addendums}")
        company = self.set_swo_addenda(company, tl_addendums)

        return company

    def set_status_ondertekenproces(self, company):
        logger.info(
            "process ({}) -> teamleader status ondertekenproces: or-id={}, company={}".format(
                self.process.id,
                self.or_id,
                company['id']
            )
        )
        # if process is ended, and we get here, all checks passed
        # also fetch related document, and set all flags to ja and true:
        company = self.set_cp_status(company, 'ja')
        company = self.set_toestemming_start(company, True)
        company = self.set_swo(company, True)

        try:
            updated_document_json = self.redis.load_document(self.dossier.id)
            company = self.addendums_update(
                company,
                DocumentBody.parse_raw(updated_document_json)
            )

        except ValidationError as e:
            logger.warning(
                f"Missing or malformed dossier for ondertekenproces: {self.dossier.id} error: {e}"
            )

        return company

    def set_status_intentieverklaring(self, company):
        logger.info(
            "process ({}) -> teamleader status intentieverklaring: or-id={}, company={}".format(
                self.process.id,
                self.or_id,
                company['id']
            )
        )
        company = self.set_cp_status(company, 'pending')
        company = self.set_intentieverklaring(company, 'pending')
        company = self.set_toestemming_start(company, False)
        company = self.set_swo(company, False)

        return company

    def find_organization(self, or_id):
        ldap_org = self.ldap.find_company(or_id)
        if not ldap_org:
            logger.info(f"ERROR in process: LDAP OR-ID not found {or_id}")
            self.slack.no_ldap_entry_found(self.dossier)
            return

        return ldap_org

    def update_company_status(self, status_update_method):
        ldap_org = self.find_organization(self.or_id)
        if not ldap_org:
            return

        company_id = ldap_org['x-be-viaa-externalUUID'].value
        company = self.tlc.get_company(company_id)
        if not company:
            self.slack.company_not_found(company_id, self.or_id)
            return

        company = status_update_method(company)
        self.tlc.update_company(company)
        return

    def teamleader_update(self):
        process_definition = self.process.processDefinitionKey
        if self.action == "ended" and process_definition == "so_ondertekenproces":
            self.update_company_status(self.set_status_ondertekenproces)
            return

        if self.action == "created" and process_definition == "Intentieverklaring_v2":
            self.update_company_status(self.set_status_intentieverklaring)
            return

        logger.info(f"Process: skipping action={self.action} and process definition={process_definition}")

    def handle_event(self, process_body: ProcessBody):
        self.body = process_body
        self.dossier = self.body.dossier
        self.process = self.body.process
        self.action = self.body.action
        self.or_id = self.dossier.externalId

        # enkel behandeling type dossier 'contentpartner'
        if self.dossier.dossierDefinition != self.SKRYV_DOSSIER_CP_ID:
            logger.info(
                f"Skipping {self.dossier.dossierDefinition}, it's not a CP process"
            )
            return

        if(self.or_id):
            self.teamleader_update()
        else:
            self.slack.external_id_empty(self.dossier)
