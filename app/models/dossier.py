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
from typing import Optional
from datetime import datetime


class Dossier(BaseModel):
    id: uuid.UUID = Field(..., description="dossier uuid")
    label: str = Field(..., description="dossier label")
    externalId: Optional[str] = None
    dossierManager: Optional[uuid.UUID] = None
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
    creator: str = Field(..., description="dossier creator")
    active: bool = Field(..., description="active true/false")
    communications: Optional[list] = []
