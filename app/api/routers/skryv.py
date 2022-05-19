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
# from app.models.contact import Contact
# from app.models.company import Company
# import uuid
from app.models.proces import Proces
from app.models.milestone import Milestone
from app.models.document import Document

router = APIRouter()

# teamleader oauth call
@router.get("/oauth")
def auth_callback(code: str, state: str = ''):
    result = app.auth_callback(code, state)
    return result


@router.post("/proces")
def proces(data: Proces):
    return app.proces_webhook(data)


@router.post("/milestone")
def milestone(data: Milestone):
    return app.milestone_webhook(data)


@router.post("/document")
def document(data: Document):
    return app.document_webhook(data)

