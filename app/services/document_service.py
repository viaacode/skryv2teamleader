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

    def company_document_update_samenwerkingsovereenkomst_eind():
        pass
        # TODO: convert this to python:
        # https://github.com/viaacode/skryv2crm/blob/6f31782e47eaba08265a34ae109518eb417127d0/src/main/app/crm.xml#L20

        # <sub-flow name="crm_company_document_update_samenwerkingsovereenkomst_eind">
        #         <choice doc:name="Check if getekende documenten">
        #             <when expression="#[flowVars.getekende_versie == null]">
        #                 <set-variable variableName="skip_event" value="true" doc:name="skip_event"/>
        #             </when>
        #             <otherwise>
        #                 <dw:transform-message doc:name="Ja - 7a - Update Samenwerkingsovereenkomst">
        #                     <dw:set-payload><![CDATA[%dw 1.0
        # %output application/java
        # ---
        # { api_group : p('teamleader.api_group'),
        #   api_secret : p('teamleader.api_secret'),
        #   track_changes : "1",
        #   company_id : flowVars.company_id,
        #   ("custom_field_" ++ p('teamleader.company.cp_status')) : p('teamleader.company.cp_status.ja'),
        #   ("custom_field_" ++ p('teamleader.company.actief')) : p('teamleader.company.actief.nee'),
        #   ("custom_field_" ++ p('teamleader.company.comment_intentieverklaring')) : "",
        #   ("custom_field_" ++ p('teamleader.company.toestemming_starten')) : "1",
        #   ("custom_field_" ++ p('teamleader.company.samenwerkingsovereenkomst')) : "1"
        # }]]></dw:set-payload>
        #                 </dw:transform-message>
        #             </otherwise>
        #         </choice>
        #     </sub-flow>

    def company_document_update_samenwerkingsovereenkomst():
        pass
        # TODO: port this to python
        # https://github.com/viaacode/skryv2crm/blob/6f31782e47eaba08265a34ae109518eb417127d0/src/main/app/crm.xml#L47

    def company_document_get_dragers_golf():
        pass
        # TODO: port this to python
        # https://github.com/viaacode/skryv2crm/blob/6f31782e47eaba08265a34ae109518eb417127d0/src/main/app/crm.xml#L104

    def company_document_set_api_fields_drager_golf():
        pass
        # TODO
        # https://github.com/viaacode/skryv2crm/blob/6f31782e47eaba08265a34ae109518eb417127d0/src/main/app/crm.xml#L185

    def company_document_set_api_fields_comment():
        pass
        # https://github.com/viaacode/skryv2crm/blob/6f31782e47eaba08265a34ae109518eb417127d0/src/main/app/crm.xml#L156

    def company_document_set_api_fields():
        pass
        # https://github.com/viaacode/skryv2crm/blob/6f31782e47eaba08265a34ae109518eb417127d0/src/main/app/crm.xml#L440

    def status_update(self):
        pass
        # 2.2 CP status -> ja, nee, pending
        # 2.3 intentieverklaring -> ingevuld, pending
        # 2.4 Toestemming starten -> true,false
        # SWO -> true,false
        # SWO addenda -> GDPR protocol,
        #                GDPR overeenkomst,
        #                Aanduiding contentpartners,
        #                Dienstverlening kunstwerken erfgooed,
        #                addendum op maat

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

        tl_org_uuid = ldap_org['x-be-viaa-externalUUID'].value

        print(
            "document teamleader update: or-id={}, TL uuid={}, document label={}, action={}".format(
                self.or_id,
                tl_org_uuid,
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
            print("adres=", self.doc_postadres())
            print("addendums=", self.doc_addendums())

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
