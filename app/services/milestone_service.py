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
        print(
            "milestone ({}) -> teamleader update: or-id={}, company={}, milestone status={} action={}".format(
                self.milestone.id,
                self.or_id,
                company['id'],
                milestone_status,
                self.action
            )
        )

        status_actions = {
            'Geen interesse': self.status_geen_interesse,
            'Misschien later samenwerking': self.status_misschien_later,
            'Akkoord en opstart': self.status_akkoord,
            'Akkoord, geen opstart': self.status_akkoord_geen_start,
            'Interesse, niet akkoord SWO': self.status_interesse
        }

        if milestone_status not in status_actions:
            # geen actie bij deze milestone status: "SWO niet akkoord"
            # by deze status is SWO wel ok
            print(
                f"warning, skipped status update voor milestone status={milestone_status}")
            # change to return company if teamleader_update does other changes...
            return

        perform_status_update = status_actions.get(milestone_status)
        company = perform_status_update(company)
        self.tlc.update_company(company)
        # return company

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

        self.status_update(company, self.milestone.status)

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
