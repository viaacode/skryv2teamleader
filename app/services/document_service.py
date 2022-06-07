#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/services/document_service.py
#
#   DocumentService, handle document webhook events
#   This skips briefing type, only process the content partner dossiers
#   We fetch addendums, postadres and other fields to update in teamleader.
#   ldap_client is used to lookup or-id and map to correct teamleader id.
#
#   In case of errors, we use slack client to post messages on #skryvbot
#

from app.models.document_body import DocumentBody
from app.services.skryv_base import SkryvBase


class DocumentService(SkryvBase):
    def __init__(self, common_clients):
        self.tlc = common_clients.teamleader
        self.ldap = common_clients.ldap
        self.slack = common_clients.slack
        self.read_configuration()

    def doc_postadres(self):
        dvals = self.document.document.value
        if 'adres_en_contactgegevens' in dvals:
            return dvals['adres_en_contactgegevens']['postadres']

    def doc_addendums(self):
        dvals = self.document.document.value
        if 'te_ondertekenen_documenten' in dvals:
            tod = dvals['te_ondertekenen_documenten']
            if 'addendum' in tod:
                return tod['addendum']

    def addendums_update(self, company):
        addendums = self.doc_addendums()
        if not addendums:
            return company

        # TODO: update some field in company here!
        for ad in addendums:
            print("addendum=", ad)

        # In group 5 LDAP (niet in group 2 Content Partner)
        # 2.6 SWO addenda : values:
        #   'GDPR protocol'
        #   'GDPR overeenkomst'
        #   'Aanduiding contentpartners (koepel)'
        #   'Dienstverlening kunstwerken erfgoedobjecten topstukken'
        #   'Specifieke voorwaarden'
        #   'Topstukkenaddendum'

        # company = self.set_custom_field(
        #     company, 'swo_addenda', []  # addendums here...
        # )

        return company

    def status_update(self, company):
        # TODO: use self.document to set correct values here!

        # 2.2 CP status -> 'ja', 'nee', 'pending'
        company = self.set_custom_field(
            company, 'cp_status', 'ja'
        )

        # 2.3 intentieverklaring -> 'ingevuld', 'pending'
        # company = self.set_custom_field(
        #     company, 'intentieverklaring', 'ingevuld'
        # )

        # 2.4 Toestemming starten -> True, False
        company = self.set_custom_field(
            company, 'toestemming_starten', True
        )

        # 2.5 SWO -> True, False
        company = self.set_custom_field(
            company, 'swo', True
        )

        company = self.addendums_update(company)
        return company

    def company_document_update_samenwerkingsovereenkomst():
        pass
        # TODO: port this to python
        # https://github.com/viaacode/skryv2crm/blob/6f31782e47eaba08265a34ae109518eb417127d0/src/main/app/crm.xml#L47

    def company_document_set_api_fields_comment():
        pass
        # https://github.com/viaacode/skryv2crm/blob/6f31782e47eaba08265a34ae109518eb417127d0/src/main/app/crm.xml#L156

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

        tl_company = self.tlc.get_company(company_id)
        # print("teamleader company to update==",
        #       json.dumps(tl_company))

        if self.action == 'updated':
            print("adres=", self.doc_postadres())
            tl_company = self.status_update(tl_company)
            self.tlc.update_company(tl_company)

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
