#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/services/skryv_base.py
#
#   Used by DocumentService, ProcessService and MilestoneService to read in config
#   variables and have a mapping of custom fields.
#   We also add some shared helpers to set custom fields here in order to save back
#   to teamleader
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
                    print(f"custom_fields[{f_label}]={f}")  # debug

        return self.custom_fields

    # method not used yet, might be handy soon:
    # def get_custom_field(self, company, field_name):
    #     for f in company['custom_fields']:
    #         if f['definition']['id'] == self.custom_fields[field_name]['id']:
    #             return f['value']

    def set_custom_field(self, company, field_name, value):
        for f in company['custom_fields']:
            if f['definition']['id'] == self.custom_fields[field_name]['id']:
                f['value'] = value

        return company

    def set_cp_status(self, company, value):
        # 2.2 CP status -> 'ja', 'nee', 'pending'
        allowed_values = ['ja', 'nee', 'pending']
        if value not in allowed_values:
            print("skipping cp_status, invalued value=", value)
            return company

        return self.set_custom_field(company, 'cp_status', value)

    def set_intentieverklaring(self, company, value):
        # 2.3 intentieverklaring -> 'ingevuld', 'pending'
        allowed_values = ['ingevuld', 'pending']

        if value not in allowed_values:
            print("skipping invalid intentieverklaring value=", value)

        return self.set_custom_field(company, 'intentieverklaring', value)

    def set_toestemming_start(self, company, value):
        # 2.4 Toestemming starten -> True, False
        if value:
            value = True
        else:
            value = False

        return self.set_custom_field(company, 'toestemming_starten', value)

    def set_swo(self, company, value):
        # 2.5 SWO -> True, False
        if value:
            value = True
        else:
            value = False

        return self.set_custom_field(company, 'swo', value)

    def set_swo_addenda(self, company, addenda_list):
        # In group 5 LDAP (niet in group 2 Content Partner)
        # 2.6 SWO addenda : values:
        #
        # 'GDPR protocol'
        # 'GDPR overeenkomst'
        # 'Dienstverlening kunstwerken erfgoedobjecten topstukken'
        # 'Specifieke voorwaarden'
        # 'Topstukkenaddendum'

        allowed_addenda = self.custom_fields.get(
            'swo_addenda')['configuration']['options']
        for d in addenda_list:
            if d not in allowed_addenda:
                print(
                    "skipping set_swo_addenda because we get an invalid addenda value d=", d
                )
                return company

        return self.set_custom_field(company, 'swo_addenda', addenda_list)
