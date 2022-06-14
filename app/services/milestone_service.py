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
from pydantic import ValidationError


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
                if ladres == {}:
                    return None

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
                if fadres == {}:
                    return None

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
        # skryv has no 'country' in address, assume belgium
        updated_address['address']['country'] = 'BE'

        if 'postbus_naam' in skryv_address:
            updated_address['address']['addressee'] = skryv_address['postbus_naam']

        # TODO: see if we can somehow fill in this extra teamleader field:
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

    def bedrijfsnaam_update(self, document_body, company):
        dvals = document_body.document.document.value
        if 'officile_naam_organisatie' in dvals:
            bedrijfsnaam = dvals['officile_naam_organisatie']
            company['name'] = bedrijfsnaam

        return company

    def bedrijfsvorm_update(self, document_body, company):
        btype_mapping = {
            'ag': 'AG',
            'bvba': 'BVBA',
            'cvba': 'CVBA',
            'cvoa': 'CVOA',
            'comm.v': 'Comm.V',
            'comm.va': 'Comm.VA',
            'esv': 'ESV',
            'ebvba': 'EBVBA',
            'eenmanszaak': 'Eenmanszaak',
            'lv': 'LV',
            'nv': 'NV',
            'sbvba': 'SBVBA',
            'se': 'SE',
            'vof': 'VOF',
            'vzw': 'VZW',
            'vereniging': 'Vereniging',
            'overige': None
        }

        dvals = document_body.document.document.value
        if 'bedrijfsvorm' in dvals:
            bedrijfsvorm = dvals['bedrijfsvorm']['selectedOption']
            company['business_type'] = btype_mapping.get('bedrijfsvorm')
            print(
                "DEBUG: bedrijfsvorm found=", bedrijfsvorm,
                " -> business_type=", company['business_type']
            )

        return company

    def orgtype_update(self, document_body, company):
        otype_mapping = {
            'archief': 'CUL - archief',
            'erfgoedbibliotheek': 'CUL - erfgoedbibliotheek',
            'erfgoedcel': 'CUL - erfgoedcel',
            'kunstenorganisatie': 'CUL - kunstenorganisatie',
            'mediabedrijf': 'MED - mediabedrijf',
            'museum': 'CUL - museum (erkend)',  # niet erkend is er ook!
            'regionale_omroep': 'MED - regionale omroep',
            'sectorinstituut': 'ALG - sectororganisatie',
            'overheidsinstelling': 'OVH - overheidsdienst'
        }

        dvals = document_body.document.document.value
        if 'adres_en_contactgegevens' in dvals:
            ac = dvals['adres_en_contactgegevens']
            if 'type_organisatie' in ac:
                type_organisatie = ac['type_organisatie']['selectedOption']
                tl_orgtype = otype_mapping[type_organisatie]

                company = self.set_type_organisatie(company, tl_orgtype)
                print(
                    "DEBUG: type organisatie found =", type_organisatie,
                    "mapped value=",
                    self.get_custom_field(company, 'type_organisatie')
                )

        return company

    def algemeen_update(self, document_body, company):
        # update email, telefoon, website, btwnummer
        dvals = document_body.document.document.value
        if 'adres_en_contactgegevens' in dvals:
            ac = dvals['adres_en_contactgegevens']

            if 'algemeen_emailadres' in ac:
                cp_mails = company['emails']
                primaryFound = False
                if 'emails' not in company:
                    company['emails'] = []

                for m in cp_mails:
                    if m['type'] == 'primary':
                        primaryFound = True
                        m['email'] = ac['algemeen_emailadres']

                if not primaryFound:
                    company['emails'].append({
                        'type': 'primary',
                        'email': ac['algemeen_emailadres']
                    })

            if 'algemeen_telefoonnummer' in ac:
                cp_phones = company['telephones']
                phoneNumberFound = False
                if 'telephones' not in company:
                    company['telephones'] = []

                for p in cp_phones:
                    if p['type'] == 'phone':
                        phoneNumberFound = True
                        p['number'] = ac['algemeen_telefoonnummer']

                if not phoneNumberFound:
                    company['telephones'].append({
                        'type': 'phone',
                        'number': ac['algemeen_telefoonnummer']
                    })

            if 'website' in ac:
                company['website'] = ac['website']

            if 'btwnummer' in ac:
                company['vat_number'] = ac['btwnummer']

        return company

    def contacts_update(self, document_body, company):
        print(f"TODO: Contacts update here on document={document_body}")
        return company

    def update_company_using_dossier(self, company, dossier_id):
        try:
            mdoc_json = self.redis.load_document(dossier_id)
            mdoc = DocumentBody.parse_raw(mdoc_json)

            company = self.bedrijfsnaam_update(mdoc, company)
            company = self.bedrijfsvorm_update(mdoc, company)
            company = self.orgtype_update(mdoc, company)
            company = self.addresses_update(mdoc, company)
            company = self.algemeen_update(mdoc, company)
            # TODO: facturatienaam
            # TODO: facturatie email adres
            # TODO: bestelbonnen
            company = self.contacts_update(mdoc, company)

        except ValidationError as e:
            print(f"Missing or malformed dossier for milestone company_update: {self.dossier.id} error: {e}")

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
            self.slack.company_not_found(company_id, self.or_id)

        status_changed, company = self.status_update(
            company,
            self.milestone.status
        )

        if status_changed:
            print(
                "milestone teamleader update: or-id={}, company={}, milestone status={} action={}".format(
                    self.or_id,
                    company['id'],
                    self.milestone.status,
                    self.action
                )
            )

            company = self.update_company_using_dossier(
                company, self.dossier.id)
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
