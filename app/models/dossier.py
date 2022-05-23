#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/models/process.py
#
#   Used in processbody
#
import uuid
from pydantic import BaseModel, Field
from datetime import datetime


class Dossier(BaseModel):
    id: uuid.UUID = Field(..., description="dossier uuid")
    label: str = Field(..., description="dossier label")
    externalId: str = Field(..., description="or id from organization")
    dossierManager: uuid.UUID = Field(...,
                                      description="dossier manager (optional)")
    dossierDefinition: uuid.UUID = Field(...,
                                         description="dossier definition uuid")
    createdAt: datetime = Field(
        None,
        description="Syncronize since given iso date (optional parameter)"
    )
    updatedAt: datetime = Field(
        None,
        description="Syncronize since given iso date (optional parameter)"
    )
    creator: uuid.UUID = Field(..., description="dossier definition uuid")
    active: bool = Field(..., description="active true/false")
