#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/models/document.py
#
#   Document model using pydantic for field validation
#

from pydantic import BaseModel, Field
from app.models.subject import Subject
from app.models.account import Account


class Document(BaseModel):
    type: str = Field(
        ...,
        description="Type of document: contract, serviceagreement "
    )
    subject: Subject
    account: Account

    class Config:
        schema_extra = {
            "example": {
                "type": "contract",
                "subject": {
                    "type": "document",
                    "id": "8ac514fc-9247-0280-be7c-9ba5627c9b8d"
                },
                "account": {
                    "type": "account",
                    "id": "7159d591-1ecc-01c7-ad5f-341091d12f60"
                }
            }
        }
