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
        self.org_ids = common_clients.org_ids
        self.slack = common_clients.slack

    def teamleader_update(self):
        # TODO make calls to ldap and update teamleader here
        print(
            "handling milestone: id={} organization_id={} status={}".format(
                self.milestone.id,
                self.or_id,
                self.milestone.status
            )
        )

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
