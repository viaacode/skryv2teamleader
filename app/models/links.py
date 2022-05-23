#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/models/document_value.py
#
#   Thisi is nested in Document model
#

from pydantic import BaseModel, Field


class Links(BaseModel):
    value: str = Field(..., description="todo somehow model links here")
    # value: dict = Field(..., description="dictionary with key values for inside document")

# TODO figure out how to make array of links here
#
#   "links": [
#     {
#       "linkType": "SCOPE",
#       "resourceType": "PROCESS",
#       "resourceId": "63ef5368-d843-11ec-8ff2-0242c0a8e003"
#     },
#     {
#       "linkType": "LINK",
#       "resourceType": "DOSSIER",
#       "resourceId": "14722c4e-3c36-48e2-86c6-e9fe09952a5d"
#     }
#   ],
