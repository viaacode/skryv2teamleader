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


class DocumentValue(BaseModel):
    value: dict = Field(...,
                        description="dictionary with key values for inside document")

# Example:
# "document": {
#     "value": {
#         "raadpleeg_hier_de_samenwerkingsovereenkomst_met_viaa": "https://s3.meemoo.docx"
#     }
# }
