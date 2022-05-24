#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/models/document.py
#
#   Used in document_body
#

import uuid
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.models.document_value import DocumentValue


class Document(BaseModel):
    id: uuid.UUID = Field(..., description="document uuid")
    version: int = Field(..., description="document version")
    definition: uuid.UUID = Field(..., description="document definition uuid")
    definitionLabel: str = Field(..., description="document definition label")
    definitionKey: str = Field(..., description="document definition key")
    readOnly: bool = Field(..., description="read only true/false")
    document: DocumentValue
    createdAt: datetime = Field(
        None,
        description="Syncronize since given iso date (optional parameter)"
    )
    updatedAt: datetime = Field(
        None,
        description="Syncronize since given iso date (optional parameter)"
    )
    links: Optional[list] = []
    subdocument: bool = Field(..., description="subdocument true/false")
