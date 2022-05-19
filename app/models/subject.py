#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/models/subject.py
#
#   Subject model used by Contact and Company models
#
import uuid
from pydantic import BaseModel, Field


class Subject(BaseModel):
    type: str = Field(..., description="subject type is company or contact")
    id: uuid.UUID = Field(
        ...,
        description="Company or contact uuid in teamleader"
    )
