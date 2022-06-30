#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/services/document_service.py
#
#   DocumentService, handle document webhook events and
#   store updated_document in redis for later use in milestones and process events
#   This skips briefing type, only process the content partner dossiers
#   In case of errors, we use slack client to post messages on #skryvbot
#

from app.models.document_body import DocumentBody
from app.services.skryv_base import SkryvBase

from viaa.configuration import ConfigParser
from viaa.observability import logging

config = ConfigParser()
logger = logging.get_logger(__name__, config=config)


class DocumentService(SkryvBase):
    def __init__(self, common_clients):
        self.tlc = common_clients.teamleader
        self.ldap = common_clients.ldap
        self.slack = common_clients.slack
        self.redis = common_clients.redis
        self.read_configuration()

    def save_cp_updated_document(self, document_body):
        if self.action != 'updated':
            logger.info(
                f"skipping document {self.action}, waiting for document 'updated' action..."
            )
            return

        # store updated document in redis for a following milestone or process webhook:
        logger.info(
            f"saving document {self.dossier.id} in redis for organization {self.or_id}"
        )
        self.redis.save_document(document_body)

    def handle_event(self, document_body: DocumentBody):
        body = document_body
        self.action = body.action
        self.document = body.document
        self.dossier = body.dossier
        self.or_id = self.dossier.externalId

        # enkel behandeling type dossier 'contentpartner', skip briefing en anderen
        if self.dossier.dossierDefinition != self.SKRYV_DOSSIER_CP_ID:
            logger.info(
                f"{self.dossier.dossierDefinition} is not a CP document, skip event"
            )
            return

        if(self.or_id):
            self.save_cp_updated_document(document_body)
        else:
            self.slack.external_id_empty(self.dossier)
