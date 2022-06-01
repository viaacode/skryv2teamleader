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

    # https://github.com/viaacode/skryv2crm/blob/6f31782e47eaba08265a34ae109518eb417127d0/src/main/app/crm.xml#L285
    def company_process_set_api_fields():
        pass

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

        SKRYV_DOSSIER_CP_ID = 'some_uuid_here'
        if self.dossier.dossierDefinition != SKRYV_DOSSIER_CP_ID:
            print(
                f"{self.dossier.dossierDefinition} is not a content partner process, skipping process event")
            return

        # TODO make calls to ldap and update teamleader here based on process action

        # TODO: figure out why in the original skryv2crm they use skryv api call to fetch a document
        # for this they get a token using skryv.username&pass to featch an oauth Bearer token, which
        # is passed in header to a route:
        #   /api/dossiers/{id}
        # some fixed id is present with value f281edf1-b706-4f14-8c57-5d139d0e0d21
        # https://github.com/viaacode/skryv2crm/blob/master/src/main/app/skryv.xml#L325

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
