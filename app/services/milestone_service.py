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


    def set_facturatienaam(self, company, facturatienaam):
        if 'addresses' not in company.keys():
            company['addresses'] = []

        fnSaved = False
        for tad in company['addresses']:
            if tad['type'] == 'invoicing':
                fnSaved = True
                tad['address']['addressee'] = facturatienaam

        if not fnSaved:
            print(f"warning: facturatienaam {facturatienaam} could not be saved")

        return company

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
            company['business_type'] = btype_mapping.get(bedrijfsvorm)
            print(
                "DEBUG: bedrijfsvorm found=", bedrijfsvorm,
                " -> business_type=", company['business_type']
            )

        return company

    # is deprecated, gaan we niet meer syncen.
    # def orgtype_update(self, document_body, company):
    #     otype_mapping = {
    #         'archief': 'CUL - archief',
    #         'erfgoedbibliotheek': 'CUL - erfgoedbibliotheek',
    #         'erfgoedcel': 'CUL - erfgoedcel',
    #         'kunstenorganisatie': 'CUL - kunstenorganisatie',
    #         'mediabedrijf': 'MED - mediabedrijf',
    #         'museum': 'CUL - museum (erkend)',  # niet erkend is er ook!
    #         'regionale_omroep': 'MED - regionale omroep',
    #         'sectorinstituut': 'ALG - sectororganisatie',
    #         'overheidsinstelling': 'OVH - overheidsdienst'
    #     }

    #     dvals = document_body.document.document.value
    #     if 'adres_en_contactgegevens' in dvals:
    #         ac = dvals['adres_en_contactgegevens']
    #         if 'type_organisatie' in ac:
    #             type_organisatie = ac['type_organisatie']['selectedOption']
    #             tl_orgtype = otype_mapping[type_organisatie]

    #             company = self.set_type_organisatie(company, tl_orgtype)
    #             print(
    #                 "DEBUG: type organisatie found =", type_organisatie,
    #                 "mapped value=",
    #                 self.get_custom_field(company, 'type_organisatie')
    #             )

    #     return company

    def update_company_email(self, company, mail_type, mail_value):
        cp_mails = company['emails']
        typeFound = False
        if 'emails' not in company:
            company['emails'] = []

        for m in cp_mails:
            if m['type'] == mail_type:
                typeFound = True
                m['email'] = mail_value

        if not typeFound:
            company['emails'].append({
                'type': mail_type,
                'email': mail_value
            })

        return company

    def update_company_phone(self, company, phone_number):
        cp_phones = company['telephones']
        phoneNumberFound = False
        if 'telephones' not in company:
            company['telephones'] = []

        for p in cp_phones:
            if p['type'] == 'phone':
                phoneNumberFound = True
                p['number'] = phone_number

        if not phoneNumberFound:
            company['telephones'].append({
                'type': 'phone',
                'number': phone_number
            })

        return company

    def algemeen_update(self, document_body, company):
        # update email, telefoon, website, btwnummer
        dvals = document_body.document.document.value
        if 'adres_en_contactgegevens' not in dvals:
            return company  # no things to update

        ac = dvals['adres_en_contactgegevens']

        if 'algemeen_emailadres' in ac:
            company = self.update_company_email(
                company,
                'primary',
                ac['algemeen_emailadres']
            )

        if 'facturatie_emailadres' in ac:
            company = self.set_facturatie_email(
                company, ac['facturatie_emailadres']
            )

        if 'algemeen_telefoonnummer' in ac:
            company = self.update_company_phone(
                company,
                ac['algemeen_telefoonnummer']
            )

        if 'website' in ac:
            company['website'] = ac['website']

        if 'btwnummer' in ac:
            vat_number = ac['btwnummer'].upper()
            if 'BE' not in vat_number:
                vat_number = "BE {}".format(vat_number)
            company['vat_number'] = vat_number

        if 'is_de_facturatienaam_verschillend_van_de_organisatienaam' in ac:
            fverschil = ac['is_de_facturatienaam_verschillend_van_de_organisatienaam']
            if fverschil.get('selectedOption') == 'ja':
                company = self.set_facturatienaam(
                    company,
                    fverschil['facturatienaam']
                )

        if 'werkt_uw_organisatie_met_bestelbonnen_voor_de_facturatie' in ac:
            bestelbon_select = ac['werkt_uw_organisatie_met_bestelbonnen_voor_de_facturatie']
            bestelbon_value = bestelbon_select.get('selectedOption')
            if bestelbon_value:
                if bestelbon_value == 'ja':
                    company = self.set_bestelbon(company, True)
                else:
                    company = self.set_bestelbon(company, False)

        return company

    def contacts_update(self, document_body, company):
        dvals = document_body.document.document.value
        ac = dvals['adres_en_contactgegevens']
        if not ac:
            print("geen adres_en_contactgegevens aanwezig in document...")
            return company

        category_map = {
            'administratie': 'administratie',
            'archief_of_collectiebeheer': 'archief ofcollectiebeheer',
            'beleid': 'beleid',
            'management': 'management',
            'marketing__communicatie': 'marcom',
            'mediaproductie': 'mediaproductie',
            'onderzoek': 'kennis/onderzoek',
            'publiekswerking_of_educatie': 'publiekswerking',
            'directie': 'directie'
        }

        cdirect = ac['gegevens_directie']
        # strange here: naam_1 but voornaam does not have underscore ???
        cp_directie = {
            'naam': cdirect.get('naam_1'),
            'voornaam': cdirect.get('voornaam'),
            'email': cdirect.get('email'),
            'functie_categorie': category_map.get(
                cdirect.get('functietitel')
            ),
            'relatie_meemoo': 'contactpersoon contract'
        }
        company = self.set_relatie_meemoo(company, cp_directie['relatie_meemoo'])
        company = self.set_functie_category(company, cp_directie['functie_categorie'])
        print("TODO: save contact directie = ", cp_directie)


        # "centrale_contactpersoon_van_de_organisatie_voor_het_afsluiten_van_de_contracten_verschillend_van_de_directie": {
        #     "selectedOption": "ja_5",
        #     "centrale_contactpersoon_van_de_organisatie_voor_het_afsluiten_van_de_contracten": {
        #       "naam_2": "Tine",
        #       "voornaam_1": "Administratie",
        #       "email_1": "administratie@testorganisatievoorwalter.be",
        #       "telefoonnummer_1": "03 456 79 78",
        #       "functie": "administratie",
        #       "functiecategorie": {
        #         "selectedOption": "marketing__communicatie"
        #       }
        #     }
        #   },


        cdienst = ac['contactpersoon_dienstverlening']
        # "naam_5": "Tine",
        #     "voornaam_5": "Extra 1",
        #     "emailadres_5": "extra1@testorganisatievoorwalter.be",
        #     "telefoonnummer_5": "09 345 67 89",
        #     "functietitel_5": "extra1",
        #     "naam_6": "Tine",
        #     "voornaam_6": "Extra 2",
        #     "emailadres_6": "extra2@testorganisatievoorwalter.be",
        #     "telefoonnummer_6": "04 567 34 45",
        #     "functietitel_6": "extra2"
        cp_administratie = {
            'naam': cdienst.get('naam_5'),
            'voornaam': cdienst.get('voornaam_5'),
            'email': cdienst.get('emailadres_5'),
            'telephone': cdienst.get('telefoonnummer_5'),
            'telephone2': cdienst.get('telefoonnummer_6'),
            'relatie_meemoo': 'contactpersoon contact'
        }

        if cdienst.get('functietitel_5'):
            cp_administratie['functie_categorie'] = category_map.get(
                cdienst.get('functietitel_5')
            )

        if cdienst.get('functietitel_6'):
            # wat hiermee ???
            cp_administratie['functie_categorie_tweede'] = category_map.get(
                cdienst.get('functietitel_6')
            )

        print("TODO: save contact administratie = ", cp_administratie)

        # if cdienst.get('naam_5'):
        #     __import__('pdb').set_trace()

        return company

    def update_company_using_dossier(self, company, dossier_id):
        try:
            mdoc_json = self.redis.load_document(dossier_id)
            mdoc = DocumentBody.parse_raw(mdoc_json)

            company = self.bedrijfsnaam_update(mdoc, company)
            company = self.bedrijfsvorm_update(mdoc, company)
            # company = self.orgtype_update(mdoc, company)  # niet meer syncen!
            company = self.addresses_update(mdoc, company)
            company = self.algemeen_update(mdoc, company)

            # contacts update also sets invoice adress adressee
            company = self.contacts_update(mdoc, company)

        except ValidationError as e:
            print(
                f"Missing or malformed dossier for milestone company_update: {self.dossier.id} error: {e}")

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
