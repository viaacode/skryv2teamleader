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


class Process(BaseModel):
    id: uuid.UUID = Field(..., description="process uuid")
    businessKey: uuid.UUID = Field(..., description="businessKey uuid")
    processDefinitionId: str = Field(...,
                                     description="Intentieverklaring_v2:id")
    processDefinitionKey: str = Field(..., description="Intentieverklaring_v2")
    startTime: datetime = Field(
        None,
        description="Syncronize since given iso date (optional parameter)"
    )
    startActivityId: str = Field(..., description="StartEvent_10e")
