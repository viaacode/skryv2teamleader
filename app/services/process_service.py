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


class ProcessService:
    def __init__(self, common_clients):
        self.tlc = common_clients.teamleader
        self.ldap = common_clients.ldap
        self.slack = common_clients.slack

    def teamleader_update(self):
        ldap_org = self.ldap.find_company(self.or_id)
        if not ldap_org:
            print(
                f"process: LDAP OR-ID not found {self.or_id} for action {self.action}")
            self.slack.no_ldap_entry_found(self.dossier)
            return

        tl_org_uuid = ldap_org['x-be-viaa-externalUUID'].value

        print(
            "process ({}) -> teamleader update: or-id={}, TL uuid={}, process action={}".format(
                self.process.id,
                self.or_id,
                tl_org_uuid,
                self.action
            )
        )
        # TODO make calls to ldap and update teamleader here based on process action

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
