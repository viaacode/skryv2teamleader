#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/models/document_body.py
#
#   Document model using pydantic for field validation
#

from pydantic import BaseModel, Field
from app.models.dossier import Dossier
from app.models.document import Document


class DocumentBody(BaseModel):
    action: str = Field(
        ..., description="type of document event ex. created"
    )
    dossier: Dossier
    document: Document

    class Config:
        schema_extra = {
            "example": {
                "action": "updated",
                "dossier": {
                    "id": "471a7f96-ad00-42e8-817a-f1c616f17b1e",
                    "label": "S.M.A.K.",
                    "externalId": "OR-np1wh8z",
                    "dossierDefinition": "90d24d34-b5b3-4942-8504-b6d76dd86ccb",
                    "createdAt": "2022-03-04T08:08:14.000+00:00",
                    "updatedAt": "2022-03-04T08:08:14.000+00:00",
                    "creator": "Tine Philips",
                    "active": True
                },
                "document": {
                    "id": "bb11836c-78d5-4c3c-8488-87ee99c0c504",
                    "version": 1,
                    "definition": "8980be8c-3b75-46ab-ab4e-abc38757b29d",
                    "definitionLabel": "Intentieverklaring meemoo V2",
                    "definitionKey": "intentieverklaring_viaa_v2",
                    "readOnly": False,
                    "document": {
                        "value": {
                            "raadpleeg_hier_de_samenwerkingsovereenkomst_met_viaa": "https://meemoo.docx"
                        },
                        "bedrijfsvorm": {
                            "selectedOption": "cvba"
                        }
                    },
                    "createdAt": "2022-05-20T13:47:34.000+00:00",
                    "updatedAt": "2022-05-20T13:47:34.000+00:00",
                    "links": [
                        {
                            "linkType": "SCOPE",
                            "resourceType": "PROCESS",
                            "resourceId": "63ef5368-d843-11ec-8ff2-0242c0a8e003"
                        },
                        {
                            "linkType": "LINK",
                            "resourceType": "DOSSIER",
                            "resourceId": "14722c4e-3c36-48e2-86c6-e9fe09952a5d"
                        }
                    ],
                    "subdocument": False
                }
            }
        }
