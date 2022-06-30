#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/api/routers/skryv.py
#
#   Webhook calls for Skryv.
#   Proces, Milestone and Document webhooks will by called by Skryv and trigger
#   updates to teamleader.
#

from fastapi import APIRouter
from app.app import main_app as app
from app.models.process_body import ProcessBody
from app.models.milestone_body import MilestoneBody
from app.models.document_body import DocumentBody

router = APIRouter()

# teamleader oauth call


@router.get("/oauth")
def auth_callback(code: str, state: str = ''):
    return app.auth_callback(code, state)


@router.post("/process")
def process(process_data: ProcessBody):
    return app.process_webhook(process_data)


@router.post("/milestone")
def milestone(ml_body: MilestoneBody):
    return app.milestone_webhook(ml_body)


@router.post("/document")
def document(doc: DocumentBody):
    return app.document_webhook(doc)
