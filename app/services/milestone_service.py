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

        self.category_map = {
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

    def set_company_status(self, company, cp_status, intentie, toestemming):
        company = self.set_cp_status(company, cp_status)
        company = self.set_intentieverklaring(company, intentie)
        company = self.set_toestemming_start(company, toestemming)
        return company

    def status_geen_interesse(self, company):
        return self.set_company_status(company, 'nee', 'ingevuld', False)

    def status_misschien_later(self, company):
        return self.set_company_status(company, 'pending', 'pending', False)

    def status_akkoord(self, company):
        return self.set_company_status(company, 'ja', 'ingevuld', True)

    def status_akkoord_geen_start(self, company):
        return self.set_company_status(company, 'ja', 'ingevuld', False)

    def status_interesse(self, company):
        return self.set_company_status(company, 'pending', 'pending', False)

    def status_update(self, company, milestone_status):
        status_actions = {
            'Geen interesse': self.status_geen_interesse,
            'Misschien later samenwerking': self.status_misschien_later,
            'Akkoord en opstart': self.status_akkoord,
            'Akkoord, geen opstart': self.status_akkoord_geen_start,
            'Interesse, niet akkoord SWO': self.status_interesse
        }

        if milestone_status not in status_actions:
            # this case happens for "SWO niet akkoord" and "SWO akkoord"
            # return false -> we don't need teamleader update
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
            print(
                f"warning: facturatienaam {facturatienaam} could not be saved")

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

    # orgtype_update is deprecated (op aanvraag Tine)
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

    def upsert_contact(self, company, existing_contacts, contact):
        # pop some fields that need different location of storing in teamleader
        primary_email = contact.pop('email')
        functie_categorie = contact.pop('functie_categorie')
        relaties_meemoo = contact.pop('relaties_meemoo')
        position = contact.pop('position')
        phone_number = contact.pop('phone')

        # check if contact already exists by searching primary email
        new_contact = True

        for ec in existing_contacts:
            if ec.get('emails') and len(ec.get('emails')) > 0:
                for em in ec.get('emails'):
                    if em['type'] == 'primary' and em['email'] == primary_email:
                        new_contact = False
                        contact = ec

        if new_contact:
            contact['custom_fields'] = []
            contact['emails'] = []
            contact['emails'].append({
                'type': 'primary',
                'email': primary_email
            })

        contact = self.set_relatie_meemoo(contact, relaties_meemoo)
        contact = self.set_functie_category(contact, functie_categorie)

        if phone_number:
            updated_phone = False
            if contact.get('telephones'):
                if len(contact.get('telephones')) > 0:
                    for p in contact.get('telephones'):
                        if p['type'] == 'phone':
                            p['number'] = phone_number
                            updated_phone = True
            else:
                contact['telephones'] = []

            if not updated_phone:
                contact['telephones'].append({
                    'type': 'phone',
                    'number': phone_number
                })

        if new_contact:
            print("adding company contact {} {}".format(
                position, primary_email
            ))
            contact_response = self.tlc.add_contact(contact)
            self.tlc.link_to_company({
                'id': contact_response['id'],
                'company_id': company['id'],
                'position': position
                # 'decision_maker': True/False?
            })
        else:
            print("updating company contact {} {} {}".format(
                contact['id'], position, primary_email
            ))
            self.tlc.update_contact(contact)
            self.tlc.update_company_link({
                'id': contact['id'],
                'company_id': company['id'],
                'position': position
                # 'decision_maker': True or False here?
            })

    def upsert_directie_contact(self, company, existing_contacts, contactgegevens):
        # if contact already exists, update it, otherwise create it
        cdirect = contactgegevens['gegevens_directie']
        position = cdirect.get('functietitel')
        cp_directie = {
            'first_name': cdirect.get('voornaam'),
            'last_name': cdirect.get('naam_1'),
            'email': cdirect.get('email'),
            'functie_categorie': self.category_map.get(position),
            'relaties_meemoo': ['contactpersoon contract'],
            'position': position,
            'phone': None
        }

        # TODO: append to relaties_meemoo
        # contactpersoon digitalisering, contactpersoon instroom...
        self.upsert_contact(company, existing_contacts, cp_directie)

    def upsert_administratie_contact(self, company, existing_contacts, contactgegevens):
        # if contact already exists, update it, otherwise create it
        # administratie contact aanmaken of updaten
        cp_admin = contactgegevens['centrale_contactpersoon_van_de_organisatie_voor_het_afsluiten_van_de_contracten_verschillend_van_de_directie']  # noqa: E501

        if cp_admin.get('selectedOption') != 'ja_5':
            print("skipping administratie contact, because it's not selected")
            return

        cadmin = cp_admin['centrale_contactpersoon_van_de_organisatie_voor_het_afsluiten_van_de_contracten']  # noqa: E501
        cp_administratie = {
            'first_name': cadmin.get('voornaam_1'),
            'last_name': cadmin.get('naam_2'),
            'email': cadmin.get('email_1'),
            'functie_categorie': self.category_map.get(
                cadmin['functiecategorie']['selectedOption']
            ),
            'relaties_meemoo': ['contactpersoon contract'],
            'position': cadmin.get('functie'),
            'phone': cadmin.get('telefoonnummer_1')
        }

        # TODO: append more optional relaties_meemoo here...
        # cp_administratie['relaties_meemoo'].append(...)
        self.upsert_contact(company, existing_contacts, cp_administratie)

    def upsert_dienstverlening_contacts(self, company, existing_contacts, contactgegevens):
        # dienstverlening 2 extra contacten aanmaken of updaten
        cdienst = contactgegevens['contactpersoon_dienstverlening']
        cp_dienst_eerste = {
            'first_name': cdienst.get('voornaam_5'),
            'last_name': cdienst.get('naam_5'),
            'email': cdienst.get('emailadres_5'),
            'functie_categorie': self.category_map.get(cdienst.get('functietitel_5')),
            'relaties_meemoo': ['contactpersoon contract'],
            'position': cdienst.get('functietitel_5'),
            'phone': cdienst.get('telefoonnummer_5')
        }

        # TODO: append relaties here...
        # cp_dienst_eerste['relaties_meemoo'].append...
        self.upsert_contact(company, existing_contacts, cp_dienst_eerste)

        cp_dienst_tweede = {
            'first_name': cdienst.get('voornaam_6'),
            'last_name': cdienst.get('naam_6'),
            'email': cdienst.get('emailadres_6'),
            'functie_categorie': self.category_map.get(cdienst.get('functietitel_6')),
            'relaties_meemoo': ['contactpersoon contract'],
            'position': cdienst.get('functietitel_6'),
            'phone': cdienst.get('telefoonnummer_6')
        }

        # TODO: append relaties here...
        # cp_dienst_tweede['relaties_meemoo'].append...
        self.upsert_contact(company, existing_contacts, cp_dienst_tweede)

    def contacts_update(self, document_body, company):
        dvals = document_body.document.document.value
        contactgegevens = dvals['adres_en_contactgegevens']
        if not contactgegevens:
            print("geen adres_en_contactgegevens aanwezig in document...")
            return company

        existing_contacts = self.tlc.company_contacts(company['id'])

        self.upsert_directie_contact(
            company, existing_contacts, contactgegevens
        )
        self.upsert_administratie_contact(
            company, existing_contacts, contactgegevens
        )
        self.upsert_dienstverlening_contacts(
            company, existing_contacts, contactgegevens
        )

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
                company, self.dossier.id
            )
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
