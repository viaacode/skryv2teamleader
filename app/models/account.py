#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/models/account.py
#
#   Account model used by company and contacts
#
import uuid
from pydantic import BaseModel, Field


class Account(BaseModel):
    type: str = Field(..., description="account type is account")
    id: uuid.UUID = Field(..., description="Account uuid in teamleader")
