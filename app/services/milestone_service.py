#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  @Author: Walter Schreppers
#
#   app/services/milestone_service.py
#
#   MilestoneService, handle milestone webhook events
#

from app.models.milestone_body import MilestoneBody
from app.models.document_body import DocumentBody
from app.services.skryv_base import SkryvBase


class MilestoneService(SkryvBase):
    def __init__(self, common_clients):
        self.tlc = common_clients.teamleader
        self.ldap = common_clients.ldap
        self.slack = common_clients.slack
        self.redis = common_clients.redis
        self.read_configuration()

    def status_geen_interesse(self, company):
        company = self.set_cp_status(company, 'nee')
        company = self.set_intentieverklaring(company, 'ingevuld')
        company = self.set_toestemming_start(company, False)
        return company

    def status_misschien_later(self, company):
        company = self.set_cp_status(company, 'pending')
        company = self.set_intentieverklaring(company, 'pending')
        company = self.set_toestemming_start(company, False)
        return company

    def status_akkoord(self, company):
        company = self.set_cp_status(company, 'ja')
        company = self.set_intentieverklaring(company, 'ingevuld')
        company = self.set_toestemming_start(company, True)
        return company

    def status_akkoord_geen_start(self, company):
        company = self.set_cp_status(company, 'ja')
        company = self.set_intentieverklaring(company, 'ingevuld')
        company = self.set_toestemming_start(company, False)
        return company

    def status_interesse(self, company):
        company = self.set_cp_status(company, 'pending')
        company = self.set_intentieverklaring(company, 'pending')
        company = self.set_toestemming_start(company, False)
        return company

    def get_skryv_postadres(self, document_body):
        dvals = document_body.document.document.value
        if 'adres_en_contactgegevens' in dvals:
            if 'postadres' in dvals['adres_en_contactgegevens']:
                return dvals['adres_en_contactgegevens']['postadres']

    def get_skryv_laadadres(self, document_body):
        dvals = document_body.document.document.value
        if 'adres_en_contactgegevens' in dvals:
            ac = dvals['adres_en_contactgegevens']
            if 'laadadres_verschillend_van_postadres' in ac:
                ld = ac['laadadres_verschillend_van_postadres']
                ladres = ld['laadadres']
                # skryv has an anoying _2 here
                skryv_address = {
                    'straat': ladres['straat_2'],
                    'huisnummer': ladres['huisnummer_2'],
                    'postcode': ladres['postcode_2'],
                    'gemeente': ladres['gemeente_2']
                }

                # if is_de_laadnaam_Verschillend...
                # skryv_address['postbus_naam'] = ...
                return skryv_address

    def get_skryv_facturatieadres(self, document_body):
        dvals = document_body.document.document.value
        if 'adres_en_contactgegevens' in dvals:
            ac = dvals['adres_en_contactgegevens']
            if 'facturatieadres_verschillend_van_postadres' in ac:
                fd = ac['facturatieadres_verschillend_van_postadres']
                fadres = fd['facturatieadres']
                # skryv has an anoying _1 here
                skryv_address = {
                    'straat': fadres['straat_1'],
                    'huisnummer': fadres['huisnummer_1'],
                    'postcode': fadres['postcode_1'],
                    'gemeente': fadres['gemeente_1']
                }

                if 'is_de_facturatienaam_verschillend_van_de_organisatienaam' in ac:
                    fact_options = ac['is_de_facturatienaam_verschillend_van_de_organisatienaam']
                    if 'ja' in fact_options['selectedOption']:
                        skryv_address['postbus_naam'] = fact_options['facturatienaam']

                return skryv_address

    def update_teamleader_address(self, company, address_type, skryv_address):
        # adress types : primary, delivery, invoicing
        if not skryv_address or skryv_address == {}:
            # skip if skryv adres was empty
            return company

        updated_address = {
            'type': address_type,
            'address': {}
        }
        updated_address['address']['line_1'] = '{} {}'.format(
            skryv_address['straat'],
            skryv_address['huisnummer']
        )
        updated_address['address']['postal_code'] = skryv_address['postcode']
        updated_address['address']['city'] = skryv_address['gemeente']
        # skryv has no 'country' in address
        updated_address['address']['country'] = 'BE'

        if 'postbus_naam' in skryv_address:
            updated_address['address']['addressee'] = skryv_address['postbus_naam']

        # TODO: see if we can somehow fill in these teamleader fields:
        # updated_address['address']['area_level_two'] = null

        if 'addresses' not in company.keys():
            company['addresses'] = []

        address_was_updated = False
        for tad in company['addresses']:
            if tad['type'] == updated_address['type']:
                tad['address'] = updated_address['address']
                address_was_updated = True

        if not address_was_updated:
            company['addresses'].append(updated_address)

        return company

    def status_update(self, company, milestone_status):
        status_actions = {
            'Geen interesse': self.status_geen_interesse,
            'Misschien later samenwerking': self.status_misschien_later,
            'Akkoord en opstart': self.status_akkoord,
            'Akkoord, geen opstart': self.status_akkoord_geen_start,
            'Interesse, niet akkoord SWO': self.status_interesse
        }

        if milestone_status not in status_actions:
            # this happens for "SWO niet akkoord" and "SWO akkoord"
            print(f"ignoring milestone status update for  {milestone_status}")
            return (False, company)

        perform_status_update = status_actions.get(milestone_status)
        company = perform_status_update(company)
        return (True, company)

    def addresses_update(self, document_body, company):
        company = self.update_teamleader_address(
            company,
            'primary',
            self.get_skryv_postadres(document_body)
        )

        company = self.update_teamleader_address(
            company,
            'delivery',
            self.get_skryv_laadadres(document_body)
        )

        company = self.update_teamleader_address(
            company,
            'invoicing',
            self.get_skryv_facturatieadres(document_body)
        )

        return company

    def contacts_update(self, document_body, company):
        print(f"TODO: Contacts update here on document={document_body}")
        return company

    def teamleader_update(self):
        if self.dossier.dossierDefinition != self.SKRYV_DOSSIER_CP_ID:
            print(
                f"{self.dossier.dossierDefinition} is not a content partner milestone, skipping milestone event")
            return

        ldap_org = self.ldap.find_company(self.or_id)
        if not ldap_org:
            self.slack.no_ldap_entry_found(self.dossier)
            return

        company_id = ldap_org['x-be-viaa-externalUUID'].value
        company = self.tlc.get_company(company_id)
        if not company:
            # TODO: make slack message here
            print(
                f"ERROR: company id={company_id} not found in teamleader for org {self.or_id}")
            return

        status_changed, company = self.status_update(
            company, self.milestone.status)

        if status_changed:
            print(
                "milestone teamleader update: or-id={}, company={}, milestone status={} action={}".format(
                    self.or_id,
                    company['id'],
                    self.milestone.status,
                    self.action
                )
            )
            mdoc_json = self.redis.load_document(self.dossier.id)
            if mdoc_json:
                mdoc = DocumentBody.parse_raw(mdoc_json)
                company = self.addresses_update(mdoc, company)
                company = self.contacts_update(mdoc, company)
            else:
                print(
                    f"milestone: no associated dossier found for id={self.dossier.id}")

            self.tlc.update_company(company)

    def handle_event(self, milestone_body: MilestoneBody):
        self.body = milestone_body
        self.action = self.body.action
        self.dossier = self.body.dossier
        self.milestone = self.body.milestone
        self.or_id = self.dossier.externalId

        if(self.or_id):
            self.teamleader_update()
        else:
            self.slack.external_id_empty(self.dossier)
