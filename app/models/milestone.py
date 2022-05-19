#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/models/milestone.py
#
#   Milestone model using pydantic for field validation
#

from pydantic import BaseModel, Field
from app.models.subject import Subject
from app.models.account import Account


class Milestone(BaseModel):
    type: str = Field(
        ...,
        description="Type of milestone... "
    )
    subject: Subject
    account: Account

    class Config:
        schema_extra = {
            "example": {
                "type": "milestone_type",
                "subject": {
                    "type": "milestone",
                    "id": "8ac514fc-9247-0280-be7c-9ba5627c9b8d"
                },
                "account": {
                    "type": "account",
                    "id": "7159d591-1ecc-01c7-ad5f-341091d12f60"
                }
            }
        }
