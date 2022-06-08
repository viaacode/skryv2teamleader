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


class ProcessService(SkryvBase):
    def __init__(self, common_clients):
        self.tlc = common_clients.teamleader
        self.ldap = common_clients.ldap
        self.slack = common_clients.slack
        self.redis = common_clients.redis
        self.read_configuration()

    def doc_postadres(self, document_body):
        dvals = document_body.document.document.value
        if 'adres_en_contactgegevens' in dvals:
            return dvals['adres_en_contactgegevens']['postadres']

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

        print("TODO: save adres = ", self.doc_postadres(document))

        addendums = self.get_addendums(document)
        if not addendums:
            print("no addendums found in document")
            return company

        tl_addendums = []
        for ad in addendums:
            ad_naam = ad['naam']['Specifieke addenda']
            tl_addendums.append(
                tl_swo_map.get(ad_naam)
            )

        print("set_swo_addenda = ", tl_addendums)
        company = self.set_swo_addenda(company, tl_addendums)

        return company

    def status_update(self, company):
        # if process is ended, and we get here, all checks passed
        # also fetch related document, and set all flags to ja and true:
        company = self.set_cp_status(company, 'ja')
        company = self.set_toestemming_start(company, True)
        company = self.set_swo(company, True)

        updated_document_json = self.redis.load_document(self.dossier.id)
        if updated_document_json:
            company = self.addendums_update(
                company,
                DocumentBody.parse_raw(updated_document_json)
            )
        else:
            print("ERROR: addendum update, could not find dossier id=",
                  self.dossier.id)

        return company

    def teamleader_update(self):
        ldap_org = self.ldap.find_company(self.or_id)
        if not ldap_org:
            print(
                f"process: LDAP OR-ID not found {self.or_id} for action {self.action}")
            self.slack.no_ldap_entry_found(self.dossier)
            return

        company_id = ldap_org['x-be-viaa-externalUUID'].value

        print(
            "process ({}) -> teamleader update: or-id={}, TL uuid={}, process action={}".format(
                self.process.id,
                self.or_id,
                company_id,
                self.action
            )
        )

        # enkel behandeling type dossier 'contentpartner'
        # https://meemoo.atlassian.net/wiki/spaces/IK/pages/818086103/contract.meemoo.be+en+Teamleader+skryv2crm
        if self.dossier.dossierDefinition != self.SKRYV_DOSSIER_CP_ID:
            print(
                f"{self.dossier.dossierDefinition} is not a content partner process, skipping process event")
            return

        if self.action == "ended":
            if self.process.processDefinitionKey == "so_ondertekenproces":
                company = self.tlc.get_company(company_id)
                company = self.status_update(company)
                self.tlc.update_company(company)

    def handle_event(self, process_body: ProcessBody):
        self.body = process_body
        self.dossier = self.body.dossier
        self.process = self.body.process
        self.action = self.body.action
        self.or_id = self.dossier.externalId

        if(self.or_id):
            self.teamleader_update()
        else:
            self.slack.external_id_empty(self.dossier)
