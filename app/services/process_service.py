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
            print("no new, addendums found in document")
            return company

        # keep existing addenda from previous process
        tl_addendums = self.get_existing_addenda(company)
        print("existing company swo_addenda", tl_addendums)

        for ad in addendums:
            ad_naam = tl_swo_map.get(ad['naam']['Specifieke addenda'])
            if ad_naam and ad_naam not in tl_addendums:
                tl_addendums.append(
                    ad_naam
                )

        print("merged company swo_addenda = ", tl_addendums)
        company = self.set_swo_addenda(company, tl_addendums)

        return company

    def set_status_ondertekenproces(self, company):
        print(
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
            print(f"Missing or malformed dossier: {self.dossier.id} error: {e}")

        return company

    # TODO: double check if this process 'start event' is needed
    # ITV gestart -> sets cp_status == pending.
    def teamleader_update(self):
        if self.action != "ended":
            print("Skipping process with action {self.action}")
            return

        ldap_org = self.ldap.find_company(self.or_id)
        if not ldap_org:
            print(f"ERROR in process: LDAP OR-ID not found {self.or_id}")
            self.slack.no_ldap_entry_found(self.dossier)
            return

        # self.action == "ended"
        if self.process.processDefinitionKey == "so_ondertekenproces":
            company_id = ldap_org['x-be-viaa-externalUUID'].value
            company = self.tlc.get_company(company_id)
            if not company:
                self.slack.company_not_found(company_id, self.or_id)
                return

            company = self.set_status_ondertekenproces(company)
            self.tlc.update_company(company)

    def handle_event(self, process_body: ProcessBody):
        self.body = process_body
        self.dossier = self.body.dossier
        self.process = self.body.process
        self.action = self.body.action
        self.or_id = self.dossier.externalId

        # enkel behandeling type dossier 'contentpartner'
        if self.dossier.dossierDefinition != self.SKRYV_DOSSIER_CP_ID:
            print(f"Skipping {self.dossier.dossierDefinition}, it's not a CP process")
            return

        if(self.or_id):
            self.teamleader_update()
        else:
            self.slack.external_id_empty(self.dossier)
