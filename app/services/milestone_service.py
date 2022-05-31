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


class MilestoneService:
    def __init__(self, common_clients):
        self.tlc = common_clients.teamleader
        self.ldap = common_clients.ldap
        self.slack = common_clients.slack

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
