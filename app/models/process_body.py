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
                "action": "created",
                "dossier": {
                    "id": "25cf6caf-d4eb-49e2-80f3-9fde8eaccd19",
                    "label": "Test Skryv",
                    "externalId": "OR-hx15s8s",
                    "dossierDefinition": "90d24d34-b5b3-4942-8504-b6d76dd86ccb",
                    "createdAt": "2022-05-19T09:17:15.000+0000",
                    "updatedAt": "2022-05-19T09:17:19.000+0000",
                    "creator": "f440f460-51e0-1034-9c23-ff9471efe8a8",
                    "active": True
                },
                "process": {
                    "id": "5004eee8-da97-11ec-883a-0242ac130004",
                    "businessKey": "25cf6caf-d4eb-49e2-80f3-9fde8eaccd19",
                    "processDefinitionId": "Intentieverklaring_v2:16:b8d43a62-d695-11ec-a5e9-0242c0a8e002",
                    "processDefinitionKey": "Intentieverklaring_v2",
                    "startTime": "2022-05-23T12:53:16.000+0000",
                    "startActivityId": "StartEvent_10e3ss5"
                }
            }
        }
