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
        # print("field_ids=", field_ids)
        self.custom_fields = {}
        for f in self.tlc.list_custom_fields():
            for f_label, f_id in field_ids.items():
                if f['id'] == f_id:
                    self.custom_fields[f_label] = f
                    # print(f"custom_fields[{f_label}]={f}")  # debug

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

    # deprecated, moest niet meer gezet worden van tine
    # def set_type_organisatie(self, company, value):
    #     return self.set_custom_field(company, 'type_organisatie', value)

    def set_facturatie_email(self, company, email_value):
        return self.set_custom_field(company, 'facturatie_email', email_value)

    def set_bestelbon(self, company, boolean_value):
        return self.set_custom_field(company, 'bestelbon', boolean_value)

    # TL_RELATIE_MEEMOO
    # relatie moet in custom field opgeslagen worden!
    # {
    #    "id": "d46ecfe6-4329-0573-a85b-9c7d27023dd7",
    #    "context": "contact",
    #    "type": "multi_select",
    #    "label": "2 - Relatie met meemoo",
    #    "group": "1 Algemeen",
    #    "required": false,
    #    "configuration": {
    #      "options": [
    #        "AIF contact",
    #        "AIF contactpersoon beeldbeheer",
    #        "AvO ambassadeur",
    #        "AvO communicatiecontact",
    #        "AvO contactpersoon CP",
    #        "AvO gebruiker",
    #        "centraal contactpersoon",
    #        "contactpersoon contract",
    #        "contactpersoon digitale instroom",
    #        "contactpersoon digitalisering film en AV",
    #        "contactpersoon GIVE-glasplaten",
    #        "contactpersoon GIVE-kranten",
    #        "contactpersoon GIVE-manuscripten",
    #        "contactpersoon GIVE-topstukken",
    #        "contactpersoon team interactie",
    #        "gedetacheerde leerkracht",
    #        "meemoo alumnus"
    #      ],
    #      "extra_option_allowed": true
    #    }
    #  },
    def set_relatie_meemoo(self, company, value):
        # OPGEPAST, FIX relatie_meemoo is multiselect!!!!
        # we moeten eerder een append doen hier!!!
        return self.set_custom_field(company, 'relatie_meemoo', value)


    # idem voor functie category moet ook custom field zijn:
    # {
    #    "id": "17348dda-11c7-0e35-855b-38a4e1123dd6",
    #    "context": "contact",
    #    "type": "single_select",
    #    "label": "1 - Functiecategorie",
    #    "group": "1 Algemeen",
    #    "required": false,
    #    "configuration": {
    #      "options": [
    #        "administratie",
    #        "archief en collectiebeheer",
    #        "beleid",
    #        "bestuur",
    #        "consultancy",
    #        "directie",
    #        "effectief lid",
    #        "IT en techniek",
    #        "kennis en onderzoek",
    #        "legal",
    #        "management",
    #        "marcom",
    #        "mediaproductie",
    #        "onderwijzend personeel",
    #        "pedagogische begeleider",
    #        "pers (geschreven)",
    #        "pers (tv)",
    #        "plaatsvervangend lid",
    #        "publiekswerking en educatie",
    #        "sales",
    #        "uitgever/auteur"
    #      ],
    #      "extra_option_allowed": true
    #    }
    #  },
    def set_functie_category(self, company, value):
        # single select, maar validate dat het goede optie is!
        return self.set_custom_field(company, 'functie_category', value)


    def set_cp_status(self, company, value):
        # 2.2 CP status -> 'ja', 'nee', 'pending'
        allowed_values = ['ja', 'nee', 'pending']
        if value not in allowed_values:
            print("skipping cp_status, invalued value=", value)
            return company

        return self.set_custom_field(company, 'cp_status', value)

    def set_intentieverklaring(self, company, value):
        # 2.3 intentieverklaring -> 'ingevuld', 'pending'
        # we also allow clearing it by passing None here
        allowed_values = ['ingevuld', 'pending', None]

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

    def get_existing_addenda(self, company):
        addenda = self.get_custom_field(company, 'swo_addenda')
        if not addenda:
            return []
        return addenda
