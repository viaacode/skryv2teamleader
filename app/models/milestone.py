#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/models/milestone.py
#
#   Milestone model using pydantic for field validation
#

import uuid
from pydantic import BaseModel, Field
from datetime import datetime


class Milestone(BaseModel):
    id: uuid.UUID = Field(..., description="process uuid")
    dossierId: uuid.UUID = Field(..., description="dossier uuid")
    key: str = Field(...,
                     description="IntermediateThrowEvent_DS_ITV_akkoordITVgeenopstart")
    status: str = Field(..., description="milestone status")
    timestamp: datetime = Field(
        None,
        description="Milestone timestamp"
    )
