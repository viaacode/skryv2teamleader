#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/models/sync_params.py
#
#   Contact and Company sync parameters
#
from pydantic import BaseModel, Field
from datetime import datetime


class SyncParams(BaseModel):
    modified_since: datetime = Field(
        None,
        description="Syncronize since given iso date (optional parameter)"
    )
    full_sync: bool = Field(
        False,
        description="""
        True synchronizes all records.
        False synchronize records since the modified_since date.
        Setting full_sync to False and not specifying modified_since is allowed,
        in this case current_date - 2 days is taken as starting date.
        """
    )

    class Config:
        schema_extra = {
            "example": {
                "modified_since": "2020-05-09T00:00:00",
                "full_sync": False
            }
        }
