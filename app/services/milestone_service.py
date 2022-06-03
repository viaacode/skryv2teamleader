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
from viaa.configuration import ConfigParser


class MilestoneService:
    def __init__(self, common_clients):
        self.tlc = common_clients.teamleader
        self.ldap = common_clients.ldap
        self.slack = common_clients.slack
        config = ConfigParser()
        self.skryv_config = config.app_cfg['skryv']
        self.SKRYV_DOSSIER_CP_ID = self.skryv_config['dossier_content_partner_id']

    # https://github.com/viaacode/skryv2crm/blob/6f31782e47eaba08265a34ae109518eb417127d0/src/main/app/crm.xml#L341
    def company_milestone_set_api_fields():
        pass

    def teamleader_update(self):
        ldap_org = self.ldap.find_company(self.or_id)
        if not ldap_org:
            self.slack.no_ldap_entry_found(self.dossier)
            return

        tl_org_uuid = ldap_org['x-be-viaa-externalUUID'].value

        print(
            "milestone ({}) -> teamleader update: or-id={}, TL uuid={}, milestone status={} action={}".format(
                self.milestone.id,
                self.or_id,
                tl_org_uuid,
                self.milestone.status,
                self.action
            )
        )
        # TODO make calls to ldap and update teamleader here based on milestone status and action

        # QAS value, todo in env var
        SKRYV_DOSSIER_CP_ID = '90d24d34-b5b3-4942-8504-b6d76dd86ccb'
        if self.dossier.dossierDefinition != SKRYV_DOSSIER_CP_ID:
            print(
                f"{self.dossier.dossierDefinition} is not a content partner milestone, skipping milestone event")
            return

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
