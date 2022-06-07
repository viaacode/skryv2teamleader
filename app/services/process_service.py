#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/services/process_service.py
#
#   ProcessService, handle process webhook events
#

from app.models.process_body import ProcessBody
from app.services.skryv_base import SkryvBase


class ProcessService(SkryvBase):
    def __init__(self, common_clients):
        self.tlc = common_clients.teamleader
        self.ldap = common_clients.ldap
        self.slack = common_clients.slack
        self.read_configuration()

    def status_update(self, company):
        print(f"TODO: check SWO akkoord in dossier {self.dossier.id}")

        # TODO: store dossier update in redis and retreive here!
        # this to get the boolean swo_akkourd out of the full dossier
        # which we don't get in this process ended event (only the uuid)
        swo_akkoord = True

        if swo_akkoord:
            # 2.2 CP status -> 'ja', 'nee', 'pending'
            company = self.set_custom_field(
                company, 'cp_status', 'ja'
            )

            # 2.4 Toestemming starten -> True, False
            company = self.set_custom_field(
                company, 'toestemming_starten', True
            )

            # 2.5 SWO -> True, False
            company = self.set_custom_field(
                company, 'swo', True
            )

            # this also only works with fetching full dossier from redis
            # company = self.addendums_update(company)

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
