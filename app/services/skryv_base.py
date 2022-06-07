#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/services/skryv_base.py
#
#   Used by DocumentService, ProcessService and MilestoneService to read in config
#   variables and have a mapping of custom fields.
#

from viaa.configuration import ConfigParser
import uuid


class SkryvBase:
    def read_configuration(self):
        config = ConfigParser()
        self.skryv_config = config.app_cfg['skryv']
        self.SKRYV_DOSSIER_CP_ID = uuid.UUID(
            self.skryv_config['dossier_content_partner_id']
        )

        self.custom_fields = self.custom_field_mapping(
            config.app_cfg['custom_field_ids']
        )

    def custom_field_mapping(self, field_ids):
        print("field_ids=", field_ids)
        self.custom_fields = {}
        for f in self.tlc.list_custom_fields():
            for f_label, f_id in field_ids.items():
                if f['id'] == f_id:
                    self.custom_fields[f_label] = f
                    # helpful print of mapping for debugging
                    print(f"custom_fields[{f_label}]={f}")

        return self.custom_fields

    def get_custom_field(self, company, field_name):
        for f in company['custom_fields']:
            if f['definition']['id'] == self.custom_fields[field_name]['id']:
                return f['value']

    def set_custom_field(self, company, field_name, value):
        for f in company['custom_fields']:
            if f['definition']['id'] == self.custom_fields[field_name]['id']:
                f['value'] = value

        return company
