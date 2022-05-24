#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/services/milestone_service.py
#
#   MilestoneService, handle milestone webhook events
#


class MilestoneService:
    def __init__(self, milestone_body):
        self.body = milestone_body 
        self.action = self.body.action
        self.dossier = self.body.dossier
        self.milestone = self.body.milestone

    def handle_event(self):
        print("handling milestone id={} status={}".format(
                self.milestone.id,
                self.milestone.status
            )
        )

