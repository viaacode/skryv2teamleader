#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/models/process_body.py
#
#   Proces model using pydantic for field validation
#

from pydantic import BaseModel, Field
from app.models.dossier import Dossier
from app.models.process import Process


class ProcessBody(BaseModel):
    action: str = Field(
        ..., description="type of process event created, updated,... "
    )
    dossier: Dossier
    process: Process

    class Config:
        schema_extra = {
            "example": {
                "action": "ended",
                "dossier": {
                    "id": "14722c4e-3c36-48e2-86c6-e9fe09952a5d",
                    "label": "S.M.A.K.",
                    "externalId": "OR-np1wh8z",
                    "dossierDefinition": "90d24d34-b5b3-4942-8504-b6d76dd86ccb",
                    "createdAt": "2022-06-03T09:16:37.000+0000",
                    "updatedAt": "2022-06-03T09:16:38.000+0000",
                    "creator": "33aeb47c-d027-1036-8f5f-d369bf7ac4f1",
                    "active": True
                },
                "process": {
                    "id": "554e1fef-e31e-11ec-883a-0242ac130004",
                    "businessKey": "471a7f96-ad00-42e8-817a-f1c616f17b1e",
                    "processDefinitionId": "so_ondertekenproces:16:b8ca9d6b-d695-11ec-a5e9-0242c0a8e002",
                    "processDefinitionKey": "so_ondertekenproces",
                    "startTime": "2022-06-03T09:19:56.000+0000",
                    "endTime": "2022-06-03T09:27:01.000+0000",
                    "durationInMillis": 424691,
                    "startActivityId": "StartEvent_1"
                }
            }
        }
