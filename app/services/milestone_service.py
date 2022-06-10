#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/services/milestone_service.py
#
#   MilestoneService, handle milestone webhook events
#

from app.models.milestone_body import MilestoneBody
from app.models.document_body import DocumentBody
from app.services.skryv_base import SkryvBase


class MilestoneService(SkryvBase):
    def __init__(self, common_clients):
        self.tlc = common_clients.teamleader
        self.ldap = common_clients.ldap
        self.slack = common_clients.slack
        self.redis = common_clients.redis
        self.read_configuration()

    def status_geen_interesse(self, company):
        company = self.set_cp_status(company, 'nee')
        company = self.set_intentieverklaring(company, 'ingevuld')
        company = self.set_toestemming_start(company, False)
        return company

    def status_misschien_later(self, company):
        company = self.set_cp_status(company, 'pending')
        company = self.set_intentieverklaring(company, 'pending')
        company = self.set_toestemming_start(company, False)
        return company

    def status_akkoord(self, company):
        company = self.set_cp_status(company, 'ja')
        company = self.set_intentieverklaring(company, 'ingevuld')
        company = self.set_toestemming_start(company, True)
        return company

    def status_akkoord_geen_start(self, company):
        company = self.set_cp_status(company, 'ja')
        company = self.set_intentieverklaring(company, 'ingevuld')
        company = self.set_toestemming_start(company, False)
        return company

    def status_interesse(self, company):
        company = self.set_cp_status(company, 'pending')
        company = self.set_intentieverklaring(company, 'pending')
        company = self.set_toestemming_start(company, False)
        return company

    def status_update(self, company, milestone_status):
        status_actions = {
            'Geen interesse': self.status_geen_interesse,
            'Misschien later samenwerking': self.status_misschien_later,
            'Akkoord en opstart': self.status_akkoord,
            'Akkoord, geen opstart': self.status_akkoord_geen_start,
            'Interesse, niet akkoord SWO': self.status_interesse
        }

        if milestone_status not in status_actions:
            # this happens for "SWO niet akkoord" and "SWO akkoord"
            print(f"ignoring milestone status update for  {milestone_status}")
            return (False, company)

        perform_status_update = status_actions.get(milestone_status)
        company = perform_status_update(company)
        return (True, company)

    def get_postadres(self, document_body):
        dvals = document_body.document.document.value
        if 'adres_en_contactgegevens' in dvals:
            return dvals['adres_en_contactgegevens']['postadres']

    def company_dossier_update(self, document_body, company):
        print("TODO: save adres in tl company = ", self.get_postadres(document_body))
        return company

    def contacts_update(self, document_body, company):
        print(f"TODO: Contacts update here on document={document_body}")
        return company

    def teamleader_update(self):
        if self.dossier.dossierDefinition != self.SKRYV_DOSSIER_CP_ID:
            print(
                f"{self.dossier.dossierDefinition} is not a content partner milestone, skipping milestone event")
            return

        ldap_org = self.ldap.find_company(self.or_id)
        if not ldap_org:
            self.slack.no_ldap_entry_found(self.dossier)
            return

        company_id = ldap_org['x-be-viaa-externalUUID'].value
        company = self.tlc.get_company(company_id)
        if not company:
            # TODO: make slack message here
            print(
                f"ERROR: company id={company_id} not found in teamleader for org {self.or_id}")
            return

        status_changed, company = self.status_update(
            company, self.milestone.status)

        if status_changed:
            print(
                "milestone teamleader update: or-id={}, company={}, milestone status={} action={}".format(
                    self.or_id,
                    company['id'],
                    self.milestone.status,
                    self.action
                )
            )
            mdoc_json = self.redis.load_document(self.dossier.id)
            if mdoc_json:
                mdoc = DocumentBody.parse_raw(mdoc_json)
                company = self.company_dossier_update(mdoc, company)
                company = self.contacts_update(mdoc, company)
            else:
                print(f"milestone: no associated dossier found for id={self.dossier.id}")

            self.tlc.update_company(company)

    def handle_event(self, milestone_body: MilestoneBody):
        self.body = milestone_body
        self.action = self.body.action
        self.dossier = self.body.dossier
        self.milestone = self.body.milestone
        self.or_id = self.dossier.externalId

        if(self.or_id):
            self.teamleader_update()
        else:
            self.slack.external_id_empty(self.dossier)
