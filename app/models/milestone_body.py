#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/models/milestone_body.py
#
#   Proces model using pydantic for field validation
#

from pydantic import BaseModel, Field
from app.models.dossier import Dossier
from app.models.milestone import Milestone


class MilestoneBody(BaseModel):
    action: str = Field(
        ..., description="type of milestone event ex. reached"
    )
    dossier: Dossier
    milestone: Milestone

    class Config:
        schema_extra = {
            "example": {
                "action": "reached",
                "dossier": {
                    "id": "471a7f96-ad00-42e8-817a-f1c616f17b1e",
                    "label": "S.M.A.K.",
                    "externalId": "OR-np1wh8z",
                    "dossierManager": "33aeb47c-d027-1036-8f5f-d369bf7ac4f1",
                    "dossierDefinition": "90d24d34-b5b3-4942-8504-b6d76dd86ccb",
                    "createdAt": "2022-05-06T08:20:03.000+0000",
                    "updatedAt": "2022-05-09T14:30:55.000+0000",
                    "creator": "33aeb47c-d027-1036-8f5f-d369bf7ac4f1",
                    "active": True
                },
                "milestone": {
                    "id": "5910ec02-b183-49b8-840d-2cdea9c6e4df",
                    "dossierId": "a66d34fd-537c-4a64-9840-b7de4e6018cb",
                    "key": "IntermediateThrowEvent_DS_ITV_akkoordITVgeenopstart",
                    "status": "Akkoord, geen opstart",
                    "timestamp": "2022-05-23T13:22:29.755Z"
                }
            }
        }
